#!/usr/bin/env python3
"""Print 'LEFT TOP RIGHT BOTTOM' (top-left origin, iTerm coordinates) for the studio floor.
Arg: '[x1,y1,x2,y2]' JSON | right | left | main | '' . Picks named displays by GEOMETRY, because
identical monitors often report identical names. Falls back to the main display, then 0 30 1920 1080."""
import json, sys
arg = (sys.argv[1] if len(sys.argv) > 1 else "").strip().strip("'\"")
if arg.startswith("["):
    print(*json.loads(arg)); sys.exit(0)
try:
    from AppKit import NSScreen
    screens = list(NSScreen.screens()); main = NSScreen.mainScreen()
    pick = {"right": max(screens, key=lambda s: s.frame().origin.x),
            "left": min(screens, key=lambda s: s.frame().origin.x)}.get(arg, main)
    h = main.frame().size.height; vf = pick.visibleFrame()
    top = int(round(h - (vf.origin.y + vf.size.height)))
    print(int(vf.origin.x), top, int(vf.origin.x + vf.size.width), int(top + vf.size.height))
except Exception:
    print({"right": "1920 30 3840 1080"}.get(arg, "0 30 1920 1080"))
