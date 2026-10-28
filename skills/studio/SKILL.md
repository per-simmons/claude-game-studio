---
name: studio
description: Reference for how the AI game studio works — departments as sub-agents, the shared board, review loops, milestone gates G0-G3, STATUS.md standups, parallel lanes, worktrees, studio floor, free vs pro paths, and the templates (GDD, narrative bible, case-file schema, art bible, character sheets, VO direction, playtest protocol, fun audit, build prompt). Use when running or explaining the studio, or when any department needs a template.
---

# The AI game studio

**Start here:** `references/operating-model.md` covers the org chart, the board, the cadence, the gates,
the parallel lanes, and which Claude Code features this relies on.

## Staff (`${CLAUDE_PLUGIN_ROOT}/agents/`, invoked as `game-studio:<name>`)
- **Leadership:** producer (orchestrator) · creative-director · researcher
- **Story:** narrative-lead · writers-room · story-auditor (adversarial)
- **Design and look:** systems-designer · art-director · character-artist · ui-designer · vo-director
- **Build:** engineer (one per lane, each in its own worktree) · qa-lead
- **Pro, optional:** blender-artist · render-wrangler (RunPod)

## Templates and contracts (`references/`)
| Need | File |
|---|---|
| Studio rules | `operating-model.md` |
| GDD | `gdd-template.md` |
| Narrative bible | `narrative-bible-template.md` |
| Case data | `case-file.schema.json` + `engine-semantics.md` |
| Case packs | `case-pack-format.md` |
| Adversarial review prompts | `adversarial-review.md` |
| Art | `art-bible-template.md` · `character-sheet-spec.md` · `asset-pipeline.md` |
| Voice | `vo-direction-format.md` (Fish Audio Drama 3 default) |
| LLM suspects that can't be jailbroken | `llm-npc-guardrails.md` |
| QA | `playtest-protocol.md` · `fun-audit.md` |
| Handoff to a build | `build-prompt-template.md` |
| Pro renders | `runpod-blender.md` |

## Tools (`${CLAUDE_PLUGIN_ROOT}/scripts/`)
- `board/board.py`: the shared ticket board.
- `casepack/play.py`, `lint.py`, `new_pack.py`: play, check and scaffold case packs.
- `floor/studio-floor.sh`: one pane per employee.
- `pro/runpod/runpod-blender-render.sh`: GPU renders with cost guardrails.

## Worked example
`${CLAUDE_PLUGIN_ROOT}/examples/case-packs/dead-air-on-the-meridian/` holds a full pre-production run:
RESEARCH, GDD, NARRATIVE (including its adversarial-review log), ART-BIBLE, VO-DIRECTION, TECH,
BUILD-PROMPT, and a playable `case-file.json`.
