# VO direction script format (Audio / VO Director)

This follows the master-sheet convention from Game Developer, "Screen/Play: Documenting Voice Assets,"
and Side's rule of "no merging dialogue with direction; one column per type of information"
(RESEARCH §1). Applied to Fish Drama 3, whose direction is free text in brackets placed *before* the
words it affects, plus scoped paired tags. Worked example:
`examples/case-packs/dead-air-on-the-meridian/VO-DIRECTION.md`.

## 1. The document
```markdown
# VO DIRECTION: "<title>"
## 1. Engine rules relied on (with doc links) — e.g. Drama 3 bracket direction, paired tags, multi-speaker,
   model header, timestamps, known failure modes
## 2. Casting — character | age/vocal type | baseline | voice-design instruction | tell signature
   (route: Voice Design → licensed library → NEVER clone a real person)
## 3. Hidden state → direction — band table, modifiers, per-character tag tables (+ "never" list)
## 4. Directed lines — the sheet (below) + lint rules + budget + fallbacks for risky effects
## 5. Sync — how timestamps drive captions and Director's View
## 6. Multi-speaker set pieces — full scripts with <|speaker:N|>
## 7. Production plan — casting page, takes, keeper selection, pickups
## 8. Cost talking point — with the price source
```

## 2. The line sheet (CSV/TSV, one row per line)
| Column | Meaning |
|---|---|
| LINE_ID | `CHR-###`, unique. Also the cache filename |
| CHARACTER | The character (not the actor) |
| CONTEXT | The situation immediately before the line |
| TRIGGER | The game event that plays it (intent + topic/card) |
| STATE | The composure band and flags it assumes |
| DIRECTION | The leading bracket, ≤ 8 words, tone and pace only |
| INLINE | `before_word → [direction]`, at most 2 |
| PAIRED | `tag: words`, at most 1 |
| TEXT | Spoken words only, with times written as words |
| INTENSITY | 1–5 |
| MODE | `authored` (pre-rendered, never paraphrased) or `writer` (the LLM may rephrase within facts) |
| TAKE | The chosen take number (LINE CHOICE) |
| NOTES | Pronunciation, phoneme pins (`<|phoneme_start|>…<|phoneme_end|>`), fallbacks |

## 3. Lint rules (enforced by code before any render)
- **V-01.** A leading direction is at most 8 words. At most 2 inline directions and 1 paired tag per
  line.
- **V-02.** Directions carry no facts, only tone, pace and attitude. They may show in a Director's
  View or video mode, never in the default player UI.
- **V-03.** **Never start a line with a sound tag** (`[sighs]`, `[laughs]`, `[clears throat]`). This
  is the Drama 3 silent-after-first-line mitigation.
- **V-04.** Numbers and times are written as words, so the timestamps match the script.
- **V-05.** Paired tags are balanced and don't nest.
- **V-06.** Live lines are at most 45 words. Authored set-piece lines are at most 70.

## 4. Turning state into direction
Write the mapping as data (a JSON table), so the voice director is deterministic code. The LLM never
writes directions. If it emits brackets, the validator strips them.
