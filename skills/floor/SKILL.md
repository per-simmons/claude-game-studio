---
name: floor
description: Open the "studio floor" — every studio employee in its own colour-coded terminal pane (iTerm2 grid on macOS, or tmux anywhere) running `claude --agent game-studio:<role>` and working its queue on the shared board, plus a live board pane. Built for filming. Use for "/game-studio:floor", "show the studio working", "open the studio floor", "rehearse the floor".
argument-hint: "[--rehearse|--print] [roles...]"
---

# /game-studio:floor

From the game folder, which must already have `studio/board.json` from `/game-studio:new`:
```
bash ${CLAUDE_PLUGIN_ROOT}/scripts/floor/studio-floor.sh $ARGUMENTS
```
- **No arguments:** the roles come from `studio.config.json` → `floor.roles`. You get one pane per role
  plus a BOARD pane that re-renders every 3 seconds.
- `--rehearse`: no Claude sessions. Each pane replays its lane's tickets. It's free, for practising
  the shot.
- `--print`: prints the exact pane commands, for any terminal you like.
- `--stop`: closes **only** the panes this script opened.

## Where it opens, and focus
- `floor.bounds` sets where the grid goes. It accepts `"right"`, `"left"`, `"main"`, or
  `[x1,y1,x2,y2]`. The named displays are found by geometry, so identical monitors still work.
- The launcher remembers your frontmost app and gives focus back after the panes open. If it has to
  start iTerm, it starts it in the background.
- If your agents are installed in `.claude/agents` instead of the plugin, set
  `floor.agent_prefix: "none"`.

## How it works
- Every pane is a real interactive Claude Code session started with `claude --agent
  game-studio:<role> -n "<Role>"`. Each one is told to loop on the board: `next`, then `claim`, the
  work, then `submit`. Reviewers also pick up `in_review` tickets that are assigned to them.
- The **producer** pane plans and routes, and doesn't spawn sub-agents for roles that already have a
  pane.
- Coordination happens only through the file-locked `studio/board.json`, so panes never collide.

## Before you go live
- The panes run the permission mode in `floor.permission` (default `acceptEdits`). Each session still
  asks before running shell commands it isn't allowed to run, so pre-approve the board script in your
  settings if you want hands-off filming.
- Every pane is a full session, so costs scale with the number of panes. Start with 4–7 roles.
- **The agent-teams alternative:** if you've enabled Claude Code's experimental agent teams, the
  Producer can run the employees as teammates in native split panes instead. The board stays the
  source of truth either way.
