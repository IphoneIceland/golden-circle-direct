#!/usr/bin/env python3
"""Give every block its sightline. Ritchie's law, 5 Sep 2026:

    "no sightline should always be there, plus this is also why we have the photos"

The arrow answers WHERE, the photo answers WHAT. Never dropped for distance,
weather or visibility. The only blocks without one are those with nothing
physical to point at.

KEYED BY BLOCK TITLE, not id — ids shift under any rebuild, titles do not
(repo law, learned when the gcd165 rebuild orphaned the whole target table).
So one table serves 5.0, 6.0, 7.0 and anything else carrying the same stop.

At a stop the target is the thing you walk TO. Never the pin itself: an arrow
from the bus dot to itself is the gcd62 bug, and this script refuses to write one.

Usage: python3 _addsight.py 6.0 [--write]
"""
import json, re, os, sys, math, unicodedata

TAG   = sys.argv[1] if len(sys.argv) > 1 else "5.0"
WRITE = "--write" in sys.argv
HERE  = os.path.dirname(os.path.abspath(__file__))

def key(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("þ", "th").replace("ð", "d").replace("æ", "ae").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()

# Every coordinate geocoded via Nominatim / Overpass on 5 Sep 2026, not
# remembered — the first hand-typed pass had Ingolfsfjall 4 km out and
# Landeyjahofn 3 km out.
TARGETS = {
 "ingolfur arnarson":            ("Ingólfsfjall",   63.9820927, -21.0388121, "the mountain named after him"),
 "selfoss":                      ("Selfoss",        63.9330,    -20.9975,    "the town across the river"),
 "hvolsvollur":                  ("Hvolsvöllur",    63.7497,    -20.2244,    "the village you are parked in"),
 "landeyjar plains":             ("Landeyjahöfn",   63.5307687, -20.1174730, "the harbour out on the plain"),
 "solheimajokull":               ("Sólheimajökull", 63.5660204, -19.2955016, "the glacier itself"),
 "reynisfjara reynisdrangar":    ("Reynisdrangar",  63.4020,    -19.0430,    "the sea stacks off the beach"),
 "vikurkirkja":                  ("Víkurkirkja",    63.4204,    -19.0080,    "the church on its hill"),
 "vik i myrdal":                 ("Reynisfjall",    63.4400532, -19.0322471, "the cliff Vik sits under"),
 "skogafoss":                    ("Skógafoss",      63.5321,    -19.5114,    "the waterfall you walk up to"),
 "seljalandsfoss gljufrabui":    ("Seljalandsfoss", 63.6156,    -19.9886,    "the waterfall you walk behind"),
}
# nothing physical is the subject
NO_SUBJECT = ("music leg",)

def km(a, b):
    dy = (a[0] - b[0]) * 111.32
    dx = (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)

cf   = os.path.join(HERE, "cues-%s.js" % TAG)
raw  = open(cf, encoding="utf-8").read()
CUES = json.loads(raw[raw.index("["):raw.rindex("]") + 1])
sc   = open(os.path.join(HERE, "script-%s.js" % TAG), encoding="utf-8").read()

BLOCK = {}
for m in re.finditer(r'\{id:"(%s\.\d+\.\d+)"' % re.escape(TAG), sc):
    seg = sc[m.start():m.start() + 900]
    t = re.search(r'title:"([^"]*)"', seg)
    c = re.search(r'cue:"((?:[^"\\]|\\.)*)"', seg)
    BLOCK[m.group(1)] = (t.group(1) if t else "?", c.group(1) if c else "")

added = skipped = unknown = 0
for c in CUES:
    if c.get("target"):
        continue
    title = BLOCK.get(c["id"], ("?", ""))[0]
    k = key(title)
    if any(n in k for n in NO_SUBJECT):
        print("  %-11s %-32s no physical subject — correctly none" % (c["id"], title[:31]))
        skipped += 1
        continue
    if k not in TARGETS:
        print("  !! %-11s %-32s NO TARGET DEFINED (key %r)" % (c["id"], title[:31], k))
        unknown += 1
        continue
    name, la, lo, why = TARGETS[k]
    d = km((c["pin"]["lat"], c["pin"]["lon"]), (la, lo))
    if d < 0.05:
        print("  !! %-11s target sits ON the pin — refusing (arrow-to-itself bug)" % c["id"])
        unknown += 1
        continue
    c["target"] = {"lat": la, "lon": lo, "name": name}
    added += 1
    print("  %-11s %-30s -> %-15s %6.2f km  %s" % (c["id"], title[:29], name, d, why))

print("\n%s: %d added, %d correctly без target, %d unresolved"
      .replace("без", "without") % (TAG, added, skipped, unknown))

if WRITE and added:
    head = raw[:raw.index("[")]
    body = ", ".join(json.dumps(c, ensure_ascii=False) for c in CUES)
    open(cf, "w", encoding="utf-8").write(head + "[" + body + "]" + raw[raw.rindex("]") + 1:])
    print("WROTE %s" % cf)
elif not WRITE:
    print("(dry run — pass --write to apply)")
