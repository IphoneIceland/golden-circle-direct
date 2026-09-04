#!/usr/bin/env python3
"""4.0 pin solver.

The app draws the sightline as a straight dashed line from the block's pin to its
target, so the pin decides both when a block fires and which way the arrow points.
A pin dumped 16 km past its subject draws an arrow backwards off the screen.

Rules, in order of authority:
  1. Stop pins never move. They are the anchors.
  2. A block only moves if it is BROKEN: its cue's direction disagrees with the
     geometry (shipped bands), or its target is over 2 km away and the move gets
     at least 1.4 km closer. Everything else is left alone.
  3. Among legal candidates, the winner satisfies the cue direction first, then
     sits closest to the subject.
  4. A cue with no direction ("At X", "Crossing X") goes to closest approach.
  5. A distant landmark (never nearer than 15 km) is visible along a whole
     stretch, so it is judged on direction only, never on distance.
  6. Blocks never go backwards; untargeted blocks keep their place unless order
     forces a nudge.

Run with --apply to write cues-4.0.js (a .bak is made first).
"""
import json,re,io,math,sys,shutil,datetime

APPLY = '--apply' in sys.argv

def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))
def brg(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c);dl=math.radians(d-b)
    y=math.sin(dl)*math.cos(p2)
    x=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360

_t=io.open('route-4.0.js',encoding='utf-8').read()
rt=json.loads(_t[_t.index('{'):_t.rindex('}')+1])
g=rt["geometry"] if isinstance(rt,dict) else rt
N=len(g)
cum=[0.0]
for i in range(1,N): cum.append(cum[-1]+hav(g[i-1][0],g[i-1][1],g[i][0],g[i][1]))
total=cum[-1]

def heading(i):
    # identical to the shipped checkers (_clockcheck.py / _blockaudit.py): a
    # four-point window straddling the pin. Solve against the same model that
    # verifies, or the fix and the check quietly disagree.
    j=min(i+3,N-1); i0=max(i-1,0)
    if j==i0: j=min(i0+1,N-1)
    return brg(g[i0][0],g[i0][1],g[j][0],g[j][1])

c=io.open('cues-4.0.js',encoding='utf-8').read()
s=c[c.index('['):c.rindex(']')+1]
try: cu=json.loads(s)
except Exception: cu=json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:',r'\1"\2":',s))

sc=io.open('script-4.0.js',encoding='utf-8').read()
CUE={};TITLE={};KIND={}
secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',sc)]
for i,(k,pos) in enumerate(secs):
    end=secs[i+1][1] if i+1<len(secs) else len(sc)
    for m in re.finditer(r'\{id:"([\d.]+)"',sc[pos:end]): KIND[m.group(1)]=k
for m in re.finditer(r'\{id:"(4\.0[\d.]*)"',sc):
    n=sc.find('{id:"',m.end()); ch=sc[m.start(): n if n>0 else len(sc)]
    cx=re.search(r'cue:\s*"((?:[^"\\]|\\.)*)"',ch); tx=re.search(r'title:\s*"((?:[^"\\]|\\.)*)"',ch)
    CUE[m.group(1)]=cx.group(1) if cx else ""; TITLE[m.group(1)]=tx.group(1) if tx else ""

# --- direction language, exactly as the shipped checker reads it ---
def claim(cue):
    lc=(cue or "").lower()
    if 'look back' in lc or 'behind' in lc or re.search(r'over (your|the) \w+ shoulder', lc): return 'back'
    if 'ahead' in lc or "12 o" in lc: return 'ahead'
    if 'left' in lc: return 'left'
    if 'right' in lc: return 'right'
    return None
def side_of(d):
    if d>=330 or d<=30: return 'ahead'
    if 30<d<150: return 'right'
    if 150<=d<=210: return 'back'
    return 'left'
def clock_of(d):
    h=round(d/30)%12
    return 12 if h==0 else h
def agrees(said,rel):
    gs,gc=side_of(rel),clock_of(rel)
    return (said==gs or (said=='ahead' and gc in (11,12,1)) or (said=='back' and gc in (5,6,7))
            or (said=='left' and gc in (7,8,9,10,11)) or (said=='right' and gc in (1,2,3,4,5)))
def rel_at(i,T):
    return (brg(g[i][0],g[i][1],T[0],T[1])-heading(i))%360
def dist_at(i,T):
    return hav(g[i][0],g[i][1],T[0],T[1])
def nearest_from(lat,lon,lo,hi):
    best=(1e18,lo)
    for i in range(lo,hi):
        d=hav(lat,lon,g[i][0],g[i][1])
        if d<best[0]: best=(d,i)
    return best[1],best[0]

IDX={}; prev=0
for x in cu:
    i,_=nearest_from(x['pin']['lat'],x['pin']['lon'],prev,N)
    IDX[x['id']]=i; prev=i
ANCHOR={k for k in IDX if KIND.get(k)=='stop'}
ids=[x['id'] for x in cu]
BY={x['id']:x for x in cu}

prop={}; reason={}; unfixable=[]
# ---- pass A: anchors and targeted blocks only. Blocks with no target take no
# part in the ordering chain here, or a story block left on a stale index would
# pin a real landmark behind itself (this is what held Hveragerði 5 km late).
solved_order=[b for b in ids if b in ANCHOR or BY[b].get('target')]
prev=0
for n,bid in enumerate(solved_order):
    x=BY[bid]; T=x.get('target')
    nxt=N-1
    for k in range(n+1,len(solved_order)):
        if solved_order[k] in ANCHOR: nxt=IDX[solved_order[k]]; break
    if bid in ANCHOR:
        prop[bid]=max(IDX[bid],prev); prev=prop[bid]; continue
    Tc=(T['lat'],T['lon'])
    cl=None if KIND.get(bid)=='stop' else claim(CUE.get(bid,''))
    lo,hi=max(prev,1),max(prev+2,nxt)
    cand=[(i,rel_at(i,Tc),dist_at(i,Tc)) for i in range(lo,hi)]
    dmin=min(z[2] for z in cand)
    cur=max(IDX[bid],prev); curd=dist_at(cur,Tc)
    curok=(cl is None) or agrees(cl,rel_at(cur,Tc))
    ok=[z for z in cand if cl is None or agrees(cl,z[1])]
    if not ok:
        # nothing on this stretch can satisfy the words. Leave the pin alone and
        # report it rather than shuffling it somewhere equally wrong.
        unfixable.append(bid); prop[bid]=cur; prev=cur; continue
    if dmin>15000:
        if curok: prop[bid]=cur; prev=cur; continue
        pick=min(ok,key=lambda z:abs(z[0]-cur)); reason[bid]='direction'
    else:
        pick=min(ok,key=lambda z:z[2])
        if curok and not (curd>2000 and curd-pick[2]>1400):
            prop[bid]=cur; prev=cur; continue
        reason[bid]='direction' if not curok else 'distance'
    prop[bid]=pick[0]; prev=pick[0]

# ---- pass B: slot the untargeted blocks into the gaps their neighbours leave
for n,bid in enumerate(ids):
    if bid in prop: continue
    a=0
    for k in range(n-1,-1,-1):
        if ids[k] in prop: a=prop[ids[k]]; break
    b=N-1
    for k in range(n+1,len(ids)):
        if ids[k] in prop: b=prop[ids[k]]; break
    run=[j for j in range(len(ids)) if ids[j] not in prop and (a==0 or True)]
    run=[j for j in run if (max([k for k in range(j+1) if ids[k] in prop], default=-1)
                            == max([k for k in range(n+1) if ids[k] in prop], default=-1))]
    k=run.index(n)+1; m=len(run)+1
    cur=IDX[bid]
    prop[bid]= cur if a<=cur<=b else a+int((b-a)*k/m)
    if prop[bid]!=cur: reason[bid]='order'
prev=-1
for bid in ids:
    if prop[bid]<prev: prop[bid]=prev; reason.setdefault(bid,'order')
    prev=prop[bid]

print("%-9s %-29s %6s %7s %5s -> %6s %7s %5s  %-9s %s"%("id","title","now%","nowkm","clk","new%","newkm","clk","why","cue"))
moved=[]; bad=[]
for bid in ids:
    x=BY[bid]; T=x.get('target'); i=prop[bid]; op=x['progress']; np_=cum[i]/total*100
    mv = abs(np_-op)>0.30
    if T:
        Tc=(T['lat'],T['lon'])
        orel=rel_at(IDX[bid],Tc); nrel=rel_at(i,Tc)
        od=dist_at(IDX[bid],Tc)/1000; nd=dist_at(i,Tc)/1000
        cl=None if KIND.get(bid)=='stop' else claim(CUE[bid])
        ok = cl is None or agrees(cl,nrel)
        tag='' if ok else '   ** CUE TEXT DISAGREES'
        print("%-9s %-29s %6.2f %7.2f %5d -> %6.2f %7.2f %5d  %-9s %s%s"%(
            bid,TITLE[bid][:29],op,od,clock_of(orel),np_,nd,clock_of(nrel),reason.get(bid,''),CUE[bid][:38],tag))
        if not ok: bad.append((bid,TITLE[bid],CUE[bid],clock_of(nrel),round(nd,2)))
    else:
        print("%-9s %-29s %6.2f %7s %5s -> %6.2f %7s %5s  %-9s %s"%(
            bid,TITLE[bid][:29],op,'-','-',np_,'-','-',reason.get(bid,''),CUE[bid][:38]))
    if mv: moved.append(bid)
print("\nmoved: %d  %s"%(len(moved),moved))
print("unfixable by moving the pin: %s"%unfixable)
print("cue-text disagreements remaining: %d"%len(bad))
for b in bad: print("   ",b)

if APPLY:
    stamp=datetime.date.today().isoformat()
    shutil.copy2('cues-4.0.js','cues-4.0.js.bak-%s-pinfix'%stamp)
    txt=io.open('cues-4.0.js',encoding='utf-8').read()
    for bid in ids:
        i=prop[bid]; lat=round(g[i][0],5); lon=round(g[i][1],5); pr=round(cum[i]/total*100,2)
        pat=re.compile(r'(\{\s*"?id"?\s*:\s*"%s"\s*,\s*"?progress"?\s*:\s*)([\d.]+)(\s*,\s*"?pin"?\s*:\s*\{\s*"?lat"?\s*:\s*)(-?[\d.]+)(\s*,\s*"?lon"?\s*:\s*)(-?[\d.]+)'%re.escape(bid))
        new,cnt=pat.subn(lambda m: m.group(1)+str(pr)+m.group(3)+str(lat)+m.group(5)+str(lon), txt)
        if cnt!=1: print("!! could not rewrite",bid,"matches",cnt); sys.exit(1)
        txt=new
    io.open('cues-4.0.js','w',encoding='utf-8').write(txt)
    print("\nwrote cues-4.0.js (backup cues-4.0.js.bak-%s-pinfix)"%stamp)
