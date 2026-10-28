---
name: gate
description: Run a milestone gate (G0 Concept, G1 Vertical slice/greenlight, G2 Content complete, G3 Polish/ship) — the Producer assembles the evidence packet against written acceptance criteria and asks the publisher to approve, cut, or kill. Use for "/game-studio:gate", "are we ready for the vertical slice", "greenlight review", "approve the milestone".
argument-hint: "G0|G1|G2|G3 [approve|changes \"notes\"|kill]"
---

# /game-studio:gate

The criteria are in `${CLAUDE_PLUGIN_ROOT}/skills/studio/references/operating-model.md` §4.

## Without a verdict: assemble the packet
1. Check each criterion against the evidence: files, `board.py list`, lint, tests, screenshots and the
   fun audit. Mark each one ✓ or ✗.
2. Write `studio/gates/<G>.md`, at most 300 words:
   - the criteria table;
   - the decisions needed, each with a recommendation;
   - the risks;
   - **kill / continue / continue with cuts**.
3. Present it and stop. Never pass your own gate.

## With a verdict (only from the user)
- **approve:** `board.py milestone <next>`. Plan the next cycle and log the approval in the gate file.
- **changes:** turn the notes into tickets with owners.
- **kill:** write `studio/POSTMORTEM.md` (what went right and what went wrong, at least 5 each) and
  archive the board.
