# Run as: blender -b file.blend -P render.py -E CYCLES -o //out/frame_#### -f 1..2 -- --cycles-device OPTIX
# (render.py runs before -f because args are processed in order.)
# Enables GPU devices in Cycles prefs; prefers OPTIX, falls back to CUDA. Exits non-zero if no GPU found
# (set ALLOW_CPU=1 to permit CPU fallback).
import bpy, sys, os
argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
want = "OPTIX"
if "--cycles-device" in argv:
    want = argv[argv.index("--cycles-device")+1].split("+")[0].upper()
prefs = bpy.context.preferences.addons["cycles"].preferences
chosen = None
for dt in [want] + [d for d in ("OPTIX","CUDA") if d != want]:
    try:
        prefs.compute_device_type = dt
    except TypeError:
        continue
    prefs.refresh_devices() if hasattr(prefs, "refresh_devices") else prefs.get_devices()
    gpus = [d for d in prefs.devices if d.type == dt]
    if gpus:
        for d in prefs.devices:
            d.use = (d.type == dt)
        chosen = dt
        break
for d in prefs.devices:
    print(f"[render.py] device {d.type:6} use={d.use} {d.name}")
if not chosen and os.environ.get("ALLOW_CPU") != "1":
    print("[render.py] FATAL: no OPTIX/CUDA device found", file=sys.stderr); sys.exit(3)
for sc in bpy.data.scenes:
    sc.cycles.device = 'GPU' if chosen else 'CPU'
print(f"[render.py] compute_device_type={chosen} scene.device={bpy.context.scene.cycles.device}")
