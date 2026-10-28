# RESEARCH: how studios make narrative detective games, and what we take from them

Compiled 2026-10-20 for the Fish Audio Drama 3 train-mystery game. Five research lanes ran in
parallel: L.A. Noire, comparable games and AI-NPC games, production pipeline and vocabulary, the Fish
API, and RunPod. Every claim has an inline source. Where a lane couldn't verify something, it says so.
Sections 1–6 are the general research and section 7 is what it means for this game.

---

## 1. The production pipeline (how a studio actually ships a narrative game)

| Stage | What it produces | Source |
|---|---|---|
| **Pre-production / concept** | Concept doc, pitch doc, art bible, GDD, prototypes, milestone deliverables | UW *Taxonomy of Video Game Development Artifacts* (https://gamer.ischool.uw.edu/files/2019/09/Taxonomy-of-Video-Game-Development-Artifacts.v.1.1.pdf) |
| **Pitch ladder** | Scott Rogers, *Level Up!*: **One-Sheet → Ten-Pager → Beat Chart → GDD** | O'Reilly chapter outline (https://www.oreilly.com/library/view/level-up-the/9780470688670/ch20.html). The contents of each document are from the book and couldn't be checked in full text online |
| **GDD** | "A highly descriptive living software design document… continuously improved upon… sometimes as often as daily" | https://en.wikipedia.org/wiki/Game_design_document |
| **The living GDD instead of the 100-page bible** | Jagex's James Sweatman argues for distributed, per-feature docs owned by their builders | MCV, "Death of the Game Design Document" (https://www.mcvuk.com/development-news/death-of-the-game-design-document/) |
| | A practice summary from a vendor blog: one-line pitch, core-loop diagram, **three pillars "that settle arguments"**, scope list with explicit cuts, per-system one-pagers written just before each system is built | https://allo.io/blog/en/game-design-document-template/ |
| **Narrative bible** | The canonical world, history, characters and, for a mystery, the hidden *fabula* (the true order of events) | UW taxonomy (above) |
| **Character bios as VO input** | Send actors "character bios, references, naming conventions, pronunciations and emotional context in advance" | Side (https://side.inc/lab/demystifying-game-vo-directing-recording-postproduction) |
| **Art bible** | Palettes, proportion references, turnarounds, reference collections, animation and icon lists, GUI and font concepts | https://gamedev.net/forums/topic/644435-what-is-an-art-bible-and-any-tips-to-make-one-better/ |
| | Riot's VFX style guide sets four goals (gameplay clarity, minimal clutter, theme, "surprise and delight") across value, colour, shape and timing | https://nexus.leagueoflegends.com/en-us/2017/10/dev-leagues-vfx-style-guide/ |
| | A vendor comparison of good art bibles: a tie-breaker rule, light direction, shadow colour as a value, an LOD floor, a named list of recurring mistakes | https://blog.makko.ai/what-public-game-art-bibles-say/ |
| **Model sheet / turnaround** | Front, side, 3/4 front, 3/4 back and back views keep a character "on-model." In 3D the ortho views become modelling planes | https://binus.ac.id/bandung/dkv/2025/11/04/character-turnarounds-understanding-form-in-2d-space/ |
| **Expression sheet** | The emotion range, which doubles as the list of portrait states | https://blog.cg-wire.com/character-sheet-animation |
| **3D** | Blockout → sculpt → retopo → UV → bake → PBR → rig → look-dev and lighting → render or glTF export, all of it in Blender | https://docs.blender.org/manual/en/latest/ |
| **UI/UX** | Wireframes plus flow diagrams. Halo 3 user research combined observation, route "scattergrams," pop-up ratings and think-aloud, and produced hundreds of changes | Wired via https://blog.kartones.net/post/wired-article-on-halo-3/ |
| **VO script format** | Master sheet columns: CHARACTER, VOICE ACTOR, CUE, **CONTEXT**, **TRIGGER**, **INFLECTION**, LOCATION, EFFECT, FILENAME (line ID), LINE CHOICE | Game Developer, "Screen/Play: Documenting Voice Assets" (https://www.gamedeveloper.com/audio/screen-play-documenting-voice-assets) |
| | Rules: "no merging dialogue with direction"; one column per type of information; give context ("shouting across a ravine or whispering?"); "the most expensive words… 'Let's figure it out in session'"; plan for pickups | Side (above) |
| | Actors need to see the full scene with their lines highlighted, not isolated cells | https://www.pocketgamer.biz/working-with-voice-talent-how-to-prep-vas-and-tap-into-their-abilities |
| **QA / playtest** | Think-aloud protocol (Lewis, 1982) | https://usabilitybok.org/think-aloud-testing ; https://gur.ucsc.edu/testing-methods |
| | Deduction games need outside testers. Golden Idol: "we had to rely on lots of testing" | https://www.gamedeveloper.com/design/case-of-the-golden-idol |
| **Milestones** | First playable → **vertical slice** ("a fully realized portion… encompassing all its essential elements") → alpha (feature complete) → beta (content complete) → gold | https://hacknplan.com/blog/understanding-vertical-slicing ; https://www.wayline.io/blog/setting-game-development-milestones-concept-launch |
| | The industry doesn't define milestones firmly, and the vertical-slice term is often misused | https://gamedeveloper.com/production/do-you-have-a-firm-definition-of-your-milestones- ; https://www.gamedeveloper.com/design/why-we-should-stop-saying-vertical-slices- |

**What we take:** the skill's department order (§ game-studio SKILL.md) follows this pipeline. There's a
the publisher approval gate at pillars and pitch, at the narrative bible, at the art bible, and at the vertical slice.

---

## 2. L.A. Noire (Team Bondi / Rockstar, 2011; remaster 2017)

### 2.1 The interrogation system
- **The loop.** The notebook logs clues and questions. You pick a topic, the witness answers, and you
  make a three-way call on that one answer. Each question "is rigidly attached to a correct or
  incorrect reply" (Kotaku review: https://kotaku.com/l-a-noire-the-kotaku-review-5802240).
- **The three verbs in the 2011 release:**
  - **Truth.** Accept the answer (Giant Bomb preview: https://www.giantbomb.com/articles/sleuthing-through-the-back-alleys-of-la-noire).
  - **Doubt.** Press without evidence: "you'll press them without out-and-out calling them a liar"
    (same source).
  - **Lie.** You "must submit evidence to prove it" (https://en.wikipedia.org/wiki/L.A._Noire).
- **Like Phoenix Wright**, "except that you only get one chance to correctly judge each answer"
  (https://www.gamesradar.com/uk/la-noire-review).
- **Intuition points.** Up to five. You can spend one to remove a wrong answer or to "Ask the Community"
  (Social Club stats). During a scene search, one reveals every clue (GamesRadar; Wikipedia). I found no
  source for a "reveal the right answer" option.
- **The verb-naming mistake.**
  - The lines were written and performed for **Coax / Force / Accuse**. After playtesting the labels
    became **Truth / Doubt / Lie**. McNamara: "it made Doubt weird… it just made Aaron [Staton] appear
    slightly psycho on the Doubt button. That's my fault, not his." The lines were never re-recorded
    (Eurogamer interview: https://www.eurogamer.net/articles/2011-11-15-l-a-forensic-brendan-mcnamara-on-l-a-noire-interview).
  - The 2017 remaster renamed them **Good Cop / Bad Cop / Accuse** "so that the options more accurately
    reflect Phelps' behavior" (https://www.eurogamer.net/articles/2017-11-09-l-a-noire-remaster-changes-its-infamous-interrogation-scene-button-prompts).
  - Kotaku said the new names were still vague and suggested previewing what Cole would say
    (https://kotaku.com/the-l-a-noire-remasters-new-dialogue-system-isnt-speci-1820520119).

### 2.2 Notebook, cues, rating
- **The notebook** holds people, places and clues. Clues gate questions. A reviewer was sure a witness
  was lying because of brake marks, but "this evidence doesn't appear in your notebook"
  (Electric Pig via https://www.csmonitor.com/Technology/Horizons/2011/0517/LA-Noire-review-roundup).
- **Search cues.** A **vibration** near clues, a **piano chime**, and investigation **music that stops
  once everything is found** (GamesRadar; Kotaku; Giant Bomb: https://www.giantbomb.com/reviews/la-noire-review).
- **Interview feedback.** A sting plays straight away to say right or wrong: "a simple jingle" (Kotaku).
- **Case rating.** 1–5 stars, from clues, questions answered correctly, damage and injuries
  (https://gamesradar.com/la-noire-achievement-guide/5).

### 2.3 Case structure and branching
- **You can't fail.** "You can't 'fail' a case… you'll always conclude it by nabbing someone… even if
  that someone isn't actually the right person" (Giant Bomb review).
- **The game covers for a poor investigation.** It brings in "a last-minute witness" (GamesRadar), and
  key clues "crop up in multiple locations" (Kotaku 2017: https://kotaku.com/l-a-noires-homicide-investigations-were-some-of-the-be-1798351067).
- **Retries were cut on purpose.** McNamara: "At one point we had a way where you would fail
  conversations and then you replay them… It lost all the drama." He also judged the game "slightly too
  easy" (Eurogamer).
- **The Homicide desk.** Several cases ask you to charge one of two men. Every man you charge is
  innocent; the real killer, Garrett Mason, can't be arrested, and choosing the "right" man changes
  only your stars (Kotaku 2017; https://lanoire.fandom.com/wiki/Garret_Mason).

### 2.4 MotionScan
- **The rig.** Depth Analysis built it: **32 cameras** in stereo pairs around a chair, 1080p at 30fps,
  about 50 cm of head movement allowed, with body motion captured separately
  (https://gizmodo.com/how-l-a-noire-conquered-the-uncanny-valley-with-a-tech-5714436).
- **The scale.** 400+ actors and 2,200+ script pages. Captured at about 1 GB/s and compressed to about
  1 KB/s in game: "we're trying not to let anybody touch the face"
  (https://mcvuk.com/development-news/the-art-of-lying-la-noire/).
- **Critique.** The tells were too easy to read: "if they're telling the truth, they'll usually stare
  unwaveringly… most liars look shifty… the question isn't whether they're lying, it's whether you have
  a clue that proves they're lying" (GamesRadar). Another review: "painfully easy to discern"
  (https://www.expertreviews.co.uk/games/ps3-games/50805/la-noire-review/2). Characters were "dead
  from the neck down" (https://www.shacknews.com/article/71015/why-cole-is-psychotic-in-la-noire).
- **Unverified:** that actors were coached on specific lie tells.

### 2.5 What critics and players said was bad
1. **Doubt didn't match the performance.** Cole has "a screaming fit when he doesn't believe that a
   drunk came home… at the time he said" (https://www.slantmagazine.com/games/review/l-a-noire-remastered).
   This became the "Press X to Doubt" meme (https://knowyourmeme.com/memes/la-noire-doubt-press-x-to-doubt).
2. **One right answer per question**, "leaving no room for… nuance" (Slant).
3. **Little at stake.** It plays like "bumper bowling; once you realize… this forgiving, the tension
   just drains away" (https://laboratorium.net/archive/2011/07/10/la_noire).
4. **The game tells you the answers.** Chimes, rumble and an instant right/wrong jingle (GamesRadar; Kotaku).
5. **Pixel hunting.** Clues are signalled by "a tinkly piano chord but never visual" (Slant).
6. **Filler.** Driving and combat padding. You can skip the action but not the interviews (Laboratorium).

### 2.6 Our fixes (applied in GDD §4)
| L.A. Noire flaw | Our fix |
|---|---|
| Doubt/Lie confusion; the verb didn't match the line | **The player speaks their own line.** There's no verb menu. Intent is classified and shown back to you, e.g. "PRESSING: Celeste, bedtime", before the suspect answers |
| Judging a statement and choosing an approach were one button | **Decoupled.** Pinning a claim ("I don't believe that") is free and silent. Approach is tone: ask, press, reassure, present |
| Instant right/wrong jingle | **No grading per answer.** The only feedback is the voice performance and the composure state |
| One chance per question, binary | Questions can be re-asked. Wrong *presentations* cost time and trust, never the case |
| Tells were readable at a glance | **Per-suspect baselines.** Nervous truth-tellers (the Colonel) and a calm liar (Nora) |
| Fail-forward with no consequence | A wrong accusation changes the ending (8 endings). The black book choice and the Ellis choice change the epilogue |
| Chimes for clue hunting | Clues are visible and named. Search costs clock time. Any assist is opt-in |
| Action filler | None. Every minute is investigation |

---

## 3. Comparable games: the one mechanic each does best

| Game | Best mechanic | How it works | What we steal | Sources |
|---|---|---|---|---|
| **Return of the Obra Dinn** (Lucas Pope, 2018) | Batched validation | Fates are confirmed only in **sets of three** "to deter guesswork." With N options each, three unknowns mean about N³ guesses with feedback only on the set. Players can still grind the third once two are certain | A five-slot accusation that's confirmed as a whole; no slot-by-slot fishing | https://en.wikipedia.org/wiki/Return_of_the_Obra_Dinn ; https://www.kokutech.com/blog/gamedev/design-patterns/unique-mechanics/return-of-the-obra-dinn ; https://steamcommunity.com/app/653530/discussions/0/1741104717711187168 |
| **The Case of the Golden Idol** (Color Gray, 2022) | Fill-in-the-blank deduction | A word bank of discovered terms goes into a story template. A segment locks when it's right, and there's a "two or fewer wrong" signal. Klavins: "If a player understands the main mystery immediately and then is stuck for thirty minutes on some technicality, that's bad." Prototyped as "excel tables" | The accusation sentence (WHO/HOW/WHEN/WHY) built from a word bank | https://en.wikipedia.org/wiki/The_Case_of_the_Golden_Idol ; https://www.gamedeveloper.com/road-to-igf-2023/-the-case-of-the-golden-idol-i-used-frequent-testing-to-improve-its-mystery-solving |
| **Her Story** (Sam Barlow, 2015) | Database search | 271 clips; **a search returns at most 5**, which saves "the more revelatory stuff… until later." Barlow tuned keyword frequency with "maths" | A searchable transcript of everything said. Specific nouns unlock deeper beats | https://www.pocketgamer.biz/feature/62104/making-of-her-story/ ; https://www.gamedeveloper.com/audio/road-to-the-igf-sam-barlow-s-i-her-story-i- |
| **Disco Elysium** (ZA/UM, 2019) | Skills as inner voices | 24 skills "speak directly to the player." Passive checks fire on their own; white checks can be retried, red checks are one-shot; the Thought Cabinet | An inner-voice "Hunch" that makes **deterministic passive checks on the performance**, never on the truth | https://en.wikipedia.org/wiki/Disco_Elysium ; https://www.gamebanshee.com/3wx3h |
| **Ace Attorney** (Capcom) | Contradiction presentation | Press or Present against one specific statement. Penalties drain the judge's patience. **Psyche-Locks** hide topics until the right proof is shown | **A contradiction is a table lookup**, `(claim_id, evidence_id)`. Nora's three locks are a lift of Psyche-Locks | https://en.wikipedia.org/wiki/Phoenix_Wright:_Ace_Attorney_%E2%80%93_Justice_for_All |
| **Paradise Killer** (Kaizen, 2020) | Open investigation plus a trial you call | Start the trial any time; "in court, you still need evidence, even if the detective has worked it out" | Accuse whenever you like, behind Briggs's Gate. A correct name without proof fails | https://www.mcvuk.com/business-news/we-never-wanted-to-force-our-beliefs-and-our-stories-on-you-make-your-own-one-up-theres-so-much-more-power-in-the-imagination-behind-the-development-of-paradise-killer/ |
| **Shadows of Doubt** (ColePowered, 2023) | Procedural cases on a cork board | "Incrimination is passed along… via connections (represented by the string)." The board "won't make logical jumps for you" | The board computes conflicts between cards the player places; the player does the deduction | https://colepowered.com/?p=33958 ; https://gameluster.com/early-access-review-shadows-of-doubt-theres-not-been-another-murder-yet/ |
| **The Roottrees are Dead** (2023/2025) | A family tree plus a period browser | Stages lock as a group; there's an "Intuition" tab | Period documents (manifest, log, menu card) as searchable sources of truth | https://en.wikipedia.org/wiki/The_Roottrees_are_Dead |
| **1000xRESIST** (sunset visitor, 2024) | Scrubbable memories | Jump around inside memories; a late reveal that they were edited | (Later cases) a scrubbable reconstruction of the night | https://en.wikipedia.org/wiki/1000xResist |
| **Pentiment** (Obsidian, 2022) | Accusation without certainty | Time blocks mean you can't investigate everything. Sawyer: "there cannot be a right answer… I'm like, 'No! There isn't!'" Accusations are remembered for years | The dawn clock forces you to choose who to press. The Black Book choice is about consequences | https://www.shacknews.com/article/146276/pentiment-josh-sawyer-no-correct-answer ; https://www.thegamer.com/interview-obsidian-josh-sawyer-pentiment/ |
| **Overboard!** (inkle, 2021) | Knowledge modelling | It tracks "what you—and what other characters—know and believe" | **A per-NPC belief state that the LLM reads and never writes** | https://www.gamedeveloper.com/design/how-get-away-murder-overboard |
| **Sherlock Holmes: Crimes & Punishments** (Frogwares, 2014) | Deduction board plus a moral verdict | Linked observations form theories; there are 3–5 possible solutions and 6–10 endings; absolve or condemn | Several wrong-accusation endings, each authored | https://en.wikipedia.org/wiki/Sherlock_Holmes:_Crimes_%26_Punishments |
| **Danganronpa** | Shooting weak points | "Truth Bullets" fired at highlighted statements; criticised for linear trials | (Avoid) | https://en.wikipedia.org/wiki/Danganronpa:_Trigger_Happy_Havoc |

---

## 4. Vocabulary

### 4.1 Structures
- **Branching narrative.** The sequence diverges on player choices, and the branches may or may not
  rejoin (Ashwell: https://heterogenoustasks.wordpress.com/2015/01/26/standard-patterns-in-choice-based-games/).
- **Dialogue tree.** Branching at the scale of one conversation: an NPC line, a menu of responses,
  reply nodes, often gated by flags.
- **Story graph / narrative graph.** A directed graph: nodes are content units, edges are transitions
  with conditions. A tree is a graph with no merges. Mysteries are graphs with merges and cycles
  (Alexander: https://thealexandrian.net/wordpress/7949/roleplaying-games/node-based-scenario-design-part-1-the-plotted-approach).
- **Quality-based narrative (QBN).** Failbetter's *Fallen London* and StoryNexus: "stories where the
  available nodes and choices depend on the player's stats"
  (https://en.wikipedia.org/wiki/Fallen_London). Emily Short: storylets "unlocked by qualities," where
  qualities are numeric and "represent absolutely everything"
  (https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/).
- **Storylet.** A small unit of content with prerequisites and an outcome (Short, same essay).
- **Salience-based narrative.** Pick "the most applicable" content from a pool. The canonical example
  is Elan Ruskin's GDC 2012 talk on Valve's fuzzy-matched dialogue rules, where the most specific
  matching rule wins (https://www.gdcvault.com/play/1015528/AI-driven-Dynamic-Dialog-through ;
  https://emshort.blog/2012/03/16/gdc-2012-talk-on-dynamic-dialogue/).
- **Waypoint narrative.** Short's *Glass*: "trigger topics advance the story… whenever we reach them"
  (Short 2016).

### 4.2 Ashwell's standard patterns (2015), plus the string of pearls
All quotes are from https://heterogenoustasks.wordpress.com/2015/01/26/standard-patterns-in-choice-based-games/ :
- **Time Cave:** "heavily-branching… little or no re-merging."
- **Gauntlet:** a linear thread "pruned by branches which end in death, backtracking, or quick
  rejoining."
- **Branch and Bottleneck:** "branches regularly rejoin, usually around events that are common to all
  versions," with state tracking keeping earlier choices meaningful. **This is our three-act frame.**
- **Quest:** organised by "geography rather than time."
- **Open Map:** a static geography with reversible travel.
- **Sorting Hat:** early branching that sorts players into linear tracks.
- **Floating Modules:** encounters gated by state with "no central plot." This is where storylets live.
- **Loop and Grow:** a central loop that unlocks more each time round.
- **String of Pearls:** *not* Ashwell's. It's Jesse Schell, *The Art of Game Design*, ch. 15: linear
  "pearls" of freedom strung on a fixed story (https://game-studies.fandom.com/wiki/String_of_Pearls).
  Inside each act we run *node-based* rather than string-of-pearls.

### 4.3 Mystery-specific mechanics
- **Deduction board / "mind palace."** The *Crimes & Punishments* board links observations into
  theories, and those theories can be wrong (Wikipedia, above). The visual style came from BBC
  *Sherlock* (https://www.hardcoregaming101.net/sherlock-holmes-crimes-punishments/). The underlying
  idea is the method of loci, which nobody owns.
- **Three Clue Rule** (Justin Alexander): "For any conclusion you want the PCs to make, include at
  least three clues." Its corollaries are permissive clue-finding, **proactive clues**, and a revelation
  list (https://thealexandrian.net/wordpress/1118/roleplaying-games/three-clue-rule).
- **Inverse Three Clue Rule:** "If the PCs have access to ANY three clues, they will reach at least ONE
  conclusion" (https://thealexandrian.net/wordpress/tag/node-based-scenario-design/page/2).
- **Node-based scenario design:** nodes connected by clues, navigable in any order (Alexander, part 1, above).
- **The red-herring economy.** There's no canonical ratio. What the sources do say:
  - Alexander warns against planting herrings at the table, because players make their own.
  - Golden Idol uses "tons of words that never factor into the solution (which grow in number…)," and
    players still feel "surprise rather than feeling cheated"
    (https://adventuregamehotspot.com/2022/11/21/the-case-of-the-golden-idol).
  - The fairness criteria we apply:
    - (a) the solution explains every herring (Van Dine #2);
    - (b) the true chain has three or more clues;
    - (c) different subsets of clues can each reach the solution (Klavins);
    - (d) the number of decoys grows with how far the player investigates.

### 4.4 The fair-play rules
**Knox's Decalogue (1929)** (https://en.wikipedia.org/wiki/Ronald_Knox):
1. The criminal is mentioned early, but the reader is never shown his thoughts.
2. No supernatural agencies.
3. At most one secret room or passage.
4. No undiscovered poisons and no long scientific explanations.
5. A rule reflecting the era's xenophobia. We cite it as history and ignore it.
6. No accident or unaccountable intuition helps the detective.
7. The detective doesn't commit the crime.
8. The detective declares every clue.
9. The Watson doesn't hide his thoughts and is slightly duller than the reader.
10. No twins or doubles unless the reader has been prepared for them.

**Van Dine's "Twenty Rules" (1928)** (https://www.umsl.edu/~gradyf/film/vandinerules.htm):
1. Equal opportunity: every clue is stated plainly.
2. No tricks beyond the ones the criminal plays.
3. No love interest.
4. The detective is never the culprit.
5. The solution comes from logic, never coincidence or a confession without a cause.
6. The detective detects.
7. There must be a corpse.
8. Nothing supernatural.
9. One detective.
10. The culprit is a prominent character.
11. Not a servant; someone not ordinarily suspected.
12. One culprit.
13. No secret societies.
14. The method is rational.
15. The solution is apparent on a re-read.
16. No dawdling description.
17. No professional criminal as the culprit.
18. No accident or suicide as the solution.
19. A personal motive.
20. A list of banned clichés (the cigarette butt, the dog that didn't bark, twins, the cipher, and so on).

**The Detection Club oath:** no "Divine Revelation, Feminine Intuition, Mumbo Jumbo, Jiggery-Pokery,
Coincidence, or Act of God" (https://en.wikipedia.org/wiki/Detection_Club). **Ellery Queen's
"Challenge to the Reader"** appears in *The Roman Hat Mystery*, 1929
(https://en.wikipedia.org/wiki/The_Roman_Hat_Mystery). Our version is **Briggs's Gate**, which avoids
the phrase.

### 4.5 Golden-age conventions and the IP line
- **The conventions:** the closed circle, the least-likely suspect (Van Dine 10 and 11), the locked room
  (Poe, 1841; already a cliché to Knox and Van Dine), and the **alibi or timetable trick**. Freeman
  Wills Crofts, a railway engineer, was "the alibi king"
  (https://en.wikipedia.org/wiki/Golden_Age_of_Detective_Fiction ;
  https://en.wikipedia.org/wiki/Locked-room_mystery ;
  https://www.goodreads.com/author_blog_posts/1014363-the-unbreakable-alibi).
- **The law.** Copyright doesn't extend to "any idea, procedure, process, system, method of operation,
  concept, principle, or discovery" (17 U.S.C. §102(b); https://www.copyright.gov/circs/circ33.pdf).
  Devices and fair-play rules are free to use. Specific texts, characters, solutions and trade dress are
  protected.
- **How the case applies it:** NARRATIVE.md §12 lists the distancing choices made after the adversarial
  review flagged an *Orient Express*-like cluster in Rev 1.

---

## 5. How studios define an interaction and a decision

- **Core loop:** "what is the user primarily doing over and over again?"
  (https://gamedesignskills.com/game-design/core-loops-in-gameplay/). **Secondary loops** run at case
  scale and **meta loops** at campaign scale.
- **Compulsion loop.** Joseph Kim, 2014: anticipation → action → reward, the conditioning built around
  the core loop (https://www.gamedeveloper.com/business/the-compulsion-loop-explained). The counter-view
  is "withdrawal driven" (https://www.gamedeveloper.com/design/compulsion-loop-is-withdrawal-driven).
  We design for the core loop and not for compulsion.
- **Meier.** "A game is a series of interesting decisions" (GDC 1989, revisited at GDC 2012:
  https://gamedeveloper.com/design/video-sid-meier-explores-interesting-decisions-in-gameplay). His
  2012 criteria are only in the video and weren't checked in text.
- **Salen & Zimmerman, *Rules of Play*.** Meaningful play needs outcomes that are **discernable** (the
  player can perceive them) and **integrated** (they matter to the larger game)
  (https://www.yorku.ca/playces/nicksmetatext/salenzimmermanreview.pdf).
- **Juul.** The player "exerts effort in order to influence the outcome" and "feels attached to the
  outcome" (https://jesperjuul.net/text/gameplayerworld/).
- **Rollings & Morris** warn against trivial choices and dominant strategies (exact wording not
  verified online).
- **Emily Short** describes *reflective* choice: expressive choices that aren't expected to branch
  (https://emshort.blog/2010/07/16/readings-news/).
- **Decision taxonomy** (a synthesis of the above): cosmetic · tactical · strategic · moral ·
  **informational/epistemic** (the main type in a deduction game) · expressive.
- **Consequence models:**
  - **Immediate vs delayed.** Immediate makes a choice discernable; delayed makes it integrated.
  - **Flags and qualities** (QBN; the "facts" in Ruskin's system).
  - **Illusion of choice.** Telltale's "Clementine will remember that," where "gameplay travels along
    the same path" (https://www.denofgeek.com/games/the-walking-dead-false-promises-telltale/).
  - **Reactivity vs branching.** Reactivity acknowledges what the player did; branching changes which
    content exists.
  - **Fail forward** (https://idiomdrottning.org/fail-forward).
  - **GUMSHOE.** Core clues are always found, and the challenge is interpreting them
    (https://en.wikipedia.com/wiki/Robin_Laws).
- **MDA** (Hunicke, LeBlanc and Zubek, 2004): Mechanics → Dynamics → Aesthetics. Its eight aesthetics
  are Sensation, Fantasy, Narrative, Challenge, Fellowship, Discovery, Expression and Submission. We
  target **Challenge, Discovery and Narrative**
  (https://course.khoury.northeastern.edu/cs5150f14/readings/hunicke_mda.pdf).
- **Schell's lenses** (1st ed. numbering): Fun (#3), **Meaningful Choices (#39)**, **Triangularity
  (#40)**, plus Surprise, Curiosity, Problem Solving, Flow, Interest Curve, Reward, Punishment and
  Feedback (https://ludoscience.com/EN/ressources/bibliographie/56-The-Art-of-Game-Design-A-Book-of-Lenses.html).
  These drive the fun audit (`game-studio/references/fun-audit.md`).

---

## 6. AI-NPC detective games, and the exploits we design against

### 6.1 Reception
- **Vaudeville** (Bumblebee, 2023; Inworld + DeepL + TTS)
  - About 7,500 sales and "very polarised" reviews. Inworld costs forced it to revert the premium
    voices (https://www.gamedeveloper.com/design/vaudeville-pre-mortem).
  - Steam rating is Mixed, 155 positive to 156 negative.
  - What reviewers reported:
    - A coroner listing victims "none of whom were t[he victims]."
    - "Three different characters confessed to the same murder — and none of them were actually guilty"
      (https://steamcommunity.com/profiles/76561198269409100/recommended/2240920/).
    - "Bullying the killer into confessing."
    - Suspects "starting to believe *you*."
    - A character announcing it's "a meta ai language model," and 3-minute waits.
    - The context overflowed because "the game saves every line of dialogue verbatim"
      (https://steamcommunity.com/profiles/76561198036395935/recommended/2240920/).
- **Uncover the Smoking Gun** (ReLU / KRAFTON, 2024)
  - Rated Positive. Exposing lies flips a suspect into a "confession mode" (https://store.steampowered.com/app/2492290).
  - Exploits and failures players found:
    - Bluffing a theory as fact can make the suspect agree.
    - A guilty robot talked into "sharing his financial gains."
    - Context lost between conversations.
    - Lies told even in confession mode
      (https://steamcommunity.com/profiles/76561197963077857/recommended/2492290/).
- **Suck Up!** (Proxima, 2025)
  - Mixed reviews. One player needed "12 inputs, all positive" before getting in, and suggested
    "3-5 positive responses guarantee entry."
  - An NPC promised a letter that never appeared in the game
    (https://steamcommunity.com/profiles/76561198109835056/recommended/2726370/).
- **Homicide Desk** (Steam)
  - Its disclosure: "Every case… is fully hand-written… an AI language model phrases their reply live…
    constrained to the written facts… length-limited and filtered."
  - It has a stress meter, and suspects "lawyer up" (https://store.steampowered.com/app/4935210/Homicide_Desk).
- **Dead Meat** (Meaning Machine): a "Mind Reader 3000" shows the suspect's inner monologue
  (https://gamespress.westeu-v2.propressroom.com/fr/Get-creative-in-DEAD-MEAT-the-detective-game-where-you-can-ask-suspect).
- **Covert Protocol** (Inworld + NVIDIA ACE, GDC 2024) and **Ubisoft NEO NPCs**: writers authored each
  NPC's knowledge base, with toxicity guardrails
  (https://www.nvidia.com/en-eu/geforce/news/nvidia-ace-gdc-gtc-2024-ai-character-game-and-app-demo-videos/ ;
  https://amp.hothardware.com/news/ubisoft-unveils-a-generative-ai-prototype-for-npcs).
- **Roblox "AI Interrogation"**: ten chances at a confession, with a fee for server costs
  (https://www.roblox.com/games/112441463632689/AI-Interrogation). Walkthrough videos of these games are
  over-performing on YouTube (YT-MARKET.md, AI-game market pull: 18x and 14x outliers).
- **Artificial Detective** (Xbox 2026 reveal) is an action game about a robot detective, **not** an LLM
  interrogation game (https://gamingbolt.com/artificial-detective-unveiled-at-xbox-partner-showcase-releases-in-2027).
- **Killer on Board**, an academic LLM prototype, reports that the "narrative paradox [was] not fully
  addressed" (https://www.springerprofessional.de/en/killer-on-board-addressing-the-narrative-paradox-by-utilizing-ll/51779846).

### 6.2 Documented exploits
1. Asking or bullying a suspect into confessing.
2. Bluffing a theory as fact.
3. Suggestibility.
4. Facts made up outside the case.
5. Breaking character.
6. Role-play takeovers ("made Gretzky promote me to Chief").
7. Deals the game's mechanics don't support.
8. Prompt injection to leak secrets ("Tricking LLM-Based NPCs into Spilling Secrets," https://arxiv.org/abs/2508.19288).
9. Memory overflow.

No Steam review quotes the literal phrase "ignore previous instructions" against a detective game. The
arXiv paper is the evidence that this attack works.

### 6.3 Defenses (adopted in GDD §6 and TECH §5)
1. **A hand-authored case as the single source of truth.**
2. **A belief state per NPC that the LLM reads and never writes** (inkle).
3. **Separate retrieval, generation and verification.** A structured knowledge tree with three agents
   cut critical hallucinations by 64.78% and "entirely prevents premature narrative disclosure"
   (https://arxiv.org/abs/2609.23043).
4. **Structured output: an intent, and the game decides the outcome.**
5. **Confession is a state transition** (Psyche-Locks; the confession mode in Smoking Gun).
6. **Pressure meters owned by the game.**
7. **The contradiction table is authored.**
8. **Memory is a ledger of facts, not a transcript.**
9. **Output is length-limited and filtered.**
10. **Thoughts go on a separate channel controlled by the game.**

**The design principle we take from this:** players forgive suspects who lie on purpose, but not
suspects who make things up.

---

## 7. What this means for our game

1. **The tell is the voice, and the reading is calibrated.** Every suspect has a baseline. There's at
   least one nervous truth-teller (the Colonel) and one calm liar (Nora). This fixes the L.A. Noire
   complaint that tells were "painfully easy."
2. **No verb menu.** You speak, the game shows you the intent it heard, and the suspect performs the
   answer. Classifying intent fixes the Doubt problem.
3. **Contradictions are table lookups, and confession is a state.** These are the Ace Attorney and
   Psyche-Lock patterns, and they close the Vaudeville and Smoking Gun exploits.
4. **The accusation is a validated multi-slot sentence** that blocks brute force, as in Obra Dinn and
   Golden Idol, behind Briggs's Gate (Paradise Killer, Queen).
5. **A searchable transcript.** Her Story's idea, applied to the player's own interviews.
6. **An inner voice for the performance, never the truth.** Disco Elysium's passive check, made
   deterministic.
7. **The dawn clock plus consequential choices** (Pentiment). Choosing who to press is the strategic
   decision. The Black Book and Ellis choices are the moral ones.
8. **Three clues for every conclusion, proactive clues** (the flagman at 4:30), and herrings the solution
   explains (Alexander, Van Dine).
9. **Fish Drama 3 matches the medium.** Free-text direction in brackets placed before the words it
   affects, scoped tags, multi-speaker in one pass with `<|speaker:N|>`, and an SSE
   stream-with-timestamps endpoint for word-synced captions. VO-DIRECTION.md and TECH.md have the
   specs, from https://docs.fish.audio/features/text-to-speech/drama-3 and
   https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech-stream-with-timestamps.
   **Not called yet.**
10. **Heavy renders run on RunPod, and the approach has been tested.** On 2026-10-20 a community RTX 3090
    at $0.22/hr rendered with Blender 5.1.2 and OptiX in 77 s end to end, for about $0.04 total, and the
    pod was confirmed terminated. Script: `game-studio/scripts/runpod-blender-render.sh`. Details in
    TECH.md §9.
