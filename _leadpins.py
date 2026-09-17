#!/usr/bin/env python3
"""LEAD PINS — stop the bus arriving after the story.  _leadpins.py <id> [--apply]

The bug this exists for (found on 4.0, 10 Sep 2026, reported by Ritchie as
"map pins in front of the script block and sightlines behind the bus"):

A pin decides WHEN a block fires. Every drive pin on 4.0 sat at the target's
CLOSEST APPROACH, so the block only appeared once the thing was already abeam —
and by the time a guide reads a hook, a point and four bullets at 90 km/h it is
two kilometres behind the coach. The cue text had then been patched to match
that late geometry ("Behind us now, across the Ölfusá — Selfoss"), which made
the lateness permanent and invisible to the checkers.

Why _clockcheck.py passed on all of it: it validates the SIDE (left/right/
ahead/back), not the hour. "Look right at 1-2 o'clock" is satisfied by anything
from 1 to 5 o'clock, so a sightline pointing four hours behind where the words
said scored a clean pass. Side alone is not enough — see the clock delta printed
below.

The fix: pin every drive block a LEAD before closest approach, scaled to how far
the target is, so the target is forward-oblique when the block fires and abeam
by the time the guide finishes talking. Then rewrite the cue's hour to the
geometry that results — the words follow the road, never the other way round.

  < 0.5 km   ->  350 m lead
  0.5-1.5 km ->  500 m
  1.5-5 km   ->  900 m
  5-15 km    -> 1500 m
  > 15 km    ->  pin untouched; a landmark that far is judged on direction only

Rules kept from _fixpins.py, learned the hard way: stop pins never move, blocks
never go backwards, resolve by PROGRESS not nearest-point, and a block is held
back rather than shoved past its neighbour.
"""
import json, re, io, math, sys, shutil, datetime, os

TAG   = sys.argv[1] if len(sys.argv) > 1 else "4.0"
APPLY = "--apply" in sys.argv
HERE  = os.path.dirname(os.path.abspath(__file__))
MINGAP = 0.22          # % of route between two drive pins
SEARCH = 6.0           # % of route either side of the current pin to look in

def cues(t):
    s = t[t.index('['):t.rindex(']')+1]
    try: return json.loads(s)
    except Exception:
        return json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:', r'\1"\2":', s))

def route(t):
    o = json.loads(t[t.index('{'):t.rindex('}')+1])
    return o["geometry"] if isinstance(o, dict) else o

def blocks(t):
    secs=[(m.group(1),m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',t)]
    kind={}
    for i,(st,k,pos) in enumerate(secs):
        end=secs[i+1][2] if i+1<len(secs) else len(t)
        for m in re.finditer(r'\{id:"([\d.]+)"',t[pos:end]): kind[m.group(1)]=k
    out={}
    for m in re.finditer(r'\{id:"([\d.]+)"',t):
        n=t.find('{id:"',m.end()); ch=t[m.start(): n if n>0 else len(t)]
        ti=re.search(r'title:\s*"((?:[^"\\]|\\.)*)"',ch)
        cu=re.search(r'cue:\s*"((?:[^"\\]|\\.)*)"',ch)
        out[m.group(1)]=(ti.group(1) if ti else "", cu.group(1) if cu else "", kind.get(m.group(1),""))
    return out

def hav(a,b,c,d):
    R=6371000.0; p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def bear(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c); dl=math.radians(d-b)
    y=math.sin(dl)*math.cos(p2)
    x=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360

def lead_for(km):
    if km < 0.5:  return 350.0
    if km < 1.5:  return 500.0
    if km < 5.0:  return 900.0
    if km < 15.0: return 1500.0
    return None

C = cues(io.open(f"{HERE}/cues-{TAG}.js",encoding="utf-8").read())
R = route(io.open(f"{HERE}/route-{TAG}.js",encoding="utf-8").read())
B = blocks(io.open(f"{HERE}/script-{TAG}.js",encoding="utf-8").read())

cmv=[0.0]
for i in range(1,len(R)): cmv.append(cmv[-1]+hav(R[i-1][0],R[i-1][1],R[i][0],R[i][1]))
TOT=cmv[-1]
def i_of(p):
    w=TOT*max(0.0,min(100.0,p))/100.0
    for i,c in enumerate(cmv):
        if c>=w: return i
    return len(R)-1
def p_of(i): return cmv[i]/TOT*100.0
def clock(d):
    h=round(d/30)%12
    return 12 if h==0 else h
def rel_at(i, t):
    j=min(i+3,len(R)-1); i0=max(i-1,0)
    trav=bear(R[i0][0],R[i0][1],R[j][0],R[j][1])
    return (bear(R[i][0],R[i][1],t["lat"],t["lon"])-trav)%360

# --- leg windows: a drive block may only live between the stops either side ---
order=[c["id"] for c in C]
kindof={cid: B.get(cid,("","",""))[2] for cid in order}
stops=[(k,c["progress"]) for k,c in zip(order,C) if kindof.get(k)=="stop"]

def window(idx):
    lo, hi = 0.0, 100.0
    for k,p in stops:
        i=order.index(k)
        if i<idx: lo=max(lo,p)
        if i>idx: hi=min(hi,p); break
    return lo,hi

rows=[]; new={}
for n,c in enumerate(C):
    cid=c["id"]; t=c.get("target"); ti,cu,kd=B.get(cid,("","",""))
    if kd!="drive" or not t:
        new[cid]=c["progress"]; continue
    lo,hi=window(n)
    # Search a WINDOW around where the block already is, not the whole leg.
    # Searching the leg let a block chase a nearer approach kilometres down the
    # road: Ingolfur Arnarson jumped from 21% to 24%, past Selfoss, dragging two
    # blocks with it. Bounding the search fixes that without the backward-only
    # rule, which had its own failure -- a block already pinned 3.4 km BEFORE its
    # bridge (1.0's Bruara) could never move forward to it.
    lo=max(lo, c["progress"]-SEARCH); hi=min(hi, c["progress"]+SEARCH)
    best=None
    for i in range(i_of(lo), i_of(hi)+1):
        d=hav(R[i][0],R[i][1],t["lat"],t["lon"])
        if best is None or d<best[0]: best=(d,i)
    dmin,imin=best
    L=lead_for(dmin/1000.0)
    if L is None:
        new[cid]=c["progress"]; rows.append((cid,ti,c["progress"],c["progress"],dmin/1000,clock(rel_at(i_of(c["progress"]),t)),clock(rel_at(i_of(c["progress"]),t)),"far — left alone")); continue
    want=max(cmv[imin]-L, cmv[i_of(lo)])
    ni=imin
    while ni>0 and cmv[ni]>want: ni-=1
    oldp=c["progress"]; npct=p_of(ni)
    rows.append((cid,ti,oldp,npct,dmin/1000,clock(rel_at(i_of(oldp),t)),clock(rel_at(ni,t)),""))
    new[cid]=npct

# monotonic + min gap, never pushing a block past the next stop
prev=-1.0
for n,c in enumerate(C):
    cid=c["id"]
    if kindof.get(cid)=="stop":
        prev=max(prev,new[cid]); continue
    lo,hi=window(n)
    v=max(new[cid], prev+MINGAP if prev>=0 else new[cid])
    v=min(v,hi)
    new[cid]=round(v,2); prev=new[cid]

print(f"{'id':9s} {'title':32s} {'now%':>6s} {'new%':>6s} {'km':>6s} {'clk':>4s}->{'clk':<4s} note")
print("-"*104)
for cid,ti,o,nn,km,co,cn,note in rows:
    nn=new[cid]
    flag="" if co==cn else "  MOVED"
    print(f"{cid:9s} {ti[:32]:32s} {o:6.2f} {nn:6.2f} {km:6.2f} {co:>4d}->{cn:<4d}{flag} {note}")

if APPLY:
    p=f"{HERE}/cues-{TAG}.js"
    shutil.copy2(p, p+".bak-"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+"-leadpins")
    txt=io.open(p,encoding="utf-8").read()
    for c in C:
        cid=c["id"]
        if abs(new[cid]-c["progress"])<1e-9: continue
        i=i_of(new[cid])
        c["progress"]=round(new[cid],2)
        c["pin"]={"lat":round(R[i][0],5),"lon":round(R[i][1],5)}
    head=txt[:txt.index('[')]
    io.open(p,"w",encoding="utf-8").write(head+json.dumps(C,ensure_ascii=False)+";\n")
    print("\nwrote", p)
