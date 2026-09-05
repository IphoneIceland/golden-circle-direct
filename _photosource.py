#!/usr/bin/env python3
"""Source drive-by photos the RELIABLE way: Wikidata subject -> its P18 image.

Commons keyword search is blunt. Asked for Keldur it returned a generic
"turf houses in Iceland, 19th century"; asked for Eyjafjallajokull it returned a
glacier tongue that is probably Gigjokull. Wikidata's P18 ("image") is curated
per subject, so the picture is guaranteed to be OF the thing.

Flow: wbsearchentities(label) -> pick the entity whose description mentions
Iceland -> claims P18 -> Commons imageinfo for licence + author + thumb.

Usage: python3 _getphotos2.py
"""
import json, os, re, subprocess, time, urllib.parse
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, "_pc5")
os.makedirs(CAND, exist_ok=True)

WANT = [
 ("kjarvalsstadir",  ["Kjarvalsstaðir"]),
 ("olgerdin",        ["Ölgerðin Egill Skallagrímsson"]),
 ("ellidaardalur",   ["Elliðaárdalur", "Elliðaár"]),
 ("kristnitokuhraun",["Kristnitökuhraun", "Svínahraun"]),
 ("hveragerdi",      ["Hveragerði"]),
 ("olfusa",          ["Ölfusá"]),
 ("ingolfur",        ["Ingólfur Arnarson"]),
 ("selfoss_town",    ["Selfoss"]),
 ("thjorsa",         ["Þjórsá"]),
 ("hella",           ["Ægissíðuhellar", "Hella, Iceland"]),
 ("landeyjahofn",    ["Landeyjahöfn"]),
 ("drangurinn",      ["Drangshlíð", "Drangurinn í Drangshlíð"]),
 ("petursey",        ["Pétursey"]),
 ("skeidflatarkirkja",["Skeiðflatarkirkja"]),
]

UA = "User-Agent: iguide-iceland/1.0 (bus guide app; iguideiceland.is)"
OK = ("cc0", "cc by", "cc by-sa", "public domain", "pd-", "attribution")

def get(url):
    for _ in range(4):
        r = subprocess.run(["curl", "-sS", "--max-time", "60", "-H", UA, url],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip().startswith("{"):
            return json.loads(r.stdout)
        time.sleep(3)
    return {}

def strip(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h or "")).strip()

manifest = []
for slug, labels in WANT:
    fname = None
    for lab in labels:
        d = get("https://www.wikidata.org/w/api.php?action=wbsearchentities&search="
                + urllib.parse.quote(lab) + "&language=en&uselang=en&limit=6&format=json")
        for hit in d.get("search", []):
            ent = get("https://www.wikidata.org/w/api.php?action=wbgetentities&ids="
                      + hit["id"] + "&props=claims|descriptions&format=json")
            e = (ent.get("entities") or {}).get(hit["id"], {})
            desc = ((e.get("descriptions") or {}).get("en") or {}).get("value", "")
            claims = (e.get("claims") or {}).get("P18") or []
            if not claims:
                continue
            fname = claims[0]["mainsnak"]["datavalue"]["value"]
            print("  %-22s %s (%s) -> %s" % (slug, hit["id"], desc[:34], fname[:44]))
            break
        if fname:
            break
    if not fname:
        print("  %-22s no Wikidata image" % slug)
        manifest.append({"slug": slug, "error": "no P18"})
        continue

    d = get("https://commons.wikimedia.org/w/api.php?action=query&titles=File:"
            + urllib.parse.quote(fname.replace(" ", "_"))
            + "&prop=imageinfo&iiprop=url|extmetadata|size&iiurlwidth=1400"
            + "&format=json&formatversion=2")
    pages = (d.get("query") or {}).get("pages") or []
    ii = (pages[0].get("imageinfo") or [{}])[0] if pages else {}
    em = ii.get("extmetadata", {})
    lic = strip(em.get("LicenseShortName", {}).get("value", ""))
    if not any(k in lic.lower() for k in OK):
        print("  %-22s licence not usable: %s" % (slug, lic))
        manifest.append({"slug": slug, "error": "licence " + lic})
        continue
    author = re.sub(r"\s*\(talk\).*$", "",
                    strip(em.get("Artist", {}).get("value", "")) or "Unknown")[:70]
    raw = os.path.join(CAND, slug + ".src")
    subprocess.run(["curl", "-sS", "--max-time", "90", "-H", UA, "-o", raw,
                    ii.get("thumburl") or ii.get("url")], capture_output=True)
    try:
        im = Image.open(raw).convert("RGB")
        if im.width > 1200:
            im = im.resize((1200, round(im.height * 1200 / im.width)), Image.LANCZOS)
        im.save(os.path.join(CAND, slug + ".webp"), "WEBP", quality=82, method=6)
        print("      -> %s  %s  %dx%d" % (lic, author[:34], im.width, im.height))
        manifest.append({"slug": slug, "file": fname, "lic": lic, "author": author,
                         "px": "%dx%d" % (im.width, im.height),
                         "descurl": ii.get("descriptionurl")})
    except Exception as ex:
        print("  %-22s convert failed %s" % (slug, ex))
        manifest.append({"slug": slug, "error": str(ex)})

json.dump(manifest, open(os.path.join(CAND, "manifest.json"), "w"),
          ensure_ascii=False, indent=1)
print("\ncandidates in %s" % CAND)
