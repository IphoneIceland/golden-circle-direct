#!/usr/bin/env python3
"""Stop pins: the blind spot in every other tool.

_clockcheck.py skips walking stops on purpose (at a stop "left" means left of the
person, not the bus). _rulercheck.py skips them too. So nothing has ever asked
the simplest question: does a stop's pin actually sit at that stop? 7.0's last
stop pin sits at BSI in Reykjavik with its target Seljalandsfoss 111 km away,
which draws a 111 km dashed line across the whole south coast.

Also dumps a named block's cue text, for settling arguments about wording:
    _stopcheck.py --cue 7.0 7.0.1.9
"""
import json,re,io,math,sys,glob,os

def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def parse(tid):
    ct=io.open('cues-%s.js'%tid,encoding='utf-8').read()
    s=ct[ct.index('['):ct.rindex(']')+1]
    try: cu=json.loads(s)
    except Exception: cu=json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:',r'\1"\2":',s))
    sc=io.open('script-%s.js'%tid,encoding='utf-8').read()
    kind={};title={};cue={}
    secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',sc)]
    for i,(k,pos) in enumerate(secs):
        end=secs[i+1][1] if i+1<len(secs) else len(sc)
        for m in re.finditer(r'\{id:"([\d.]+)"',sc[pos:end]): kind[m.group(1)]=k
    for m in re.finditer(r'\{id:"([\d.]+)"',sc):
        n=sc.find('{id:"',m.end()); ch=sc[m.start(): n if n>0 else len(sc)]
        t=re.search(r'title:\s*"((?:[^"\\]|\\.)*)"',ch); c=re.search(r'cue:\s*"((?:[^"\\]|\\.)*)"',ch)
        title[m.group(1)]=t.group(1) if t else ''
        cue[m.group(1)]=c.group(1) if c else ''
    return cu,kind,title,cue

if '--cue' in sys.argv:
    tid=sys.argv[sys.argv.index('--cue')+1]
    cu,kind,title,cue=parse(tid)
    for bid in sys.argv[sys.argv.index('--cue')+2:]:
        print("%s | %s | kind=%s\n   CUE: %s"%(bid,title.get(bid,''),kind.get(bid,''),cue.get(bid,'')))
    sys.exit()

TOURS=sorted({os.path.basename(f)[5:-3] for f in glob.glob('cues-*.js') if '.bak' not in f},
             key=lambda s: float(s))
print("=== STOP PINS FAR FROM THEIR OWN TARGET ===")
found=False
for tid in TOURS:
    try: cu,kind,title,cue=parse(tid)
    except Exception: continue
    for x in cu:
        if kind.get(x['id'])!='stop': continue
        T=x.get('target')
        if not T: continue
        d=hav(x['pin']['lat'],x['pin']['lon'],T['lat'],T['lon'])/1000
        if d>8:
            found=True
            print("  %-5s %-10s %-28s -> %-22s %8.1f km   (pin at %.2f%%)"
                  %(tid,x['id'],title.get(x['id'],'')[:28],T['name'][:22],d,x['progress']))
if not found: print("  none")
