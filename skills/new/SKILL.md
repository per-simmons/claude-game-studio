---
name: new
description: Start a new game with the AI game studio. Asks about five questions, sets up the project folder, the board and the config, then the Producer runs the studio to the first gate. Use when someone says "/game-studio:new", "make a game", "start a game studio", "new murder mystery", or hands over a one-line game idea.
argument-hint: "[one-line premise]"
---

# /game-studio:new: kick off the studio

You're about to act as the **Producer** (`${CLAUDE_PLUGIN_ROOT}/agents/producer.md`), and the user is
the **publisher**. Keep it friendly and fast. The user may never have made a game before.

## 1. Ask five questions, all in one message
If `$ARGUMENTS` has a premise, use it as the answer to Q1 and ask the rest.
1. **The premise, in one line.** For example: "a jewel thief on a 1920s airship."
2. **What kind of game?**
   - (a) A **mystery case pack**: interrogate suspects, solve it, share it. This is the fastest route,
     with a full example included.
   - (b) Something else. Describe it, and the studio adapts the GDD templates.
3. **How long should one playthrough take?** Default: 20–40 minutes.
4. **Free path or pro path?**
   - **Free:** 2D art from any image generator you already use, and a placeholder voice. No keys.
   - **Pro** adds local Blender scenes and RunPod GPU renders.
   - The VO department is **Fish Audio Drama 3**. It stays off until you add a key from
     https://fish.audio.
5. **Do you want to watch the studio work?** Studio floor mode puts every employee in its own
   colour-coded terminal pane. It needs iTerm2 on macOS or tmux. Also ask for the **project folder
   name**; the default is a slug of the premise.

## 2. Set up
- If `<folder>/studio/studio.config.json` doesn't exist:
  1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/project/` into the folder, including the dotfiles.
  2. Fill in `game.title`, `game.premise`, `game.kind`, `game.session_minutes` and `path`.
  3. On the pro path, run `/game-studio:setup` checks for Blender and RunPod.
  4. Run `git init` if the folder isn't a repo. Engineer worktrees need git.
- Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/board/board.py init --game "<title>"` in the folder.
- Seed the **M0 Concept** tickets with `board.py add`:
  - `researcher`: reference games and prior art for this premise. Reviewer: creative-director.
  - `creative-director`: one-sheet, pillars, 60-second pitch. Depends on research. Reviewer: the
    publisher, at the gate.
  - For mysteries, `writers-room`: a premise-level case outline with twist options. Reviewer:
    narrative-lead.
  - `story-auditor` (mode A): a speed-solve estimate of the outline.

## 3. Run
- **If floor mode is on:** tell the user to run
  `bash ${CLAUDE_PLUGIN_ROOT}/scripts/floor/studio-floor.sh` from the project folder, or offer to run
  it for them. Then keep acting as the Producer here.
- **Otherwise:** act as the Producer in this session. Launch the ready tickets **in parallel**, with
  several Agent tool calls in one message, each with `subagent_type: "game-studio:<owner>"`. Then route
  the reviews.
- **For mystery case packs**, the studio's deliverable is a playable pack (`/game-studio:case-pack`),
  and a web engine is optional (see `examples/case-packs/dead-air-on-the-meridian/BUILD-PROMPT.md`).
- Stop at **G0** and present `studio/gates/G0.md`, at most 300 words. Write `studio/STATUS.md`.

## Rules
Read `${CLAUDE_PLUGIN_ROOT}/skills/studio/references/operating-model.md`. Never call a paid API the
config hasn't enabled. No IP. Everything happens in the project folder.
