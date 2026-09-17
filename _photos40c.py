#!/usr/bin/env python3
"""Pass C — the picks, resolved by hand from one Wikidata SPARQL query.

Passes A and B burned themselves on the MediaWiki rate limiter: an empty reply
reads exactly like "this subject has no picture", so Hekla and Esja were both
reported imageless. One SPARQL query returned every P18 at once; the right
entity was then chosen by hand (three different Haukadalurs, two Kjalarnes
entities, and "Skálholt" whose own P18 is a photo of a car park). This pass only
fetches licence + file for those decided picks, six seconds apart.
"""
import json, os, re, subprocess, time, urllib.parse
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__)); CAND=os.path.join(HERE,"_pc40")
UA="User-Agent: iguide-iceland/1.0 (bus guide app; iguideiceland.is)"
OK=("cc0","cc by","cc by-sa","public domain","pd-","attribution")
PICKS={
 "hekla":"2006-05-21-153901 Iceland Stórinúpur.jpg",
 "esja":"Esja (2571116699).jpg",
 "kerid":"Kerid-08-Krater-1980-gje.jpg",
 "bruara":"Miðhusaskogur 031.JPG",
 "laugarvatn":"Laugarvatn.jpg",
 "mosfellsbaer":"Mosfellsbaer2011.jpg",
 "kjalarnes":"2014-04-27 12-27-10 Iceland - Kjalarnesi Grundarhverfi.JPG",
 "ingolfsfjall":"Ingólfsfjall.JPG",
 "haukadalur":"Valle Haukadalur desde Laugarfjall, Suðurland, Islandia, 2014-08-16, DD 102.JPG",
 "skalholt":"Skálholtskirkja 2015-07-19.jpg",
 "sog":"Sog1.JPG",
}
def strip(h): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>","",h or "")).strip()
man=[]
for slug,f in PICKS.items():
    url=("https://commons.wikimedia.org/w/api.php?action=query&titles=File:"
         +urllib.parse.quote(f.replace(" ","_"))
         +"&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=1400&format=json&formatversion=2")
    d={}
    for _ in range(5):
        r=subprocess.run(["curl","-sS","--max-time","60","-H",UA,url],capture_output=True,text=True)
        if r.returncode==0 and r.stdout.strip().startswith("{"):
            d=json.loads(r.stdout); break
        time.sleep(12)
    p=((d.get("query") or {}).get("pages") or [{}])[0]
    ii=(p.get("imageinfo") or [{}])[0]; em=ii.get("extmetadata",{})
    lic=strip(em.get("LicenseShortName",{}).get("value",""))
    if not any(k in lic.lower() for k in OK):
        print("  %-16s licence %r — SKIPPED"%(slug,lic)); man.append({"slug":slug,"error":"licence "+lic}); time.sleep(6); continue
    author=re.sub(r"\s*\(talk\).*$","",strip(em.get("Artist",{}).get("value","")) or "Unknown")[:70]
    raw=os.path.join(CAND,slug+".src")
    subprocess.run(["curl","-sS","--max-time","120","-H",UA,"-o",raw, ii.get("thumburl") or ii.get("url")],capture_output=True)
    try:
        im=Image.open(raw).convert("RGB")
        if im.width>1200: im=im.resize((1200,round(im.height*1200/im.width)),Image.LANCZOS)
        im.save(os.path.join(CAND,slug+".webp"),"WEBP",quality=82,method=6)
        print("  %-16s %-22s %-30s %dx%d"%(slug,lic,author[:30],im.width,im.height))
        man.append({"slug":slug,"file":f,"lic":lic,"author":author,"px":"%dx%d"%(im.width,im.height),"descurl":ii.get("descriptionurl")})
    except Exception as ex:
        print("  %-16s convert failed %s"%(slug,ex)); man.append({"slug":slug,"error":str(ex)})
    time.sleep(6)
json.dump(man,open(os.path.join(CAND,"manifest-c.json"),"w"),ensure_ascii=False,indent=1)
print("done")
