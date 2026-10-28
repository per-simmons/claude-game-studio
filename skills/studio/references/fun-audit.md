# Fun audit (Creative Director + QA, run at every milestone gate)

The audit is built on MDA (target aesthetics for a mystery: **Challenge, Discovery, Narrative**) and on
Schell's lenses (Meaningful Choices #39, Triangularity #40, Surprise, Curiosity, Problem Solving, Flow,
Interest Curve, Reward, Punishment and Feedback). See RESEARCH §5.

Score each item **Pass / Weak / Fail**, with evidence from the playtest logs or telemetry. Any **P0**
failure blocks the gate.

## P0: must pass
1. **The 60-second rule.** After the first minute, a newcomer can say who they are, what happened,
   what their goal is and what to click next. Measured by `playtest-protocol.md` §2a, never by
   opinion.
2. **First wow under 2 minutes** (the hook lands). Example: the first directed line that makes a viewer
   lean in.
3. **The core skill is real.** At least one moment per session where *listening* changed what the
   player did (logged: they acted on a tell or a baseline deviation).
4. **Honest nerves.** The player misreads at least one honest-but-nervous character, and finds out
   later that they did. (Calibrated tells; L.A. Noire's "too readable" flaw is fixed.)
5. **Meaningful choices (Schell #39).** Every heavy decision changed what the player saw later
   (*integrated*), and the player could perceive that (*discernable*).
6. **Fair (Knox/Van Dine).** In the debrief, no tester says they felt cheated by information they
   couldn't have had. On a re-watch, the key clues are audible or visible.
7. **Not too easy.** The speedrun bot's path is at or above the floor, and no AI or human tester solved
   it in under 10 minutes.
8. **Not stuck.** No tester was stuck for more than 7 minutes without a proactive clue or Hunch nudge
   arriving.
9. **Unbreakable.** Red-team pass, plus zero leaks in human sessions.
10. **No dead air.** No pause over 4 s between a player's turn and the first audio. Over 2.5 s is Weak.
    Between consecutive voiced beats, no gap over 0.25 s (measured, `vo-director.md` pacing defaults).

## P1: should pass
11. **The interest curve** has a hook, a rising middle, a dip of confusion after the first reframe, a
    climax, and release (Schell).
12. **Surprise.** At least 2 "oh!" moments per session (the twist layers), heard in think-aloud.
13. **Triangularity (#40).** There's a safe-but-slow option and a risky-but-fast one (accusing early,
    bluff-presenting), and testers notice the trade.
14. **Reward and punishment.** A miss costs something, but never ends the case early.
15. **Every set piece lands.** The face-off is the clip a viewer would share.
16. **Every herring is honest.** Testers can explain each red herring after the reveal.
17. **The ending feels earned.** The confession quotes something the player found.

## P2: polish
18. Replay value (the other endings tempt you).
19. Accessibility toggles work.
20. **Filmability.** The Director's View is readable at 1080p; captions don't cover the focal point;
    the Video Mode logs line up.

## The output
A table with `Item | Score | Evidence | Fix`. Put it in `qa/fun-audit-<milestone>.md` and summarise it
in 3 lines to the Producer.
