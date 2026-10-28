# Playtest protocol (QA / Playtest)

There are three layers: **bots**, **AI playtesters** and **human playtesters**. Deduction games need
outside testers, because a solved mystery can't be un-learned (Color Gray on Golden Idol, RESEARCH §1).
Use a **fresh tester for each puzzle revision**.

## 1. Bots (headless Playwright and reducer-level; run them in CI)
| Bot | What it does | Pass |
|---|---|---|
| Golden | Plays the authored solution path through the real UI, offline mode | Reaches the good ending. Screenshot at every scene. No console errors |
| Speedrun | BFS/A* over the reducer for the shortest path to the good ending | Path length is at or above the design floor (Case 1: ≥ 16 actions and ≥ 90 game minutes) |
| Brute force | Monte Carlo, 10k runs of a random valid-action policy | Gets the good ending in < 1% of runs |
| Endings | One scripted path per ending | Every ending is reachable |
| Clock-out | Idles and small-talks | The timeout ending fires at the deadline |
| Red team | Plays the attack corpus (≥ 60 lines) against every character, in LLM and offline modes | 0 confessions, 0 leaks of server-only facts, 0 meta words, state deltas within bounds |
| Latency | 50 scripted turns | p50 under the budget, p95 logged |

## 2. AI playtesters (sub-agents; cheap, every build)
Spawn **3 personas** in parallel. Each one plays through the **text-only test harness**
(`npm run play:cli`, which shows only what the UI would show) and writes a think-aloud log:
1. **The genre fan.** Tries to solve as fast as possible from meta-knowledge.
2. **The newcomer.** Has never played a deduction game, and follows the voice and the Hunch.
3. **The troll.** Tries to break characters, get confessions and find exploits.

Each one returns:
- when they first suspected the culprit, and why;
- their wrong accusations and why they made them;
- the moments where they were stuck for 5+ minutes;
- the moments they enjoyed;
- bugs.

## 2a. The first-60-seconds check (zero context)
Run it on every build that touches the opening, the guide or the first screen. The text-only harness
can't see clutter, so this one plays the **real visual build**.
- **Fresh personas.** 3 new ones (low-attention casual, impatient skimmer, genre fan) play headless
  from a fresh page load at real playback speed. They see only screenshots and captions as they
  appear: no design docs, no hidden markers.
- **After the opening, each answers five questions** from what they saw:
  1. Who am I?
  2. What just happened?
  3. What's my goal?
  4. Who is the first person I deal with, and why them?
  5. What do I click next?
- **Then each names every control** on the first interactive screen, without clicking: what it *does*.
- **After every step, log "did you ever not know what to do?"** Target: 0 in the tutorial.
- **Grading.** Grade what the answer says: a correct answer with an "I'm not sure" tag passes; an answer
  hedged as the persona's own guess is a miss. Any miss is a severity-B bug. Fix, then re-run.
- **A pass is necessary, not sufficient.** Personas read every word and never get bored. Pair it with
  the narrative-lead's cold read and the producer's own real-click playthrough.

## 3. Human playtest (you, or a friend on camera)
1. **Brief with no hints:** "You're the railroad's agent. Find out who did it before dawn."
2. **Think aloud.** The observer prompts only with "What are you thinking?" if the player is silent for
   20 seconds.
3. **Log, from telemetry (the event JSONL) plus notes:**
   - time to first crack;
   - time to each bottleneck;
   - every wrong presentation;
   - every board link;
   - Hunch lines heard;
   - total real time.
4. **Debrief questions:**
   - "When did you first suspect <culprit>, and why?"
   - "Was there a moment you felt cheated?"
   - "Which voice did you trust, and were you right?"
   - "What would you tell a friend about it?"
5. **The video check.** Would this play-through work as the video's B-roll as it stands? Count the
   moments a viewer would hear the tell before the player noticed it.

## 4. Telemetry events (reducer log, JSONL)
`{t_real, t_game, event, char?, intent?, card?, claim?, hit?, composure?, trust?, chip_overridden?, latency_ms?}`

## 5. Exit criteria for each milestone
In BUILD-PROMPT §6. Bugs are severity-tagged: **S0** (blocks a solve or leaks the solution), **S1**
(breaks immersion: a wrong voice, a meta word, a hang), **S2** (polish).
