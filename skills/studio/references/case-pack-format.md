# Case-pack format (v1)

A **case pack** is one complete, playable mystery in a folder. It's what users make, share and play.
The studio produces one from a one-line premise (`/game-studio:case-pack new "<premise>"`). The
terminal player and the web engine both load it.

```
<pack-id>/
  casepack.json        manifest (required)
  case-file.json       the whole case as data; schema: case-file.schema.json (required)
  README.md            spoiler-free blurb + how to play (required)
  NARRATIVE.md         human-readable bible, SPOILERS (recommended)
  VO-DIRECTION.md      voice casting + direction tables (optional)
  ART-BIBLE.md         look + scene list (optional)
  art/                 portraits/<CH-ID>/<state>.png, scenes/<place>.png, props/<E-ID>.png (optional)
  audio/               pre-rendered authored lines <line-id>.<ext> + <line-id>.json word timings (optional)
  LICENSE              the pack's own licence (default CC BY 4.0)
```

## casepack.json
```json
{
  "format": "casepack/1",
  "id": "dead-air-on-the-meridian",
  "title": "Dead Air on the Meridian",
  "premise": "A radio gossip king is murdered on a snowbound 1936 sleeper train.",
  "blurb": "Six frightened passengers. Four hours to dawn. Everyone is hiding something — only one of them killed.",
  "version": "1.0.0",
  "authors": ["Game Studio example"],
  "license": "CC-BY-4.0",
  "content_rating": "Teen: implied violence, adult secrets, no gore",
  "play_minutes": [20, 40],
  "case_file": "case-file.json",
  "voices": { "provider_default": "placeholder", "fish_voice_ids": {} },
  "art": { "style": "deco noir gouache", "portraits": "art/portraits", "scenes": "art/scenes" },
  "spoiler_files": ["NARRATIVE.md", "case-file.json"],
  "lint": { "passed": true, "linter_version": "1", "min_path_actions": 18 }
}
```

## Rules a pack must pass (`python3 scripts/casepack/lint.py <pack>`)
1. `case-file.json` is structurally valid. It's also validated against the full JSON Schema if
   `jsonschema` is installed.
2. Every referenced ID exists.
3. **Three Clue Rule:** each proof category has at least 3 routes, with optional branches off.
4. Every herring card has a `herring_resolution`.
5. Every ending is reachable.
6. **Leak check:** no proof category can be filled from Act-1 cards.
7. The minimal path to the true ending is at least 16 actions (configurable).
8. No solution fact appears in a writer storylet's `facts_allowed` before its gate.
9. The offline player can finish the true ending (`play.py --autoplay-solution`).

## The sharing loop
1. Premise.
2. `/game-studio:case-pack new`, which runs the writers' room, the narrative lead and the adversarial
   reviewers.
3. The linter.
4. Play it in the terminal (free) or in the web engine.
5. Zip the folder and share it.
6. Anyone loads it with `play.py <pack>` or by dropping it into `engine/packs/`.
