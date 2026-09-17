#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_pinaudit.py — read-only. Hunt for the next Vogar.

THE BUG THIS LOOKS FOR (found on 12.0, 17 Sep 2026)
Vogar was pinned at the village. The village sits 1.66 km off Reykjanesbraut, so
the drawn line turned off the main road, looped the village and came back — 4.5
km and 9 minutes of driving the coach never does. The app uses that line to work
out how far through the journey you are, so a line that is long by 14 minutes
fires cues in the wrong place.

THE TEST — drop-one, the same one that caught Vogar
Route the tour with all its stops, then route it again with one stop removed,
and see how much distance that stop was costing. Repeat for every stop.

A stop that costs distance is NOT automatically wrong. Gullfoss costs 90 km and
the coach absolutely goes there. What made Vogar wrong is that it is a
DRIVE-PAST — the manuscript introduces it with 🚌, not 📍 — and the coach never
leaves the main road for it.

   costs distance + marked 📍  = correct, that's a stop
   costs distance + marked 🚌  = SUSPECT, the line detours for nothing

An earlier version of this script measured each pin against a "through-road"
drawn first-stop-to-last. That is meaningless on a loop tour, where first and
last are both BSÍ and the through-road has zero length — it reported Gullfoss as
suspect on 2.0 and 3.0, which is nonsense. Drop-one works on loops and one-ways
alike.

  python3 _pinaudit.py            # every tour with a built route
  python3 _pinaudit.py 5.0 7.0    # just these
"""
import json, math, os, re, subprocess, sys, time, glob

GCD  = "/Users/ritchiej/Documents/golden-circle-direct/"
MS   = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/"
WARN = 1.0   # km a drive-past may cost before it is worth a look

def osrm_geo(pts):
    co = ";".join("%f,%f" % (p[1], p[0]) for p in pts)
    out = subprocess.run(["curl", "-s",
          "http://router.project-osrm.org/route/v1/driving/%s"
          "?overview=full&geometries=geojson" % co],
          capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
        if d.get("code") != "Ok": return None
        return [(c[1], c[0]) for c in d["routes"][0]["geometry"]["coordinates"]]
    except Exception:
        return None


def hav(a, b):
    R = 6371.0088
    la1, lo1 = math.radians(a[0]), math.radians(a[1])
    la2, lo2 = math.radians(b[0]), math.radians(b[1])
    return 2*R*math.asin(math.sqrt(math.sin((la2-la1)/2)**2 +
                math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))


def osrm_km(pts):
    co = ";".join("%f,%f" % (p[1], p[0]) for p in pts)
    out = subprocess.run(["curl", "-s",
          "http://router.project-osrm.org/route/v1/driving/%s?overview=false" % co],
          capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
        if d.get("code") != "Ok": return None
        return d["routes"][0]["distance"] / 1000.0
    except Exception:
        return None

def stop_kinds(tag):
    """{stop title lowercased: 'stop'|'drive'} taken from the BUILT script.

    An earlier version read the markdown and looked for "+ ## 📍" headings. Most
    manuscripts do not use that spelling — 2.0 has exactly one such heading in
    the whole file — so nearly every stop came back unclassified and Gullfoss
    was reported as a drive-past on 2.0 and 3.0, which is nonsense: it is the
    headline stop of the tour. The built JS already carries kind:"stop" or
    kind:"drive" per section, decided by the same parser the app uses, so ask
    that instead of re-deriving it badly. (17 Sep 2026)
    """
    f = GCD + "script-%s.js" % tag
    if not os.path.exists(f): return {}
    out = subprocess.run(["node", "-e",
        'global.window={};eval(require("fs").readFileSync(process.argv[1],"utf8"));'
        'console.log(JSON.stringify(window.__SCRIPT__.sections.map('
        's=>[s.title,s.kind])))', f], capture_output=True, text=True).stdout
    try:
        secs = json.loads(out)
    except Exception:
        return {}
    kinds = {}
    for title, kind in secs:
        if kind == "stop":
            kinds[title.strip().lower()] = "stop"
    return kinds


def pins_for(tag):
    """Re-derive the builder's stop coordinates from the drawn route's legs."""
    s = open(GCD + "route-%s.js" % tag, encoding="utf-8").read()
    j = json.loads(s[s.index("{"):s.rindex("}")+1])
    geo, legs = j["geometry"], j["legs"]
    names = re.search(r'via (.+?)\. Stop coordinates', s)
    stops = [x.strip() for x in re.split(r'→', names.group(1))] if names else []
    tot, run, fr = sum(l["km"] for l in legs), 0.0, [0.0]
    for l in legs:
        run += l["km"]; fr.append(run / tot)
    pins = [tuple(geo[min(int(f * (len(geo)-1)), len(geo)-1)]) for f in fr]
    return stops, pins, tot

TOURS = re.findall(r'id:"([^"]+)"', open(GCD + "tours.js", encoding="utf-8").read())
want  = sys.argv[1:] or TOURS
flagged, checked = [], 0

for tag in want:
    if not os.path.exists(GCD + "route-%s.js" % tag):
        print("%-6s (no route file — not built)\n" % tag); continue
    stops, pins, tot = pins_for(tag)
    kinds = stop_kinds(tag)
    full = osrm_km(pins); time.sleep(0.8)
    if full is None:
        print("%-6s (router declined)\n" % tag); continue
    print("%-6s %d stops, %.1f km with every stop" % (tag, len(pins), full))
    for i, name in enumerate(stops):
        if i == 0 or i == len(pins)-1:       # start and end define the tour
            print("        %-32s  (endpoint)" % name[:32]); continue
        less = osrm_km(pins[:i] + pins[i+1:]); time.sleep(0.8)
        checked += 1
        if less is None:
            print("        %-32s  (router declined)" % name[:32]); continue
        cost = full - less
        mark = kinds.get(name.lower(), "drive")
        flag = ""
        if cost >= WARN and mark != "stop":
            # SECOND STAGE, and it matters. A waypoint that costs distance is
            # only a Vogar if the coach would have driven past it ANYWAY. Drop
            # it, redraw, and see where the road goes: if the new line still
            # passes close to the pin, the pin is making the coach leave a road
            # it was already on — that is the bug. If the new line goes somewhere
            # else entirely, the waypoint is DEFINING the route, not detouring
            # from it, and the distance it "costs" is the tour itself.
            #
            # Without this stage the script cried wolf over Selfoss on the three
            # Golden Circle tours (drop it and the router returns via Þingvellir,
            # 28 km away — Selfoss is what forces the southern return) and over
            # Reykjanesviti on 13.0 (the turnaround point of the loop).
            geo2 = osrm_geo(pins[:i] + pins[i+1:]); time.sleep(0.8)
            near = min(hav(pins[i], q) for q in geo2) if geo2 else 99.0
            if near < 1.0:
                flag = ("  <-- SUSPECT: costs %.1f km, yet the coach passes "
                        "%.2f km away without it" % (cost, near))
                flagged.append((tag, name, cost))
            else:
                flag = "  (route-defining — without it the road goes %.0f km elsewhere)" % near
        print("        %-32s  costs %6.1f km  %-5s%s" % (name[:32], cost, mark, flag))
    print()

print("=" * 72)
print("%d stops tested." % checked)
if flagged:
    print("SUSPECT — drive-past stops the drawn line detours to:")
    for t, n, c in sorted(flagged, key=lambda x: -x[2]):
        print("   %-6s %-30s %.1f km" % (t, n, c))
else:
    print("No drive-past stop costs the line more than %.1f km. Clean." % WARN)
print("Pins are Ritchie's call — this reports, it does not move anything.")
