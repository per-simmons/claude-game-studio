# Asset pipeline: 2D concept → character sheets → Blender → final in-game art

**Owners:** Art Director (style, QA), Character Artist (sheets, portraits), 3D/Blender Artist
(scenes, props, proxies), Lighting/Render (look-dev, finals, RunPod).

## 0. Hard rules
- **Image generation uses the route in `studio.config.json` → `image`.** On the free path that's `manual`: the studio writes
  prompts to `art/prompts/` and you paste them into any image generator you like. With `command` it runs your own CLI.
  Never hardcode API keys.
  - Batch requests; image generators have rate limits.
  - Each change is a **fresh generation from the original prompt** with the fix written in. Don't
    chain edits, because edits make skin waxy.
  - If a generator stalls, retry 3–4× while checking for the output file.
- **Optional recording guard.** If `pro.respect_recording` is true, check that the recorder process (default `obs`)
  isn't running before any heavy local render. If it is, render remotely or wait.
- **Never steal focus.** Blender runs with `-b` (background). Any viewer runs headless, or off your main
  work area.
- **Invented brands only.** No real logos, liveries or trademarks in any generated or modelled asset.

## 1. Stages
| # | Stage | Input | Output | Tool | Gate |
|---|---|---|---|---|---|
| 1 | Mood and style frames | Art bible §1–3 | 3 style frames per key scene | image route (config) | **The publisher approves the look** |
| 2 | Character sheets | Art bible §4 + `character-sheet-spec.md` | turnaround, expressions, costume, sheet.json | image route (config) | Art Director's on-model QA |
| 3 | Blockout | Scene list + camera specs | `blender/scenes/<S>.blend` greybox at the final camera | Blender `-b -P` scripts | Composition check against the style frame |
| 4 | Set dressing and props | Period references | Kitbashed interiors, hero props modelled (the evidence must be exact) | Blender scripts; procedural materials | Prop close-ups match the clue text exactly |
| 5 | Look-dev and lighting | Art bible rules (2-temperature, key light frame-left, shadow hex) | Lit scenes, saved camera, render settings | Blender | 64 px thumbnail test |
| 6 | Lighting proxies | Scene camera and light rig + a grey bust per character pose | `proxy/<pose>.png` | Blender | n/a |
| 7 | Portraits | Turnaround + proxy as inputs | `portrait/<state>.png` with alpha | the image route, then a cutout (rembg or a mask) | On-model QA plus a light-match check |
| 8 | Iteration renders | Scenes | 960×540, 64 samples | **Local** Blender (respect the recording guard if it's on) | n/a |
| 9 | Final renders | Approved scenes | 1920×1080 or 3840×2160, 256–512 samples, OIDN denoise, plus an object-index pass | **RunPod** (`runpod-blender.md`) | Vision QA at 100% crops, and the compression test |
| 10 | Hotspot masks | Object-index pass | PNG masks → JSON polygons (`tools/masks_to_polys.py`) | Python | Every hotspot in the case file has a mask |
| 11 | Export | Finals | WebP/AVIF at 2 sizes, manifest.json | ffmpeg / sharp | Asset manifest lint |

## 2. Blender conventions
- Every scene is built by a script (`build_scene.py --scene S1`), so it can be rebuilt and diffed. Save
  the `.blend` as a cache, never as the source of truth.
- Use metric units. The camera's sensor is 36 mm. Colour management is AgX (Blender 4+/5 default), with
  the look saved in the file.
- Collections: `ENV`, `PROPS_EVIDENCE` (each prop's object index = its hotspot ID), `LIGHTS`, `PROXY`.
- Pack textures (`bpy.ops.file.pack_all()`) before uploading to RunPod, or pass `EXTRA_FILES`.
- Keep Blender versions the same locally and on the pod (`BLENDER_VERSION` env var; tested on 5.1.2).

## 3. Vision QA (before the publisher sees anything)
For every final:
- audit a 100% crop of each hotspot;
- check the clue is readable after `ffmpeg -b:v 4M` (the YouTube test);
- check the light direction and the shadow colour;
- check for anachronisms.

Report failures as `asset | rule | fix`.
