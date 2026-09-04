#!/usr/bin/env python3
"""Every block of every tour: photo, pin, sightline. One row each, with evidence.

Three questions per block, answered from data rather than memory:
  PHOTO     does this block get a picture, and is it a picture of THIS block?
  PIN       is it on the road, in order, and near what the block talks about?
  SIGHTLINE is there one, does it point where the cue says, is it a credible
            distance to see?
"""
import json, re, io, math, unicodedata, sys

TOURS = ["1.0","2.0","3.0","4.0","5.0","6.0","7.0","9.0","10.0"]

def cues(t):
    x=t[t.index('['):t.rindex(']')+1]
    try: return json.loads(x)
    except Exception: return json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:',r'\1"\2":',x))
def route(t):
    o=json.loads(t[t.index('{'):t.rindex('}')+1]); return o["geometry"] if isinstance(o,dict) else o
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
def claim(cue):
    c=(cue or "").lower()
    if 'look back' in c or 'behind' in c or re.search(r'over (your|the) \w+ shoulder', c): return 'back'
    if 'ahead' in c or '12 o' in c: return 'ahead'
    if 'left' in c: return 'left'
    if 'right' in c: return 'right'
    return None
def side_of(d):
    if d>=330 or d<=30: return 'ahead'
    if 30<d<150: return 'right'
    if 150<=d<=210: return 'back'
    return 'left'
def clock_of(d):
    h=round(d/30)%12
    return 12 if h==0 else h
def agrees(said, rel):
    gs,gc=side_of(rel),clock_of(rel)
    return (said==gs or (said=='ahead' and gc in (11,12,1)) or (said=='back' and gc in (5,6,7))
            or (said=='left' and gc in (7,8,9,10,11)) or (said=='right' and gc in (1,2,3,4,5)))

# photo table, read straight out of the shipped app so this audits what ships
app=io.open('index.html',encoding='utf-8').read()
tbl=app[app.index('const STOPPHOTOS={'):]; tbl=tbl[:tbl.index('};')]
PHOTOS=dict(re.findall(r'"([^"]+)":\s*\{src:"images/stops/([^"]+)\.webp"',tbl))
def photokey(t):
    t=unicodedata.normalize('NFD',t or '')
    t=''.join(c for c in t if unicodedata.category(c)!='Mn')
    t=t.replace('þ','th').replace('ð','d').replace('æ','ae').lower()
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9 -]',' ',t)).strip()

problems=[]
for tid in TOURS:
    src=io.open(f'script-{tid}.js',encoding='utf-8').read()
    C={c['id']:c for c in cues(io.open(f'cues-{tid}.js',encoding='utf-8').read())}
    R=route(io.open(f'route-{tid}.js',encoding='utf-8').read()); n=len(R)
    ss=[(m.group(1),m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',src)]
    print(f"\n{'='*96}\n{tid}\n{'='*96}")
    prev=-1
    for si,(stitle,kind,pos) in enumerate(ss):
        end=ss[si+1][2] if si+1<len(ss) else len(src)
        body=src[pos:end]
        print(f"\n── {stitle}   [{kind}]")
        for m in re.finditer(r'\{id:"([\d.]+)"',body):
            nx=body.find('{id:"',m.end()); ch=body[m.start(): nx if nx>0 else len(body)]
            bid=m.group(1)
            title=(re.search(r'title:\s*"((?:[^"\\]|\\.)*)"',ch) or [None,''])[1]
            cue=(re.search(r'cue:\s*"((?:[^"\\]|\\.)*)"',ch) or [None,''])[1]
            c=C.get(bid)
            flags=[]
            # PHOTO
            ph = PHOTOS.get(photokey(title)) if kind=='stop' else None
            photo = ph or ('—' if kind=='stop' else '')
            # PIN
            pinbit=''
            if not c:
                flags.append('NO CUE ENTRY')
            else:
                off=min(hav(c['pin']['lat'],c['pin']['lon'],p[0],p[1]) for p in R)
                if off>400: flags.append(f'PIN {off:.0f}m OFF-ROAD')
                if c['progress']<prev: flags.append('PROGRESS GOES BACKWARDS')
                prev=max(prev,c['progress'])
                pinbit=f"{c['progress']:5.1f}%"
            # SIGHTLINE
            sl=''
            if c and c.get('target'):
                t=c['target']
                d=hav(c['pin']['lat'],c['pin']['lon'],t['lat'],t['lon'])/1000
                pi=min(range(n),key=lambda z:hav(c['pin']['lat'],c['pin']['lon'],R[z][0],R[z][1]))
                j=min(pi+3,n-1); i0=max(pi-1,0)
                trav=brg(R[i0][0],R[i0][1],R[j][0],R[j][1])
                rel=(brg(c['pin']['lat'],c['pin']['lon'],t['lat'],t['lon'])-trav)%360
                h=clock_of(rel)
                sl=f"→{t['name'][:18]} {d:.1f}km @{h}"
                said=claim(cue)
                if said and kind!='stop' and not agrees(said,rel):
                    flags.append(f"CUE SAYS {said.upper()} BUT GEOMETRY IS {h} O'CLOCK")
                if d>70: flags.append(f'SIGHTLINE {d:.0f} km — not visible')
            print(f"   {bid:9s} {title[:32]:34s} {pinbit:7s} {photo:22s} {sl}")
            if cue: print(f"             \"{cue[:82]}\"")
            for f in flags:
                print(f"             ⚠ {f}")
                problems.append(f"{tid} {bid} {title[:26]} — {f}")

print(f"\n\n{'='*96}\nPROBLEMS: {len(problems)}\n{'='*96}")
for p in problems: print("  "+p)
