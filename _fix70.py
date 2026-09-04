#!/usr/bin/env python3
# One-off: remove two duplicate stops I added to 7.0, renumber, repair Threads index.
import re, io, sys
P = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/7.0 Glacial Lagoon.md"
t = io.open(P, encoding="utf-8").read()
orig = t

# 1. delete 7.43 Kirkjubaejarklaustur + 7.44 Eldgja (both duplicate 7.31 / 7.41)
i = t.index("  > ### 7.43 ⛪ Kirkjubæjarklaustur")
j = t.index("  > ### 7.45 \U0001f3da️ Höfðabrekka")
removed = t[i:j]
t = t[:i] + t[j:]
print("removed %d chars, %d lines" % (len(removed), removed.count("\n")))

# 2. drop the 1918-flood bullet from Hofdabrekka (word-for-word dupe of 7.41)
for ln in t.split("\n"):
    if "Nobody died in Katla's 1918 flood" in ln:
        t = t.replace(ln + "\n", "")
        print("dropped dupe bullet")
        break

# 3. dead thread tag: #settlement has no Threads section -> #migration
t = t.replace("\U0001f9f5 #geology #settlement", "\U0001f9f5 #geology #migration")

# 4. renumber heading lines only: 7.45->7.43, 7.46->7.44, 7.47->7.45
for frm, to in ((45, 43), (46, 44), (47, 45)):
    t, n = re.subn(r'(?m)^(\s*> ### )7\.%d(\s)' % frm, r'\g<1>7.%d\g<2>' % to, t)
    print("heading 7.%d -> 7.%d : %d" % (frm, to, n))

# 5. Threads index repairs
t = t.replace("- 7.42 Vík í Mýrdal — The Southern Outpost",
              "- 7.44 Vík í Mýrdal — The Southern Outpost")
t = t.replace("- 7.43 Seljalandsfoss & Gljúfrabúi — Inside the Waterfall",
              "- 7.45 Seljalandsfoss & Gljúfrabúi — Inside the Waterfall")

GEO_NEW = ("- 7.42 Sveinn Pálsson — the country doctor who worked out how glaciers move\n"
           "- 7.43 Höfðabrekka — the farm that moved uphill\n")
anchor = "- 7.41 Katla — The Sleeping Giant Under the Ice\n"
assert t.count(anchor) == 1, t.count(anchor)
t = t.replace(anchor, anchor + GEO_NEW)

# #technology section gets Sveinn Palsson
tech = "- 7.6 Hellisheiðarvirkjun — The Dragon's Breath\n"
k = t.index("### ⚙️ Technology")
t = t[:k] + t[k:].replace(tech, tech + "- 7.42 Sveinn Pálsson — the country doctor who worked out how glaciers move\n", 1)

# #migration section gets Hofdabrekka
mig = "- 7.28 Hjörleifshöfði — Blood-Brother and Witch-in-the-Ice\n"
k = t.index("### \U0001f6a2 Migration & Settlement")
t = t[:k] + t[k:].replace(mig, mig + "- 7.43 Höfðabrekka — the farm that moved uphill\n", 1)

assert t != orig
io.open(P, "w", encoding="utf-8").write(t)
print("written")
