# VO DIRECTION: "Dead Air on the Meridian" (Fish Audio Drama 3)

> **Status: spec only. No Fish Audio API calls have been made** (the shipped example ships with the voice off). The
> game uses a `VoiceProvider` interface with a placeholder (TECH §6). This document is the contract the
> Fish implementation must meet when you turn it on.

**Sources for every Drama 3 behaviour cited:**
- Drama 3 docs: https://docs.fish.audio/features/text-to-speech/drama-3
- Stream-with-timestamps: https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech-stream-with-timestamps
- TTS request schema: https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech
- Voice design: https://docs.fish.audio/features/voice-design
- Launch blog: https://fish.audio/blog/fish-audio-drama-3/
- Model card: https://huggingface.co/fishaudio/drama-3

---

## 1. The Drama 3 rules this game relies on

| Rule | Source | How we use it |
|---|---|---|
| Free-text direction in `[brackets]`, written "the way you'd brief a voice actor," with **no fixed tag list** | D3 docs | The voice director writes the direction from the suspect's hidden state |
| **A tag affects everything after it, so position matters.** A new bracket mid-line starts a new read | Fish brief; blog | Tells land on specific words: `In bed. [voice catches on the time] Since eleven.` |
| Point sounds and pauses go in brackets where they happen: `[shaky breath]`, `[small laugh]`, `[pause]` | D3 docs | Breathing, swallows and laughs in the middle of an answer |
| Paired tags change only the words they wrap: `<whisper>`, `<emphasis>`, `<soft>`, `<fast>`, `<slow>`, `<stress>`, `<forceful>` | D3 docs | Word-level tells: `<fast>twenty to one</fast>`. Nora's over-precise times |
| Multi-speaker: `reference_id` is an **array**, and each turn starts with `<|speaker:N|>` | D3 docs; HF card (up to 16 speakers) | Face-offs and the confession scene in one pass |
| **The `model: drama-3` header is required.** Without it, the request **silently falls back to s2.1-pro** | TTS schema | Hard-code it in the proxy and assert it in tests |
| SSE stream with **word-level** segments `{text,start,end}` per `chunk_seq`, plus `chunk_audio_offset_sec`. The alignment is a **cumulative snapshot**: replace it, don't append. No speaker field | Stream-with-timestamps | Word-synced captions; QA catches silent takes |
| Known failure: **sometimes a take says the first line and then goes silent.** Mitigations: a reference voice for every speaker, **don't start a line with a sound tag**, render a few takes | r/LocalLLaMA report via DRAMA3-PRODUCT.md §1; the blog says "render a few" | Lint rule V-03; silent-take detector (TECH §6.4) |
| Billing counts direction tags as characters (MCP/web; assumed for the API) | MCP docs | Keep directions to **≤ 8 words**. Budget in §8 |

---

## 2. Casting: voice profiles

**Casting route (in this order):**
1. **Voice Design**: `POST /v1/voice-design` with `model: voice-design-1` and a text instruction. It
   returns candidate voices at $0.01 per request, which we persist with `POST /model`. No real person's
   voice is used.
2. Fish's public library, filtered with `licensed=true`.
3. **Never clone a real person.** The model licence forbids imitating "an identifiable natural person
   without that person's prior consent."

The three public doc voices (Adrian `bf322df2…`, Delia `c70cfb98…`, Sheila `f3a2b900…`) are only for
smoke tests.

| Character | Age / vocal type | Baseline delivery | Voice Design instruction (draft) | Tell signature |
|---|---|---|---|---|
| **Nora Pell** | 29. Light mezzo, clear diction | Quiet, exact, faintly warm. A secretary's measured pace. Never hurried | "A composed American woman, late twenties, soft clear mezzo, precise diction of a 1930s private secretary, warm but reserved, very even pace." | Almost none. Time answers come **too ready and too exact**. Under heavy evidence she gets *colder and slower*, never tearful |
| **Celeste Varga** | 38. Rich alto, "Hungarian" accent | Theatrical, gracious, imperious, with stagey pauses | "A glamorous 1930s film actress, late thirties, rich low alto, cultivated Central European accent in English, theatrical and imperious." | **The accent slips into flat western-Pennsylvania vowels.** She laughs too bright. *Fallback in §4.3* |
| **Teddy Lowell** | 26. Bright tenor | Easy charm, quick wit, a mid-Atlantic put-on | "A charming young American man, mid twenties, bright tenor, quick and playful, a slightly put-on upper-class drawl." | Speeds up, jokes, **laughs a beat too early**. The drawl drops toward a New Jersey edge |
| **Dr. Julian Ashcombe** | 56. Dry baritone | Clipped, clinical, faintly bored | "A dry, precise American physician in his fifties, cool baritone, clipped clinical diction, faintly weary." | Over-precise medical vocabulary, a dry throat, `[clears throat]`, words chosen too carefully |
| **Col. Ambrose Hargreave** | 71. Booming bass-baritone | Hearty, warm, rambling, a raconteur | "A hearty American man in his seventies, booming warm bass-baritone, a retired engineer who loves telling stories, slightly gravelly." | **Louder, barking, parade-ground** when lying about rank. *Honest* outrage when you doubt the alibi, the same loudness for a different reason. **Very soft** about Martha |
| **Ellis Monroe** | 44. Warm, resonant baritone | Formal, measured, courteous, observant | "A dignified American man in his forties, warm resonant baritone, formal and courteous, measured professional pace, intelligent and observant." **No exaggerated dialect** (sensitivity rule) | Company-rulebook language, precise railroad detail, a careful flattening of warmth |
| **Conductor Briggs** | 60. Gravel baritone | Steady, Midwestern, dry humour | "A steady Midwestern American railroad conductor around sixty, gravelly baritone, plain-spoken, dry humour." | n/a. He's the reliable voice |
| **The Agent's Hunch** (narrator) | Neutral, about 40 | Noir inner voice, close-miked, low | "An intimate noir narrator, low and close, unhurried, slightly wry, as if thinking aloud." | n/a |
| **Desmond Crane** (radio clips only) | 52. Polished broadcaster tenor | A 1930s radio announcer | "A 1930s American radio gossip broadcaster, fast polished tenor, theatrical, sly." Render with a radio filter in post | n/a |
| **Dottie Hale** | 16. Plain, young | Shy, Oklahoma plain-spoken | "A shy American teenage girl from rural Oklahoma, plain and soft-spoken." | n/a |
| **The flagman** (one scene) | 50s | Cold, stamping | "A cold, tired American railroad flagman, fifties, rough voice." | n/a |

---

## 3. Hidden state → Drama 3 direction

The **voice director** is deterministic code. Its inputs are `{suspect, beat.tone, composure_band,
is_lie, topic_heat, last_player_intent, crack_stage}`. It outputs a **leading direction**, plus at most
two **inline directions** and at most one paired tag, placed on the key words the beat marks as
`stress_words[]`.

### 3.1 Base direction by band (each suspect overrides it in §3.3)
| Band | Leading direction (generic) |
|---|---|
| Composed (70–100) | *(the suspect's baseline, §2)* |
| Strained (40–69) | `[a little guarded]` + the suspect's tell on hot topics only |
| Cracking (15–39) | `[struggling to keep steady]`, `[breath unsteady]` + a tell on most lines |
| Broken (<15) | Only an authored crack beat. The direction is written in the beat |

### 3.2 Modifiers
| Condition | Inline direction or tag |
|---|---|
| `is_lie` and band ≥ Strained | The suspect's **lie tell** on `stress_words` (e.g. Celeste `[the accent slipping]`) |
| `topic_heat == 3` (the secret topic) | A pause before the key noun: `[a beat too long]` |
| Last intent was `PRESS` on a **true** statement | **Honest indignation**: `[stung, genuinely offended]` (the trap) |
| Last intent was `REASSURE` and trust ≥ 60 | `[softening]` |
| Last intent was `THREATEN` | `[cold]` (Nora), `[stiffening, formal]` (Ellis), `[bristling]` (Colonel) |
| A presentation just hit (crack stage 1) | The authored crack line, e.g. `[voice drops]` + `<whisper>` on the confession clause |
| `META` intent | `[baffled]` or `[politely puzzled]` |

### 3.3 Per-suspect tag tables
**Nora.** The whole design depends on her sounding fine.
| State | Direction |
|---|---|
| Baseline | `[quiet, precise, faintly warm]` |
| Lie about time | `[evenly]` … `<fast>twenty to one</fast>` *(too ready, too exact)* |
| Composure hit (alibi, motive) | `[very still]`, `[a slight coolness entering]` |
| Two locks open | `[slower, colder, choosing each word]` |
| Confession | `[perfectly level, almost relieved]` |
| Never | Crying, voice breaking, whispering in panic. She doesn't do that |

**Celeste**
| State | Direction |
|---|---|
| Baseline | `[theatrical, gracious, a cultivated Central European accent]` |
| Lie | `[a practised, theatrical calm]` + a stress word: `[the accent slipping into flat Pittsburgh vowels]` |
| Pressed | `[laughing too brightly]`, `[imperious, covering]` |
| Crack | `[the accent gone entirely, flat and small]` |

**Colonel**
| State | Direction |
|---|---|
| Baseline | `[hearty, warm, rambling]` |
| Lie (rank) | `[louder, parade-ground bark]` |
| Alibi pressed (honest) | `[genuinely affronted, booming]` |
| The watch / Martha | `[quiet, the bluster gone]` + `<soft>` |

**Ashcombe**
| State | Direction |
|---|---|
| Baseline | `[dry, clipped, faintly bored]` |
| Lie | `[too careful]` + `[clears throat]` mid-line *(never at the start, rule V-03)* |
| Crack | `[tired, almost relieved]` |

**Ellis**
| State | Direction |
|---|---|
| Baseline | `[formal, courteous, measured]` |
| Lie | `[precise, by the rulebook]` |
| Secret out, trust kept | `[warm, low, honest]` |
| Secret out, reported | `[formal, emptied out]` |

**Teddy**
| State | Direction |
|---|---|
| Baseline | `[easy charm, a put-on drawl]` |
| Lie | `[quick, joking]` `[laughs a beat early]` |
| Crack | `[the drawl gone, plain New Jersey, scared]` |

---

## 4. Sample directed lines (VO script format)

The columns follow the Game Developer master-sheet convention: CHARACTER, CUE, CONTEXT, TRIGGER,
INFLECTION (our direction), plus LINE ID and INTENSITY 1–5 (RESEARCH §1). **Authored** means the line
is pre-rendered and never paraphrased. **Writer** means the LLM may rephrase it within `facts_allowed`.

| LINE ID | CHARACTER | CONTEXT | TRIGGER | INT | TEXT (as sent to Drama 3) | MODE |
|---|---|---|---|---|---|---|
| BRG-001 | Briggs | Opening, corridor, lantern | Game start | 2 | `[low, steady, tired] He asked me to wake him the minute there was word on the line. [pause] I knocked. The door wasn't locked.` | Authored |
| BRG-004 | Briggs | Teaching the rule | After the first interview | 2 | `[dry, plain-spoken] Everybody on this car's scared of something, Agent. [a beat] Scared ain't guilty.` | Authored |
| NOR-010 | Nora | First meeting, holding the black book | ASK: Crane | 2 | `[quiet, precise, grief held in tight] He wrote everything down, Agent. Everyone on this car is in here. [a small, steady breath] I'm sorry. I think you'll need it.` | Authored |
| NOR-021 | Nora | Alibi | ASK: last night | 2 | `[quiet, precise] I went aft about midnight. [evenly] The Colonel and I sat until <fast>twenty to one</fast>. Then I went to bed.` | Writer (facts locked) |
| NOR-022 | Nora | Her job | ASK: typing / E-DRAFTS | 1 | `[faintly warm] He never touched a typewriter in his life. [a ghost of a smile] He called it women's work.` | Authored (it's a trap later) |
| NOR-040 | Nora | C-STOP hit | PRESENT: E-LOG vs CL-NOR-2 | 3 | `[very still] Then I'm wrong about when I went aft. [evenly] I'd no watch, Agent. The Colonel will tell you I stayed till twenty to one.` | Authored |
| NOR-060 | Nora | C-TYPE hit | CONFRONT | 4 | `[a slight coolness entering] I said that, didn't I. [a long pause] Then I misspoke.` | Authored |
| CEL-012 | Celeste | Alibi lie | ASK: last night | 3 | `[a practised, theatrical calm] In bed, darling. Since eleven. [the accent slipping into flat Pittsburgh vowels] I never left the room.` | Writer |
| CEL-030 | Celeste | Crack: the ear-clip | PRESENT: E-EARRING → CL-CEL-1 | 5 | `[the accent gone entirely, flat and small] I went to pay him. [shaky breath] And he looked at me like I was mad. [voice drops] He said he'd never written to me in his life.` | Authored |
| HAR-015 | Colonel | Honest alibi, pressed | PRESS: CL-NOR alibi | 4 | `[genuinely affronted, booming] Are you calling me a liar, sir? [pounding the table] She sat right there till twenty to one, <emphasis>by my watch</emphasis>.` | Authored |
| HAR-050 | Colonel | The watch payoff | The watch gate opens | 3 | `[quiet, the bluster gone] Martha's buried in Denver. [pause] <soft>It's her time.</soft> I'm not ready to leave it.` | Authored |
| ASH-020 | Ashcombe | Lying about sleep | ASK: what did you hear | 3 | `[too careful] I took a draught at eleven. [clears throat] Chloral, a modest dose. I heard nothing whatever.` | Writer |
| ASH-041 | Ashcombe | Crack | PRESENT: E-BOOK → CL-ASH-1 | 5 | `[tired, almost relieved] Fourteen months. Box eleven twenty-nine. [a dry swallow] The letters were typed. A poor machine. The e's were broken.` | Authored |
| ELL-012 | Ellis | Lie | ASK: 12:15–12:35 | 3 | `[precise, by the rulebook] From a quarter past, I was in the smoking room seeing to the shoes, sir. Company practice is to chalk each pair to its room.` | Writer |
| ELL-031 | Ellis | Secret kept, tier 2 | REASSURE after Dottie | 2 | `[warm, low, honest] While I was at my seat, Miss Pell never went aft. [a beat] And nobody came forward from that club car at twenty to one.` | Authored |
| TED-014 | Teddy | Lie | ASK: last night | 3 | `[easy charm, a put-on drawl] Cards, old man. Till one. [laughs a beat early] Fellow named Morton. Or Norton.` | Writer |
| HUN-007 | Hunch | Passive check | A Celeste tell fired | 1 | `[low, close, wry] Her vowels went flat on "eleven."` | Authored |
| HUN-019 | Hunch | Passive check | Nora's exact-time latency flag | 1 | `[low, close] Twenty to one. She said it the same way twice.` | Authored |
| CRN-RADIO | Crane | Title screen radio | Title | 3 | `[fast, polished, sly radio patter] Good evening, America. [a confiding drop] This is Desmond Crane, <emphasis>and I hear everything.</emphasis>` | Authored (radio filter) |

### 4.1 Lint rules for every line sent to the voice
- **V-01.** At most 8 words in a leading direction, and at most 2 inline directions plus 1 paired tag
  per line.
- **V-02.** Directions use tone and pace words only. They never contain new facts, which would show up
  on screen in Director's View.
- **V-03.** **Never start a line with a sound tag** (`[sighs]`, `[clears throat]`, `[laughs]`). This
  avoids the silent-after-first-line failure. A leading *direction* such as `[quiet, precise]` is fine.
- **V-04.** Speak times as words, "twenty to one." Don't write `12:40`, so that `normalize` can't expand
  digits in a way that breaks timestamp-to-word matching (TECH §6.3).
- **V-05.** Paired tags must be balanced and must not nest.
- **V-06.** Lines are at most 45 spoken words (the persona limit), and authored crack lines at most 70.

### 4.2 Line budget (for cost; §8)
- About 120 authored lines across the cast, averaging 140 characters with directions, which is about
  17k characters.
- Plus about 60 writer lines per playthrough at about 160 characters, which is about 10k.

### 4.3 Fallback for Celeste's accent slip (test T-01)
Drama 3's docs show emotion, pace and whisper directions. **An accent shift in the middle of a line,
inside one voice, isn't documented.** Test it first, with three takes.

If it doesn't hold, use multi-speaker as a single-character trick:
- Make two Voice Design voices: **Celeste-Countess** (accented) and **Celeste-Ruth** (the same timbre
  instruction, with "a flat western-Pennsylvania accent").
- Render the slip as `<|speaker:0|>In bed, darling. Since eleven. <|speaker:1|>[flat, small] I never left
  the room.`
- `reference_id = [countess_id, ruth_id]`.

---

## 5. Word sync and Director's View
- Lines are rendered through `/v1/tts/stream/with-timestamps` (SSE). The client keeps the latest
  alignment snapshot per `chunk_seq` and adds `chunk_audio_offset_sec` to each segment's `start` and
  `end`.
- The caption reveals each word at `start`. The **direction text** (`[voice catches on the time]`) is
  shown in small italics above the caption, at the point in the line where it applies. It's taken from
  our own tagged script, not the alignment, because direction tags are assumed not to come back as
  segments (UNVERIFIED, test T-02).
- **Mapping tagged text to segments:** strip `[...]`, `<tag>`, `</tag>` and `<|...|>`. Lowercase, and
  drop punctuation and apostrophes, to match the "Ive"/"dont" style in the docs. Walk the segments in
  order and assign each one to the next script token. Record any mismatches for QA.

---

## 6. The face-off scene: "The Denver Time" (multi-speaker, one render)

**Speakers:** 0 = Nora, 1 = Colonel, 2 = Briggs, 3 = the Agent (a Voice Design "player" voice, used
only in Video Mode replays; live, the player's own mic line plays). `reference_id = [nora, colonel,
briggs, agent]`. Rendered once the watch gate is open.

The Agent's live line triggers it: *"Colonel, what time do you make it?"* The two times are **filled in at
runtime**: `{colonel_time}` is the game clock plus one hour and `{rail_time}` is the game clock, both
written as words. So the scene renders live, as one multi-speaker stream, at the moment you ask. A
Briggs animation (pulling out his railroad watch) covers the first-audio latency. The text below shows
it at game time 3:10.

```
<|speaker:1|>[hearty, pulling out the watch] Time? [chuckles] Ten past four, son. Long night.
<|speaker:2|>[flat, steady] It's ten past three, Colonel.
<|speaker:1|>[puzzled, a little louder] Nonsense. I've had this watch since nineteen-oh-two.
<|speaker:2|>[dry] Railroad time, sir. We set back an hour at Cinder Junction. It's on the menu card.
<|speaker:0|>[a fraction too quick] The Colonel's tired, Agent. [evenly] It's been a dreadful night for everyone.
<|speaker:1|>[slowly, working it out] I don't fiddle my watch. [quiet, the bluster gone] Not since Martha. [pause] <soft>She's buried in Denver.</soft>
<|speaker:3|>[low, careful] So when you say she sat with you till twenty to one…
<|speaker:1|>[very quiet] Twenty to twelve. [a long breath] God help me. Twenty to twelve.
<|speaker:0|>[very still] Then the Colonel's watch was wrong, Agent. [evenly] And I had none of my own to check it.
<|speaker:2|>[grim, low] Funny thing, miss. You asked him the time.
<|speaker:0|>[a long pause] [slower, colder, choosing each word] I asked a lonely old man what time it was. [a slight coolness entering] That isn't a crime.
```

The scene ends with the Agent's choice: present more, or go to Briggs's Gate.

**The confession** (Ending A, also multi-speaker, authored):
```
<|speaker:0|>[perfectly level, almost relieved] He laughed when Miss Varga left. [pause] Then he knocked on my door and told me to come in. [evenly] He said I'd be taken off at Oakland in front of the newspapers.
<|speaker:0|>[quiet, precise] I'd typed every word that man ever said, Agent. Four years. [a slight coolness] He never once read what I wrote. [a beat] Until tonight.
<|speaker:2|>[low] And the microphone?
<|speaker:0|>[very still] It was the nearest thing to hand. [pause] <whisper>It always was.</whisper>
```

---

## 7. Production plan for VO (when the Fish key is on)
1. **Cast:** Voice Design with 2–4 candidates per role (§2). The publisher picks from a casting page with A/B
   players. Persist the chosen voices with `POST /model`, and pin their IDs in `voices.json`.
2. **Authored pass:** pre-render every authored line, 3 takes each. The silent-take detector
   auto-rejects bad ones. The director (the publisher or the vo-director) picks the keeper, `LINE CHOICE` in the
   sheet. Cache key: `sha256(model, text, voice ids, params, take)`.
3. **Writer lines:** rendered live through the stream endpoint, then cached.
4. **Pickups:** if a performance fails review, change only the direction words and re-render. Never
   change facts.

## 8. Cost talking point (for the video)
- At the blog's launch price of **$10 per 1M characters through Nov 12, then $50 list**:
  - authored lines: about 17k chars × 3 takes, roughly $0.51 at launch;
  - one playthrough's live lines: about 10k chars, roughly **$0.10 at launch, or $0.50 at list**.
- Artificial Analysis quotes $15/M. The pricing docs don't list `drama-3` yet. State "about ten cents
  of voice per playthrough at the launch price" and cite the blog.
