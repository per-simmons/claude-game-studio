# Character sheet spec (Character Artist)

One folder per character, `art/sheets/<CH-ID>/`. Model sheet, turnaround and expression sheet are
standard practice (RESEARCH §1).

| File | Content | Size | How |
|---|---|---|---|
| `turnaround.png` | Front, 3/4 front, side, 3/4 back and back, on one sheet, neutral pose, flat even light, grey background, **height lines** | 3072×1024 | Image gen (subscription), one fresh chat per attempt |
| `expressions.png` | A 3×3 grid: neutral/baseline, guarded, cracking, broken, plus up to 5 **character specials** from the art bible | 2048×2048 | Image gen with `turnaround.png` as the reference input |
| `costume.png` | Props and costume details with call-outs (fabric, period, colour hex) | 2048×1536 | Image gen |
| `ortho-front.png`, `ortho-side.png` | Clean orthographic crops for Blender reference planes | 1024×1024 | Cropped from the turnaround |
| `proxy/<pose>.png` | A Blender grey-bust lighting proxy at the scene camera | 1024×1024 | `blender -b -P proxy_bust.py -- --char <id> --pose <pose>` |
| `portrait/<state>.png` | **Final in-game portraits**, one per expression state, lit to match the scene | 1024×1280, alpha | Image gen with inputs (turnaround + proxy), then a cutout |
| `sheet.json` | `{id, height_cm, palette:{accent, ...}, silhouette_hook, props[], states[], do[], dont[]}` | | Hand-authored from the art bible |

**Prompt skeleton for every character generation:**
```
<style line from art bible §1>. Character: <name>, <age>, <silhouette hook>. Costume: <costume>.
Accent colour <hex> appears in <where>. Expression: <state description>. Lighting: key from frame-left,
<warm/cold> per art bible; shadows deep oxblood-brown, never black. Period 1936; no modern items;
no real logos or text. Natural matte skin, real texture (NOT plastic). Neutral grey background.
```
Avoid "flawless," "hyperrealistic," "8k," "glossy" and "airbrushed." They make the skin plastic, as
experience with image models shows.

**On-model QA** (vision check on every output):
1. The silhouette hook is present.
2. The accent colour is present.
3. The props are correct.
4. The light comes from the left.
5. There's no anachronism.
6. The face matches the turnaround.
7. Hands are sane.

Any failure means regenerating in a **new chat** from the original prompt, with the fix written into
it. Never chain edits.
