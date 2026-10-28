# Blender realism spec (photoreal renders by script)

Read this before building any Blender scene meant to look real. Scripted scenes built from primitives
with flat colours always look like a blockout, however good the lighting is. Realism comes from **real
assets, real materials, real scale, imperfection, and physically based light**, and then from checking
the render against photographs.

## 0. The bar
Every final render must pass this check: *"Shown next to a real photo of the same kind of space, would a
stranger believe both are photographs?"* The art-director scores each render 1–10 against a reference photo.
Anything under 8 goes back with notes. Greybox is a layout tool, never a final. In a real-time game
the bar applies to the **live frame the player sees**, not only the Cycles render (§10).

## 1. Collect references before you model
- Gather 6–12 reference photos of the real thing: a period interior, the object, the light at that time of
  night. Use public-domain archives (Library of Congress, Wikimedia Commons, museum collections). Save
  them to `art/refs/<scene>/` with a SOURCES.md.
- Write the measured dimensions down from the refs (real-world metres; Blender units = metres). Wrong
  scale is the most common reason a render reads as fake.

## 2. Source assets. Don't model what already exists.
Free, script-downloadable, CC0 (no attribution needed):
- **Poly Haven**: `https://api.polyhaven.com/assets?t=textures|models|hdris&categories=...`, then
  `https://api.polyhaven.com/files/<id>` for download URLs (choose 2k or 4k, blend or gltf). It has scanned
  props (lamps, books, bottles, glassware, chairs, lanterns), wood, fabric and metal PBR sets, and night HDRIs.
- **ambientCG**: `https://ambientcg.com/api/v2/full_json?q=<term>&include=downloadData` for PBR sets
  (leather, velvet, veneer, brass, carpet, plaster), each with Color, Roughness, Normal, Displacement and AO maps.
- Optional, account needed: BlenderKit, or Sketchfab (CC-BY, credit it in CREDITS.md).
Record every asset in `art/CREDITS.md` (id, source, licence).

## 3. Modelling rules
- **No raw primitives in a final.** Every hard edge gets a bevel (Bevel modifier, 2–3 segments, about 3–6 mm
  at real scale) so it catches a highlight. Real objects don't have razor edges.
- Add the detail a camera sees: panel mouldings, trim strips, seams, screw heads, piping on upholstery,
  stitched cushions (Cloth sim or a sculpted displacement), curtains with folds (cloth sim, then apply).
- Repeated detail (rivets, panel grids, carpet pattern) comes from Geometry Nodes or arrays, not by hand.
- Clutter tells a story: an ashtray with ash, a half-drunk glass, a coat on a hook, papers out of square.
  Nothing perfectly aligned.

## 4. Materials (Principled BSDF, PBR only)
- Never a flat base colour on a final surface. Every material has a colour map plus roughness and normal
  maps (or a procedural substitute: noise-driven roughness, bump from a texture).
- Use real-world values: varnished wood roughness 0.25–0.45; brass metallic 1.0, roughness 0.2–0.35
  with fingerprint and smudge variation; velvet with the **Sheen** weight about 0.5–1.0; glass with
  Transmission 1.0, IOR 1.45–1.52, and real thickness (solidify).
- Imperfection layer: edge wear (Pointiness/AO-masked lighter edges), dust on upward faces (a geometry normal Z mask),
  grime in crevices (an AO mask), slight colour variation per object (Object Info → Random → hue/value).

## 5. Light like a cinematographer
- Use **practical lights** you can see in shot: lamp bulbs (Point/Area at the bulb, blackbody 2400–2900 K, with
  IES profiles if you have them), lamp shades with Translucent or Transmission so they glow.
- Motivated fill only. Exterior night: a night or moon HDRI at low strength (Poly Haven). Moonlight is a Sun
  lamp at about 0.05–0.2 strength, 4100–5500 K. Contrast comes from warm interior against cool exterior.
- Atmosphere: a Volume Scatter (density 0.002–0.02) in interiors for haze and light shafts. Snow outside
  is a particle system with real flakes (an instanced small mesh), plus motion blur.
- Stay in the AgX view transform (Blender 4+). Expose with the camera (Film exposure), never by cranking
  every lamp.

## 6. Camera
- Use real lenses: 24–35 mm for interiors, 50–85 mm for portrait or prop shots. Eye-height 1.5–1.6 m, verticals straight.
- Depth of field on (f/2.8–5.6) with a focus object, so the background falls off slightly.
- Add slight imperfection in compositing: lens distortion 0.5–1%, chromatic aberration 0.2–0.5, film grain, a soft glare (Fog Glow) on practicals.

## 7. Render settings (Cycles)
- GPU (OptiX). Use Adaptive sampling with a 0.01 noise threshold, max 1024–4096 samples, OptiX denoiser with
  albedo and normal passes, Light Paths max bounces 12 (transmission 12, volume 2), clamping indirect at 10.
- Previews run locally at 25% and 128 samples. Finals go on **RunPod** (RTX 4090/A6000). A 1920×1080 final
  usually takes 1–6 GPU-min, which is cents. Use the bundled RunPod script with its cost guardrails, and
  delete the pods afterwards.
- Output 16-bit EXR plus a PNG, and save the .blend with packed or relative textures.

## 8. The realism loop (required)
1. Build at greybox, check the camera and composition against the approved style frame, then lock the camera.
2. Swap in sourced assets and PBR materials, then do a preview render.
3. Make a contact sheet: render | reference photo | style frame. The art-director scores realism and fidelity to
   the style frame (1–10 each), with specific notes ("brass reads plastic: raise metallic, add smudge
   roughness"; "edges too sharp"; "wall too clean").
4. Iterate. At most 4 rounds per scene, about 30 min each. Then a final RunPod render, then vision QA at 100% crop.

## 9. When realism can't be reached in time
If a scene still scores under 7 after 4 rounds, keep the Blender render as the **depth, light and layout
pass**, and paint over it with the image generator in edit mode, with the render as the input image ("keep the
geometry and lighting exactly, make every surface photoreal"). Label it in CREDITS.md as a hybrid. Never ship a
greybox as final art.
- **A hybrid is a publisher decision at the gate, never a silent fallback.** Shipped hybrids shown as flat
  stills drew the publisher's note "This looks like GPT image gen work." If the game promises 3D, the
  fallback is the Cycles render itself, or another realism round.

## 10. The render-to-live gap (real-time engines)
A baked diffuse pass makes metals go flat or black, because metalness and roughness don't bake. Close the gap
before scoring:
- Hero metals, glass and porcelain stay live-lit, with a reflection probe or box-projected room environment.
- Window exteriors are real (rendered plates or CC0 assets with depth and light), never a gradient or blur.
- Higher-resolution lightmaps for close-up hero objects. A per-scene grade calibrated to the Cycles still
  (within about ±0.25 EV), with the shadow floor matched.
- Keep the frame-rate target (60 fps at 1920×1080 on the target machine), measured headless on a real GPU.
- Check: a contact sheet per room of live | Cycles | reference, scored by the art-director (`art-director.md`,
  the live gate).
