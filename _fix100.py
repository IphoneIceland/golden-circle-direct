#!/usr/bin/env python3
# 10.0 Threads index: renumber Vatnaleid, add the 23 missing cross-references,
# normalise two dead tags, add the #film and #food sections, drop empty #safety.
import re, io
P = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/10.0 Snæfellsnes South.md"
t = io.open(P, encoding="utf-8").read()
orig = t
I = " " * 6

# --- dead tags on blocks ---------------------------------------------------
t = t.replace("\U0001f9f5 #geology #saga", "\U0001f9f5 #geology #literature")
t = t.replace("\U0001f9f5 #nature #geology", "\U0001f9f5 #wildlife #geology")

# --- Vatnaleid moved 10.36 -> 10.41 ---------------------------------------
t = t.replace("- 10.36 Vatnaleið —", "- 10.41 Vatnaleið —")

# --- new index entries, each inserted after an existing anchor line --------
ADD = [
 ("- 10.28 Saxhóll — a scoria crater and the Neshraun lava",
  ["- 10.34 Búlandshöfði — marine shells sealed under lava dated to about 1.1 million years",
   "- 10.37 Berserkjahraun — a 4,000-year-old lava field from four Ljósufjöll cones",
   "- 10.38 Kolgrafarfjörður — the 2004 causeway and what it did to a fjord"]),
 ("- 10.9 Borgarnes — the graveyard chapters of Egils saga",
  ["- 10.34 Búlandshöfði — Eyrbyggja saga's Þrælaskriður, the Slave Screes",
   "- 10.35 Mávahlíð — Eyrbyggja saga's Geirríður, accused of night-riding",
   "- 10.37 Berserkjahraun — the two berserkers and the road they were paid in a bath for",
   "- 10.40 Helgafell — Eyrbyggja saga chapter 11: the mountain opens and the dead are welcomed in"]),
 ("- 10.33 Fróðá — eighteen ghosts, tried at the door",
  ["- 10.35 Mávahlíð — the kveldriða charge, answered in court instead of at a stake",
   "- 10.40 Helgafell — the three wishes, first written down in 1955"]),
 ("- 10.33 Fróðá — a priest, a door-court, and the year 1000",
  ["- 10.39 Bjarnarhöfn — the church of 1856–58, the last of its kind standing",
   "- 10.40 Helgafell — Þórólfur's holy mountain: nobody was to look at it unwashed"]),
 ("- 10.31 The Tern Capital — pole-to-pole commuters beside the car park",
  ["- 10.39 Bjarnarhöfn — the settler named for the direction he would not go"]),
 ("- 10.32 Ólafsvík — the harbour swap of 1687",
  ["- 10.2 Ölgerðin Egill Skallagrímsson — the brewery named for a saga poet"]),
 ("- 10.17 Axlar-Björn — Iceland's one serial killer, executed 1596",
  ["- 10.4 Kjalarnes — the assembly that met before the Alþingi existed",
   "- 10.35 Mávahlíð — a witchcraft charge that got a court date, not a fire"]),
 ("- 10.31 The Tern Capital — 17,000 nests and an Antarctic commute",
  ["- 10.15 Ytri-Tunga — the seals that keep office hours",
   "- 10.38 Kolgrafarfjörður — fifty thousand tonnes of herring, twice in six weeks"]),
 ("- 10.21 The Bárður Statue — Ragnar Kjartansson's 300 tonnes, 1985",
  ["- 10.1 Jóhannes Sveinsson Kjarval — the cod fisherman who became legal tender"]),
 ("- 10.26 Malarrif & Vatnshellir — the 1946 lighthouse over the lava tube",
  ["- 10.41 Vatnaleið — the 2001 road over the spine"]),
]
for anchor, new in ADD:
    a = I + anchor + "\n"
    assert t.count(a) == 1, (anchor, t.count(a))
    t = t.replace(a, a + "".join(I + n + "\n" for n in new))

# 10.41 Vatnaleid already renumbered under #geology and #technology; the
# #technology copy was the same stale line, so drop the duplicate we just made.
dupe = I + "- 10.41 Vatnaleið — the 2001 road over the spine\n"
if t.count(dupe) == 2:
    i = t.index(dupe)
    t = t[:i] + t[i + len(dupe):]

# --- swap the empty #safety section for #film and #food -------------------
old_tail = I + "### ⚠️ Safety  #safety\n"
assert old_tail in t
new_tail = (I + "### 🎬 Film & TV  #film\n"
            "\n"
            + I + "- 10.36 Kirkjufell — the arrowhead mountain from *Game of Thrones*\n"
            "\n"
            + I + "### 🍽️ Food & Drink  #food\n"
            "\n"
            + I + "- 10.39 Bjarnarhöfn — hákarl, and why the shark has to rot before it is safe\n")
t = t.replace(old_tail, new_tail)

assert t != orig
io.open(P, "w", encoding="utf-8").write(t)
print("10.0 threads index patched")
