#!/usr/bin/env python3
"""Does each sightline point where the cue TEXT claims? Geometry vs words.

Restoring a target by title is only half the job — the pins moved when blocks
were added, so an arrow that read "on your left" in August can read 4 o'clock
now. This compares the computed clock bearing (target vs direction of travel)
against what the block's cue line actually says, and flags every disagreement.
"""
import os, json, re, io, math, sys

def cues(t):
    s = t[t.index('['):t.rindex(']')+1]
    try: return json.loads(s)
    except Exception:
        return json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:', r'\1"\2":', s))

def route(t):
    o = json.loads(t[t.index('{'):t.rindex('}')+1])
    return o["geometry"] if isinstance(o, dict) else o

def blocks(t):
    """id -> (title, cue, section kind). Stops are excluded from the direction
    test: at a walking stop there is no direction of travel, so 'on your left'
    means left of the person, not left of the bus."""
    secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"', t)]
    kind={}
    for i,(k,pos) in enumerate(secs):
        end=secs[i+1][1] if i+1<len(secs) else len(t)
        for m in re.finditer(r'\{id:"([\d.]+)"', t[pos:end]): kind[m.group(1)]=k
    out = {}
    for m in re.finditer(r'\{id:"([\d.]+)"', t):
        n = t.find('{id:"', m.end()); ch = t[m.start(): n if n > 0 else len(t)]
        ti = re.search(r'title:\s*"((?:[^"\\]|\\.)*)"', ch)
        cu = re.search(r'cue:\s*"((?:[^"\\]|\\.)*)"', ch)
        out[m.group(1)] = (ti.group(1) if ti else "", cu.group(1) if cu else "", kind.get(m.group(1),""))
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
    """Every acceptable side the words allow -- not just the first one found.

    "Look back and left - Ingolfsfjall" is BOTH back and left, and 8 o'clock
    satisfies it. Reading only the first marker reported that correct cue wrong.
    """
    c = cue.lower()
    m = re.search(r'(\d{1,2})(?:\s*[–-]\s*\d{1,2})?\s*o.clock', c)
    clock = int(m.group(1)) if m else None
    # A positional cue ("we're driving under it now", "crossing the Sog") says
    # where you ARE, not which way to look, and any left/right in it usually
    # belongs to something else in the sentence -- 10.0's Bulandshofdi reads
    # "the headland the road is cut into, sea on your left", where "left" is the
    # SEA. Position wins, unless the cue also names a clock.
    if clock is None and re.search(r"\b(driving (under|through)|crossing|pulling into|passing)\b", c):
        return None, None
    sides = []
    if 'look back' in c or 'behind' in c or re.search(r'over (your|the) \w+ shoulder', c): sides.append('back')
    if 'ahead' in c or '12 o' in c: sides.append('ahead')
    if 'left' in c: sides.append('left')
    if 'right' in c: sides.append('right')
    return (sides or None), clock

def clock_of(d): 
    h = round(d/30) % 12
    return 12 if h==0 else h

def side_of(d):
    if d>=330 or d<=30: return 'ahead'
    if 30<d<150: return 'right'
    if 150<=d<=210: return 'back'
    return 'left'

def _cumdist(R):
    """Cumulative metres along the route, for resolving a block by progress."""
    cm=[0.0]
    for i in range(1,len(R)): cm.append(cm[-1]+hav(R[i-1][0],R[i-1][1],R[i][0],R[i][1]))
    return cm
def idx_by_progress(cm, pct):
    """Resolve a block to a route index by its PROGRESS, never by nearest point.

    On an out-and-back tour the same road is driven twice. A nearest-point search
    picks whichever pass is closer, and on 7.0 that put the checker on the
    OUTBOUND pass at 25% while judging blocks that fire homeward at 75% --
    heading 80 degrees instead of 261, which flips left and right and reported
    three correct cues as wrong. The app places the dot by progress; so do we.
    """
    want=cm[-1]*max(0.0,min(100.0,pct))/100.0
    for i,c in enumerate(cm):
        if c>=want: return i
    return len(cm)-1

bad = 0; checked = 0

# The audited set is derived from tours.js ready:true — never hand-kept.
# (Hand-kept lists rot: 14.0 was built and shipped unaudited because it was
#  missing from three of these scripts. 4 Sep 2026.)
def _ready_tours():
    import re as _re
    t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tours.js"),
             encoding="utf-8").read()
    return _re.findall(r'\{id:"([^"]+)"[^}]*?ready:\s*true', t)

for tid in _ready_tours():
    C = cues(io.open(f"cues-{tid}.js",encoding="utf-8").read())
    R = route(io.open(f"route-{tid}.js",encoding="utf-8").read())
    B = blocks(io.open(f"script-{tid}.js",encoding="utf-8").read())
    n = len(R); rows=[]; CM=_cumdist(R)
    for c in C:
        t = c.get("target")
        if not t: continue
        checked += 1
        pin = c["pin"]
        pi = idx_by_progress(CM, c["progress"])
        j = min(pi+3, n-1); i0 = max(pi-1, 0)
        trav = bearing(R[i0][0],R[i0][1],R[j][0],R[j][1])
        rel = (bearing(pin["lat"],pin["lon"],t["lat"],t["lon"]) - trav) % 360
        gc, gs = clock_of(rel), side_of(rel)
        title, cue, knd = B.get(c["id"], ("","",""))
        if knd == "stop": continue
        cs, ck = claim(cue)
        if cs is None: continue
        ok = any(s==gs
                 or (s=='ahead' and gc in (11,12,1))
                 or (s=='back'  and gc in (5,6,7))
                 or (s=='left'  and gc in (7,8,9,10,11))
                 or (s=='right' and gc in (1,2,3,4,5))
                 for s in cs)
        if not ok:
            rows.append(f"    {c['id']:9s} {title[:34]:34s} says {"/".join(cs):11s} -> geometry {gc} o'clock ({gs}), {t['name'][:22]}")
    if rows:
        bad += len(rows)
        print(f"  {tid}:"); print("\n".join(rows))

print(f"\nchecked {checked} sightlines with a directional claim — {bad} disagree with the cue text")
