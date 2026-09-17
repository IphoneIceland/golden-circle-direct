#!/usr/bin/env python3
"""Where the Norse Expansion globe and the tour app already describe the same ground.

The raids map carries 337 places with lat/lon. The tour app carries stop pins.
This finds the places that are literally the same spot, which is the join the
combined map would be built on -- no new data, no guessing.
"""
import io,re,json,math

raids=json.load(open('/tmp/raids.json'))

def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

stops=[]
for t in ['1.0','2.0','3.0','4.0','5.0','6.0','7.0','9.0','10.0','14.0']:
    sc=io.open('script-%s.js'%t,encoding='utf-8').read()
    kind={}
    secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',sc)]
    for i,(k,pos) in enumerate(secs):
        end=secs[i+1][1] if i+1<len(secs) else len(sc)
        for m in re.finditer(r'\{id:"([\d.]+)"',sc[pos:end]): kind[m.group(1)]=k
    titles={}
    for m in re.finditer(r'\{id:"([\d.]+)"[^}]*?title:"((?:[^"\\]|\\.)*)"',sc):
        titles[m.group(1)]=m.group(2)
    raw=io.open('cues-%s.js'%t,encoding='utf-8').read()
    cu=json.loads(raw[raw.index('['):raw.rindex(']')+1])
    for c in cu:
        if kind.get(c['id'])=='stop':
            stops.append((t,c['id'],titles.get(c['id'],''),c['pin']['lat'],c['pin']['lon']))

print("tour stops with pins: %d"%len(stops))
best={}
for r in raids:
    for t,bid,title,la,lo in stops:
        d=hav(r['lat'],r['lon'],la,lo)
        if d<12 and (r['name'] not in best or d<best[r['name']][0]):
            best[r['name']]=(d,r.get('year'),r['cat'],t,title)

print("\nRAIDS-MAP PLACES THAT LAND ON A TOUR STOP (within 12 km)")
for n,(d,y,c,t,title) in sorted(best.items(), key=lambda kv: kv[1][0]):
    print("  %-34s %-6s %-11s %5.1f km  ->  %-5s %s"%(n[:34],y,c,d,t,title[:32]))
print("\n%d of the 337 raids places sit on ground a tour already stops at."%len(best))

ice=[r for r in raids if 63<=r['lat']<=67 and -25<=r['lon']<=-13]
print("%d of the 337 are in Iceland at all."%len(ice))
json.dump(sorted(best.keys()),open('/tmp/overlap.json','w'),ensure_ascii=False)
