# GDD template (the living document)

This is the Systems Designer's document, co-owned with the Creative Director, and it's kept short on
purpose. RESEARCH §1 explains why the 100-page bible is dead: write per-system one-pagers *just before*
each system is built, and link to the bible documents rather than copying them in.
Worked example: `examples/case-packs/dead-air-on-the-meridian/GDD.md`.

```markdown
# GDD: "<title>"

## 1. One-sheet
| Genre | Platform | Session length | Player fantasy | Hook | USP | Audience |

## 2. Pillars (3–4; they settle arguments)
1. <verb-led pillar>. One line on what it forbids.
**Anti-pillars:** what we won't do.

## 3. Loops
### 3.1 Core loop: one interaction, moment to moment
ASCII diagram + a numbered walk-through of one real exchange, including the exact on-screen feedback.
### 3.2 What a decision looks like
Table: Weight | Decision | Cost/risk | Type (cosmetic / tactical / strategic / moral / informational / expressive)
Show each one is discernable now AND integrated later (Salen & Zimmerman).
### 3.3 Secondary loop (one level/case)
### 3.4 Meta loop (series)

## 4. Primary system (e.g. interrogation): what we keep, what we fix from the reference game
Fix table: reference flaw → our design. Intent/verb table: intent | example | effect | cost.

## 5. Feedback model: hidden state → what the player perceives
State variables, bands, per-character signatures, inner-voice/assist rules, calibration.

## 6. Authored structure vs generative AI (only if LLMs are used)
Pipeline diagram + exploit → defence table (see references/llm-npc-guardrails.md).

## 7. Inventory / evidence / board
Card types, notebook tabs, linking rules, the economy of risky actions.

## 8. Win/validation
How a solution is entered, how it's validated (batched? all-or-nothing?), the gate before it.

## 9. Clock / pacing / session length
Action cost table, a minimum-path budget, real-time estimate, scheduled events, the interest curve.

## 10. Failure states (fail forward; no "game over" from controls)

## 11. Set pieces

## 12. Screens / UI list

## 13. Scope: vertical slice / full / later / cut

## 14. Accessibility
```

**Quality bar:**
- Every system names the pillar it serves.
- Every decision row has a cost.
- The core loop can be explained in 60 seconds to someone who doesn't play games.
- There's a cut list.
- Every claim about another game cites RESEARCH.md.
