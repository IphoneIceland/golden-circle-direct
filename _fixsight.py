#!/usr/bin/env python3
"""Restore the wiped sightlines — and only ever move a pin that this makes right.

The whole pipeline in one pass, because the three steps are not independent:
  1. rehome the targets the rebuild orphaned, matched on block TITLE (ids are
     worthless across a rebuild);
  2. strip the self-pointing stop arrows the rebuild reintroduced (exact
     self-pointers only — Kjarvalsstaðir at 248 m is a real thing out a window);
  3. re-apply the before-abeam law, but ONLY to pins whose arrow currently
     disagrees with the cue text, and ONLY when a candidate position actually
     makes it agree. A pin that already reads true is never touched, and a pin
     with no better home stays put and gets reported.

That last rule is the one I got wrong the first time: I moved 121 pins
including tours that were already correct, and broke a good one on 5.0.
"""
import json, re, io, math, subprocess

GOOD = "d120f99"
REBUILT = ["1.0", "2.0", "3.0", "4.0", "9.0", "10.0"]   # tours that lost targets
ALL     = ["1.0", "2.0", "3.0", "4.0", "5.0", "6.0", "7.0", "9.0", "10.0"]
SPECIAL = {
    "🌍 Almannagjá":            {"lat": 64.409242, "lon": -20.751818, "name": "Skjaldbreiður"},
    "⚖️ Lögberg & the Alþingi": {"lat": 64.259536, "lon": -21.122538, "name": "Lögberg (Law Rock)"},
}

sh = lambda c: subprocess.run(c, shell=True, capture_output=True, text=True).stdout

def cues(t):
    s = t[t.index('['):t.rindex(']')+1]
    try: return json.loads(s)
    except Exception:
        return json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:', r'\1"\2":', s))

def route(t):
    o = json.loads(t[t.index('{'):t.rindex('}')+1])
    return o["geometry"] if isinstance(o, dict) else o

def meta(t):
    """block id -> (title, cue text, section kind)"""
    secs = [(m.group(2), m.start()) for m in
            re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"', t)]
    kind = {}
    for i, (k, pos) in enumerate(secs):
        end = secs[i+1][1] if i+1 < len(secs) else len(t)
        for m in re.finditer(r'\{id:"([\d.]+)"', t[pos:end]):
            kind[m.group(1)] = k
    out = {}
    for m in re.finditer(r'\{id:"([\d.]+)"', t):
        n = t.find('{id:"', m.end()); ch = t[m.start(): n if n > 0 else len(t)]
        ti = re.search(r'title:\s*"((?:[^"\\]|\\.)*)"', ch)
        cu = re.search(r'cue:\s*"((?:[^"\\]|\\.)*)"', ch)
        out[m.group(1)] = (ti.group(1) if ti else "", cu.group(1) if cu else "",
                           kind.get(m.group(1), ""))
    return out

def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def bearing(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c);dl=math.radians(d-b)
    y=math.sin(dl)*math.cos(p2)
    x=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360

def claim(cue):
    c = cue.lower()
    if 'look back' in c or 'behind' in c or 'shoulder' in c: return 'back'
    if 'ahead' in c or '12 o' in c: return 'ahead'
    if 'left' in c:  return 'left'
    if 'right' in c: return 'right'
    return None

def side_of(d):
    if d>=330 or d<=30: return 'ahead'
    if 30<d<150: return 'right'
    if 150<=d<=210: return 'back'
    return 'left'

def clock_of(d):
    h = round(d/30)%12
    return 12 if h==0 else h

def agrees(said, rel):
    gs, gc = side_of(rel), clock_of(rel)
    return (said == gs
            or (said=='ahead' and gc in (11,12,1))
            or (said=='back'  and gc in (5,6,7))
            or (said=='left'  and gc in (7,8,9,10,11))
            or (said=='right' and gc in (1,2,3,4,5)))

restored = stripped = movedn = 0
unresolved = []

for tid in ALL:
    C = cues(io.open(f"cues-{tid}.js", encoding="utf-8").read())
    R = route(io.open(f"route-{tid}.js", encoding="utf-8").read())
    M = meta(io.open(f"script-{tid}.js", encoding="utf-8").read())
    n = len(R)

    # ---- 1. rehome orphaned targets, by title ----
    if tid in REBUILT:
        oldC = cues(sh(f"git show {GOOD}:cues-{tid}.js"))
        oldM = meta(sh(f"git show {GOOD}:script-{tid}.js"))
        by_title = {}
        for c in oldC:
            if c.get("target") and oldM.get(c["id"]):
                by_title.setdefault(oldM[c["id"]][0].strip(), c["target"])
        for c in C:
            if not c.get("target"):
                t = M.get(c["id"], ("","",""))[0].strip()
                if t in by_title:
                    c["target"] = by_title[t]; restored += 1

    # ---- 2. specials + strip exact self-pointers ----
    for c in C:
        title = M.get(c["id"], ("","",""))[0].strip()
        if title in SPECIAL and tid in REBUILT:
            c["target"] = SPECIAL[title]; continue
        t = c.get("target")
        if t and hav(c["pin"]["lat"], c["pin"]["lon"], t["lat"], t["lon"]) < 30:
            c["target"] = None; stripped += 1

    # ---- 3. before-abeam, but only where it fixes something ----
    cum=[0.0]
    for i in range(1,n): cum.append(cum[-1]+hav(R[i-1][0],R[i-1][1],R[i][0],R[i][1]))
    tot=cum[-1]
    prog=lambda i:100.0*cum[i]/tot
    idx =lambda p:min(range(n),key=lambda i:abs(prog(i)-p))

    def rel_at(i, t):
        j=min(i+3,n-1); i0=max(i-1,0)
        trav=bearing(R[i0][0],R[i0][1],R[j][0],R[j][1])
        return (bearing(R[i][0],R[i][1],t["lat"],t["lon"])-trav)%360

    for k,c in enumerate(C):
        t=c.get("target")
        if not t or M.get(c["id"],("","",""))[2]=="stop": continue
        said=claim(M.get(c["id"],("","",""))[1])
        if not said: continue
        here=idx(c["progress"])
        if agrees(said, rel_at(here,t)):        # already true — hands off
            continue
        lo = idx(C[k-1]["progress"])+1 if k>0 else 0
        hi = idx(C[k+1]["progress"])-1 if k+1<len(C) else n-1
        if hi<=lo: unresolved.append((tid,c["id"],M[c["id"]][0],said,"no room")); continue
        best=None
        for i in range(lo,hi+1):
            if agrees(said, rel_at(i,t)):
                d=hav(R[i][0],R[i][1],t["lat"],t["lon"])
                if best is None or d<best[1]: best=(i,d)
        if best is None:
            g=clock_of(rel_at(here,t))
            unresolved.append((tid,c["id"],M[c["id"]][0],said,f"reads {g} o'clock everywhere in its leg"))
            continue
        c["pin"]={"lat":round(R[best[0]][0],5),"lon":round(R[best[0]][1],5)}
        c["progress"]=round(prog(best[0]),2)
        movedn+=1

    for i in range(1,len(C)):
        if C[i]["progress"]<C[i-1]["progress"]: C[i]["progress"]=C[i-1]["progress"]

    head=io.open(f"cues-{tid}.js",encoding="utf-8").read().split("window.__CUES__")[0]
    io.open(f"cues-{tid}.js","w",encoding="utf-8").write(
        head+"window.__CUES__ = "+json.dumps(C,ensure_ascii=False)+";\n")
    print(f"  {tid}: {sum(1 for c in C if c.get('target'))} sightlines")

print(f"\nrestored {restored} targets, stripped {stripped} self-pointers, moved {movedn} pins")
if unresolved:
    print(f"\n{len(unresolved)} the geometry cannot satisfy — cue TEXT vs ground, for the scripts chat:")
    for u in unresolved:
        print(f"  {u[0]:5s} {u[1]:9s} {u[2][:34]:34s} text says {u[3]:5s} — {u[4]}")
