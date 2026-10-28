---
name: case-pack
description: Make, check, play and share mystery "case packs" — playable murder mysteries as a data folder. `new "<one-line premise>"` runs the writers' room, narrative lead and adversarial story auditors to produce a fair, linted, playable pack; `lint <pack>` checks fairness rules; `play <pack>` plays it free in the terminal. Use for "/game-studio:case-pack", "make a mystery from this premise", "play the example case", "check my case pack".
argument-hint: "new \"<premise>\" | lint <pack-dir> | play <pack-dir>"
---

# /game-studio:case-pack

The format is in `${CLAUDE_PLUGIN_ROOT}/skills/studio/references/case-pack-format.md`. The engine
contract is in `engine-semantics.md`.

## `play <pack>`
Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/casepack/play.py <pack>`. It's free, offline, and runs in a
terminal. Tell the user to run it in their own terminal, because it's interactive. A good first one:
`${CLAUDE_PLUGIN_ROOT}/examples/case-packs/the-locked-study` (about 10 minutes), then *Dead Air on
the Meridian* (20–40 minutes).

## `lint <pack>`
Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/casepack/lint.py <pack>`. It checks nine rules: schema, IDs,
the Three Clue Rule, herrings, reachable endings, Act-1 leaks, the minimal path, gates, and whether it
can be finished offline. Explain each FAIL in plain words and propose the fix.

## `new "<premise>"`
This is the sharing loop. Act as the Producer and run this pipeline on the board:
1. Scaffold the pack: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/casepack/new_pack.py packs/<slug>`.
2. Launch in parallel:
   - **writers-room** drafts NARRATIVE.md from `narrative-bible-template.md`.
   - **researcher** gathers period and setting facts for the premise.
3. **narrative-lead** reviews, up to 3 rounds.
4. Launch **story-auditor ×3 in parallel**, one per mode (A, B and C, from `adversarial-review.md`).
   Then the narrative-lead applies their fixes.
5. **writers-room** transcribes the bible into `case-file.json` against the schema. Then run `lint.py`
   until it passes, and `play.py <pack> --autoplay-solution`.
6. Optional: art prompts from the **art-director** and **character-artist** (portrait prompts), and
   **vo-director** casting briefs for Fish Audio Drama 3.
7. Hand over a spoiler-free README and the `play` command. To share it, zip the folder; anyone can play
   it with `play.py`.

**Quality bar:**
- Lint PASS.
- The adversarial log is filled in.
- The original IP check is done.
- Playtime is close to the premise's target.
