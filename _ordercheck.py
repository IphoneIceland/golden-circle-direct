#!/usr/bin/env python3
"""Blocks whose landmark is passed BEFORE the block before them.

The pin solver can only place a block between its neighbours -- a block that
fires out of sequence is worse than one that fires late. So when a block's
subject sits earlier on the road than the previous block's subject, no pin can
fix it: the two blocks are in the wrong order in the SCRIPT.

That is a scripts-chat call, not a map one, so this prints the swap needed and
what it would buy instead of quietly shuffling narrative order.
"""
import json,re,io,math,glob,os

def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

TOURS=sorted({os.path.basename(f)[5:-3] for f in glob.glob('cues-*.js') if '.bak' not in f},
             key=lambda s: float(s))
rows=[]
for tid in TOURS:
    try:
        ct=io.open('cues-%s.js'%tid,encoding='utf-8').read()
        s=ct[ct.index('['):ct.rindex(']')+1]
        try: cu=json.loads(s)
        except Exception: cu=json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:',r'\1"\2":',s))
        rt=io.open('route-%s.js'%tid,encoding='utf-8').read()
        o=json.loads(rt[rt.index('{'):rt.rindex('}')+1])
        g=o["geometry"] if isinstance(o,dict) else o
        sc=io.open('script-%s.js'%tid,encoding='utf-8').read()
    except Exception: continue
    N=len(g); cum=[0.0]
    for i in range(1,N): cum.append(cum[-1]+hav(g[i-1][0],g[i-1][1],g[i][0],g[i][1]))
    total=cum[-1]
    kind={};title={}
    secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',sc)]
    for i,(k,pos) in enumerate(secs):
        end=secs[i+1][1] if i+1<len(secs) else len(sc)
        for m in re.finditer(r'\{id:"([\d.]+)"',sc[pos:end]): kind[m.group(1)]=k
    for m in re.finditer(r'\{id:"([\d.]+)"',sc):
        n=sc.find('{id:"',m.end()); ch=sc[m.start(): n if n>0 else len(sc)]
        t=re.search(r'title:\s*"((?:[^"\\]|\\.)*)"',ch)
        title[m.group(1)]=t.group(1) if t else ''
    ideal={}
    for x in cu:
        T=x.get('target')
        if not T or kind.get(x['id'])=='stop': continue
        i=min(range(N), key=lambda k: hav(T['lat'],T['lon'],g[k][0],g[k][1]))
        ideal[x['id']]=(cum[i]/total*100, hav(T['lat'],T['lon'],g[i][0],g[i][1])/1000,
                        hav(x['pin']['lat'],x['pin']['lon'],T['lat'],T['lon'])/1000, T['name'])
    ids=[x['id'] for x in cu]
    for n,bid in enumerate(ids):
        if bid not in ideal: continue
        ip,dmin,dnow,tname=ideal[bid]
        if dnow-dmin < 1.5: continue          # already close enough
        prev=None
        for k in range(n-1,-1,-1):
            if ids[k] in ideal or kind.get(ids[k])=='stop': prev=ids[k]; break
        pp=BY=None
        if prev:
            pp = ideal[prev][0] if prev in ideal else next(x['progress'] for x in cu if x['id']==prev)
        if pp is not None and ip < pp - 0.2:
            rows.append((tid,bid,title.get(bid,'')[:26],tname[:20],dnow,dmin,ip,prev,
                         title.get(prev,'')[:22],pp))

print("=== BLOCKS THE ROAD REACHES BEFORE THE BLOCK IN FRONT OF THEM ===")
print("    (no pin can fix these -- the two blocks are the wrong way round in the script)\n")
if not rows: print("  none")
for tid,bid,ti,tn,dnow,dmin,ip,prev,pti,pp in rows:
    print("  %-5s %-10s %-26s -> %-20s  now %5.1f km, could be %4.1f km" % (tid,bid,ti,tn,dnow,dmin))
    print("        road reaches it at %5.2f%%, but %s (%s) already fired at %5.2f%%  -> SWAP THEM"
          % (ip,prev,pti,pp))
