#!/usr/bin/env python3
"""WINDOW AUDIT — what is physically beside the road, and does the script say it?

The old gap audit asked "does this leg have enough blocks?". That passed while
14.0 drove out of Reykjavik with nothing to say about Reykjavik. This asks the
other question: take the real route geometry, ask OpenStreetMap what stands
within sight of that corridor, and diff it against every word of the script.

ONE query per feature type, using Overpass's linestring form
    node(around:RADIUS, lat1,lon1, lat2,lon2, ...)
instead of a query per sample point. 243 point-queries was a five-hour job;
this is four queries.

Network goes through curl — the Mac's python has no CA bundle.

Usage: python3 _windowaudit.py 5.0
"""
import json, re, sys, math, os, subprocess, time

TAG  = sys.argv[1] if len(sys.argv) > 1 else "5.0"
HERE = os.path.dirname(os.path.abspath(__file__))
STEP = 1.5      # km between corridor vertices
RAD  = 4000     # metres either side of the road
OUT  = os.path.join(HERE, "_windowaudit-%s.json" % TAG)

def km(a, b):
    dy = (a[0] - b[0]) * 111.32
    dx = (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)

# ---------------------------------------------------------------- geometry
rt = open(os.path.join(HERE, "route-%s.js" % TAG), encoding="utf-8").read()
pts = [(float(a), float(b)) for a, b in
       re.findall(r"\[\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\]", rt)]
if pts and abs(pts[0][0]) < 30:
    pts = [(b, a) for a, b in pts]
cum = [0.0]
for i in range(1, len(pts)):
    cum.append(cum[-1] + km(pts[i - 1], pts[i]))
TOTAL = cum[-1]

corr, last = [], None
for i, p in enumerate(pts):
    if last is None or km(p, last) >= STEP:
        corr.append((p, cum[i] / TOTAL * 100))
        last = p

# ---------------------------------------------------------------- script
sc  = open(os.path.join(HERE, "script-%s.js" % TAG), encoding="utf-8").read()
SEC = re.findall(r'\{title:"([^"]+)", kind:"(\w+)"', sc)

def flat(s):
    rep = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ý":"y","þ":"th",
           "ð":"d","æ":"ae","ö":"o","å":"a","ä":"a","ü":"u"}
    s = s.lower()
    for k, v in rep.items():
        s = s.replace(k, v)
    return s

HAY, HAYF = sc.lower(), flat(sc)

def said(name):
    n = name.lower().strip()
    if len(n) < 4:
        return True, "too-short"
    if n in HAY:
        return True, "exact"
    nf = flat(n)
    if nf in HAYF:
        return True, "flat"
    stem = re.sub(r"(fjall|fell|vatn|hraun|vik|nes|holt|dalur|kirkja|foss|"
                  r"jokull|ey|a|i|ur|inn)$", "", nf)
    if len(stem) >= 5 and stem in HAYF:
        return True, "stem:" + stem
    return False, ""

# ---------------------------------------------------------------- overpass
LINE = ",".join("%.5f,%.5f" % p for p, _ in corr)
QUERIES = {
 # Notability filter: a feature with a wikidata/wikipedia tag is one somebody
 # thought worth writing about. Without it the corridor returns every drainage
 # ditch and farmhouse on the south coast (153 "gaps", almost all noise).
 "wikidata-node": 'node(around:%d,%s)["wikidata"]["name"];',
 "wikidata-way":  'way(around:%d,%s)["wikidata"]["name"];',
 "peak":     'node(around:%d,%s)["natural"~"^(peak|volcano)$"]["name"];',
 "bigwater": 'way(around:%d,%s)["natural"~"^(water|bay)$"]["name"];',
 "historic": 'node(around:%d,%s)["historic"~"^(archaeological_site|castle|church|manor|memorial|monument|ruins|wreck|aircraft)$"]["name"];',
}
# osm.ch was dropped: it answered a valid query with 0 elements and an HTTP 200,
# which silently wiped the entire "natural" category out of a completed audit.
# An endpoint that lies quietly is worse than one that errors.
EPS = ["https://overpass-api.de/api/interpreter",
       "https://overpass.kumi.systems/api/interpreter"]

print("route %.1f km | %d geometry points | corridor of %d vertices every %.1f km, %d m each side"
      % (TOTAL, len(pts), len(corr), STEP, RAD), flush=True)
print("sections: %s" % " | ".join("%s(%s)" % (t, k) for t, k in SEC), flush=True)

def run(name, tmpl):
    body = "[out:json][timeout:120];(" + (tmpl % (RAD, LINE)) + ");out center tags;"
    for a in range(6):
        ep = EPS[a % len(EPS)]
        t0 = time.time()
        r = subprocess.run(["curl", "-sS", "--max-time", "150", "-X", "POST", ep,
                            "--data-urlencode", "data=" + body],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            d = json.loads(r.stdout)
            if not d.get("elements") and a < 2:
                print("  %-14s 0 elements — retrying elsewhere, that is almost"
                      " certainly a lie" % name, flush=True)
                time.sleep(10); continue
            print("  %-14s %4d elements  (%.0fs, %s)"
                  % (name, len(d.get("elements", [])), time.time() - t0,
                     ep.split("//")[1].split("/")[0]), flush=True)
            return d
        print("  %-14s retry %d (%s)" % (name, a + 1,
              (r.stderr or r.stdout or "")[:60].replace("\n", " ")), flush=True)
        time.sleep(8)
    print("  %-14s FAILED" % name, flush=True)
    return {"elements": []}

found = {}
for nm, tmpl in QUERIES.items():
    d = run(nm, tmpl)
    for el in d.get("elements", []):
        t  = el.get("tags", {})
        n  = t.get("name")
        if not n:
            continue
        c = el.get("center") or el
        if "lat" not in c:
            continue
        best = min(((km((c["lat"], c["lon"]), p), pr) for p, pr in corr),
                   key=lambda x: x[0])
        kind = (t.get("place") or t.get("natural") or t.get("waterway")
                or t.get("historic") or nm)
        if n not in found or best[0] < found[n]["km"]:
            found[n] = {"kind": kind, "km": best[0], "prog": best[1],
                        "lat": c["lat"], "lon": c["lon"]}

# ---------------------------------------------------------------- report
far  = max(range(len(pts)), key=lambda i: km(pts[0], pts[i]))
TURN = cum[far] / TOTAL * 100

rows = []
for n, v in found.items():
    ok, how = said(n)
    rows.append(dict(name=n, in_script=ok, match=how,
                     leg=("outbound" if v["prog"] <= TURN else "return"), **v))
rows.sort(key=lambda r: r["prog"])
miss = [r for r in rows if not r["in_script"]]
out  = [r for r in miss if r["leg"] == "outbound"]

print("\n" + "=" * 84)
print("NAMED FEATURES BESIDE THE ROAD %d   NOT IN SCRIPT %d   (outbound %d)"
      % (len(rows), len(miss), len(out)))
print("turnaround at %.1f%%; a RETURN-leg miss retraces road already covered outbound"
      % TURN)
print("=" * 84)
for r in miss:
    print("  %-8s %5.1f%%  %5.1f km  %-14s %s"
          % (r["leg"], r["prog"], r["km"], r["kind"], r["name"]))

json.dump({"tag": TAG, "total_km": round(TOTAL, 1), "turnaround_pct": round(TURN, 1),
           "corridor_vertices": len(corr), "radius_m": RAD,
           "sections": SEC, "rows": rows},
          open(OUT, "w"), ensure_ascii=False, indent=1)
print("\nwrote %s" % OUT)
