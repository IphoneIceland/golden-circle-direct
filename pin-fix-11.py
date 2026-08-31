#!/usr/bin/env python3
"""Anchor 11.0 drive-cue pins to their landmarks: nearest route-geometry point,
searched ONLY within the cue's own section progress window (loop tour — the
return leg reuses roads). Run AFTER build-route.py 11.0. Landmarks cross-checked
against OSM/Nominatim 31 Aug 2026."""
import json,re,math
ANCHOR={
 (1,1):(64.1374,-21.9346),(1,2):(64.1398,-21.9155),(1,3):(64.1289,-21.8148),
 (1,4):(64.1500,-21.7800),(1,5):(64.2110,-21.7950),(1,6):(64.3097,-21.9039),
 (1,7):(64.3614,-21.8131),(1,8):(64.3900,-21.8400),(1,9):(64.5310,-21.8960),
 (3,1):(64.5850,-22.0800),(3,2):(64.7300,-22.2700),(3,3):(64.8060,-22.3220),
 (3,4):(64.8720,-22.3700),(3,5):(64.8330,-22.6500),
 (5,1):(64.8290,-23.3850),(5,2):(64.8060,-23.4610),(5,3):(64.7950,-23.5500),(5,4):(64.7930,-23.5850),
 (7,1):(64.7550,-23.6450),(7,2):(64.7480,-23.7000),(7,3):(64.7440,-23.7750),(7,4):(64.7460,-23.8050),
 (9,1):(64.8460,-23.9290),(9,2):(64.8900,-23.9100),(9,3):(64.9230,-23.8210),(9,4):(64.9250,-23.8000),
 (11,1):(64.9050,-23.6500),
 (13,1):(64.9550,-22.9850),(13,2):(64.8850,-22.8800),
}
def hav(a,b):
    la1,lo1,la2,lo2=map(math.radians,(a[0],a[1],b[0],b[1]))
    return 2*6371000*math.asin(math.sqrt(math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
geo=json.loads(re.search(r'"geometry":\s*(\[\[.*?\]\])',open("route-11.0.js").read(),re.S).group(1))
cum=[0.0]
for i in range(1,len(geo)): cum.append(cum[-1]+hav(geo[i-1],geo[i]))
total=cum[-1]
raw=open("cues-11.0.js").read()
m=re.search(r'=\s*(\[.*\])\s*;?\s*$',raw,re.S)
cues=json.loads(m.group(1))
stopprog={int(c["id"].split(".")[2]):c["progress"] for c in cues if int(c["id"].split(".")[2])%2==0}
win={1:(0,stopprog[2]),3:(stopprog[2],stopprog[4]),5:(stopprog[4],stopprog[6]),
     7:(stopprog[6],stopprog[8]),9:(stopprog[8],stopprog[10]),11:(stopprog[10],stopprog[12]),
     13:(stopprog[12],100.0)}
for c in cues:
    p=c["id"].split("."); sec,blk=int(p[2]),int(p[3])
    if (sec,blk) in ANCHOR:
        lo,hi=win[sec]; best=(1e18,None)
        for i,g in enumerate(geo):
            pr=cum[i]/total*100
            if pr<lo-0.3 or pr>hi+0.3: continue
            d=hav(ANCHOR[(sec,blk)],g)
            if d<best[0]: best=(d,i)
        d,i=best
        c["pin"]={"lat":round(geo[i][0],6),"lon":round(geo[i][1],6)}
        c["progress"]=round(min(max(cum[i]/total*100,lo+0.05),hi-0.05),2)
        print("%-10s prog %6.2f  snap %5.0fm"%(c["id"],c["progress"],d))
prev=0;bad=[]
for c in cues:
    if c["progress"]<prev-0.01: bad.append(c["id"])
    prev=max(prev,c["progress"])
assert not bad,("monotonic violations",bad)
open("cues-11.0.js","w").write(raw[:m.start(1)]+json.dumps(cues,ensure_ascii=False)+";\n")
print("monotonic: clean")
