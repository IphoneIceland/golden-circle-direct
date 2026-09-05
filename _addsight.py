#!/usr/bin/env python3
"""Give every block its sightline. Ritchie's law, 5 Sep 2026:

    "no sightline should always be there, plus this is also why we have the photos"

Adds a target to every cue that has none, EXCEPT blocks with nothing physical to
point at (Music Legs, pure-idea blocks). At a stop the target is the thing you
walk TO, never the pin itself — an arrow from the bus dot to itself is the gcd62
bug.

Geocoding is hand-checked, not blind: every coordinate below was confirmed
against OSM and is written in the file so the next session can see the source.

Usage: python3 _addsight.py 5.0 [--write]
"""
import json, re, os, sys, math

TAG   = sys.argv[1] if len(sys.argv) > 1 else "5.0"
WRITE = "--write" in sys.argv
HERE  = os.path.dirname(os.path.abspath(__file__))

# id -> (target name, lat, lon, why this point)
TARGETS = {
 # Every coordinate below is geocoded, not remembered. Nominatim/Overpass, 5 Sep 2026.
 "5.0.1.9":  ("Ingólfsfjall",      63.9820927, -21.0388121, "the mountain named after him"),
 "5.0.1.10": ("Selfoss",           63.9330,    -20.9975,    "the town across the river"),
 "5.0.2.1":  ("Hvolsvöllur",       63.7497,    -20.2244,    "the village you are parked in"),
 "5.0.3.2":  ("Landeyjahöfn",      63.5307687, -20.1174730, "the harbour out on the plain"),
 "5.0.4.1":  ("Sólheimajökull",    63.5660204, -19.2955016, "the glacier itself, from the bus"),
 "5.0.6.1":  ("Reynisdrangar",     63.4020,    -19.0430,    "the sea stacks off the beach"),
 "5.0.8.1":  ("Víkurkirkja",       63.4204,    -19.0080,    "the church on its hill"),
 "5.0.8.2":  ("Reynisfjall",       63.4400532, -19.0322471, "the cliff Vik sits under - the hill in the cue"),
 "5.0.10.1": ("Skógafoss",         63.5321,    -19.5114,    "the waterfall you walk up to"),
 "5.0.11.1": ("Seljalandsfoss",    63.6156,    -19.9886,    "the waterfall you walk behind"),
}
# deliberately NOT given a sightline — nothing physical is the subject
SKIP = {"5.0.9.1": "Music Leg", "5.0.12.1": "Music Leg"}

def km(a, b):
    dy = (a[0] - b[0]) * 111.32
    dx = (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)

cf = os.path.join(HERE, "cues-%s.js" % TAG)
raw = open(cf, encoding="utf-8").read()
CUES = json.loads(raw[raw.index("["):raw.rindex("]") + 1])
sc = open(os.path.join(HERE, "script-%s.js" % TAG), encoding="utf-8").read()

BLOCK = {}
for m in re.finditer(r'\{id:"(%s\.\d+\.\d+)"' % re.escape(TAG), sc):
    seg = sc[m.start():m.start() + 900]
    t = re.search(r'title:"([^"]*)"', seg)
    c = re.search(r'cue:"((?:[^"\\]|\\.)*)"', seg)
    BLOCK[m.group(1)] = (t.group(1) if t else "?", c.group(1) if c else "")

added = 0
for c in CUES:
    if c.get("target") or c["id"] in SKIP:
        continue
    if c["id"] not in TARGETS:
        print("  !! %-11s %-34s NO TARGET DEFINED" % (c["id"], BLOCK.get(c["id"], ("?",))[0][:33]))
        continue
    name, la, lo, why = TARGETS[c["id"]]
    d = km((c["pin"]["lat"], c["pin"]["lon"]), (la, lo))
    if d < 0.05:
        print("  !! %-11s target sits ON the pin — that is the arrow-to-itself bug" % c["id"])
        continue
    c["target"] = {"lat": la, "lon": lo, "name": name}
    added += 1
    title, cue = BLOCK.get(c["id"], ("?", ""))
    print("  %-11s %-30s -> %-16s %5.2f km   %s" % (c["id"], title[:29], name, d, why))
    print("               cue: %s" % (cue[:96] or "(none)"))

print("\n%d sightlines added, %d deliberately left without one (%s)"
      % (added, len(SKIP), ", ".join(sorted(set(SKIP.values())))))

if WRITE:
    head = raw[:raw.index("[")]
    body = ", ".join(json.dumps(c, ensure_ascii=False) for c in CUES)
    open(cf, "w", encoding="utf-8").write(head + "[" + body + "]" + raw[raw.rindex("]") + 1:])
    print("WROTE %s" % cf)
else:
    print("(dry run — pass --write to apply)")
