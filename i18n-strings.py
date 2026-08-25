#!/usr/bin/env python3
"""
Pull every translatable string out of every tour script into one corpus.

  python3 i18n-strings.py            # writes _tr/corpus.json

Keyed by a hash of the English text, not by position, so:
  * a line shared between tours is translated once and lands in both
  * adding a tour later reuses whatever it already has in common
  * reordering blocks never silently shifts a translation onto the wrong line

What is deliberately NOT in here:
  say[0] the name, say[1] the pronunciation  — Icelandic stays Icelandic
  tags, ids, kinds, emoji                    — machinery, not prose
"""
import json, os, re, hashlib, subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))
OUT = "_tr"
TOURS = re.findall(r'id:"([^"]+)"', open("tours.js", encoding="utf-8").read())

NODE = r'''
const out=[];
const ids=%s;
for(const id of ids){
  global.window={};
  require("./script-"+id+".js");
  const S=global.window.__SCRIPT__;
  S.sections.forEach((s,si)=>{
    out.push({tour:id, ctx:"section title", t:s.title});
    s.blocks.forEach(b=>{
      const where = "tour "+id+" / "+s.title+" / "+b.title;
      out.push({tour:id, ctx:"block title — "+where, t:b.title});
      if(b.cue)     out.push({tour:id, ctx:"cue, tells the guest where to look — "+where, t:b.cue});
      if(b.point)   out.push({tour:id, ctx:"the point of the block — "+where, t:b.point});
      if(b.mic)     out.push({tour:id, ctx:"the spoken close — "+where, t:b.mic});
      if(b.weather) out.push({tour:id, ctx:"bad-weather alternative — "+where, t:b.weather});
      if(b.pre)     out.push({tour:id, ctx:"intro paragraph — "+where, t:b.pre});
      (b.heads||[]).forEach(x=>out.push({tour:id, ctx:"sub-heading — "+where, t:x}));
      (b.bullets||[]).forEach(x=>out.push({tour:id, ctx:"fact bullet — "+where, t:x}));
      (b.say||[]).forEach(x=>{ if(x[2]) out.push({tour:id,
        ctx:"gloss for the name \""+x[0]+"\" — "+where, t:x[2]}); });
    });
  });
}
console.log(JSON.stringify(out));
''' % json.dumps(TOURS)

raw = json.loads(subprocess.run(["node", "-e", NODE], capture_output=True,
                                text=True, check=True).stdout)

seen, corpus = {}, []
for r in raw:
    t = r["t"]
    if not isinstance(t, str) or not t.strip():
        continue
    h = hashlib.sha1(t.encode("utf-8")).hexdigest()[:10]
    if h in seen:
        seen[h]["tours"].add(r["tour"])
        continue
    e = {"id": h, "en": t, "ctx": r["ctx"], "tours": {r["tour"]}}
    seen[h] = e
    corpus.append(e)

for e in corpus:
    e["tours"] = sorted(e["tours"])

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "corpus.json"), "w", encoding="utf-8") as f:
    json.dump(corpus, f, ensure_ascii=False, indent=1)

words = sum(len(e["en"].split()) for e in corpus)
print("%d unique strings, %d words, %d raw occurrences across %s"
      % (len(corpus), words, len(raw), ", ".join(TOURS)))
