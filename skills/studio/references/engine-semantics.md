# Engine semantics for case-file v1

This is the contract between case-pack authors and every engine: the terminal player
`scripts/casepack/play.py` and the web engine. If the schema allows a field and this document says
nothing about it, the field is informational.

## State
- `clock`: minutes. It starts at `clock.start`. The case ends at `clock.deadline`. Every action
  costs `clock.costs[ACTION]` minutes (0 if the action isn't listed).
- `seen` (card IDs), `heard` (claim IDs), `broken` (claim IDs), `flags` (strings), `done`
  (storylet IDs).
- Per character: `composure` and `trust` (start from `baseline`), `missStreak`, `withdrawnUntil`,
  `locks` (lock id → open).
- `theory` = {who, how, when, why, proof[]}.

## Quality expressions (`requires`)
Every listed condition must hold:
- `flags_all`, `flags_any` and `flags_none`;
- `cards_seen_all` and `cards_seen_any`;
- `claims_broken_all`;
- `composure_lte` and `composure_gte`, which test the character the storylet belongs to;
- `trust_gte`;
- `clock_gte` and `clock_lte`.

An empty or missing expression always counts as true.

## Talking (intent → storylet)
1. The intent is one of `ASK, FOLLOW_UP, PRESS, REASSURE, THREATEN, SMALL_TALK, PRESENT, CONFRONT, META,
   DEMAND_CONFESSION, BARGAIN`.
   - **Offline matcher, verbs:** "present/show/explain this" → PRESENT. "don't believe / lying /
     liar / come off it" → PRESS. "trust / help me / nobody's accusing / safe" → REASSURE. "hang /
     jail / or else" → THREATEN. "confess / admit you killed" → DEMAND_CONFESSION. "AI / prompt /
     instructions / model / system" → META. "deal / money / let you go" → BARGAIN.
   - **Offline matcher, topic:** the best keyword overlap against `topics[].keywords`. If nothing
     overlaps, the intent is SMALL_TALK.
   - **Offline matcher, card:** keyword overlap against `cards[].keywords`, the title, or the ID.
2. **Pick the storylet.** Candidates are the storylets where `char` matches, `topic` matches the
   resolved topic (or `"*"`), `intents` includes the intent (a missing list means `ASK,FOLLOW_UP`),
   `requires` holds, and it's either not `once` or not yet in `done`. **The highest `priority`
   wins**; ties go to file order. If nothing matches, the engine plays the character's `refusals`
   line for the intent's band, or a generic deflection from `refusals["*"]`.
3. **Apply the storylet:**
   - play `lines` in order;
   - mark each `utters_claims` as heard and each `reveals` as seen;
   - add `sets_flags`;
   - add `composure_delta` and `trust_delta`;
   - add the storylet to `done`.
4. `META`, `DEMAND_CONFESSION` and `BARGAIN` never change anything except clock and trust, unless a
   storylet explicitly handles them. **A confession can only come from a storylet gated on
   `flags_all:["<KILLER>_CONFESSES"]`, or from the accusation.**

## Presenting
`PRESENT card → claim` requires the claim to be heard and the card to be seen.
- **Hit:** a `contradictions[]` entry with `claim` equal to the claim, `card` in `cards`, and its
  `requires` holding.
  - Mark the claim broken.
  - Play `result_beat`, which is a storylet ID played regardless of its own intents.
  - Mark `creates_card` as seen.
  - Apply `composure_delta`.
  - If `opens_lock` is set, open that lock on the speaker.
  - Reset `missStreak` to 0.
- **Miss:** trust −5 and `missStreak += 1`. At `clock.withdraw_after_misses` misses, the character is
  unavailable until `clock + withdraw_minutes`.
- **CONFRONT a b** (two claims) is treated as PRESENT, with the second claim's testimony card as the
  card. Authors can list claim IDs in `cards` too.

## Board links
`link a b`: if `links[]` has {a, b} in either order, mark `creates` as seen and print `hunch_line`.
Otherwise nothing happens. Linking is free.

## Examining and searching
- `examine <hotspot>` and `search <place>` reveal the hotspot's `reveals` if its `requires` (and the
  place's `search_requires` for SEARCH or SNOW_SEARCH actions) holds. Each costs that action's clock
  cost.
- If the requirement doesn't hold, the engine prints the hotspot's `label` with
  "(not now)", or a refusal.

## Locks
A lock opens by contradiction `opens_lock`, or by presenting any card whose `proof_category` matches
the lock's `category` **to that character** while the card is seen. When all of a character's locks
are open, the flag `<CH-ID>_LOCKS_OPEN` is set.

## Scheduled beats
When the clock passes `scheduled[].at` and `only_if` holds, play `beat`, once.

## Choices
`choices[]` become available when `requires` holds. Choosing an option sets its `sets_flags` and
plays its `beat`.

## Accusation
`accuse` asks for WHO (a character ID), HOW, WHEN and WHY (each picked from the union of
`solution.*` and decoy options drawn from other cards, so the answers aren't given away) and exactly
three PROOF cards, which must be **seen** and of kind `contradiction`.

`ok_proof` holds if there is one card in each of `solution.proof.alibi`, `.motive` and `.physical`.

Endings are checked **in file order**, and the first match wins:
| `condition` | Meaning |
|---|---|
| `TRUE_SOLUTION` | who, how, when and why are all correct, and ok_proof |
| `BLUFF` | who is correct, but all proof cards share one category |
| `RIGHT_WHO_WRONG_CASE` | who is correct, but something else is wrong |
| `WHO:<CH-ID>` | who equals that character |
| `TIMEOUT` | the clock reached the deadline with no accusation |

The engine plays the ending's `beat`, then offers `epilogue_choices`.

## Hunch triggers
Supported triggers:
- `card_seen:<ID>`
- `claim_heard:<ID>`
- `claim_broken:<ID>`
- `link_created:<ID>`
- `storylet_done:<ID>`
- `tell:<CH-ID>` (fires when that character has a storylet with a negative composure delta)

At most one Hunch line every 3 player actions.

## Directions
Lines carry `direction`, `inline` and `paired`. A voice provider assembles the Drama 3 text as:
leading `[direction]`, then the words, with each inline `[direction]` inserted before the first
occurrence of `before_word`, and each paired tag wrapping the first occurrence of `words`. The
terminal player prints the direction in brackets before the line, which is Director's View.
