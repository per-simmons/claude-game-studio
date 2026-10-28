---
name: status
description: Producer's daily standup — reads the board and writes studio/STATUS.md (per-lane done/next/blockers, burndown, cost, retro) and summarises it in chat. Use for "/game-studio:status", "where are we", "standup", "what's the studio doing".
---

# /game-studio:status

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board/board.py standup` and `board.py check` in the game
   folder.
2. Rewrite `studio/STATUS.md` using its template:
   - milestone, cycle number and the frozen cycle goal;
   - a lane table of done, next and blockers;
   - burndown (approved or done, out of planned);
   - open bugs by severity;
   - cost so far, if known;
   - a three-line retro (keep, change, try).
3. In chat, summarise it in three lines or fewer: progress, blockers, the next decision for the
   publisher (with a recommendation). Link STATUS.md and BOARD.md.
