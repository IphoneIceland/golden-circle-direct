#!/usr/bin/env python3
"""Second pass for the subjects Wikidata P18 missed — Wikipedia lead image.

Wikidata returned "no P18" for Hekla and Esja, which plainly do have pictures:
wbsearchentities throttles and an empty reply looks identical to an entity with
no image. So this pass asks the article itself (en first, then is) for its lead
image, then Commons for the licence. Same licence gate as everywhere else.
"""
import json, os, re, subprocess, time, urllib.parse
from PIL import Image

HERE=os.path.dirname(os.path.abspath(__file__)); CAND=os.path.join(HERE,"_pc40")
os.makedirs(CAND,exist_ok=True)
UA="User-Agent: iguide-iceland/1.0 (bus guide app; iguideiceland.is)"
OK=("cc0","cc by","cc by-sa","public domain","pd-","attribution")

WANT=[("kristnitokuhraun",[("is","Kristnitökuhraun"),("is","Svínahraun")]),
      ("ingolfsfjall",[("en","Ingólfsfjall"),("is","Ingólfsfjall")]),
      ("sog",[("en","Sog (river)"),("is","Sog (á)")]),
      ("kerid",[("en","Kerið"),("is","Kerið")]),
      ("bruara",[("en","Brúará"),("is","Brúará")]),
      ("haukadalur",[("en","Haukadalur, Bláskógabyggð"),("is","Haukadalur í Biskupstungum")]),
      ("laugarvatn",[("en","Laugarvatn"),("is","Laugarvatn")]),
      ("hekla",[("en","Hekla"),("is","Hekla")]),
      ("laugarvatnshellir",[("is","Laugarvatnshellir"),("en","Laugarvatnshellir")]),
      ("gljufrasteinn",[("en","Gljúfrasteinn"),("is","Gljúfrasteinn")]),
      ("mosfellsbaer",[("en","Mosfellsbær"),("is","Mosfellsbær")]),
      ("kjalarnes",[("en","Kjalarnes"),("is","Kjalarnes")]),
      ("esja",[("en","Esja"),("is","Esja")]),
      ("olgerdin",[("is","Ölgerðin Egill Skallagrímsson"),("en","Ölgerðin Egill Skallagrímsson")]),
     ]

def get(url, tries=4):
    for _ in range(tries):
        r=subprocess.run(["curl","-sS","--max-time","60","-H",UA,url],capture_output=True,text=True)
        if r.returncode==0 and r.stdout.strip().startswith("{"):
            return json.loads(r.stdout)
        time.sleep(2)
    return {}
def strip(h): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>","",h or "")).strip()

man=[]
for slug,cands in WANT:
    fname=None
    for wiki,title in cands:
        d=get(f"https://{wiki}.wikipedia.org/w/api.php?action=query&titles="
              +urllib.parse.quote(title)+"&prop=pageimages&piprop=original&format=json&formatversion=2")
        pg=((d.get("query") or {}).get("pages") or [{}])[0]
        orig=(pg.get("original") or {}).get("source")
        if orig:
            fname=urllib.parse.unquote(orig.rsplit("/",1)[-1]); break
        time.sleep(1)
    if not fname:
        print("  %-20s no article image"%slug); man.append({"slug":slug,"error":"no lead image"}); continue
    d=get("https://commons.wikimedia.org/w/api.php?action=query&titles=File:"
          +urllib.parse.quote(fname)+"&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=1400&format=json&formatversion=2")
    pages=(d.get("query") or {}).get("pages") or []
    ii=(pages[0].get("imageinfo") or [{}])[0] if pages else {}
    em=ii.get("extmetadata",{}); lic=strip(em.get("LicenseShortName",{}).get("value",""))
    if not any(k in lic.lower() for k in OK):
        print("  %-20s licence not usable: %r"%(slug,lic)); man.append({"slug":slug,"error":"licence "+lic}); continue
    author=re.sub(r"\s*\(talk\).*$","",strip(em.get("Artist",{}).get("value","")) or "Unknown")[:70]
    raw=os.path.join(CAND,slug+".src")
    subprocess.run(["curl","-sS","--max-time","90","-H",UA,"-o",raw,ii.get("thumburl") or ii.get("url")],capture_output=True)
    try:
        im=Image.open(raw).convert("RGB")
        if im.width>1200: im=im.resize((1200,round(im.height*1200/im.width)),Image.LANCZOS)
        im.save(os.path.join(CAND,slug+".webp"),"WEBP",quality=82,method=6)
        print("  %-20s %s | %s | %dx%d | %s"%(slug,lic,author[:30],im.width,im.height,fname[:40]))
        man.append({"slug":slug,"file":fname,"lic":lic,"author":author,"px":"%dx%d"%(im.width,im.height),"descurl":ii.get("descriptionurl")})
    except Exception as ex:
        print("  %-20s convert failed %s"%(slug,ex)); man.append({"slug":slug,"error":str(ex)})
json.dump(man,open(os.path.join(CAND,"manifest-b.json"),"w"),ensure_ascii=False,indent=1)
print("done")
