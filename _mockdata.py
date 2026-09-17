#!/usr/bin/env python3
"""Pull the two datasets the combined-map mockup needs, from the real sources.

  /tmp/raids_slim.json  337 Norse-world places lifted out of Norse-Expansion-16K-v39.html
  /tmp/tours_slim.json  the ten tour routes and their stop pins, from route-*.js / cues-*.js

Nothing here is invented: every coordinate comes off disk.
"""
import io,json,re

r=json.load(open('/tmp/raids.json'))
slim=[{"n":x["name"],"la":round(x["lat"],3),"lo":round(x["lon"],3),
       "y":x.get("year"),"c":x["cat"],
       "b":(x.get("blurb") or "")[:240],
       "t":(x.get("teach") or "")[:260]} for x in r]
io.open('/tmp/raids_slim.json','w',encoding='utf-8').write(json.dumps(slim,ensure_ascii=False))
print("raids_slim.json  %d places  %.0f KB"%(len(slim),len(json.dumps(slim,ensure_ascii=False))/1024))

NAMES={'1.0':'Golden Circle Direct','2.0':'Golden Circle Snowmobiling','3.0':'Golden Circle Lagoons',
       '4.0':'Golden Circle Friðheimar','5.0':'South Coast','6.0':'South Coast Combo',
       '7.0':'Glacial Lagoon','9.0':'Snæfellsnes North','10.0':'Snæfellsnes South',
       '14.0':'Reykjanes South Loop'}
out={}
for t,name in NAMES.items():
    raw=io.open('route-%s.js'%t,encoding='utf-8').read()
    o=json.loads(raw[raw.index('{'):raw.rindex('}')+1])
    g=o["geometry"] if isinstance(o,dict) else o
    g=[[round(a,4),round(b,4)] for a,b in g[::6]]          # thinned for a mockup
    sc=io.open('script-%s.js'%t,encoding='utf-8').read()
    kind={}
    secs=[(m.group(2),m.start()) for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"',sc)]
    for i,(k,pos) in enumerate(secs):
        end=secs[i+1][1] if i+1<len(secs) else len(sc)
        for m in re.finditer(r'\{id:"([\d.]+)"',sc[pos:end]): kind[m.group(1)]=k
    titles={m.group(1):m.group(2) for m in
            re.finditer(r'\{id:"([\d.]+)"[^}]*?title:"((?:[^"\\]|\\.)*)"',sc)}
    craw=io.open('cues-%s.js'%t,encoding='utf-8').read()
    cu=json.loads(craw[craw.index('['):craw.rindex(']')+1])
    stops=[{"n":titles.get(c['id'],''),"la":round(c['pin']['lat'],4),"lo":round(c['pin']['lon'],4)}
           for c in cu if kind.get(c['id'])=='stop']
    out[t]={"name":name,"route":g,"stops":stops}
io.open('/tmp/tours_slim.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False))
print("tours_slim.json  %d tours  %d stops  %.0f KB"%(
    len(out),sum(len(v['stops']) for v in out.values()),
    len(json.dumps(out,ensure_ascii=False))/1024))
