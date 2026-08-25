#!/usr/bin/env python3
"""
Builds route-N.js and cues-N.js for a tour from the stop sequence in its script.

  python3 build-route.py 5.0

Stop coordinates come from OpenStreetMap (Nominatim), the road geometry from
OSRM — the same two sources the 1.0 route was built from. Stops are pinned;
blocks on a drive leg are spaced evenly along that leg.
"""
import json, math, re, subprocess, sys, time, urllib.parse, urllib.request

tag = sys.argv[1]
UA = {"User-Agent": "golden-circle-direct/1.0 (tour app)"}

PLACES = {
  "BSI":"BSÍ Bus Terminal, Reykjavík, Iceland", "HVOL":"Hvolsvöllur, Iceland",
  "SOLH":"Sólheimajökull, Iceland", "REYN":"Reynisfjara, Iceland",
  "VIK":"Vík í Mýrdal, Iceland", "SKOG":"Skógafoss, Iceland",
  "SELJ":"Seljalandsfoss, Iceland",
}
NICE = {"BSI":"BSÍ Bus Terminal","HVOL":"Hvolsvöllur","SOLH":"Sólheimajökull",
        "REYN":"Reynisfjara","VIK":"Vík í Mýrdal","SKOG":"Skógafoss","SELJ":"Seljalandsfoss"}
MATCH = [("Hvolsvöllur","HVOL"),("Sólheimajökull","SOLH"),("Reynisfjara","REYN"),
         ("Vík","VIK"),("Skógafoss","SKOG"),("Seljalandsfoss","SELJ"),
         ("Reykjavík","BSI"),("BSÍ","BSI")]

def fetch(url):
    # this Python has no CA bundle wired up; curl does
    out=subprocess.run(["curl","-sSL","-A",UA["User-Agent"],url],capture_output=True,text=True,check=True).stdout
    return json.loads(out)

def geocode(q):
    u="https://nominatim.openstreetmap.org/search?"+urllib.parse.urlencode({"q":q,"format":"json","limit":1})
    d=fetch(u)
    if not d: raise SystemExit("no result for "+q)
    return round(float(d[0]["lat"]),6), round(float(d[0]["lon"]),6)

S=json.loads(subprocess.run(["node","-e",
  'global.window={};eval(require("fs").readFileSync("script-%s.js","utf8"));console.log(JSON.stringify(window.__SCRIPT__));'%tag],
  capture_output=True,text=True,check=True).stdout)

def keyfor(t):
    for w,k in MATCH:
        if w in t: return k
    return None

# stop order, straight out of the document's section headings
seq=["BSI"]
for sec in S["sections"]:
    dest = sec["title"].split("→")[-1] if "→" in sec["title"] else sec["title"]
    k=keyfor(dest)
    if k and k!=seq[-1]: seq.append(k)
if seq[-1]!="BSI": seq.append("BSI")
print("stops:", " → ".join(NICE[k] for k in seq))

PIN={}
for k in dict.fromkeys(seq):
    PIN[k]=geocode(PLACES[k]); print("  %-16s %s"%(NICE[k],PIN[k])); time.sleep(1.1)

co=";".join("%f,%f"%(PIN[k][1],PIN[k][0]) for k in seq)
r=fetch("http://router.project-osrm.org/route/v1/driving/%s?overview=full&geometries=geojson"%co)["routes"][0]
geo=[[round(c[1],5),round(c[0],5)] for c in r["geometry"]["coordinates"]]
legs=[{"km":round(l["distance"]/1000,1),"min":round(l["duration"]/60)} for l in r["legs"]]
tot=sum(l["km"] for l in legs)
prog=[0.0]; a=0.0
for l in legs: a+=l["km"]; prog.append(round(a/tot*100,2))
at={}
for i,k in enumerate(seq): at.setdefault(k,prog[i])

ends=[]; hi=0.0
for sec in S["sections"]:
    dest = sec["title"].split("→")[-1] if "→" in sec["title"] else sec["title"]
    p=at.get(keyfor(dest), prog[-1])
    if p<hi: p=hi
    hi=p; ends.append((p,keyfor(dest)))

cues=[]
for si,sec in enumerate(S["sections"]):
    end,key=ends[si]; start=ends[si-1][0] if si>0 else 0.0
    n=len(sec["blocks"])
    for bi,b in enumerate(sec["blocks"]):
        if sec["kind"]=="stop" and key in PIN:
            lat,lon=PIN[key]
            cues.append({"id":b["id"],"progress":round(end,2),"pin":{"lat":lat,"lon":lon},
                         "target":{"lat":lat,"lon":lon,"name":NICE[key]}})
        else:
            cues.append({"id":b["id"],"progress":round(start+(end-start)*((bi+1)/n),2),
                         "pin":None,"target":None})

open("route-%s.js"%tag,"w",encoding="utf-8").write(
 "// %s route — OSRM driving via %s. Stop coordinates from OpenStreetMap.\nwindow.__ROUTE__ = %s;\n"
 % (tag," → ".join(NICE[k] for k in seq),
    json.dumps({"km":round(r["distance"]/1000,1),"min":round(r["duration"]/60),
                "legs":legs,"geometry":geo},ensure_ascii=False)))
open("cues-%s.js"%tag,"w",encoding="utf-8").write(
 "// %s cue points — stops pinned from OpenStreetMap, drive blocks spaced along their leg.\nwindow.__CUES__ = %s;\n"
 % (tag,json.dumps(cues,ensure_ascii=False)))
back=sum(1 for i in range(1,len(cues)) if cues[i]["progress"]<cues[i-1]["progress"])
print("route %.1f km, %d min, %d points | cues %d, pinned %d, backwards %d, span %.2f%%→%.2f%%"
      % (r["distance"]/1000, r["duration"]/60, len(geo), len(cues),
         sum(1 for c in cues if c["pin"]), back, cues[0]["progress"], cues[-1]["progress"]))
