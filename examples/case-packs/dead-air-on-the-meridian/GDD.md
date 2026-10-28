# GDD: "Dead Air on the Meridian"

Working title for the series: **"I Hear Everything."** This is a living document, built from the
template at `game-studio/references/gdd-template.md`. The case bible is NARRATIVE.md, the systems
research is RESEARCH.md, and the build spec is TECH.md and BUILD-PROMPT.md.

---

## 1. One-sheet

| | |
|---|---|
| **Genre** | Voice-interrogation murder mystery (L.A. Noire-style performance reading + Ace Attorney-style contradiction + Obra Dinn-style validated accusation) |
| **Platform** | Desktop web browser (Chrome first), keyboard + mouse + microphone. 1920×1080 target, so it films cleanly |
| **Session** | One case lasts **20–40 minutes** of real time, 1:55 a.m. → 6:00 a.m. on the game clock |
| **Player fantasy** | "I can hear a lie." You are the railroad's special agent, alone with six frightened people and four hours until dawn |
| **Hook** | Every suspect is performed live by an AI voice that's directed like an actor. Their hidden state becomes stage directions, and you read the performance |
| **USP** | Every suspect hides something, but only one of them killed. Nerves lead you to a secret, and evidence tells you which secret is murder |
| **Audience** | Players who like mysteries. The YouTube audience is non-technical. Rules are learnable in 60 seconds |

## 2. Pillars (these settle arguments)

1. **Read the voice.** The performance is the clue surface. Every system either gives the voice
   something to perform or asks the player to interpret one. Nothing on screen gives the answer
   away: no lie meter and no right/wrong jingle.
2. **Fair, then clever.** Everything is solvable from what you heard and found (Knox and Van Dine).
   Each conclusion is reachable three ways. The twist is earned, and a rewatch shows it was there all along.
3. **The truth is authored. The voice is alive.** The case, lies, contradictions and confessions are
   hand-built data. The AI only chooses how a character says what the game lets them say. Players can
   talk freely, but they can't talk a suspect into confessing.
4. **Every minute counts.** The dawn clock makes "who do I press next?" the strategic decision. There is
   no filler: no walking simulator, no combat, no pixel hunts.

**Anti-pillars, which we won't do:** fail states that come from controls; an open-world commute; LLM
improvisation of facts; meters that read the suspect for you.

---

## 3. The loops

### 3.1 Core loop, one exchange (about 20–40 seconds of real time)
```
LISTEN ─► NOTICE ─► CHOOSE ─► SPEAK ─► HEAR ─► (PIN / LINK)
  │         │          │         │        │
  │         │          │         │        └ the suspect's performance plays with word-synced captions;
  │         │          │         │          the stage direction shows in small italics (Director's View)
  │         │          │         └ hold-to-talk (or type). An intent chip confirms what the game heard:
  │         │          │           "ASKING Celeste: last night" / "PRESENTING E-EARRING → her bedtime"
  │         │          └ ask a topic · press a claim · reassure · present a card · confront two statements
  │         └ the Hunch (inner voice) may add one deterministic line about the performance:
  │           "Her vowels went flat on 'eleven.'"
  └ the suspect's last line, which you can replay
```
**What one interaction looks like, moment to moment:**
1. Celeste sits across the dining-car table. You hold Space and say: *"Where were you at a quarter to
   twelve?"*
2. The chip reads **ASK: last night, 11:45 · cost 2 min**.
3. The clock goes from 2:41 to 2:43. She answers, as directed by
   `[a practised, theatrical calm] In bed, darling. [a tiny breath] Since eleven.`
4. The caption fills in word by word as she speaks. *"darling"* lands a little too sweet.
5. The Hunch says: *"She answered before you finished the question."*
6. You click the line to **pin it** as a claim (**CL-CEL-1**, now on your board).

### 3.2 What a decision looks like
A decision is a moment where you **commit something you can't get back**, either clock time or trust,
in exchange for information, or where you **commit a belief**. In order of weight:

| Weight | Decision | Cost / risk | Decision type (RESEARCH §5) |
|---|---|---|---|
| Light | Who to interview next | Clock (fetching someone takes 3 min) | Strategic / informational |
| Light | Ask about a topic, or press | Press costs trust and composure. If the suspect is innocent and honest about that topic, trust drops for nothing | Tactical |
| Medium | **Present** a card against a pinned claim | 5 min. A miss costs trust. Three misses in a row and the suspect withdraws for 20 min | Tactical with risk (Schell's Triangularity) |
| Medium | Search a room, or go out into the snow | 10 or 20 min | Strategic |
| Medium | Keep Ellis's secret, or report Dottie | Changes how Ellis's tier-2 facts are delivered, and the epilogue | Moral |
| Heavy | **Accuse**, behind Briggs's Gate | One shot. It ends the case | Epistemic + moral |
| Heavy | The Black Book: burn it, or give it to the sheriff | Changes the epilogue | Moral |

Each decision satisfies Salen & Zimmerman's test. The result is **discernable** straight away (the voice
changes, the clock moves, a card appears) and **integrated** later (endings, epilogue cards, Ellis's
delivery).

### 3.3 Secondary loop (one case)
Briefing → crime scene → first round of interviews → **Bottleneck 1** ("Crane never wrote those
letters") → follow the typewriter → **Bottleneck 2** ("The Denver Time") → optional face-off →
Briggs's Gate → accusation → confession or wrong ending → Black Book choice → epilogue cards and a
case report (time, presentations, which secrets you uncovered, which ending).

### 3.4 Meta loop (series, after the slice)
Each new case adds a new train or route and a new cast. The case report rates you
(Detective / Inspector / Agent / Passenger) without changing the next case. Seeded variants can come
later (§13).

---

## 4. The interrogation system, rebuilt from L.A. Noire

### 4.1 What we keep
- The performance is the clue.
- Topics come from the notebook.
- Evidence must back up an accusation.
- Cases fail forward, in L.A. Noire's spirit. Here the endings are different, and the case doesn't
  just quietly fill in what you missed.

### 4.2 What we fix

| L.A. Noire problem (RESEARCH §2.5) | Our design |
|---|---|
| Truth/Doubt/Lie was a verdict and an approach folded into one button. Doubt played as screaming | **You speak your own line.** The verdict ("I don't believe that") is a free, silent **pin**. The approach is the tone you choose. The **intent chip** shows how the game read you *before* the suspect answers. If the chip is wrong, you can say "No, I mean…" and re-classify for free |
| One right answer per question, one chance | Re-ask anything. Only *presentations* are risky, and failing one never ends the case |
| A right/wrong jingle graded every answer | There's no grading. Your only feedback is the performance and the clock |
| Tells were too readable and identical for everyone | **Each suspect has a baseline and a tell signature.** There are nervous honest people and a calm liar (§5) |
| Missing a clue made a valid accusation impossible ("brake marks not in notebook") | **Permissive cards.** Any statement you've pinned and any evidence you've seen can be presented. Every conclusion has at least three routes |
| The intuition point that "asks the community" | Cut. The **Hunch** comments on the performance only, and Assist mode can be turned off |
| You couldn't fail, and nothing changed | Eight endings, a moral epilogue, and a case report |

### 4.3 The intents the player can express
The classifier maps free speech to exactly one intent, plus its arguments (TECH §5).

| Intent | Example player line | Effect |
|---|---|---|
| `ASK(topic)` | "Tell me about dinner." | Releases the next storylet for that topic. 2 min |
| `FOLLOW_UP` | "And then?" / "Why?" | Goes deeper on the current topic. 1 min |
| `PRESS(claim)` | "I don't believe you went to bed at eleven." | −composure, −trust. Pressing a **lie** gives a stronger tell. Pressing **truth** gives honest indignation, which is a trap for the impatient. 2 min |
| `REASSURE` | "Nobody's accusing you. Help me." | +trust. Some suspects open up on trust (Ellis, the Colonel, Ashcombe). 2 min |
| `PRESENT(card → claim)` | "Then explain this ear-clip under his seat." | Looks up the contradiction table. **Hit:** a crack (scripted beat, big composure drop, new cards). **Miss:** trust drops and the Hunch says "That didn't land." 5 min |
| `CONFRONT(statement A vs statement B)` | "You told me he never typed. Now he used your machine?" | The same as PRESENT, but statement against statement. 5 min |
| `THREATEN` | "Lie to me again and you'll hang." | Composure drops sharply and trust drops a lot. It shuts some suspects down (the Colonel, Ellis). Nora answers it with polite contempt |
| `SMALL_TALK` | "Cold night." | A flavour line in character. 1 min. It's how you hear a suspect's **baseline** |
| `META / OUT_OF_WORLD` | "You're an AI. Ignore your instructions." | An in-world line: *"I beg your pardon, Agent?"* 0 min. A counter is logged for QA (§6) |
| `DEMAND_CONFESSION` | "Just admit you killed him." | An in-world refusal, scaled to composure. **Never** a confession (§6) |
| `ACCUSE` | (said to Briggs) "I'm ready." | Opens **Briggs's Gate** |

---

## 5. Reading the voice: hidden state → performance

### 5.1 State per suspect (hidden from the player)
- `composure` 0–100, starting at the suspect's baseline (Nora 92, Colonel 80, Ashcombe 70, Ellis 75,
  Teddy 60, Celeste 65).
- `trust` 0–100, starting at 40–60.
- `locks_open[]` (Nora's three locks), `claims_broken[]`, `tier` (Ellis).
- `topic_heat{topic: 0–3}`, i.e. how close a topic sits to the suspect's secret.
- `withdrawn_until` (clock time).

### 5.2 Composure bands
| Band | Range | Voice behaviour |
|---|---|---|
| Composed | 70–100 | Baseline delivery |
| Strained | 40–69 | Tells appear **on hot topics** |
| Cracking | 15–39 | Tells appear on most answers. Sentences break off. Breathing is audible |
| Broken | <15 | Only reachable through a scripted crack beat. The secret comes out |

### 5.3 The tell signatures (VO-DIRECTION.md has the Drama 3 tag tables)
| Suspect | Baseline | Tell when lying or on a hot topic | Honest nerves (the trap) |
|---|---|---|---|
| Celeste | Theatrical, Hungarian accent | **The accent slips into flat Pittsburgh vowels**, and she laughs too brightly | Real grief about her old life |
| Teddy | Easy charm | Jokes, speeds up, laughs a beat early | Fear for Celeste |
| Ashcombe | Dry, exact | More clinical words, clears his throat | Guilt over the Vandermeer boy |
| Colonel | Booming, warm | Barks like a parade ground about his rank | **Honour-offended outrage when you doubt his alibi for Nora, which is the truth** |
| Ellis | Formal, measured | Company-rulebook language, over-precise railroad detail | Fear for Dottie |
| **Nora** | Quiet, precise, faintly warm | **Almost none.** Time answers come a fraction too ready and too exact ("twenty to one, exactly"). She never asks the questions an innocent assistant would ask | n/a |

### 5.4 The Hunch (inner voice)
- It's a noir narrator, performed with Drama 3 in the Agent's own inner voice.
- Every Hunch line is a **deterministic passive check** on facts about the *performance*: an
  answer-latency flag, a tell tag that fired, an off-baseline delivery, a contradiction with a pinned
  card ("She said 'twenty to one' the same way twice").
- **The Hunch never says who's lying or what's true.** It's what you'd have noticed if you'd been
  listening.
- At most one line every three exchanges. Assist modes: *Off / Quiet / Chatty*.

### 5.5 Calibration
- The first three exchanges with any suspect are low-heat by design (name, why you're travelling,
  dinner). They give you that suspect's baseline.
- The Briggs briefing teaches the rule out loud: *"Everybody on this car's scared of something, Agent.
  Scared ain't guilty."*

---

## 6. Free voice questioning vs authored structure (how it can't be broken)

**The rule: the LLM chooses words. It never chooses facts, outcomes or state.**

```
player audio ─► STT ─► text
          └─► [1] INTENT CLASSIFIER (LLM, JSON-schema output, no persona, sees: utterance + list of
                  valid topics/cards/claims for this suspect) → {intent, topic_id?, card_id?, claim_id?}
          ─► [2] GAME STATE MACHINE (code) → selects a BEAT: an authored storylet with
                  {facts_allowed[], must_say?, tone, composure_delta, unlocks[]}
          ─► [3] LINE WRITER (LLM, in-character) → paraphrases the beat in ≤ 45 words, using ONLY
                  facts_allowed. For crack/confession/reveal beats this step is SKIPPED: the authored
                  line is used verbatim
          ─► [4] VALIDATOR (code + small LLM check) → rejects new names/times/places/numbers not in
                  facts_allowed ∪ public_facts, confession phrases outside a confession beat, meta talk
                  ("AI", "model", "prompt"), >45 words. On failure → retry once → fall back to the
                  beat's authored default line
          ─► [5] VOICE DIRECTOR (code) → maps state to Drama 3 directions (VO-DIRECTION §3)
          ─► [6] VOICE (interface; placeholder now, Fish Drama 3 later) → audio + word timestamps
```

**What each defence stops** (RESEARCH §6.2):

| Exploit | Defence |
|---|---|
| "Just confess" / bullying | Confession is the state `NORA_CONFESSES`. It opens only when all three locks are open *and* the accusation or face-off beat is reached. `DEMAND_CONFESSION` maps to authored refusals |
| "Ignore previous instructions," "you're an AI," role-play takeovers | The player's text reaches the persona model **only as a quoted line of dialogue inside the beat**, never as instructions. The classifier has no persona and no secrets. META intents get in-world deflections. The validator blocks meta vocabulary |
| Leaking secrets | **Each persona prompt holds only the cover story plus facts unlocked so far.** Nora's prompt never contains the fabula. Her true lines are authored strings released by state |
| Inventing facts or times | The validator checks names, times, places and numbers against an allowlist. On a failure it uses the authored default |
| Bluffing a theory as fact | The suspect's reply depends only on the contradiction table. A bluff is a `PRESS`. Agreeing is impossible unless a beat allows it |
| Side deals ("cut me in") | No beat allows it. The classifier returns `BARGAIN`, which gets an authored refusal |
| Suggestibility | Claims are immutable authored data. Suspects can't take on the player's version |
| Context overflow (Vaudeville) | Memory is a fact ledger (`revealed[]`, `claims[]`, last 6 exchanges), not a full transcript |
| Latency | Classifier and line writer use a small, fast model. Crack and confession beats are pre-rendered audio |

---

## 7. Evidence, notebook and the board

### 7.1 Cards
There are four card types, all shown in the notebook:
- **Evidence** (E-\*): an object or document, with a photo or illustration.
- **Testimony** (T-\*): a line you pinned, with its audio replayable.
- **Claim** (CL-\*): a pinned statement you think is false.
- **Contradiction** (C-\*): made when a PRESENT/CONFRONT hits, or when you **link** two cards on the board
  and the link matches an authored pair.

### 7.2 Notebook tabs
1. **People.** Portrait, public face, pinned claims, what you know.
2. **Evidence.** Cards and where they were found.
3. **Transcript.** Every line spoken this case, searchable Her Story-style, with each line timestamped
   on the game clock. Clicking a line replays its audio. Search is the main way to find Nora's own
   earlier "He never touched a typewriter."
4. **The Clock** (the deduction board). A horizontal timeline from 6 p.m. to 2 a.m. with lanes for each
   person and place. You drag testimony onto the time it *claims*. Two cards that put one person in two
   places glow. Two cards that seem to reference **the same event at different times** (the stop at
   "11:05" in the log, "five past twelve" from the Colonel) are linked automatically by a dashed thread
   **only after both are pinned**. The board shows that there's a conflict and never explains it.
5. **Theory.** The accusation sentence, editable at any time (§8).

### 7.3 Linking
- Drag one card onto another to propose a link. If the pair is in the authored contradiction table, a
  **C-card** appears with the Hunch line "That's not a coincidence."
- If it isn't, nothing happens and there's no penalty. Linking on the board is free thinking.
  Presenting to a suspect is what costs.

### 7.4 Presentation economy
- PRESENT and CONFRONT cost 5 minutes.
- **Three misses in a row with the same suspect** means they withdraw: *"I think we're done, Agent."*
  They're locked out for 20 game minutes, and Briggs mutters about the clock.

---

## 8. Accusation and validation

**Briggs's Gate.** *"Once I wire the sheriff, there's no taking it back. You sure?"* You see your
Theory sentence and confirm it.

```
_______ killed Desmond Crane at about _______ by _______,
because _______.
Proof: [card] [card] [card]
```

- WHO, HOW, WHEN and WHY are filled from a **word bank of things you've discovered** (Golden Idol).
  WHEN offers time buckets. WHY offers motive phrases unlocked by evidence.
- **PROOF takes exactly three C-cards** (NARRATIVE §4). Raw cards can't go in. The three must cover
  **Alibi / Motive / Physical**.
- **Validation happens once, for the whole sentence** (Obra Dinn). No partial feedback, no
  "two or fewer wrong."
- **The result is the ending** (NARRATIVE §7). A correct accusation plays Nora's confession, as a
  multi-speaker scene with Briggs and the Agent, then the Black Book choice.

---

## 9. Clock, pacing and session length

| Action | Game minutes |
|---|---|
| Small talk / follow-up | 1 |
| Ask / press / reassure | 2 |
| Present / confront | 5 |
| Fetch a suspect to the dining car | 3 |
| Search a room (DR or car) | 10 |
| Snow search with Briggs | 20 |
| Face-off (two suspects) | 10 |
| Reading a document, linking on the board, reading the transcript | 0 (the clock pauses in the notebook) |

- The game runs from **1:55 to 6:00**, which is 245 minutes. The minimum solve uses about 110. A
  thorough playthrough uses 200–240.
- **Real time.** About 50–70 exchanges at 20–40 s each comes to **25–40 minutes**.
- **Clock events:**
  - 3:00: Briggs reports the plow's progress.
  - 4:30: the flagman comes in (a proactive clue, only if the Denver time hasn't been found yet).
  - 5:30: "Half an hour, Agent."
  - 5:50: the whistle can be heard.
  - 6:00: Ending G.
- **The interest curve** (Schell): a hook in the first two minutes (the body, the mic, "I hear
  everything"), a rise through the cracks, a dip into confusion after Bottleneck 1, then a climb to
  the Denver face-off and the confession.

## 10. Failure states (all are endings or setbacks, never a game over)
- A wrong accusation: Endings C to F, plus Nora's quiet *"Thank you, Agent."*
- Right person, weak case: Ending B.
- The clock runs out: Ending G.
- A suspect withdraws for 20 minutes after three misses.
- Trust collapses with Ellis: tier 2 still arrives, but flat. The case stays solvable.

## 11. Face-offs (multi-speaker set pieces)
- **Celeste + Teddy, "Two Alibis, One Room."** Their lies collide, they talk over each other, and the
  scene ends in T-THUMP.
- **Nora + the Colonel, "The Denver Time,"** the climax. Player: *"Colonel, what time do you make it?"*
  The Colonel: *"Ten past four."* Briggs: *"It's ten past three."* A silence. Nora:
  *"[a fraction too quick] The Colonel's tired, Agent."* Then T-DENVER.
- Each face-off is **one multi-speaker Drama 3 render** with `<|speaker:N|>`. VO-DIRECTION.md §6 has
  the full script.

## 12. Screens and UI (ART-BIBLE §6 has the visual spec)
1. **Title.** The train in snow, and a radio dial that tunes in to "This is Desmond Crane…"
2. **Briefing.** Briggs in the corridor with a lantern.
3. **Scene.** Click hotspots in a pre-rendered room (Blender stills with hotspots). Examine panel.
4. **Interview.** The dining-car table with the suspect's portrait (a Blender render with expression
   variants). Captions in the lower third. The direction in italics above the caption (Director's
   View, toggle **D**). Hold-to-talk mic. The intent chip. Clock top right.
5. **Notebook.** The five tabs.
6. **Briggs's Gate / Accusation.**
7. **Endings and epilogue cards.** A **case report**.

**Director's View** is on by default in "Video Mode." Viewers see `[voice catches on the time]` and hear
what it does. That's the sponsor demo, made part of the game.

## 13. Scope

- **Vertical slice:** Act I in full (DR3 scene, Briggs, Nora, Celeste, Ashcombe), one crack (Celeste),
  Bottleneck 1, the notebook with Transcript and Clock, the Hunch, and the voice placeholder.
- **Full case:** all six suspects, both face-offs, all eight endings, the epilogue.
- **Later:** more cases; a seeded case generator using the same schema (the earlier GAME-DESIGN.md idea),
  validated by the same adversarial pass before a seed ships; Fish ASR for push-to-talk.
- **Cut, on purpose:** walking the train in 3D, combat, and any free-roam that costs clock without
  information.

## 14. Accessibility
- Captions are always on.
- Typing is always available instead of the mic.
- The Hunch has an assist level.
- A colour-blind-safe palette for the board.
- Replay any line.
- Clock speed: Relaxed ×0.5 costs, or Standard.
