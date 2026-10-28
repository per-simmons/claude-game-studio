#!/usr/bin/env bash
# runpod-blender-render.sh — render a .blend with Cycles on a throwaway RunPod GPU pod, then TERMINATE it.
#
# USAGE
#   runpod-blender-render.sh <scene.blend> <frames> [outdir]
#     <frames>  Blender -f syntax: "1..2", "1,5,9", "10"  (or "anim" to use -a)
#     [outdir]  local dir for PNGs + logs (default: ./runpod-out-<timestamp>)
#
# ENV (all optional)
#   RUNPOD_ENV_FILE   file to source for RUNPOD_API_KEY (optional; otherwise RUNPOD_API_KEY must already be set)
#   GPU_IDS           comma list tried in order (default: 4090,3090,A5000,A4500,A4000,4000 Ada — full RunPod ids)
#   CLOUD_TYPES       clouds tried in order (default "COMMUNITY,SECURE"); every GPU in a cloud before the next
#   MAX_PRICE         $/hr ceiling; GPUs priced above are skipped (default 0.40)
#   MAX_MINUTES       hard wall-clock cap; watchdog kills the run and terminates the pod (default 20)
#   BLENDER_VERSION   Linux tarball fetched on the pod (default 5.1.2; match your local Blender)
#   CYCLES_DEVICE     OPTIX (default) | CUDA   (render.py falls back OPTIX->CUDA automatically)
#   DISK_GB           container disk (default 20)
#   EXTRA_FILES       space-separated local paths uploaded next to the .blend (textures, caches...)
#   KEEP_POD=1        do NOT terminate at exit (debug only — you pay until you remove it)
#
# GUARDRAILS
#   * price ceiling checked against the live GraphQL price before create
#   * pod is created with --terminate-after (server-side kill at MAX_MINUTES+10) as a backstop
#   * local watchdog sends SIGTERM to this script after MAX_MINUTES
#   * trap on EXIT/INT/TERM/HUP: pod stop + pod delete of ONLY the pod this script created; verifies gone
#
# REQUIRES  runpodctl >= 2.3, ssh/scp, python3, an account SSH key (~/.runpod/ssh/runpodctl-ssh-key)
# Output frames: <outdir>/frames/frame_####.png ; logs: <outdir>/run.log, <outdir>/blender.log
set -uo pipefail

BLEND=${1:?usage: runpod-blender-render.sh <scene.blend> <frames> [outdir]}
FRAMES=${2:?frames e.g. 1..2}
OUT=${3:-./runpod-out-$(date +%Y%m%d-%H%M%S)}
HERE=$(cd "$(dirname "$0")" && pwd)
RENDER_PY="$HERE/render.py"
export PATH=/opt/homebrew/bin:$PATH

ENVF=${RUNPOD_ENV_FILE:-}
if [ -z "${RUNPOD_API_KEY:-}" ] && [ -n "$ENVF" ] && [ -f "$ENVF" ]; then set -a; . "$ENVF"; set +a; fi
[ -n "${RUNPOD_API_KEY:-}" ] || { echo "no RUNPOD_API_KEY" >&2; exit 2; }

GPU_IDS=${GPU_IDS:-"NVIDIA GeForce RTX 4090,NVIDIA GeForce RTX 3090,NVIDIA RTX A5000,NVIDIA RTX A4500,NVIDIA RTX A4000,NVIDIA RTX 4000 Ada Generation"}
CLOUD_TYPES=${CLOUD_TYPES:-COMMUNITY,SECURE}
MAX_PRICE=${MAX_PRICE:-0.40}
MAX_MINUTES=${MAX_MINUTES:-20}
BLENDER_VERSION=${BLENDER_VERSION:-5.1.2}
CYCLES_DEVICE=${CYCLES_DEVICE:-OPTIX}
DISK_GB=${DISK_GB:-20}
SSH_KEY=${SSH_KEY:-$HOME/.runpod/ssh/runpodctl-ssh-key}
BV_MAJMIN=$(echo "$BLENDER_VERSION" | cut -d. -f1,2)
BLENDER_URL="https://download.blender.org/release/Blender${BV_MAJMIN}/blender-${BLENDER_VERSION}-linux-x64.tar.xz"

[ -f "$BLEND" ] || { echo "no such blend: $BLEND" >&2; exit 2; }
[ -f "$RENDER_PY" ] || { echo "render.py must sit next to this script" >&2; exit 2; }
mkdir -p "$OUT/frames"; OUT=$(cd "$OUT" && pwd)
LOG="$OUT/run.log"; : > "$LOG"
log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG" >&2; }
POD_NAME="blender-render-$$-$(date +%s)"
T0=$(date +%s); POD_ID=""; PRICE=0; T_CREATE=0

if pgrep -x "${RECORDER_PROCESS:-obs}" >/dev/null 2>&1; then log "NOTE: a screen recorder is running; fine, all compute is remote."; fi

gql(){ curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $RUNPOD_API_KEY" \
         https://api.runpod.io/graphql -d "$1"; }

# ---------- teardown (always) ----------
cleanup(){
  rc=$?
  trap - EXIT; trap '' INT TERM HUP   # teardown must not be interrupted
  [ -n "${WATCHDOG_PID:-}" ] && kill "$WATCHDOG_PID" 2>/dev/null
  # catch a pod created but not yet recorded (killed mid-create): match our unique name
  if [ -z "$POD_ID" ]; then
    POD_ID=$(runpodctl pod list 2>/dev/null | python3 -c "import json,sys
try: print(' '.join(p['id'] for p in json.load(sys.stdin) if p.get('name')=='$POD_NAME'))
except Exception: print('')")
  fi
  if [ -n "$POD_ID" ]; then
    if [ "${KEEP_POD:-0}" = 1 ]; then log "KEEP_POD=1 — leaving $POD_ID running (YOU ARE BEING BILLED)"; else
      log "teardown: stopping + deleting pod $POD_ID"
      runpodctl pod stop "$POD_ID" >>"$LOG" 2>&1
      for i in 1 2 3 4 5; do
        runpodctl pod delete "$POD_ID" >>"$LOG" 2>&1 && break; sleep 3
      done
      if runpodctl pod list 2>/dev/null | grep -q "\"$POD_ID\""; then
        log "!!! pod $POD_ID STILL LISTED — remove it manually: runpodctl pod delete $POD_ID"; rc=9
      else log "verified: pod $POD_ID no longer in pod list"; fi
    fi
    T1=$(date +%s)
    python3 -c "s=$T1-$T_CREATE; p=$PRICE; print(f'pod lifetime {s}s at \${p}/hr ~= \${s/3600*p:.4f} (+ small disk)')" | tee -a "$LOG" >&2
  fi
  log "total wall time $(( $(date +%s) - T0 ))s, exit $rc"
  exit $rc
}
trap cleanup EXIT
trap 'exit 143' TERM; trap 'exit 130' INT; trap 'exit 129' HUP   # signals -> EXIT trap with non-zero rc

# ---------- watchdog ----------
( sleep $((MAX_MINUTES*60)); echo "[watchdog] ${MAX_MINUTES}m cap hit — terminating" >>"$LOG"; kill -TERM $$; pkill -TERM -P $$ ) &
WATCHDOG_PID=$!

# ---------- pick GPU under price ceiling ----------
PRICES=$(gql '{"query":"query { gpuTypes { id communityPrice securePrice } }"}')
price_of(){ echo "$PRICES" | python3 -c "
import json,sys; g={x['id']:x for x in json.load(sys.stdin)['data']['gpuTypes']}
x=g.get(sys.argv[1]); print((x or {}).get('communityPrice' if sys.argv[2]=='COMMUNITY' else 'securePrice') or 0)" "$1" "$2"; }

TERM_AT=$(date -u -v+$((MAX_MINUTES+10))M +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d "+$((MAX_MINUTES+10)) min" +%Y-%m-%dT%H:%M:%SZ)
IFS=',' read -ra GPUS <<<"$GPU_IDS"
IFS=',' read -ra CLOUDS <<<"$CLOUD_TYPES"
for C in "${CLOUDS[@]}"; do
 [ -n "$POD_ID" ] && break
 for G in "${GPUS[@]}"; do
  P=$(price_of "$G" "$C")
  if python3 -c "import sys; sys.exit(0 if 0 < $P <= $MAX_PRICE else 1)"; then :; else
    log "skip $C $G: price \$$P/hr vs ceiling \$$MAX_PRICE"; continue; fi
  PUB=(); [ "$C" = COMMUNITY ] && PUB=(--public-ip)   # community needs a public-IP host for scp; secure has one
  log "creating $C pod on $G (\$$P/hr), terminate-after $TERM_AT"
  RES=$(runpodctl pod create --name "$POD_NAME" --template-id runpod-ubuntu-2404 \
        --gpu-id "$G" --gpu-count 1 --cloud-type "$C" --container-disk-in-gb "$DISK_GB" \
        --ports "22/tcp" ${PUB[@]+"${PUB[@]}"} --terminate-after "$TERM_AT" \
        --env '{"NVIDIA_DRIVER_CAPABILITIES":"all"}' 2>&1)
  echo "$RES" | head -3 >>"$LOG"
  POD_ID=$(echo "$RES" | python3 -c "import json,sys
try: print(json.load(sys.stdin).get('id',''))
except Exception: print('')")
  if [ -n "$POD_ID" ]; then PRICE=$P; GPU="$G ($C)"; T_CREATE=$(date +%s); break; fi
  log "create failed on $C $G: $(echo "$RES" | head -1 | head -c 200)"
 done
done
[ -n "$POD_ID" ] || { log "could not create a pod on any GPU in [$GPU_IDS] under \$$MAX_PRICE/hr"; exit 4; }
log "pod $POD_ID created on $GPU"

# ---------- wait for public IP + SSH port ----------
IP=""; PORT=""
while :; do
  # NOTE: `runpodctl pod get` (2.3.0) returns publicIp/portMappings = null even once mapped; REST has them.
  J=$(curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" "https://rest.runpod.io/v1/pods/$POD_ID")
  read -r IP PORT < <(echo "$J" | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: print('', ''); sys.exit()
ip=d.get('publicIp') or ''; pm=d.get('portMappings') or {}
port=pm.get('22') or pm.get(22) or ''
if not (ip and port):
  rt=(d.get('runtime') or {});
  for p in (rt.get('ports') or []):
    if p.get('privatePort')==22 and p.get('isIpPublic'): ip, port = p['ip'], p['publicPort']
print(ip or '', port or '')")
  [ -n "$IP" ] && [ -n "$PORT" ] && break
  sleep 5
done
T_UP=$(date +%s); log "pod has $IP:$PORT after $((T_UP-T_CREATE))s"
SSHO=(-i "$SSH_KEY" -p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -o ServerAliveInterval=15 -o LogLevel=ERROR)
SCPO=(-i "$SSH_KEY" -P "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR)
until ssh "${SSHO[@]}" root@"$IP" true 2>/dev/null; do sleep 5; done
log "ssh up after $(( $(date +%s)-T_CREATE ))s"
ssh "${SSHO[@]}" root@"$IP" 'nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader' | tee -a "$LOG" >&2

# ---------- install blender (background) while uploading ----------
ssh "${SSHO[@]}" root@"$IP" "set -e; mkdir -p /job/out; cd /opt
  (apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq xz-utils libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libxkbcommon0 libsm6 libice6 libegl1 >/dev/null) &
  curl -sSfL '$BLENDER_URL' -o b.tar.xz; wait
  tar -xf b.tar.xz && rm b.tar.xz && ln -sf /opt/blender-${BLENDER_VERSION}-linux-x64/blender /usr/local/bin/blender
  blender --version | head -1" >>"$LOG" 2>&1 &
INSTALL_PID=$!
scp "${SCPO[@]}" "$BLEND" "$RENDER_PY" ${EXTRA_FILES:-} root@"$IP":/job/ 2>>"$LOG" \
  || { sleep 3; ssh "${SSHO[@]}" root@"$IP" mkdir -p /job; scp "${SCPO[@]}" "$BLEND" "$RENDER_PY" ${EXTRA_FILES:-} root@"$IP":/job/ ; } || { log "upload failed"; exit 5; }
log "uploaded $(basename "$BLEND") + render.py"
wait $INSTALL_PID || { log "blender install failed (see run.log)"; tail -20 "$LOG" >&2; exit 6; }
T_READY=$(date +%s); log "blender installed $(tail -1 "$LOG") — $((T_READY-T_UP))s for deps+download"

# ---------- render ----------
B=$(basename "$BLEND")
if [ "$FRAMES" = anim ]; then FARG="-a"; else FARG="-f $FRAMES"; fi
log "render: blender -b $B -P render.py -E CYCLES -o /job/out/frame_#### -F PNG $FARG -- --cycles-device $CYCLES_DEVICE"
ssh "${SSHO[@]}" root@"$IP" "cd /job && blender -b '$B' -P render.py -E CYCLES -o /job/out/frame_#### -F PNG $FARG -- --cycles-device $CYCLES_DEVICE" >"$OUT/blender.log" 2>&1
BRC=$?
T_REND=$(date +%s); log "blender exit $BRC in $((T_REND-T_READY))s"
grep -E "\[render.py\]|Saved:|Time:|Error|FATAL" "$OUT/blender.log" | tee -a "$LOG" >&2

# ---------- fetch ----------
scp "${SCPO[@]}" "root@$IP:/job/out/*" "$OUT/frames/" 2>>"$LOG" || log "fetch failed"
ls -la "$OUT/frames" | tee -a "$LOG" >&2
[ $BRC -eq 0 ] && [ -n "$(ls "$OUT/frames" 2>/dev/null)" ] || exit 7
log "OK — frames in $OUT/frames"
exit 0
