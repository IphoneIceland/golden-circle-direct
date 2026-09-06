#!/usr/bin/env python3
"""Pin solver, any tour:  _fixpins.py <tour-id> [--apply]

The app draws the sightline as a straight dashed line from a block's pin to its
target, so the pin decides both when a block fires and which way the arrow
points. A pin dumped past its subject draws the arrow backwards off the screen.

Every rule below was learned by getting it wrong first:

  1. Stop pins never move. They are the anchors.
  2. Resolve a block to a route index by its PROGRESS, never by searching for the
     nearest route point. On an out-and-back tour a nearest-point search matches
     whichever pass is closer, often the HOMEWARD leg -- that dragged every 7.0
     pin to 92% and produced targets 197 km away.
  3. Use the SAME heading model the shipped checkers verify with (a four-point
     window straddling the pin). Solving against a different model "fixed" 4.0
     and introduced two fresh disagreements.
  4. Proximity dominates; the clock only breaks ties. A solver that minimised
     clock error first dragged Kjarvalsstadir 35 km down the road to find a 9.
  5. A block moves only if it is BROKEN: the cue direction disagrees with the
     geometry, or the target is over 2 km away and the move gains 1.4 km+.
  6. A cue with no direction ("At X", "Crossing X") goes to closest approach.
  7. A distant landmark (never nearer than 15 km) is judged on direction only.
  8. DO NO HARM: a move that pushes a later block off a good pin is reverted.
     Fixing Snaefellsjokull on 10.0 shoved Londrangar from a perfect 0.65 km /
     9 o'clock out to 5.5 km. A repair that breaks its neighbour is not a repair.
  9. Blocks never go backwards.
"""
import json,re,io,math,sys,shutil,datetime

APPLY = '--apply' in sys.argv
TID = [a for a in sys.argv[1:] if not a.startswith('--')][0]

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

_t=io.open('route-%s.js'%TID,encoding='utf-8').read()
rt=json.loads(_t[_t.index('{'):_t.rindex('}')+1])
g=rt["geometry"] if isinstance(rt,dict) else rt
N=len(g)
cum=[0.0]
for i in range(1,N): cum.append(cum[-1]+hav(g[i-1][0],g[i-1][1],g[i][0],g[i][1]))
total=cum[-1]

def heading(i):
    j=min(i+3,N-1); i0=max(i-1,0)
    if j==i0: j=min(i0+1,N-1)
    return brg(g[i0][0],g[i0][1],g[j][0],g[j][1])

c=io.open('cues-%s.js'%TID,encoding='utf-8').read()
s=c[c.index('['):c.rindex(']')+1]
try: cu=json.loads(s)
except Exception: cu=json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:',r'\1"\2":',s))

sc=io.open('script-%s.js'%TID,encoding='utf-8').read()
CUE={};TITLE={};KIND={}
secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',sc)]
for i,(k,pos) in enumerate(secs):
    end=secs[i+1][1] if i+1<len(secs) else len(sc)
    for m in re.finditer(r'\{id:"([\d.]+)"',sc[pos:end]): KIND[m.group(1)]=k
for m in re.finditer(r'\{id:"([\d.]+)"',sc):
    n=sc.find('{id:"',m.end()); ch=sc[m.start(): n if n>0 else len(sc)]
    cx=re.search(r'cue:\s*"((?:[^"\\]|\\.)*)"',ch); tx=re.search(r'title:\s*"((?:[^"\\]|\\.)*)"',ch)
    CUE[m.group(1)]=cx.group(1) if cx else ""; TITLE[m.group(1)]=tx.group(1) if tx else ""

def claim(cue):
    """Every acceptable side the words allow, not just the first one found.

    "Look back and left" is BOTH, and 8 o'clock satisfies it. And a positional
    cue ("we're driving under it now", "crossing the Sog") says where you ARE,
    not which way to look -- any left/right in it usually belongs to something
    else in the sentence, as in 10.0's "the headland the road is cut into, sea
    on your left", where "left" is the SEA. Position wins unless a clock is named.
    """
    c=(cue or "").lower()
    hasclock = re.search(r"\d{1,2}\s*(?:[\u2013-]\s*\d{1,2}\s*)?o.?clock", c)
    if not hasclock and re.search(r"\b(driving (under|through)|crossing|pulling into|passing)\b", c):
        return None
    sides=[]
    if 'look back' in c or 'behind' in c or re.search(r'over (your|the) \w+ shoulder', c): sides.append('back')
    if 'ahead' in c or '12 o' in c: sides.append('ahead')
    if 'left' in c: sides.append('left')
    if 'right' in c: sides.append('right')
    return sides or None
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
    return any(s==gs or (s=='ahead' and gc in (11,12,1)) or (s=='back' and gc in (5,6,7))
               or (s=='left' and gc in (7,8,9,10,11)) or (s=='right' and gc in (1,2,3,4,5))
               for s in said)
def rel_at(i,T): return (brg(g[i][0],g[i][1],T[0],T[1])-heading(i))%360
def dist_at(i,T): return hav(g[i][0],g[i][1],T[0],T[1])

def idx_of_progress(pct):
    want=total*max(0.0,min(100.0,pct))/100.0
    for i,cc in enumerate(cum):
        if cc>=want: return i
    return N-1

IDX={x['id']: idx_of_progress(x['progress']) for x in cu}
ANCHOR={x['id'] for x in cu if KIND.get(x['id'])=='stop'}
ids=[x['id'] for x in cu]
BY={x['id']:x for x in cu}

def solve(locked):
    prop={}; reason={}; unfix=[]
    solved_order=[b for b in ids if b in ANCHOR or BY[b].get('target')]
    prev=0
    for n,bid in enumerate(solved_order):
        x=BY[bid]; T=x.get('target')
        nxt=N-1
        for k in range(n+1,len(solved_order)):
            if solved_order[k] in ANCHOR: nxt=IDX[solved_order[k]]; break
        if bid in ANCHOR or bid in locked:
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
            # No point on this stretch can satisfy the words. That is a cue-TEXT
            # error, not a pin error -- Gljufrasteinn is on the RIGHT on 1.0/2.0/3.0
            # (you drive east past it) and only on the left on 4.0 (you drive west).
            # Name it and leave the pin alone; never shuffle a pin to hide wording.
            unfix.append(bid); prop[bid]=cur; prev=cur; continue
        if dmin>15000:
            if curok: prop[bid]=cur; prev=cur; continue
            pick=min(ok,key=lambda z:abs(z[0]-cur)); reason[bid]='direction'
        else:
            pick=min(ok,key=lambda z:z[2])
            if curok and not (curd>2000 and curd-pick[2]>1400):
                prop[bid]=cur; prev=cur; continue
            reason[bid]='direction' if not curok else 'distance'
        prop[bid]=pick[0]; prev=pick[0]
    for n,bid in enumerate(ids):
        if bid in prop: continue
        a=0
        for k in range(n-1,-1,-1):
            if ids[k] in prop: a=prop[ids[k]]; break
        b=N-1
        for k in range(n+1,len(ids)):
            if ids[k] in prop: b=prop[ids[k]]; break
        cur=IDX[bid]
        prop[bid]= cur if a<=cur<=b else (a+b)//2
        if prop[bid]!=cur: reason[bid]='order'
    prev=-1
    for bid in ids:
        if prop[bid]<prev: prop[bid]=prev; reason.setdefault(bid,'order')
        prev=prop[bid]
    return prop,reason,unfix

def harmed(prop):
    """Blocks the solution leaves WORSE than it found them."""
    out=[]
    for bid in ids:
        T=BY[bid].get('target')
        if not T or bid in ANCHOR: continue
        Tc=(T['lat'],T['lon']); cl=claim(CUE.get(bid,''))
        db,da=dist_at(IDX[bid],Tc),dist_at(prop[bid],Tc)
        ob=cl is None or agrees(cl,rel_at(IDX[bid],Tc))
        oa=cl is None or agrees(cl,rel_at(prop[bid],Tc))
        if (ob and not oa) or (da-db>1000 and db<2500): out.append(bid)
    return out

locked=set()
for _round in range(8):
    prop,reason,unfix=solve(locked)
    bad=harmed(prop)
    if not bad: break
    progress=False
    for b in bad:
        n=ids.index(b)
        for k in range(n-1,-1,-1):          # lock the upstream move that caused it
            u=ids[k]
            if u not in ANCHOR and u not in locked and prop[u]!=IDX[u]:
                locked.add(u); progress=True; break
    if not progress:
        for b in bad: locked.add(b)         # last resort: leave the victim alone

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
print("held back to avoid harming a neighbour: %s"%sorted(locked))
print("unfixable by moving the pin: %s"%unfix)
print("harm introduced: %s"%harmed(prop))
print("cue-text disagreements remaining: %d"%len(bad))
for b in bad: print("   ",b)

if APPLY:
    stamp=datetime.date.today().isoformat()
    shutil.copy2('cues-%s.js'%TID,'cues-%s.js.bak-%s-pinfix'%(TID,stamp))
    txt=io.open('cues-%s.js'%TID,encoding='utf-8').read()
    for bid in ids:
        i=prop[bid]; lat=round(g[i][0],5); lon=round(g[i][1],5); pr=round(cum[i]/total*100,2)
        pat=re.compile(r'(\{\s*"?id"?\s*:\s*"%s"\s*,\s*"?progress"?\s*:\s*)([\d.]+)(\s*,\s*"?pin"?\s*:\s*\{\s*"?lat"?\s*:\s*)(-?[\d.]+)(\s*,\s*"?lon"?\s*:\s*)(-?[\d.]+)'%re.escape(bid))
        new,cnt=pat.subn(lambda m: m.group(1)+str(pr)+m.group(3)+str(lat)+m.group(5)+str(lon), txt)
        if cnt!=1: print("!! could not rewrite",bid,"matches",cnt); sys.exit(1)
        txt=new
    io.open('cues-%s.js'%TID,'w',encoding='utf-8').write(txt)
    print("\nwrote cues-%s.js (backup cues-%s.js.bak-%s-pinfix)"%(TID,TID,stamp))
