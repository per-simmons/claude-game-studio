# ART BIBLE: "Dead Air on the Meridian"

This follows the template at `game-studio/references/art-bible-template.md`. The asset pipeline is in
§7 and in `game-studio/references/asset-pipeline.md`.

## 1. The look in one line
**Deco noir in gouache.** A 1936 luxury train painted like a mid-century illustration: chrome and burl
walnut, frosted glass, lit like a film noir. The warm lamps inside hide things. The cold snow light
outside shows them.

## 2. Rules (the tie-breakers)
1. **Two colour temperatures.** Interiors are lit by warm practicals: amber 2700K table lamps and brass
   sconces. Truth is lit cold: snow-blue 7500K moonlight through the windows. **Evidence close-ups are
   always lit cold.** If a colour choice is in doubt, pick the cold one for clues and the warm one for
   people.
2. **The light comes from the window side.** Every interior key light is the window (cold) or the table
   lamp (warm), and both are on frame left. Shadows are **deep oxblood-brown (#2a1614)**, never
   black.
3. **Silhouette first.** Every suspect must be recognisable as a black shape at 64 px (§4).
4. **Period-true, nothing borrowed.** Everything is 1934–1937 American rail, with an invented railroad
   and insignia. No real railroad logos, no real liveries, no famous-sleeper blue-and-gold livery, and nothing
   that suggests any adaptation of a famous train novel (NARRATIVE §12).
5. **Readability beats atmosphere.** Hotspots and evidence must read at 1080p on YouTube compression:
   high contrast at the focal point and a soft falloff everywhere else.
6. **Recurring mistakes to reject:** modern plastics; LED-blue light inside; streamline-moderne
   shapes so exaggerated they look sci-fi; noir clichés like venetian blinds and fedora silhouettes
   (period railcars had pull-down shades); mismatched eras such as 1950s domes.

## 3. Palette
| Token | Hex | Use |
|---|---|---|
| Midnight | #0f1a2b | Night outside, UI background |
| Snow-blue | #a9c4de | Cold key light, truth accents |
| Brass | #c9a227 | Deco trim, UI rules, the clock |
| Lamp amber | #e8a85a | Warm practicals |
| Oxblood | #6e1f1f | Upholstery, dried blood, danger accents |
| Ivory | #efe6d2 | Linen, paper, caption text |
| Walnut | #4a2e1f | Panelling |
| Shadow | #2a1614 | All shadows |
| Telegram green | #6f8f6a | Telegraph-blank tint (the one cool-green paper in the game) |

Each character has a signature accent (§4) that appears on their portrait frame and notebook tab.

## 4. Characters: design specs

For every character the sheet must contain:
- a **turnaround** (front, 3/4, side, back);
- an **expression sheet** with the band states (Composed, Guarded, Cracking, Broken) plus the specials
  listed below;
- one **costume detail sheet** of their props.

The spec is in `game-studio/references/character-sheet-spec.md`.

| Character | Silhouette hook | Costume (Dec 1936) | Accent colour | Props | Expression specials |
|---|---|---|---|---|---|
| **Nora Pell** (29) | A narrow, upright column; a neat **rolled chignon** | A grey wool cardigan over a high-collar ivory blouse, a dark A-line skirt, flat T-strap shoes. *No wristwatch* in interviews (it's in DR4) | Dove grey #8d9199 | Steno pad, the black notebook (she hands it over), pencil behind the ear in Act I | "Helpful": faint, sad half-smile. "Very still": unblinking calm. The confession: level, almost relieved. *Never* crying |
| **Celeste Varga** (38) | A broad-brimmed shape even indoors (she has her **hat box**), and a fur-collar **travelling coat over a satin nightdress** | Platinum finger-waves, pencil brows, a diamond ear-clip on the **right ear only** (the left one is under Crane's seat) | Oxblood #6e1f1f | Cigarette holder, compact, the $2,000 envelope in her coat | "Theatrical": head tilted. "Accent slip": the face falls by a fraction and the eyes drop. "Ruth": no make-up glamour, small |
| **Teddy Lowell** (26) | Long and lean, with a **loosened white tie** | A tuxedo a little too shiny (rented), pomaded hair with a lock falling loose | Champagne #d9c48a | A deck of cards, a cheap lighter dressed up as an expensive one | "Charm": a wink. "Laughs early": grin with worried eyes. "Scared": jaw tight |
| **Dr. Julian Ashcombe** (56) | **Round spectacles** and a stoop | A charcoal three-piece suit, a watch chain, a **blood fleck on the right cuff** | Bottle green #2f4a3a | Leather medical bag, cotton wool, a chloral bottle (seal unbroken) | "Clinical": brows level. "Clears throat": hand at his collar. "Guilt": looks at his hands |
| **Col. Ambrose Hargreave** (71) | A **barrel chest**, a white walrus moustache, ramrod posture | A tweed Norfolk jacket, a regimental-style tie (an invented stripe), a waistcoat with a **pocket watch on a chain** | Khaki #8a7a4f | Brandy snifter, the pocket watch, a cane he doesn't need | "Booming". "Affronted" (honest). "Martha": soft, eyes wet, the watch held open |
| **Ellis Monroe** (44) | A **white porter's jacket**, crisp and squared | A white jacket with brass buttons, a black cap with the badge "GREAT MERIDIAN", and the name card **YOUR PORTER: ELLIS MONROE** | Ivory with brass | A whisk broom, a shoe chalk stub, a pocket notebook (his linen count) | "Formal". "Rulebook": eyes front. "Warm": a real smile at last. Dignity at every stage; no caricature (sensitivity rule) |
| **Conductor Walter Briggs** (60) | **A lantern** and a big conductor's cap | A navy uniform with brass, a railroad watch on a fob, a ticket punch | Navy #1f2f4d | Lantern, logbook, the railroad watch | "Steady". "Dry". "Grim" |
| **Desmond Crane** (52, victim) | A sleek **pencil moustache** and slick hair | A smoking jacket over a dress shirt (on the body) | Gold #c9a227 | The ribbon microphone, the black notebook | Body: no gore. One dark temple wound, lit cold, partly hidden |
| **Dottie Hale** (16) | A man's **oversized coat** and boots | A feed-sack print dress under a borrowed company blanket | Wheat #c8a86b | A paper sack of sandwiches | "Shy" |

**Content limits:** no gore and no visible blood beyond one dark wound and a pink-stained towel. The
victim is shown mostly by implication (a hand, a fallen microphone case strap).

## 5. Scenes

Everything is 1920×1080. **Bg** means a Blender-rendered background (Cycles). **2D** means painted
or image-generated portrait layers.

| # | Scene | Camera / framing | Lighting | Hotspots | Medium |
|---|---|---|---|---|---|
| S1 | **DR3, the crime scene** | 28 mm, eye height, looking toward the window | A cold moonlit window on the left, a warm lamp knocked askew, cold fill on the floor | Body (implied), mic case on the rack, table (ice bucket, untouched soda, telegraph pad), jacket on the hook, briefcase (longhand drafts), connecting door to DR2, under the seat (ear-clip), towels (2) | Bg + prop close-ups |
| S2 | **Mesquite dining car: the interview table** | 50 mm, over the Agent's shoulder onto the suspect seat | A warm table lamp key, cold window rim light, deep oxblood shadows | Suspect portrait layer, the menu card on the table, Briggs's logbook | Bg + 2D portraits |
| S3 | **Larkspur corridor** | 24 mm, down the corridor | Sconces, frosted DR doors, the porter's seat at the far end with the name card | DR doors 1–6, smoking room, shoe lockers | Bg |
| S4 | **DR4, Nora's room** | 35 mm | Tidy. One towel on the rail and an empty hook. The typewriter with the wristwatch on it | Typewriter, dictation folder (fair copies), towel rail, window, the brass flush plate | Bg + props |
| S5 | **Juniper club car** | 35 mm, toward the bar | The bar **shutter down**, one amber night lamp | The brass notice "This car closes at midnight", the card table | Bg |
| S6 | **Sundown observation car** | 28 mm, toward the rear platform glass | Blue snow light, brandy glass stain on a chair arm | The Colonel's chair, the spilled-brandy stain | Bg |
| S7 | **Trackside snow, beside Larkspur** | 24 mm, low, lantern-lit | **Cold everything** except the lantern pool (amber) | Under DR3's window (latched, nothing below it), **under DR4** (towel half-buried, telegram scraps), bootprints toward the head end on the far side | Bg + lantern-mask interaction |
| S8 | **Baggage car** | 35 mm | One bare bulb, trunks, a blanket nest | Dottie (2D) | Bg + 2D |
| S9 | **Title** | The train stopped in the pass, seen from above the slide | Snow glow, warm windows | n/a | Bg (hero render, 4K) |
| S10 | **Epilogue cards** | Painted vignettes | Varies by ending | n/a | 2D |

**Prop close-ups (cold-lit, each 1080×1080):** the microphone (dented grille plus the thread), the
telegraph pad (plus a rubbing state), the letter (the broken *e* visible), the typewriter and a test
line, the Colonel's watch (the face reading an hour ahead), the ear-clip, the menu card, the 1918 photo
(chevrons readable when you zoom), the towel, the scraps ("—BY ONE IN MY EMPL—").

## 6. UI

- **Frame:** brass hairlines with Deco corner fans on midnight, and a film-grain overlay (about 3%).
- **Type** (all Google Fonts, OFL):
  - Display: **Poiret One**, used only for titles.
  - UI labels: **Josefin Sans**.
  - Captions: **Libre Caslon Text** at 30 px with a 2 px shadow.
  - Directions (Director's View): Libre Caslon *italic*, 20 px, snow-blue.
  - Typed documents: **Special Elite**. The broken *e* is a custom SVG glyph swap, so the clue is
    exactly the same everywhere it appears.
- **The interview screen:**
  - the suspect portrait (2D) in a brass oval frame, at the centre-left;
  - the clock, top right, as a Deco dial;
  - the intent chip, above the mic button;
  - captions in the lower third, with the direction in italics above them;
  - the notebook tab, bottom right.
- **The board ("The Clock"):** a timeline from 6 p.m. to 2 a.m. Lanes are people and places. Cards are
  little polaroid or telegram slips. A conflict glows with a red thread. Same-event threads are dashed
  brass.
- **Motion:** cards slide with a 120 ms ease-out. The clock hand ticks rather than sweeping. Nothing
  bounces.

## 7. Asset pipeline (what's 2D and what's Blender)

| Asset class | How it's made | Why |
|---|---|---|
| Environments S1–S9 | **Blender (Cycles)**, kitbashed period railcar interiors, rendered locally at 1080p for iteration, final at 2× on **RunPod** (TECH §9) | Consistent camera, lighting and geometry, and the hotspots line up with real geometry (we export the hotspot masks as a cryptomatte or object-index pass) |
| Hero props | Blender models with close-up renders | They're inspected up close, so they must be exactly right (the broken *e*, the watch hands) |
| Character portraits and expressions | **2D**: image generation via the configured image generator (the `image` route in studio.config.json), led by the character sheet plus a **Blender lighting proxy** | Painterly faces look better than our 3D in the time we have. The proxy keeps light direction and colour matching the background |
| Lighting proxy | A Blender grey mannequin bust at the S2 camera, lit exactly as S2, rendered per character pose | It's given to image gen as a reference input, so every portrait matches the scene's lighting |
| Character turnarounds | 2D image-gen sheets (front, 3/4, side, back), then a **Blender bust** blockout from the ortho views for the lighting proxy | The standard model-sheet practice (RESEARCH §1) |
| UI | HTML/CSS/SVG, no raster except grain | Crisp at any size |
| Epilogue cards | 2D image gen in the same style | Low cost, and there are many endings |

**The consistency loop:** `sheet → proxy render → portrait gen (sheet + proxy as inputs) → vision QA
(on-model? light from the left? accent colour present? no modern items?) → regenerate in a **fresh
chat** if it fails`. Never chain edits, because edits make skin waxy .

## 8. References (for mood, not for copying)
- **Edward Hopper**, *Compartment C, Car 293* (1938): a woman alone in a lamp-lit train compartment at
  night. The emotional key for the interview framing (https://en.wikipedia.org/wiki/Compartment_C,_Car_293).
- **Henry Dreyfuss's 1938 *20th Century Limited*** and the **1934 *Pioneer Zephyr***: the period
  streamline-Deco vocabulary of brushed metal, banded trim and porthole lamps
  (https://en.wikipedia.org/wiki/20th_Century_Limited ; https://en.wikipedia.org/wiki/Pioneer_Zephyr).
  Use the vocabulary and invent the liveries.
- **Pullman heavyweight drawing rooms** (pre-1937 open-window cars): panelling, berths, washstands, the
  annex (https://en.wikipedia.org/wiki/Pullman_Company).
- **Art Deco travel posters of the late 1920s and 1930s**: flat, graphic and monumental. Use them for
  title and card compositions (https://en.wikipedia.org/wiki/Art_Deco).
- **Noir cinematography** (chiaroscuro, motivated practicals): John Alton's *Painting with Light*
  (1949) is the craft text (https://en.wikipedia.org/wiki/John_Alton).

## 9. Quality bar
- Every background passes the **64 px thumbnail test**: the focal hotspot is still the brightest,
  highest-contrast spot.
- Every portrait passes the **on-model test** against its sheet: silhouette hook, accent colour, props.
- Every evidence close-up passes the **YouTube test**: the clue is readable after a 1080p encode at 4
  Mbps. Simulate it with `ffmpeg -b:v 4M` and inspect a 100% crop.
