#!/usr/bin/env python3
"""Drive-by photos for 4.0 — Wikidata subject -> its P18 image.  _photos40.py

Same reliable route as _photosource.py: Commons keyword search is blunt, but
P18 is curated per subject so the picture is definitely OF the thing. Added
here: the entity must actually be the Icelandic one. Searching "Selfoss"
without that check returns a waterfall in the north, a football club and a
town, and the first one with a picture wins — which is how you end up showing
guests the wrong Selfoss on the way to the right one.
"""
import json, os, re, subprocess, time, urllib.parse
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, "_pc40")
os.makedirs(CAND, exist_ok=True)

# slug, search labels (first hit with P18 + an Icelandic entity wins), must-see word
WANT = [
 ("olgerdin",       ["Ölgerðin Egill Skallagrímsson"]),
 ("kristnitokuhraun",["Kristnitökuhraun", "Svínahraun"]),
 ("hveragerdi",     ["Hveragerði"]),
 ("ingolfsfjall",   ["Ingólfsfjall"]),
 ("selfoss_town",   ["Selfoss, Iceland", "Selfoss (town)", "Selfoss"]),
 ("olfusa",         ["Ölfusá"]),
 ("sog",            ["Sog (river)", "Sog"]),
 ("kerid",          ["Kerið"]),
 ("bruara",         ["Brúará"]),
 ("skalholt",       ["Skálholt"]),
 ("icelandic_horse",["Icelandic horse"]),
 ("tungufljot",     ["Tungufljót"]),
 ("haukadalur",     ["Haukadalur, Bláskógabyggð", "Haukadalur"]),
 ("laugarvatn",     ["Laugarvatn"]),
 ("hekla",          ["Hekla"]),
 ("laugarvatnshellir",["Laugarvatnshellir", "Laugarvatn caves"]),
 ("gljufrasteinn",  ["Gljúfrasteinn"]),
 ("laxnes",         ["Laxnes", "Mosfellsdalur"]),
 ("mosfellsdalur",  ["Mosfellsdalur"]),
 ("mosfellsbaer",   ["Mosfellsbær"]),
 ("kjalarnes",      ["Kjalarnes"]),
 ("esja",           ["Esja"]),
]

UA = "User-Agent: iguide-iceland/1.0 (bus guide app; iguideiceland.is)"
OK = ("cc0", "cc by", "cc by-sa", "public domain", "pd-", "attribution")

def get(url):
    for _ in range(4):
        r = subprocess.run(["curl","-sS","--max-time","60","-H",UA,url],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            return json.loads(r.stdout)
        time.sleep(3)
    return {}

def strip(h): return re.sub(r"\s+"," ", re.sub(r"<[^>]+>","", h or "")).strip()

manifest=[]
for slug, labels in WANT:
    fname=None; qid=None; desc=""
    for lab in labels:
        d=get("https://www.wikidata.org/w/api.php?action=wbsearchentities&search="
              +urllib.parse.quote(lab)+"&language=en&uselang=en&limit=8&format=json")
        for hit in d.get("search", []):
            ent=get("https://www.wikidata.org/w/api.php?action=wbgetentities&ids="
                    +hit["id"]+"&props=claims|descriptions&format=json")
            e=(ent.get("entities") or {}).get(hit["id"], {})
            dsc=((e.get("descriptions") or {}).get("en") or {}).get("value","")
            claims=(e.get("claims") or {})
            # P17 country must be Iceland (Q189) where the entity has one at all
            ctry=[c["mainsnak"].get("datavalue",{}).get("value",{}).get("id")
                  for c in claims.get("P17",[])]
            if ctry and "Q189" not in ctry: continue
            if not ctry and "iceland" not in (dsc+" "+hit.get("description","")).lower():
                if slug not in ("icelandic_horse",): continue
            p18=claims.get("P18") or []
            if not p18: continue
            fname=p18[0]["mainsnak"]["datavalue"]["value"]; qid=hit["id"]; desc=dsc
            break
        if fname: break
    if not fname:
        print("  %-20s no Wikidata image" % slug); manifest.append({"slug":slug,"error":"no P18"}); continue
    print("  %-20s %s (%s) -> %s" % (slug, qid, desc[:32], fname[:42]))
    d=get("https://commons.wikimedia.org/w/api.php?action=query&titles=File:"
          +urllib.parse.quote(fname.replace(" ","_"))
          +"&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=1400&format=json&formatversion=2")
    pages=(d.get("query") or {}).get("pages") or []
    ii=(pages[0].get("imageinfo") or [{}])[0] if pages else {}
    em=ii.get("extmetadata",{})
    lic=strip(em.get("LicenseShortName",{}).get("value",""))
    if not any(k in lic.lower() for k in OK):
        print("      licence not usable: %s" % lic); manifest.append({"slug":slug,"error":"licence "+lic}); continue
    author=re.sub(r"\s*\(talk\).*$","", strip(em.get("Artist",{}).get("value","")) or "Unknown")[:70]
    raw=os.path.join(CAND, slug+".src")
    subprocess.run(["curl","-sS","--max-time","90","-H",UA,"-o",raw, ii.get("thumburl") or ii.get("url")],capture_output=True)
    try:
        im=Image.open(raw).convert("RGB")
        if im.width>1200: im=im.resize((1200, round(im.height*1200/im.width)), Image.LANCZOS)
        im.save(os.path.join(CAND, slug+".webp"),"WEBP",quality=82,method=6)
        print("      -> %s | %s | %dx%d" % (lic, author[:34], im.width, im.height))
        manifest.append({"slug":slug,"qid":qid,"file":fname,"lic":lic,"author":author,
                         "px":"%dx%d"%(im.width,im.height),"descurl":ii.get("descriptionurl")})
    except Exception as ex:
        print("      convert failed %s" % ex); manifest.append({"slug":slug,"error":str(ex)})

json.dump(manifest, open(os.path.join(CAND,"manifest.json"),"w"), ensure_ascii=False, indent=1)
print("\ncandidates in", CAND)
