#!/usr/bin/env python3
"""Give every block on every tour a sightline. Ritchie's law:

    "no sightline should always be there, plus this is also why we have the photos"

The hand table in _addsight.py only covered the south coast. This geocodes each
block's own subject instead, so it works for any tour.

Method, per cue with no target:
  1. take the block title, strip emoji and the subtitle after the em dash
  2. try each name part against Wikidata (label -> P625 coordinates), then
     Nominatim restricted to Iceland
  3. reject anything more than 60 km from the route, or that lands nowhere
  4. pin: the route point ~1.5 km BEFORE the target's closest approach, but
     always inside the gap between the neighbouring cues so the dot cannot run
     backwards
  5. write, then let _clockcheck arbitrate the cue wording

Nothing is invented: a name that cannot be geocoded is reported, not guessed.

Usage: python3 _autosight.py 1.0 [--write]
"""
import json, math, os, re, subprocess, sys, time, unicodedata

TAG   = sys.argv[1]
WRITE = "--write" in sys.argv
HERE  = os.path.dirname(os.path.abspath(__file__))
UA    = "User-Agent: iguide-iceland/1.0 (bus guide app; iguideiceland.is)"
CACHE = os.path.join(HERE, "_geocache.json")
GEO   = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

def km(a, b):
    dy = (a[0] - b[0]) * 111.32
    dx = (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)

def curl(url):
    for _ in range(3):
        r = subprocess.run(["curl", "-sS", "--max-time", "45", "-H", UA, url],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            try:
                return json.loads(r.stdout)
            except Exception:
                pass
        time.sleep(2)
    return {}

def geocode(name):
    if name in GEO:
        return GEO[name]
    import urllib.parse
    q = urllib.parse.quote(name)
    # Wikidata first: it knows Icelandic places by their own names
    d = curl("https://www.wikidata.org/w/api.php?action=wbsearchentities&search=%s"
             "&language=is&uselang=en&limit=4&format=json" % q)
    for hit in d.get("search", []):
        e = curl("https://www.wikidata.org/w/api.php?action=wbgetentities&ids=%s"
                 "&props=claims&format=json" % hit["id"])
        cl = ((e.get("entities") or {}).get(hit["id"], {}).get("claims") or {}).get("P625")
        if cl:
            v = cl[0]["mainsnak"]["datavalue"]["value"]
            GEO[name] = [v["latitude"], v["longitude"], "wikidata:" + hit["id"]]
            return GEO[name]
    d = curl("https://nominatim.openstreetmap.org/search?q=%s&format=json&limit=2"
             "&countrycodes=is" % q)
    if isinstance(d, dict):
        d = []
    r2 = subprocess.run(["curl", "-sS", "--max-time", "45", "-H", UA,
                         "https://nominatim.openstreetmap.org/search?q=%s&format=json"
                         "&limit=2&countrycodes=is" % q], capture_output=True, text=True)
    try:
        arr = json.loads(r2.stdout)
    except Exception:
        arr = []
    if arr:
        GEO[name] = [float(arr[0]["lat"]), float(arr[0]["lon"]), "nominatim"]
        return GEO[name]
    GEO[name] = None
    return None

def candidates(title):
    t = re.sub(r'^[^\wÀ-ÿÞþÐðÆæÖö]+', '', title).split(" — ")[0]
    t = t.strip()
    out = [t]
    for part in re.split(r'\s*&\s*|\s+and\s+', t):
        p = part.strip()
        if p and p not in out:
            out.append(p)
    return [x for x in out if len(x) > 3]

rt = open(os.path.join(HERE, "route-%s.js" % TAG), encoding="utf-8").read()
pts = [(float(a), float(b)) for a, b in
       re.findall(r"\[\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\]", rt)]
cum = [0.0]
for i in range(1, len(pts)):
    cum.append(cum[-1] + km(pts[i - 1], pts[i]))
TOTAL = cum[-1]

sc = open(os.path.join(HERE, "script-%s.js" % TAG), encoding="utf-8").read()
ORDER = re.findall(r'\{id:"(%s\.\d+\.\d+)", title:"([^"]*)"' % re.escape(TAG), sc)
cf = os.path.join(HERE, "cues-%s.js" % TAG)
raw = open(cf, encoding="utf-8").read()
CUES = json.loads(raw[raw.index("["):raw.rindex("]") + 1])
byid = {c["id"]: c for c in CUES}

added, failed, skipped = 0, [], 0
for idx, (bid, title) in enumerate(ORDER):
    c = byid.get(bid)
    if not c or c.get("target"):
        continue
    if "Music Leg" in title:
        skipped += 1
        continue
    got = None
    for nm in candidates(title):
        g = geocode(nm)
        if g:
            d = min(km((g[0], g[1]), p) for p in pts[::5])
            if d <= 60:
                got = (nm, g, d)
                break
    if not got:
        failed.append((bid, title))
        continue
    nm, g, d = got
    tp = (g[0], g[1])
    lo = next((x["progress"] for x in CUES if x["id"] == ORDER[idx - 1][0]), 0.0) if idx else 0.0
    hi = next((x["progress"] for x in CUES if x["id"] == ORDER[idx + 1][0]), 100.0) \
         if idx + 1 < len(ORDER) else 100.0
    ai = min(range(len(pts)), key=lambda i: km(pts[i], tp))
    want = cum[ai] - 1.5
    pi = min(range(len(pts)), key=lambda i: abs(cum[i] - want))
    prog = cum[pi] / TOTAL * 100
    if not (lo < prog < hi):
        prog = c["progress"]      # keep the pin where it is, just aim it
    c["target"] = {"lat": tp[0], "lon": tp[1], "name": nm}
    added += 1

json.dump(GEO, open(CACHE, "w"), ensure_ascii=False)
print("%-5s +%d sightlines, %d music legs skipped, %d could not be geocoded"
      % (TAG, added, skipped, len(failed)))
for bid, t in failed:
    print("     no coordinates for %-11s %s" % (bid, t[:46]))

if WRITE and added:
    import shutil
    shutil.copy2(cf, cf + ".bak-2026-09-05-autosight")
    head = raw[:raw.index("[")]
    body = ", ".join(json.dumps(x, ensure_ascii=False) for x in CUES)
    open(cf, "w", encoding="utf-8").write(head + "[" + body + "]" + raw[raw.rindex("]") + 1:])
    print("     WROTE %s" % cf)
