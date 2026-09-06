#!/usr/bin/env python3
"""The check the other tools do not do: DISTANCE, and the ruler.

_clockcheck.py asks whether the arrow points the right way. It does not ask
whether the thing is anywhere near you. Rauðhólar on 4.0 sat 16.1 km past
Rauðhólar and passed every audit for weeks, because at 16 km the bearing still
happened to land in the "right" band.

Two questions here, per tour:
  LATE/EARLY  how far is each block's pin from its own target, and how close does
              the route actually get to that target inside the same leg? A pin
              far from a subject the route drives right past is a misplaced pin.
  RULER       are the drive blocks on a leg spaced at a constant interval? That
              is the fingerprint of blocks laid out by dividing the leg into
              equal parts instead of being aimed at anything.

Distant landmarks (mountains the route never gets within 15 km of) are exempt
from LATE/EARLY: you see Hekla for forty minutes, closest approach means nothing.
"""
import json,re,io,math,sys,glob,os

def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def load(tid):
    ct=io.open('cues-%s.js'%tid,encoding='utf-8').read()
    s=ct[ct.index('['):ct.rindex(']')+1]
    try: cu=json.loads(s)
    except Exception: cu=json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:',r'\1"\2":',s))
    rt=io.open('route-%s.js'%tid,encoding='utf-8').read()
    o=json.loads(rt[rt.index('{'):rt.rindex('}')+1])
    g=o["geometry"] if isinstance(o,dict) else o
    sc=io.open('script-%s.js'%tid,encoding='utf-8').read()
    kind={};title={}
    secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',sc)]
    for i,(k,pos) in enumerate(secs):
        end=secs[i+1][1] if i+1<len(secs) else len(sc)
        for m in re.finditer(r'\{id:"([\d.]+)"',sc[pos:end]): kind[m.group(1)]=k
    for m in re.finditer(r'\{id:"([\d.]+)"',sc):
        n=sc.find('{id:"',m.end()); ch=sc[m.start(): n if n>0 else len(sc)]
        t=re.search(r'title:\s*"((?:[^"\\]|\\.)*)"',ch)
        title[m.group(1)]=t.group(1) if t else ''
    return cu,g,kind,title

TOURS=sorted({os.path.basename(f)[5:-3] for f in glob.glob('cues-*.js') if '.bak' not in f},
             key=lambda s: float(s))
late=[];rulers=[]
for tid in TOURS:
    try: cu,g,kind,title=load(tid)
    except Exception as e:
        print("skip %s (%s)"%(tid,e)); continue
    N=len(g)
    cum=[0.0]
    for i in range(1,N): cum.append(cum[-1]+hav(g[i-1][0],g[i-1][1],g[i][0],g[i][1]))
    total=cum[-1]
    # leg boundaries = the stop blocks
    stops=[i for i,x in enumerate(cu) if kind.get(x['id'])=='stop']
    def leg_of(n):
        lo=0;hi=len(cu)-1
        for s in stops:
            if s<=n: lo=s
            if s>=n: hi=s;break
        return lo,hi
    def idx_of(pct):
        want=total*pct/100
        for i,c in enumerate(cum):
            if c>=want: return i
        return N-1
    for n,x in enumerate(cu):
        T=x.get('target')
        if not T or kind.get(x['id'])=='stop': continue
        d=hav(x['pin']['lat'],x['pin']['lon'],T['lat'],T['lon'])
        lo,hi=leg_of(n)
        a=idx_of(cu[lo]['progress']); b=idx_of(cu[hi]['progress'])
        if b<=a: a,b=0,N-1
        dmin=min(hav(T['lat'],T['lon'],g[i][0],g[i][1]) for i in range(a,b+1))
        if dmin>15000: continue                    # distant landmark, exempt
        if d>2500 and d-dmin>1500:
            late.append((tid,x['id'],title.get(x['id'],'')[:30],T['name'][:24],d/1000,dmin/1000))
    # ruler: runs of >=4 consecutive drive blocks at a constant progress step
    prog=[x['progress'] for x in cu]
    run=[]
    for i in range(1,len(prog)-1):
        step1=round(prog[i]-prog[i-1],2); step2=round(prog[i+1]-prog[i],2)
        if step1>0.3 and abs(step1-step2)<0.02:
            if not run: run=[i-1,i,i+1]
            else: run.append(i+1)
        else:
            if len(run)>=4: rulers.append((tid,cu[run[0]]['id'],cu[run[-1]]['id'],len(run),round(prog[run[1]]-prog[run[0]],3)))
            run=[]
    if len(run)>=4: rulers.append((tid,cu[run[0]]['id'],cu[run[-1]]['id'],len(run),round(prog[run[1]]-prog[run[0]],3)))

print("=== PINS FAR FROM A SUBJECT THE ROUTE DRIVES PAST ===")
if not late: print("  none")
for r in sorted(late,key=lambda r:-r[4]):
    print("  %-5s %-10s %-30s -> %-24s pin %6.1f km   route gets to %5.1f km" % r)
print("\n=== EVENLY-SPACED RUNS (ruler fingerprint) ===")
if not rulers: print("  none")
for r in rulers:
    print("  %-5s %s .. %s  %d blocks at exactly %.3f%% steps" % r)
