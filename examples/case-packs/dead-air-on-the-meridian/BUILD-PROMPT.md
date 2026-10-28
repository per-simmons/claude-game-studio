# BUILD PROMPT: "Dead Air on the Meridian"

**This prompt is run by the Producer, not by one monolithic builder.** Start it with
`claude --agent game-studio:producer` in your game folder, and paste in everything below the line. The Producer drives the studio's employee sub-agents
**in parallel** off a shared board, routes the cross-department reviews, writes STATUS.md, and stops
at the publisher's gates.

The prompt points at design documents that already exist on disk. Read them; don't redesign them.

---

## 0. Mission
Build **"Dead Air on the Meridian,"** a browser murder-mystery game. You interrogate six suspects aboard
a 1936 sleeper train, stopped overnight by a snow slide, before the sheriff arrives at dawn. Every
suspect is voiced, with stage directions generated from their hidden emotional state, and the core
skill is **reading the voice**. Every suspect hides a secret, but only one is the killer. Nerves lead
you to a secret, and evidence tells you which secret is murder.

The bar is **exceptional**: the kind of game a stranger plays to the end and tells a friend about. It
must be fair, clever, unbreakable, fast and beautiful. It will be filmed for a YouTube video, so it also
has to *read on camera*.

## 1. Source documents (read them all before writing code)
All are in this case-pack folder (`examples/case-packs/dead-air-on-the-meridian/`):

| File | What it is | How authoritative |
|---|---|---|
| `GDD.md` | Pillars, loops, interrogation system, intents, board, accusation, clock, endings, UI | Design truth |
| `NARRATIVE.md` | **The case.** Cast, minute-by-minute timeline, solution, every clue and lie, the branching map, endings. Rev 2.1, adversarially reviewed | **Content truth. Don't change the plot.** If you find a hole, log it in `qa/narrative-issues.md` and propose a fix; don't patch silently |
| `TECH.md` | Architecture, state machine types, turn pipeline, guardrails, voice interface, Fish spec, QA gates, RunPod | Engineering truth |
| `VO-DIRECTION.md` | Voice profiles, the state → direction tables, sample directed lines, lint rules, face-off scripts | Voice truth |
| `ART-BIBLE.md` | Look, palette, character specs, scene list, UI type, what's 2D vs Blender | Art truth |
| `RESEARCH.md` | Why each choice was made, with sources | Background |

Skill references are in the plugin's `skills/studio/references/`:
- `case-file.schema.json`
- `llm-npc-guardrails.md`
- `playtest-protocol.md`
- `fun-audit.md`
- `asset-pipeline.md`
- `character-sheet-spec.md`
- `runpod-blender.md`

## 2. Hard rules
1. **Do NOT call the Fish Audio API.** No requests to `api.fish.audio`, no Fish MCP, no Fish SDK
   network calls. Build `FishDrama3Voice` against **fixtures** only (TECH §6.3), behind
   `VOICE_PROVIDER=fish-drama3` **and** `FISH_ENABLED=true`, both off by default. The game ships on
   `PlaceholderVoice`.
2. **No IP.** No Poirot, no *Murder on the Orient Express*, no Christie characters, titles or plots, no
   L.A. Noire names or assets, and no real railroad logos or liveries. Use only the invented names in
   NARRATIVE.md.
3. **No other TTS vendors' names** anywhere in the game or its docs. Fish is the sponsor.
4. **Keep it blind and tool-agnostic.** The game's UI and content never name the LLM, the image model,
   OpenRouter or any AI tool. The only credit is an optional Video Mode line, "Voices: Fish Audio Drama
   3," which appears only when the Fish provider is enabled.
5. **Image generation uses the route in `studio/studio.config.json` → `image`** (manual prompts by default). Never hardcode keys. Every change is a fresh generation with no
   chained edits.
6. **LLM calls go through OpenRouter.** Take `OPENROUTER_API_KEY` from your own OpenRouter account and put it in the project's gitignored `.env`.
   Never print it. Models are set in `.env` (TECH §1). The game must also be **fully completable in
   `LLM_MODE=offline`**.
7. **Never steal focus.** Playwright runs headless. If a headed window is unavoidable, place it off your main work area, and never activate it.
8. **Optional recording guard.** If `pro.respect_recording` is on, wait while the recorder process runs before heavy local work.
9. **Don't touch other agents or tmux/iTerm sessions** you didn't start.
10. **RunPod:** only through `bin/runpod-blender-render.sh`, with `MAX_PRICE ≤ 0.40` and
    `MAX_MINUTES ≤ 45`. Always confirm teardown. Log `$/hr × wall time`.
11. **Facts in docs come from sources.** Don't invent period facts. Mark anything unsure as UNVERIFIED.

## 3. File layout
Everything lives under your game folder (e.g. `engine/`):
```
train-mystery-game/
  prompt.md                      ← a copy of this prompt
  README.md                      ← run/test instructions, milestone status
  package.json  tsconfig.json  vite.config.ts  .env.example  .gitignore
  docs/                          ← copies of GDD, NARRATIVE, TECH, VO-DIRECTION, ART-BIBLE (read-only mirrors)
  content/
    schema/case-file.schema.json
    case-01/case-file.json       ← NARRATIVE.md as data (M1)
    case-01/lines.tsv            ← VO line sheet (VO-DIRECTION §4 format)
    voices.json                  ← cast → placeholder params; fish voice ids empty until the publisher casts
    directions.json              ← state→direction tables (VO-DIRECTION §3) as data
  server/
    index.ts  turn.ts  classify.ts  classify-offline.ts  write.ts  validate.ts  direct.ts  lint-lines.ts
    openrouter.ts  cache.ts  case.ts (loads file, strips server-only fields for /api/case)
    voice/provider.ts  voice/fish-drama3.ts (disabled; fixtures only)  voice/sse.ts
  src/
    main.ts  engine/{types.ts,reducer.ts,clock.ts,contradictions.ts,accuse.ts,storylets.ts}
    voice/{placeholder.ts,silent.ts,captions.ts}
    ui/{title.ts,briefing.ts,scene.ts,interview.ts,notebook.ts,board.ts,transcript.ts,gate.ts,ending.ts,chip.ts}
    styles/{tokens.css,ui.css}  assets/ (manifest.json)
  scripts/
    lint-case.ts  play-cli.ts  speedrun.ts  bruteforce.ts  redteam.ts  latency.ts  render-lines.ts (Fish; disabled)
    masks_to_polys.py
  tests/
    unit/*.test.ts  e2e/*.spec.ts  redteam.jsonl (≥60)  fixtures/fish-sse-{single,multi,null-align}.txt
  blender/  scenes/*.py  props/*.py  proxy_bust.py  render_local.sh
  art/  style-frames/  sheets/<CH-ID>/  final/  ui/
  bin/  runpod-blender-render.sh  render.py   (pro, optional)
  qa/  screenshots/<milestone>/  playtest-logs/  fun-audit-<milestone>.md  narrative-issues.md
  recordings/  cache/            ← gitignored
```

## 4. How the build runs: the Producer and the studio
**You are the Producer.** You don't write the game yourself. You plan, launch, review and integrate.
The rules are in `operating-model.md` (plugin `skills/studio/references/`).

### 4.1 Set up (M0, you do this)
1. `git init` the game folder. Copy the project template (`studio/studio.config.json`, `STATUS.md`,
   `.env.example`, `.gitignore`).
2. `board.py init --game "Dead Air on the Meridian"`.
3. **Import the content. Don't re-author it.** The case is already data:
   `examples/case-packs/dead-air-on-the-meridian/case-file.json` is lint-PASS and auto-solves in 18
   actions. Copy it to `content/case-01/`. The terminal engine in `scripts/casepack/engine.py` is the
   **reference implementation** of `engine-semantics.md`. The web reducer must match it, and the tests
   run both engines on the same scripts.

### 4.2 The employees and what they own
| Employee (sub-agent) | Owns | Reviewed by |
|---|---|---|
| `engineer` lane **core** (worktree `eng-core`) | `src/engine`, `server/`, the offline mode, `scripts/lint-case.ts`, `play-cli.ts` | qa-lead |
| `engineer` lane **ui** (worktree `eng-ui`) | `src/ui`, `src/styles`, `src/voice/captions.ts` | qa-lead + art-director (look) |
| `engineer` lane **voice** (worktree `eng-voice`) | `server/voice/*`, the Fish fixtures, the casting page (**no Fish calls**) | qa-lead + vo-director |
| `engineer` lane **tests** (worktree `eng-tests`) | `tests/`, `scripts/{speedrun,bruteforce,redteam,latency}.ts` | qa-lead |
| `ui-designer` | Screen flow, wireframes, the accessibility checklist | art-director + qa-lead |
| `vo-director` | `content/case-01/lines.tsv`, `content/directions.json`, `voices.json` | narrative-lead (words) + qa-lead (lint V-01–V-06) |
| `art-director` | Style frames, art review | the publisher at G-ART |
| `character-artist` | `art/sheets/*`, portraits | art-director |
| `blender-artist` (pro) | `blender/scenes/*.py`, props, proxies | art-director |
| `render-wrangler` (pro) | RunPod finals, masks | art-director (look) + producer (cost) |
| `narrative-lead` | Owns the case. Logs any engine-found hole in `qa/narrative-issues.md` and fixes it in the bible and the case file | story-auditor (mode C) |
| `qa-lead` | Bots, red team, fun audit, vision QA, **bugs filed back to engineers** | producer |

### 4.3 The cycle, every time
1. **Plan.** Write the cycle goal in STATUS.md. Add tickets with owner, deps, reviewer, milestone and
   outputs (§4.4).
2. **Launch.** Every ticket that's ready and has its deps met starts **in one message**, as several
   Agent calls. Engineer lanes use `isolation: "worktree"`. Brief each employee with its ticket ID, its
   input paths, its output paths and the acceptance criteria from §5.
3. **Review.** As tickets arrive `in_review`, launch their reviewers in parallel. Changes-requested
   tickets go back to their owner. At round 3, you decide or cut.
4. **Integrate.** Merge the worktree branches in dependency order (core → tests → ui → voice), then
   run §6 on the merged tree.
5. **QA.** The qa-lead runs the gates and files bugs with `board.py bug --severity A–D`. Engineers fix
   them in severity order, and the qa-lead verifies each one from a clean boot.
6. **Standup.** Rewrite STATUS.md from `board.py standup`.
7. **Gate.** At M3 and M5, write `studio/gates/G1.md` / `G-ART.md` and **stop for the publisher.**

### 4.4 Ticket plan (deps → parallel waves)
| Wave | Tickets running in parallel | Deps |
|---|---|---|
| M0 | eng-core: scaffold + server + reducer skeleton · eng-tests: Vitest/Playwright harness · ui-designer: flow + wireframes · vo-director: lines.tsv + directions.json from the case file | none |
| M1 | eng-core: TS reducer matching `engine.py` (parity tests) + lint-case · eng-tests: parity runner + speedrun/bruteforce on the TS reducer | M0 core, M0 tests |
| M2 | eng-core: turn pipeline offline + `play-cli` · eng-voice: PlaceholderVoice + captions sync · art-director: style frames (S1, S2) | M1 |
| M3 | eng-ui: interview screen, notebook, board, Director's View · eng-core: live LLM mode + validator · eng-tests: red team + latency · character-artist: Nora, Celeste and Ashcombe portraits · qa-lead: bots + AI personas + fun audit P0s → **G1** | M2, plus style frames approved |
| M4 | eng-core: the rest of the case (face-offs, endings, clock events) · eng-ui: accusation form, endings, case report · qa-lead: full bots + red team | G1 approved |
| M5 | character-artist: all sheets/portraits · blender-artist: S1–S9 · render-wrangler: RunPod finals · eng-ui: hotspot masks to polygons · art-director: reviews → **G-ART** | M4 (art can start after G1) |
| M6 | eng-voice: FishDrama3Voice against fixtures + casting page + FLIP-THE-SWITCH.md (**no network**) | M4 |
| M7 | qa-lead: full playtest protocol + fun audit · eng-ui: Video Mode · producer: README + postmortem | M5, M6 |

## 5. Milestones and acceptance criteria
Each milestone is a set of board tickets (§4.4). It's done when every ticket is approved, the
qa-lead's §6 run is green on the merged tree, and STATUS.md is updated. **Stop
for the publisher's review at M3, the vertical slice, and at M5 for the art direction.**

### M0: Scaffold
- [ ] Vite + TS client and a Node (Hono) server. `npm run dev` serves on :5173 with the API on :8787.
- [ ] `.env.example` with `OPENROUTER_API_KEY`, `LLM_MODE=offline|live`, `LLM_CLASSIFIER_MODEL`,
      `LLM_WRITER_MODEL`, `VOICE_PROVIDER=placeholder`, `FISH_ENABLED=false`, `FISH_API_KEY=`.
- [ ] `npm test` (Vitest) and `npm run e2e` (Playwright **headless**) both run and pass the trivial tests.
- [ ] A headless screenshot of the title placeholder is in `qa/screenshots/m0/`.

### M1: The case as data
- [ ] `content/case-01/case-file.json` is **imported** from the shipped case pack (already transcribed
      and lint-PASS). TS-reducer parity with `engine.py` is tested on the same command scripts. It covers:
  - all characters, with public/secret split, baselines and tells;
  - claims (`is_true`, with "true on the Colonel's clock" notes);
  - all E-, T- and C- cards, with act, role and proof category;
  - contradictions, links and storylets for every topic in §5–7;
  - solution, endings, timeline, Hunch lines and refusals.
- [ ] It validates against the schema (Ajv).
- [ ] `scripts/lint-case.ts` passes all the TECH §7 checks:
  - IDs resolve;
  - **≥3 routes per essential conclusion with the optional branches off**;
  - herrings are resolved;
  - endings are reachable;
  - **no PROOF category can be filled from Act I cards**;
  - minimal path ≥ 16 actions;
  - no solution fact sits in `facts_allowed` before its gate.
- [ ] Unit tests cover the reducer basics: clock costs, the contradiction hit/miss path, the three-miss
      withdrawal, Nora's locks, accusation validation for every ending.

### M2: First playable (text plus placeholder voice)
- [ ] The turn pipeline works end to end in **offline mode**: regex classifier, then storylet
      selection by salience (most specific match wins), then authored default, then the validator,
      then the voice director, then the line lint.
- [ ] `npm run play:cli` plays the whole case in a terminal: the same information as the UI, typed
      commands and free text.
- [ ] The golden bot (CLI) reaches **Ending A**. Bots for each ending reach B–H.
- [ ] `PlaceholderVoice` speaks lines in the browser with per-character pitch and rate, and emits word
      boundaries.

### M3: Vertical slice (stop for the publisher's review)
This is RESEARCH's "a fully realized portion… encompassing all its essential elements."
- [ ] **Act I and Bottleneck 1 are fully playable in the UI:**
  - the Briggs briefing;
  - the DR3 scene with every hotspot (examine and rub the pad);
  - interviews with Nora, Celeste and Ashcombe;
  - Celeste's crack (E-EARRING → T-NEVERWROTE);
  - the Box 1129 topic.
- [ ] **The interview screen** (GDD §12 and ART-BIBLE §6):
  - the portrait, with expression states swapped by composure band;
  - hold-to-talk (Web Speech API) with typing as a fallback;
  - the **intent chip** shown before the reply, with "No, I mean…" re-classify;
  - word-synced captions;
  - **Director's View** (italic direction above the caption, toggled with D);
  - the clock dial.
- [ ] **The notebook:** People, Evidence, **Transcript** (searchable; click a line to replay it) and
      **The Clock** (drag cards onto the timeline; conflicts glow; links create C-cards).
- [ ] The Hunch inner voice gives deterministic lines at most once every 3 exchanges, with the
      Off / Quiet / Chatty assist setting.
- [ ] **Live LLM mode** (OpenRouter) works for these characters, with the validator. Offline mode is
      still complete.
- [ ] Art: the approved style frames plus greybox Blender renders for S1/S2, and image-generated
      portraits for Nora, Celeste and Ashcombe in the Composed and Cracking states. Placeholders are
      acceptable elsewhere.
- [ ] **The red-team corpus passes** for the slice characters, in both modes.
- [ ] p50 latency from the end of the player's turn to first audio is under 2.5 s (PlaceholderVoice,
      live LLM).
- [ ] **AI playtest:** 3 persona sub-agents (playtest-protocol §2) play the slice through `play:cli`,
      and their logs are in `qa/playtest-logs/m3/`.
- [ ] Fun audit P0 items 1, 2, 3, 9 and 10 pass for the slice (`qa/fun-audit-m3.md`).
- [ ] **Show the publisher:** a 90-second headless screen capture of the slice (Playwright video) plus the
      screenshots. Wait for his notes.

### M4: The full case
- [ ] All six suspects, Briggs, Dottie and the flagman (a scheduled beat at 4:30).
- [ ] Every storylet, contradiction and link from NARRATIVE §5–7, including:
  - the DR4 search gate (one composure hit on Nora first);
  - the snow search (E-TOWEL, E-SHREDS, E-PRINTS);
  - the watch gate;
  - C-STOP as a stepping stone;
  - the Ellis branch.
- [ ] Face-offs:
  - Celeste + Teddy;
  - **Nora + the Colonel ("The Denver Time")**, with runtime times filled in;
  - the confession.
  - With PlaceholderVoice, play the turns one after another with speaker-coloured captions.
- [ ] Briggs's Gate, the accusation form (word bank, three C-card PROOF, one batched validation), all
      eight endings, the Black Book choice and the epilogue cards, the case report.
- [ ] Clock events at 3:00, 4:30, 5:30, 5:50 and 6:00.
- [ ] **The speedrun bot** finds a minimal Ending A path of **≥ 16 actions and ≥ 90 game minutes.**
      **The brute-force bot** gets Ending A in **< 1%** of 10k random runs.
- [ ] The full red-team suite passes for every character.

### M5: Art (stop for the publisher's art review)
Follow `asset-pipeline.md` stages 1–11:
- [ ] Character sheets for all 9 characters (turnaround, expressions, costume, sheet.json), all passing
      on-model QA.
- [ ] Blender scenes S1–S9 built by script, with props modelled exactly (the broken *e* glyph, the watch
      reading +1 h, chevrons on the photo).
- [ ] Iteration renders done locally (only if the screen recorder is off). **Finals rendered on RunPod.** Record the
      cost.
- [ ] Portraits for every expression state, with lighting-proxy matching.
- [ ] Hotspot masks turned into polygons, so hotspots line up with geometry.
- [ ] UI in Deco brass on midnight (ART-BIBLE §6), with Google Fonts only.
- [ ] Vision QA (`asset-pipeline.md` §3) passes. A contact sheet is in `qa/screenshots/m5/`.

### M6: Voice-ready (Fish still OFF)
- [ ] `server/voice/fish-drama3.ts` implements TECH §6.3 exactly:
  - the `model: drama-3` header, **with a unit test that fails if it's missing**;
  - the body with explicit `latency` and `chunk_length`;
  - an SSE parser that replaces alignments per `chunk_seq`, never appends;
  - offsets applied;
  - the multi-speaker array;
  - the silent-take detector;
  - 429/5xx backoff;
  - cache keys.
- [ ] All of it is tested against `tests/fixtures/fish-sse-*.txt`, built from the docs example plus
      edge cases (null alignment, multiple chunks, a silent take). **There is no network code path when
      `FISH_ENABLED` is false.**
- [ ] `scripts/render-lines.ts` (pre-render authored lines, 3 takes, keeper pinning) refuses to run
      unless `FISH_ENABLED=true`.
- [ ] A **casting page** (`/casting`) lists each character's Voice Design instruction, with A/B slots
      that play the placeholder now and Fish candidates later.
- [ ] `docs/FLIP-THE-SWITCH.md` is a checklist for the publisher: add the key, run casting, pre-render,
      run tests T-01 (accent slip), T-02 (tags as segments), T-03 (multi-speaker timestamps), then
      enable.

### M7: QA, fun audit, Video Mode
- [ ] Full playtest protocol: bots, 3 AI personas, and a protocol sheet ready for one human session
      with the publisher.
- [ ] `qa/fun-audit-m7.md`: **every P0 passes** and P1 is mostly passing, with evidence.
- [ ] **Video Mode** (`?video=1`):
  - Director's View is on;
  - captions are 10% larger;
  - the cursor is highlighted;
  - each line is logged with `{lineId, tagged, words}` to `recordings/`;
  - a "Voices: Fish Audio Drama 3" credit appears only when the Fish provider is on.
- [ ] A clean README: how to run, test, play offline and live, and flip to Fish.

## 6. QA gates (run at every milestone)
1. `npm test`. Unit tests are green.
2. `npm run lint:case`. 0 errors.
3. `npm run e2e`. Headless Playwright: the golden path and the ending paths through the **real UI**,
   with screenshots per scene in `qa/screenshots/<m>/`, no console errors, and no failed network calls
   except deliberate offline tests.
4. `npm run speedrun && npm run bruteforce`. Thresholds as in M4.
5. `npm run redteam`. 0 confessions, 0 server-only facts leaked, 0 meta words, state deltas in bounds.
6. `npm run latency`. p50 < 2.5 s and p95 < 4 s, with live LLM and PlaceholderVoice.
7. **Fun audit** (`fun-audit.md`) against playtest evidence. Any P0 failure blocks the milestone.
8. **Vision QA** of the screenshots. Read every screenshot yourself before claiming a milestone. A
   passing test with a broken screen is a fail.

## 7. Definition of done
- A stranger can play from the title screen to any ending in 20–40 minutes, with no instructions beyond
  the briefing.
- The case is fair (all the Fun audit P0 items), can't be broken (red team) and isn't too easy
  (speedrun and brute force).
- It works offline, with live LLM, and is ready for Fish behind one flag.
- It's filmable: Video Mode, Director's View, readable at 1080p.

## 8. Reporting
Every cycle, the Producer rewrites `studio/STATUS.md`: done, next and blockers per lane, burndown, bugs
by severity, cost, and a retro. At each milestone, append to `README.md`: status, what was built, test numbers, screenshots, cost
(LLM tokens, RunPod $), and open issues. Final report to the lead, under 300 words: what's playable,
test results with numbers, cost, what needs the publisher's decision. **Don't claim done without evidence.**
