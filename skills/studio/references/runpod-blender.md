# Headless Blender Cycles on RunPod (tested 2026-10-20)

**Script:** `scripts/runpod-blender-render.sh` with `scripts/render.py` next to it, plus
`scripts/make_test_blend.py` for a smoke scene.
**Key:** `RUNPOD_API_KEY` in your environment, or in a file named by `RUNPOD_ENV_FILE` (see `studio.config.json` → `runpod.env_file`). Never print it.
**CLI:** `runpodctl` (2.3.x) at `/opt/homebrew/bin/runpodctl`.

## Usage
```bash
# smoke test (~$0.01 at $0.22/hr; ~80 s)
blender --background --factory-startup --python scripts/make_test_blend.py -- /tmp/smoke.blend
MAX_MINUTES=20 MAX_PRICE=0.40 scripts/runpod-blender-render.sh /tmp/smoke.blend 1..2 /tmp/smoke-out

# real job: a scene's frames (or "anim"), textures packed or passed via EXTRA_FILES
MAX_MINUTES=45 MAX_PRICE=0.40 EXTRA_FILES="tex/a.png tex/b.exr" \
  scripts/runpod-blender-render.sh blender/scenes/S1.blend 1 art/final/S1
```
Output goes to `<outdir>/frames/frame_####.png`, with `run.log` and `blender.log` alongside.

**Environment knobs:**
| Variable | Default / meaning |
|---|---|
| `GPU_IDS` | 4090 → 3090 → A5000 → A4500 → A4000 → 4000 Ada |
| `CLOUD_TYPES` | `COMMUNITY,SECURE` |
| `MAX_PRICE` | $/hr ceiling |
| `MAX_MINUTES` | Watchdog cap |
| `BLENDER_VERSION` | `5.1.2`; match your local Blender |
| `CYCLES_DEVICE` | `OPTIX`, falling back to CUDA |
| `DISK_GB` | Container disk size |
| `KEEP_POD=1` | Debug only: you pay until you remove the pod |

## What happens
1. Price check: the live GPU price must be at or below `MAX_PRICE`. Each GPU is tried in order, on
   community cloud, then secure cloud.
2. Create: `runpodctl pod create --template-id runpod-ubuntu-2404 --cloud-type COMMUNITY --public-ip
   --ports 22/tcp --container-disk-in-gb 20 --terminate-after <now+cap+10m>
   --env {"NVIDIA_DRIVER_CAPABILITIES":"all"}`, using the image `runpod/base:1.0.2-ubuntu2404` (cached
   on hosts, so there's no pull wait).
3. Wait for SSH. **The IP and port come from the REST API** (`https://rest.runpod.io/v1/pods/<id>`),
   because `runpodctl pod get` returns null `publicIp` in 2.3.0.
4. `scp` the .blend, render.py and any extra files up. On the pod, install the X/GL libs and fetch the
   official Blender Linux tarball from download.blender.org.
5. Render: `blender -b scene.blend -P render.py -E CYCLES -o /job/out/frame_#### -F PNG -f <frames> --
   --cycles-device OPTIX`. render.py enables GPU devices, falls back from OptiX to CUDA, and **exits 3
   rather than render silently on the CPU** unless `ALLOW_CPU=1` is set.
6. `scp` the frames back, then teardown: **stop and delete only the pod this script created**, and
   check the list to confirm it's gone.

## Cost guardrails (never remove these)
- A price ceiling, checked before create.
- `--terminate-after`, so the pod is killed server-side even if this Mac dies.
- A local watchdog at `MAX_MINUTES`.
- A teardown trap on EXIT, INT, TERM and HUP that can't be interrupted, and a non-zero exit if the run
  was cancelled by a signal.
- Never touch other pods. The script lists them first and acts only on its own ID or name.
- No network volumes. One pod per job. Batch frames so the roughly 70 s setup is paid once.

## Smoke-test record (2026-10-20)
| Item | Result |
|---|---|
| GPU | RTX 3090, community cloud, **$0.22/hr**. The 4090 had no capacity |
| Pod creation to SSH ready | 34 s |
| Setup (libs + Blender 5.1.2) | 33 s |
| Render | 5 s: 2 frames, 640×360, 64 samples, OptiX confirmed (`device OPTIX use=True NVIDIA GeForce RTX 3090`) |
| Total wall time | 77 s |
| Session cost | About **$0.04**, almost all from one stalled attempt that exposed the null-IP gotcha (now fixed) |
| Teardown | Both pods created were deleted; the final pod list was `[]` |
| Frames | 640×360 PNGs, correct, grainy because there was no denoise. Copies were kept by the authors |

## Gotchas
- `runpodctl pod get` returns a null IP, so read it from the REST API.
- Capacity errors come and go, so retry or move to the next GPU.
- Community cloud needs `--public-ip` for scp, because the RunPod SSH proxy can't do scp or sftp.
- On macOS, bash 3.2 with `set -u` and an empty array crashes; this is handled.
- The "HIP library" warning in the log is harmless.
- **Estimate before batching.** A 4K, 512-sample interior on a 3090 is guessed at 30–90 s per frame.
  That isn't measured, so time the first frame and extrapolate.
