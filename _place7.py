#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Where on the Fellsfjara -> Vik leg does each new 7.0 block belong, and which
way does the guest actually look? Same geometry the shipped checker uses."""
import json, re, io, math, sys
sys.path.insert(0, ".")
from _clockcheck import route, hav, bearing, cues

geo = route(io.open("route-7.0.js", encoding="utf-8").read())
C = cues(io.open("cues-7.0.js", encoding="utf-8").read())
pts = [(p[0], p[1]) if isinstance(p, (list, tuple)) else (p["lat"], p["lon"]) for p in geo]

cum = [0.0]
for i in range(1, len(pts)):
    cum.append(cum[-1] + hav(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1]))
total = cum[-1]

def at_progress(pr):
    want = total * pr / 100.0
    lo = min(range(len(cum)), key=lambda i: abs(cum[i] - want))
    return lo

def clock(i, tlat, tlon):
    a = max(0, i - 2); b = min(len(pts) - 1, i + 2)
    head = bearing(pts[a][0], pts[a][1], pts[b][0], pts[b][1])
    br = bearing(pts[i][0], pts[i][1], tlat, tlon)
    rel = (br - head + 360) % 360
    h = round(rel / 30.0) % 12
    return (12 if h == 0 else h), hav(pts[i][0], pts[i][1], tlat, tlon) / 1000.0

TARGETS = {
    "Mýrdalsjökull": (63.63333, -19.05),          # ice-cap centre, north of the sandur
    "Höfðabrekka":   (63.42417, -18.93361),       # the farm on the ridge east of Vík
    "Vík":           (63.41806, -19.00611),
}

print("route length %.1f km, %d points" % (total/1000.0, len(pts)))
for name, (tl, tn) in TARGETS.items():
    print("\n== %s" % name)
    for pr in [72.0, 72.5, 73.0, 73.5, 74.0, 74.3, 74.6, 74.9, 75.1, 75.2, 75.3, 75.38]:
        i = at_progress(pr)
        h, d = clock(i, tl, tn)
        side = "right" if 1 <= h <= 5 else ("left" if 7 <= h <= 11 else ("ahead" if h == 12 else "behind"))
        print("  %5.2f%%  %.5f,%.5f  %2d o'clock (%-6s) %6.1f km" % (pr, pts[i][0], pts[i][1], h, side, d))

print("\n== existing 7.0.11.1 (Katla) ==")
for c in C:
    if c["id"] in ("7.0.10.1", "7.0.11.1", "7.0.12.1"):
        print(" ", c["id"], c["progress"], c["pin"], c.get("target"))
