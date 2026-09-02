#!/usr/bin/env python3
"""Two narrow, provable corrections — and a rule against drawing lies.

1. Tours 1.0-4.0: the route is byte-identical to the audited commit, so an
   audited pin is still exactly right. Copy it back verbatim, but ONLY when
   doing so leaves progress monotonic — no cleverness, no reordering.

2. Tours 9.0/10.0: the route changed AND 10.0 runs the leg in reverse, so
   title order and route order disagree. I tried to be clever here and put pins
   125 km from their targets. So: pins are left exactly as the rebuild left
   them, and instead any restored sightline that is not physically credible —
   over 70 km, roughly the best a bus window ever gives — is DROPPED.

Dropping is the correct outcome, not a cop-out: HANDOVER's own law says where a
truthful line is impossible the line goes, because an arrow pointing at nothing
is worse than no arrow.
"""
import json, re, io, math, subprocess

GOOD = "d120f99"
MAX_KM = 70.0

sh = lambda c: subprocess.run(c, shell=True, capture_output=True, text=True).stdout

def cues(t):
    s = t[t.index('['):t.rindex(']')+1]
    try: return json.loads(s)
    except Exception:
        return json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:', r'\1"\2":', s))

def titles(t):
    o = {}
    for m in re.finditer(r'\{id:"([\d.]+)"', t):
        n = t.find('{id:"', m.end()); ch = t[m.start(): n if n > 0 else len(t)]
        x = re.search(r'title:\s*"((?:[^"\\]|\\.)*)"', ch)
        o[m.group(1)] = (x.group(1) if x else "").strip()
    return o

def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

# ---- 1. verbatim pin restore where the road did not move ----
for tid in ["1.0", "2.0", "3.0", "4.0"]:
    C = cues(io.open(f"cues-{tid}.js", encoding="utf-8").read())
    T = titles(io.open(f"script-{tid}.js", encoding="utf-8").read())
    oldC = cues(sh(f"git show {GOOD}:cues-{tid}.js"))
    oldT = titles(sh(f"git show {GOOD}:script-{tid}.js"))
    by_title = {}
    for c in oldC:
        t = oldT.get(c["id"], "")
        if t: by_title.setdefault(t, c)

    trial = [dict(c) for c in C]
    moved = 0
    for c in trial:
        o = by_title.get(T.get(c["id"], ""))
        if o and c.get("target") and c["pin"] != o["pin"]:
            c["pin"] = o["pin"]; c["progress"] = o["progress"]; moved += 1
    if all(trial[i]["progress"] >= trial[i-1]["progress"] for i in range(1, len(trial))):
        C = trial
        note = f"{moved} audited pins restored"
    else:
        note = "SKIPPED — restoring would break progress order"
    head = io.open(f"cues-{tid}.js", encoding="utf-8").read().split("window.__CUES__")[0]
    io.open(f"cues-{tid}.js","w",encoding="utf-8").write(
        head+"window.__CUES__ = "+json.dumps(C,ensure_ascii=False)+";\n")
    print(f"  {tid}: {note}")

# ---- 2. drop sightlines nobody could actually see ----
dropped = 0
for tid in ["1.0","2.0","3.0","4.0","5.0","6.0","7.0","9.0","10.0"]:
    C = cues(io.open(f"cues-{tid}.js", encoding="utf-8").read())
    T = titles(io.open(f"script-{tid}.js", encoding="utf-8").read())
    hits = []
    for c in C:
        t = c.get("target")
        if not t: continue
        km = hav(c["pin"]["lat"], c["pin"]["lon"], t["lat"], t["lon"]) / 1000
        if km > MAX_KM:
            hits.append(f"{c['id']} {T.get(c['id'],'')[:28]} -> {t.get('name','?')} at {km:.0f} km")
            c["target"] = None; dropped += 1
    head = io.open(f"cues-{tid}.js", encoding="utf-8").read().split("window.__CUES__")[0]
    io.open(f"cues-{tid}.js","w",encoding="utf-8").write(
        head+"window.__CUES__ = "+json.dumps(C,ensure_ascii=False)+";\n")
    for h in hits: print(f"  dropped {tid} {h}")

print(f"\n{dropped} not-credible sightlines dropped")
