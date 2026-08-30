#!/usr/bin/env python3
"""
Assemble '11.0 Snæfellsnes.md' from the Solar Eclipse export.

Blocks are kept VERBATIM and renumbered; only the section skeleton, four
eclipse-only blocks, and cue lines that the new route makes untrue change.
Three new blocks (Ytri-Tunga, Kirkjufell, Berserkjahraun) are written fresh
from Ritchie's own research pages, marked NEW for the Editor pass.
"""
import re, os

SRC = next(p for p in [os.path.expanduser("~/Documents/RitchWiki"), os.path.expanduser("~/mnt/RitchWiki")] if os.path.isdir(p)) + "/Tour Scripts/_source Solar Eclipse (for 11.0).md"
OUT = next(p for p in [os.path.expanduser("~/Documents/RitchWiki"), os.path.expanduser("~/mnt/RitchWiki")] if os.path.isdir(p)) + "/Tour Scripts/11.0 Snæfellsnes.md"

import sys as _sys
if os.path.exists(OUT):
    _sys.exit("REFUSING: %s already exists — it has hand edits (eclipse excision). Move it aside first if you really want to regenerate." % OUT)
raw = open(SRC, encoding="utf-8").read()
lines = raw.split("\n")

# ---- carve the source into blocks keyed by E-number ------------------------
HEAD = re.compile(r'^\s*> #{2,3}\s+(?:\[?E\.(\d+)\]?|E\.(\d+))?\s*(.*)$')
starts = []   # (line_idx, enum or None, title)
for i, l in enumerate(lines):
    m = re.match(r'^\s*> #{2,3}\s+(.*)$', l)
    if m:
        t = m.group(1)
        em = re.match(r'^\[?E\.(\d+)\]?\s*', t) or re.match(r'^E\.(\d+)\s*', t)
        starts.append((i, int(em.group(1)) if em else None, t))
sec = re.compile(r'^\+ #{1,2} |^## |^\+ ## ')
def block_text(si):
    a = starts[si][0]
    b = len(lines)
    for j in range(a+1, len(lines)):
        if sec.match(lines[j]) or re.match(r'^\s*> #{2,3}\s+', lines[j]):
            b = j; break
    return "\n".join(lines[a:b]).rstrip()

BLK = {}
INTRO = None
for si,(i,e,t) in enumerate(starts):
    if e is not None: BLK[e] = block_text(si)
    elif "Three Names" in t: INTRO = block_text(si)
    # eclipse briefing (no E-number) deliberately not captured

missing = [e for e in list(range(1,15))+list(range(16,40)) if e not in BLK]
if missing: raise SystemExit("missing blocks: %s" % missing)

def renum(txt, old, new):
    txt = re.sub(r'(> #{2,3}\s+)\[?E\.%d\]?\s*' % old, r'\g<1>11.%d ' % new, txt, count=1)
    return txt

# ---- the three NEW blocks --------------------------------------------------
YTRI = """  > ### 11.15 🦭 Ytri-Tunga — The Seals Keep Office Hours

  > *Turning down the farm track to Ytri-Tunga.*

  <callout>🎣 The staff at this stop are unionised: they turn up in June and July, lie about all day, and get photographed doing it. **Seals. The staff are seals.**</callout>

  - Ytri-Tunga is a working **farm** in **Staðarsveit** whose shoreline hosts one of Snæfellsnes's most reliable **seal colonies** — the **landowner built the track and the car park** so you can reach the shore without marching through the fields.
  - The regulars are **harbour seals** — found all along the Snæfellsnes coast, and this shore is **the best place on the peninsula to get close to them**. The bigger, shyer **grey seal** turns up *sometimes* — the wildlife survey's word, not mine (**Sólrún Þórðardóttir, 2020**).
  - **June and July are the office hours.** Outside them the rocks can be bare — the seals are wild, not payroll.
  - House rules: **keep your distance, keep it quiet, no feeding.** A seal that flees into the water because of you has paid for your photo.

  🎯 One farmer built a car park so strangers could watch seals do absolutely nothing — and it became one of the best-loved shores on the peninsula.

  🎤 The seals keep office hours, and we've arrived inside them. Act like clients, not paparazzi.

  🌫️ Weather pivot (if the seals are elsewhere): "Empty rocks today — the colony commutes. Those skerries are their desks, and by June they're all back at work."

  + ### 🗣️ How to say it:
    - **Ytri-Tunga** [**EE**-tree **TOON**-ga] — the farm and its seal beach; 'the outer tongue' of land
    - **Staðarsveit** [**STA**-thar-svayt] — the farm district along this southern shore
    - **landselur** [**LAND**-sel-ur] — the harbour seal, literally 'land seal'

  🧵 #wildlife
"""

KIRK = """  > ### 11.34 ⛰️ Kirkjufell — The Church, Not the Arrowhead

  > *Ahead on the spit — the lone striped peak, with Kirkjufellsfoss by the car park.*

  <callout>🎣 Half this bus already has this mountain as a screensaver. My job isn't to introduce it — **it's to correct it.**</callout>

  - **463 metres**, standing alone on a spit — about **130 metres taller than the Eiffel Tower** — and the trick isn't height, it's **isolation**: nothing beside it to spoil the silhouette.
  - The stripes are the whole geology lesson: **alternating lava and sediment**, stacked through successive ice ages, then **carved by glaciers into a lone nunatak** — rock that kept its head above the ice sheet. **Not a volcano.** No crater, no magma; the ice cut everything else down around it.
  - The name is **Kirkjufell — 'church mountain'** — centuries older than television. *Game of Thrones* (seasons **6 and 7**) only ever calls it **"the mountain shaped like an arrowhead"** — a line in a script, not a name. Danish sailors called it **Sukkertoppen**, the sugar top. Church: original. Arrowhead: fan fiction. Sugar: the Danes were hungry.
  - **Kirkjufellsfoss**, the little three-tier falls, sits in the foreground like a location scout placed it. **It was ice.** Ten minutes of walking, a lifetime of screensavers.
  - One duty line: the climb is officially rated **very demanding and dangerous**, with **fatal accidents on record — the most recent in October 2022**. We admire from the waterfall; the summit belongs to equipped mountaineers.

  🎯 Nobody built Kirkjufell up. The ice subtracted an entire landscape — and left the best bit standing.

  🎤 It survived the ice age and it survived HBO. It will survive your two hundred photographs — take them.

  🌫️ Weather pivot (if cloud hides it): "The mountain is in there — 463 metres of it, modelling for radar today. Kirkjufellsfoss works at ground level all year; start there."

  + ### 🗣️ How to say it:
    - **Kirkjufell** [**KIRK**-yu-fetl] — 'church mountain', the lone 463 m peak
    - **Kirkjufellsfoss** [**KIRK**-yu-fetls-foss] — the three-tier falls in every postcard
    - **Grundarfjörður** [**GRUN**-dar-fyur-thur] — the fishing town next door, roughly 900 people
    - **Sukkertoppen** [**SUK**-er-top-en] — the Danish sailors' nickname: 'the sugar top'
    - **nunatak** [**NOO**-na-tak] — rock that stood above the ice sheet while glaciers planed the rest

  🧵 #geology #film
"""

BERS = """  > ### 11.35 🪨 Berserkjahraun — The Severance Package Was a Bath

  > *Crossing the rust-red lava on Road 54 — Berserkjahraun on both sides.*

  <callout>🎣 Iceland's first recorded construction contract: clear a road through this lava and marry the farmer's daughter. **The contractors finished the job. They should have read the fine print.**</callout>

  - Erupted about **4,000 years ago** from a row of **scoria cones of the Ljósufjöll volcanic system** — **Rauðakúla, Grákúla and Kothraunskúla** — rough **aa lava** that crawled to the sea at **Bjarnarhöfn** and **Hraunsfjörður** and has been gathering moss ever since.
  - **Eyrbyggja Saga** supplies the labour dispute: two **Swedish berserkers** were promised a farmer's daughter if they could clear a path through the lava. **They succeeded** — whereupon their master **Víga-Styrr** had them killed, **unarmed, in the bath**, and buried in the lava.
  - The path — **Berserkjagata** — is **still clearly visible** a thousand years on. And when archaeologists excavated the grave beside it, **they found the bones of two men.** The saga kept receipts.

  🎯 A 4,000-year-old lava field, a 1,000-year-old road, and the oldest lesson in construction: **get paid up front.**

  🎤 Two berserkers built the first road through here. The pay was a farmer's daughter — and the severance package was a bath they never left.

  🌫️ Weather pivot (if the craters are hidden): "No red craters today — but the lumps under the moss either side of us are the berserkers' lava, and this road is doing exactly what their path did."

  + ### 🗣️ How to say it:
    - **Berserkjahraun** [ber-**SERK**-ya-hroyn] — 'the berserkers' lava field'
    - **Berserkjagata** [ber-**SERK**-ya-**GA**-ta] — the saga-era path they cleared, still visible
    - **Eyrbyggja Saga** [**AYR**-big-ya] — the saga that recorded the whole grim bargain
    - **Víga-Styrr** [**VEE**-ga-stir] — the master who ordered the bath
    - **Ljósufjöll** [**LYOH**-su-fyutl] — the volcanic system the craters belong to

  🧵 #geology #saga
"""

# ---- fixed cue rewrites (route direction changed) --------------------------
def swap_cue(txt, new_cue):
    return re.sub(r'^(\s*> \*).*(\*\s*)$', r'\g<1>%s\g<2>' % new_cue, txt,
                  count=1, flags=re.M)

b27 = swap_cue(BLK[27], "Turning down to Djúpalónssandur — the beach at the volcano's foot.")
b31 = swap_cue(BLK[31], "Passing Rif on the left — the flat little harbour village on the point.")
b32 = swap_cue(BLK[32], "Still passing Rif — look at the roadside posts for the terns.")

# ---- assemble --------------------------------------------------------------
OUTV = []
OUTV.append("# Welcome onboard your Snæfellsnes tour — you will see it's split into how we will drive the tour today.\n")
OUTV.append("🚌 Is drive sections\n\n📍Our stops today\n")
OUTV.append("Anything with an underline is clickable.\n")
OUTV.append("▶︎ Click these arrows to read the section information.\n\n*******\n")

def add(sect, blocks):
    OUTV.append(sect + "\n")
    for b in blocks: OUTV.append(b + "\n")

add("+ # 🚌 BSÍ Bus Terminal → Borgarnes",
    [INTRO] + [renum(BLK[e], e, e) for e in range(1, 9)])
add("+ ## 📍 Borgarnes", [renum(BLK[9], 9, 9)])
add("+ ## 🚌 Borgarnes → Ytri-Tunga", [renum(BLK[e], e, e) for e in range(10, 15)])
add("+ ## 📍 Ytri-Tunga", [YTRI])
add("+ ## 🚌 Ytri-Tunga → Arnarstapi", [renum(BLK[e], e, e) for e in range(16, 20)])
add("+ ## 📍 Arnarstapi", [renum(BLK[e], e, e) for e in range(20, 23)])
add("+ ## 🚌 Arnarstapi → Djúpalónssandur", [renum(BLK[e], e, e) for e in range(23, 27)])
add("+ ## 📍 Djúpalónssandur", [renum(b27, 27, 27)])
add("+ ## 🚌 Djúpalónssandur → Ólafsvík",
    [renum(BLK[28], 28, 28), renum(BLK[29], 29, 29),
     renum(b31, 31, 30), renum(b32, 32, 31)])
add("+ ## 📍 Ólafsvík", [renum(BLK[36], 36, 32)])
add("+ ## 🚌 Ólafsvík → Kirkjufell", [renum(BLK[37], 37, 33)])
add("+ ## 📍 Kirkjufell", [KIRK])
add("+ ## 🚌 Grundarfjörður → BSÍ Bus Terminal",
    [BERS, renum(BLK[38], 38, 36), renum(BLK[39], 39, 37)])

doc = "\n".join(OUTV)
# global relabel: any leftover E.n cross-references
doc = doc.replace("E.1 ", "11.1 ")
open(OUT, "w", encoding="utf-8").write(doc)

# ---- review report ---------------------------------------------------------
print("wrote %s (%d bytes)" % (OUT, len(doc)))
drops = [30, 33, 34, 35]
print("dropped blocks: E.%s + eclipse briefing" % ", E.".join(map(str, drops)))
print("\n-- eclipse/totality mentions REMAINING (need eyes): --")
for i, l in enumerate(doc.split("\n"), 1):
    if re.search(r'eclipse|totality|corona|glasses', l, re.I):
        print("  line %d: %s" % (i, l.strip()[:120]))
print("\n-- cue lines for direction sanity: --")
for l in doc.split("\n"):
    if re.match(r'^\s*> \*', l): print("  " + l.strip()[:110])
