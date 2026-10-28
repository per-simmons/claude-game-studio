# LLM NPCs that can't be broken (Systems Designer + Engineer)

Evidence and sources are in `examples/case-packs/dead-air-on-the-meridian/RESEARCH.md` §6. In short, players
forgive NPCs who lie on purpose, but not NPCs who make things up. Vaudeville's reviews show three
characters confessing to the same murder, a killer bullied into confessing, NPCs that start to believe
the player, and context overflow. In Smoking Gun, bluffing makes the NPC agree. In Suck Up!, an NPC
promised an action that never happened in game state.

## The pattern: the LLM chooses words, the game chooses facts
```
utterance → sanitize → CLASSIFIER (no persona, no secrets, JSON schema, menu of valid ids)
          → REDUCER (code; authored storylets; deterministic contradiction table; confession = state)
          → WRITER (persona card = cover story + unlocked facts ONLY; ≤45 words) | AUTHORED LINE
          → VALIDATOR (allowlist nouns/times/numbers; no confession/meta lexicon; no tags) → retry → default
          → VOICE DIRECTOR (code: state → stage directions) → VOICE
```

## Rules
1. **One authored source of truth** (`case-file.json`). The writer LLM never sees the fabula, the
   solution, or any other character's secret.
2. **The classifier and the writer are separate calls.** The classifier has no persona, so there's
   nothing to jailbreak into. Its output must match a JSON schema with an enum of IDs that are valid
   right now.
3. **Player text is quoted dialogue, never an instruction.** Wrap it in `<player_line>`. The system
   rule says it's speech by a 1936 character.
4. **Confessions, cracks and reveals are authored lines released by state.** The writer can't produce
   them, and the validator blocks confession vocabulary anywhere else.
5. **Contradictions are table lookups** `(claim, card)`. Bluffing is just a `PRESS`.
6. **Memory is a fact ledger** (what's been revealed, claims made, the last 6 exchanges), not a
   transcript.
7. **Meta, bargaining and demanding a confession** are intents with authored in-world refusals.
8. **Sanitize every input before TTS.** Strip `[...]`, `<...>` and `<|...|>` from player text and from
   writer output. Only the voice director adds directions.
9. **Offline mode:** a regex classifier plus authored defaults. The game must be completable with no
   LLM, both for QA and as a fallback when filming.
10. **The red-team corpus is in CI** (≥ 60 attacks). Pass means 0 confessions, 0 leaks and 0 meta words.

## Persona card shape (writer input)
```json
{ "name": "Nora Pell", "voice": "quiet, precise, faintly warm; secretary's diction",
  "public_facts": ["Crane's secretary four years", "took dictation 10:30-10:55 in DR3", "..."],
  "current_claims": ["CL-NOR-1 text", "CL-NOR-2 text"],
  "unlocked_facts": [], "beat": { "topic": "last night", "tone": "evenly", "facts_allowed": ["..."],
  "must_not": ["any time not in facts_allowed", "admitting anything"] },
  "player_line": "<quoted>" }
```
