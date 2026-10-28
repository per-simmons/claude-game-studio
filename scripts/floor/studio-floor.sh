#!/usr/bin/env bash
# studio-floor.sh: open the "studio floor". Each employee gets its own colour-coded terminal pane,
# running an interactive Claude Code session as that studio agent, working its queue on the shared
# board. One extra pane shows the live board. Made to look good on camera.
#
# USAGE (from your game project folder, after /game-studio:setup):
#   studio-floor.sh [roles...]            # default roles from studio.config.json → floor.roles
#   studio-floor.sh --rehearse [roles...] # no Claude sessions: each pane replays the board only (free, for practice)
#   studio-floor.sh --print [roles...]    # print the commands instead of opening panes
#   studio-floor.sh --stop                # close ONLY the panes this script opened (iTerm2 or tmux)
#
# ENV / CONFIG (studio/studio.config.json → "floor")
#   terminal   "iterm2" (macOS) | "tmux" (any OS) | "print"
#   roles      ["producer","narrative-lead","writers-room","art-director","character-artist","engineer","qa-lead"]
#   bounds     [x1,y1,x2,y2] | "right" | "left" | "main" (default main). The floor never takes focus from your current app.
#   agent_prefix "game-studio:" (plugin install, default) | "none" (agents installed in .claude/agents)
#   permission "acceptEdits" (default) | any --permission-mode value the user is comfortable with
#
# Coordination is ONLY through studio/board.json (scripts/board/board.py takes a file lock), so every
# pane can work in parallel without talking to the others. The producer pane plans and reviews; the
# other panes loop: next → claim → work → submit.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"          # plugin root
PROJ="$(pwd)"
CFG="$PROJ/studio/studio.config.json"
BOARD="python3 '$ROOT/scripts/board/board.py'"

MODE="live"; ROLES=()
for a in "$@"; do
  case "$a" in
    --rehearse) MODE="rehearse" ;;
    --print) MODE="print" ;;
    --stop) MODE="stop" ;;
    *) ROLES+=("$a") ;;
  esac
done

cfg() { python3 - "$CFG" "$1" "$2" <<'PY'
import json, sys
try:
    c = json.load(open(sys.argv[1]))
except Exception:
    c = {}
cur = c
for k in sys.argv[2].split("."):
    cur = cur.get(k, {}) if isinstance(cur, dict) else {}
print(json.dumps(cur) if isinstance(cur, (list, dict)) and cur else (cur if cur not in ({}, None) else sys.argv[3]))
PY
}

[ -f "$PROJ/studio/board.json" ] || { echo "No studio/board.json here. Run /game-studio:new first (or cd into your game folder)." >&2; exit 1; }
TERMINAL="$(cfg floor.terminal iterm2)"
IDS_FILE="$PROJ/studio/.floor-windows"
if [ "$MODE" = "stop" ]; then
  if [ "$TERMINAL" = "tmux" ]; then tmux kill-session -t studio-floor 2>/dev/null && echo "floor stopped"; exit 0; fi
  [ -f "$IDS_FILE" ] || { echo "no floor windows recorded"; exit 0; }
  for wid in $(cat "$IDS_FILE"); do
    tty=$(osascript -e "tell application \"iTerm\" to get tty of current session of (first window whose id is $wid)" 2>/dev/null) || continue
    [ -n "$tty" ] && pkill -KILL -t "${tty#/dev/}" 2>/dev/null || true
    sleep 0.3; osascript -e "tell application \"iTerm\" to close (first window whose id is $wid)" >/dev/null 2>&1 || true
  done
  rm -f "$IDS_FILE"; echo "floor stopped"; exit 0
fi
[ "$MODE" = "print" ] && TERMINAL="print"
PERM="$(cfg floor.permission acceptEdits)"
PREFIX="$(cfg floor.agent_prefix 'game-studio:')"; [ "$PREFIX" = "none" ] && PREFIX=""
if [ ${#ROLES[@]} -eq 0 ]; then
  while IFS= read -r r; do ROLES+=("$r"); done < <(python3 -c "
import json,sys
try: r=json.load(open('$CFG')).get('floor',{}).get('roles')
except Exception: r=None
print('\n'.join(r or ['producer','narrative-lead','writers-room','art-director','character-artist','engineer','qa-lead']))")
fi

# Lane colours (dark backgrounds so default text stays readable), RGB 0-255.
colour() { case "$1" in
  producer) echo "40 34 8" ;; creative-director) echo "48 30 8" ;; researcher) echo "20 30 30" ;;
  narrative-lead|writers-room|story-auditor) echo "48 12 16" ;;
  systems-designer) echo "30 20 40" ;; art-director|character-artist) echo "10 36 20" ;;
  blender-artist|render-wrangler) echo "8 36 38" ;; ui-designer) echo "34 12 38" ;;
  vo-director) echo "40 18 30" ;; engineer) echo "10 20 46" ;; qa-lead) echo "30 30 30" ;; *) echo "20 20 20" ;; esac; }

title() { python3 -c "import sys;print(sys.argv[1].replace('-',' ').title())" "$1"; }

floor_prompt() { # $1 role
  if [ "$1" = "producer" ]; then
    echo "You are on the studio floor as the PRODUCER. Read studio/STATUS.md and the board ($BOARD list). Plan or continue the current cycle: add tickets with owners/deps/reviewers, keep STATUS.md current every few minutes from '$BOARD standup', and route reviews. Other employees are running in their own panes and will pick up tickets assigned to them; do NOT spawn sub-agents for roles that have a pane. Stop at gates and wait for the publisher."
  else
    echo "You are on the studio floor as $1. Work your queue until the producer ends the cycle: loop { $BOARD next --owner $1 ; if a ticket: $BOARD claim <id> --by $1, do it per your role, $BOARD submit <id> --by $1 --note '<what/where>' ; also review tickets in_review where you are the reviewer ; if nothing: wait 60 seconds and check again }. Print one short line each time a ticket moves."
  fi
}

pane_cmd() { # $1 role
  local r="$1"
  if [ "$MODE" = "rehearse" ]; then
    echo "cd '$PROJ' && clear && while true; do clear; printf '\\033]0;%s\\007' '$r'; echo '== $r =='; $BOARD list | grep -i '$r' || echo '(no tickets yet)'; sleep 5; done"
  else
    local p; p="$(floor_prompt "$r")"; p=${p//\'/\'\\\'\'}
    echo "cd '$PROJ' && clear && claude --agent '${PREFIX}$r' -n '$(title "$r")' --permission-mode '$PERM' '$p'"
  fi
}
BOARD_CMD="cd '$PROJ' && while true; do clear; cat studio/BOARD.md 2>/dev/null | head -60; sleep 3; done"

N=$(( ${#ROLES[@]} + 1 ))
case "$TERMINAL" in
print)
  for r in "${ROLES[@]}"; do echo "[$r] $(pane_cmd "$r")"; done; echo "[board] $BOARD_CMD" ;;
tmux)
  command -v tmux >/dev/null || { echo "tmux not found (brew install tmux / apt install tmux)" >&2; exit 1; }
  S="studio-floor"; tmux kill-session -t "$S" 2>/dev/null || true
  tmux new-session -d -s "$S" -n floor "$BOARD_CMD"
  tmux select-pane -t "$S" -T "BOARD"
  for r in "${ROLES[@]}"; do
    tmux split-window -t "$S" "$(pane_cmd "$r")"; tmux select-pane -T "$(title "$r")"
    read -r R G B <<< "$(colour "$r")"; tmux select-pane -P "bg=#$(printf '%02x%02x%02x' $R $G $B)"
    tmux select-layout -t "$S" tiled >/dev/null
  done
  tmux set -t "$S" pane-border-status top; tmux set -t "$S" pane-border-format " #{pane_title} "
  echo "Studio floor is running in tmux session '$S'. Attach with: tmux attach -t $S" ;;
iterm2)
  [ "$(uname)" = "Darwin" ] || { echo "iterm2 mode is macOS-only; set floor.terminal to tmux" >&2; exit 1; }
  BOUNDS="$(cfg floor.bounds '')"
  # floor.bounds: [x1,y1,x2,y2] | "right" | "left" | "main". Named displays are found by geometry
  # (display names are often identical across identical monitors).
  read -r X0 Y0 X9 Y9 < <(python3 "$HERE/display-bounds.py" "$BOUNDS")
  # Never steal focus: remember the frontmost app now, give it focus back after the panes open.
  # Launch iTerm in the background if needed, and note the default window it opens on launch
  # (on whatever display) so we can close it: only our panes should appear, only on the floor display.
  FRONT_APP="$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null || echo "")"
  LAUNCHED=0; OURS=""
  if ! pgrep -x iTerm2 >/dev/null; then
    LAUNCHED=1; open -g -a iTerm; for _ in 1 2 3 4 5 6 7 8 9 10; do sleep 0.5; pgrep -x iTerm2 >/dev/null && break; done; sleep 2
  fi
  COLS=$(( N <= 4 ? 2 : (N <= 9 ? 3 : 4) )); ROWS=$(( (N + COLS - 1) / COLS )); GAP=6
  CW=$(( (X9 - X0 - GAP*(COLS+1)) / COLS )); CH=$(( (Y9 - Y0 - GAP*(ROWS+1)) / ROWS ))
  i=0
  open_pane() { # $1 label $2 cmd $3 "r g b"
    local col=$(( i % COLS )) row=$(( i / COLS ))
    local x1=$(( X0 + GAP + col*(CW+GAP) )) y1=$(( Y0 + GAP + row*(CH+GAP) ))
    read -r R G B <<< "$3"
    local c=${2//\\/\\\\}; c=${c//\"/\\\"}
    local wid; wid=$(/usr/bin/osascript <<OSA
tell application "iTerm"
  set w to (create window with default profile)
  set bounds of w to {$x1, $y1, $(( x1 + CW )), $(( y1 + CH ))}
  tell current session of w
    set name to "$1"
    set background color to {$(( R*257 )), $(( G*257 )), $(( B*257 ))}
    write text "$c"
  end tell
  return id of w
end tell
OSA
)
    OURS="$OURS $wid"; i=$(( i + 1 )); sleep 0.4
  }
  open_pane "BOARD" "$BOARD_CMD" "12 12 12"
  for r in "${ROLES[@]}"; do open_pane "$(title "$r")" "$(pane_cmd "$r")" "$(colour "$r")"; done
  echo "$OURS" > "$IDS_FILE"
  if [ "$LAUNCHED" = "1" ]; then  # close the default window iTerm opened at launch (it isn't one of ours)
    for wid in $(osascript -e 'tell application "iTerm" to get id of every window' | tr ',' ' '); do
      case " $OURS " in *" $wid "*) ;; *) osascript -e "tell application \"iTerm\" to close (first window whose id is $wid)" >/dev/null 2>&1 || true ;; esac
    done
  fi
  if [ -n "$FRONT_APP" ] && [ "$FRONT_APP" != "iTerm2" ]; then osascript -e "tell application \"$FRONT_APP\" to activate" >/dev/null 2>&1 || true; fi
  echo "Studio floor: $N panes open on [$X0,$Y0,$X9,$Y9] (${ROLES[*]} + board). Focus returned to ${FRONT_APP:-the previous app}." ;;
*) echo "unknown floor.terminal '$TERMINAL' (use iterm2, tmux or print)" >&2; exit 1 ;;
esac
