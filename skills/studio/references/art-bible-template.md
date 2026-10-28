# Art bible template (Art Director)

Worked example: `examples/case-packs/dead-air-on-the-meridian/ART-BIBLE.md`. Good art bibles state a **tie-breaker
rule, the light direction, the shadow colour as a value, a level-of-detail floor, and a named list of
recurring mistakes** (RESEARCH §1).

```markdown
# ART BIBLE: "<title>"
## 1. The look in one line
## 2. Rules (tie-breakers) — light temperature logic, light direction, shadow colour hex, silhouette test,
   period/IP rule (no real logos/liveries/adaptation looks), readability > atmosphere, recurring mistakes
## 3. Palette — token | hex | use (+ one accent per character)
## 4. Characters — table: silhouette hook | costume (dated) | accent | props | expression specials
   (+ content limits: gore, etc.)
## 5. Scenes — # | scene | camera (mm, height, direction) | lighting | hotspots | medium (Blender bg / 2D / both)
   + prop close-up list
## 6. UI — frame, type (Google Fonts only, licence), screen layouts, board style, motion rules
## 7. Asset pipeline — asset class | how made | why  (see asset-pipeline.md)
## 8. References — for mood not copying; each with a source link
## 9. Quality bar — thumbnail test, on-model test, compression test
```

**Quality bar for the art bible itself:**
- A new artist could produce an on-model asset from it with no other context.
- Every rule is testable by a vision-QA pass.
