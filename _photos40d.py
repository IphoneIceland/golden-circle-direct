#!/usr/bin/env python3
"""Pass D — the five subjects with no Wikidata image, searched on Commons.

Commons keyword search is blunt (the reason the repo prefers P18), so nothing
here ships unlooked-at: this prints candidates and downloads them for review,
it does not wire anything into the app.
"""
import json, os, re, subprocess, time, urllib.parse
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); CAND=os.path.join(HERE,"_pc40d")
os.makedirs(CAND,exist_ok=True)
UA="User-Agent: iguide-iceland/1.0 (bus guide app; iguideiceland.is)"
OK=("cc0","cc by","cc by-sa","public domain","pd-","attribution")
Q={"gljufrasteinn":'Gljúfrasteinn',
   "laugarvatnshellir":'Laugarvatnshellir',
   "kristnitokuhraun":'Svínahraun lava',
   "olgerdin":'Ölgerðin Egill Skallagrímsson',
   "laxnes":'Laxnes Mosfellsdalur'}
def j(url):
    for _ in range(5):
        r=subprocess.run(["curl","-sS","--max-time","60","-H",UA,url],capture_output=True,text=True)
        if r.returncode==0 and r.stdout.strip().startswith("{"): return json.loads(r.stdout)
        time.sleep(12)
    return {}
def strip(h): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>","",h or "")).strip()
out={}
for slug,q in Q.items():
    d=j("https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srlimit=6&srsearch="
        +urllib.parse.quote(q)+"&format=json&formatversion=2")
    hits=[h["title"] for h in (d.get("query") or {}).get("search",[])]
    print(slug, "->", hits)
    out[slug]=[]
    for n,title in enumerate(hits[:4]):
        time.sleep(6)
        dd=j("https://commons.wikimedia.org/w/api.php?action=query&titles="+urllib.parse.quote(title)
             +"&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=900&format=json&formatversion=2")
        p=((dd.get("query") or {}).get("pages") or [{}])[0]
        ii=(p.get("imageinfo") or [{}])[0]; em=ii.get("extmetadata",{})
        lic=strip(em.get("LicenseShortName",{}).get("value",""))
        if not any(k in lic.lower() for k in OK): print("    skip",title,lic); continue
        auth=re.sub(r"\s*\(talk\).*$","",strip(em.get("Artist",{}).get("value","")) or "Unknown")[:60]
        f=os.path.join(CAND,f"{slug}-{n}.jpg")
        subprocess.run(["curl","-sS","--max-time","90","-H",UA,"-o",f,ii.get("thumburl") or ii.get("url")],capture_output=True)
        try:
            im=Image.open(f).convert("RGB"); im.thumbnail((560,560)); im.save(f,"JPEG",quality=78)
            print("    %s | %s | %s"%(os.path.basename(f),lic,auth[:34]))
            out[slug].append({"n":n,"title":title,"lic":lic,"author":auth,"url":ii.get("url")})
        except Exception as e: print("    convert fail",e)
    time.sleep(6)
json.dump(out,open(os.path.join(CAND,"cands.json"),"w"),ensure_ascii=False,indent=1)
print("done")
