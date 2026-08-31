#!/usr/bin/env python3
"""10.0 Snæfellsnes North — 11.0's blocks re-ordered for the north-about route
(BSÍ → Borgarnes → Vatnaleið/Selvallafoss → Kirkjufell → Ólafsvík → Djúpalónssandur
→ Arnarstapi → Ytri-Tunga → BSÍ), with cue lines flipped where the road reverses.
Content verbatim from 11.0 except: flipped cue lines (table below), 11.36's
time-bound decompression bullet + mic dropped/swapped for the outbound pass, and a
clearly-marked PENDING Selvallafoss stop block (no facts invented — scripts chat owes it).
Refuses to overwrite an existing output."""
import os,re,sys
base=next(p for p in [os.path.expanduser("~/Documents/RitchWiki"), os.path.expanduser("~/mnt/RitchWiki")] if os.path.isdir(p))+"/Tour Scripts"
SRC=base+"/11.0 Snæfellsnes.md"; OUT=base+"/10.0 Snæfellsnes North.md"
if os.path.exists(OUT): sys.exit("REFUSING: %s exists — move it aside to regenerate."%OUT)
raw=open(SRC,encoding="utf-8").read()

# carve blocks: number -> text (intro carried as number 0)
blocks={}
heads=[(m.start(),m.group(1)) for m in re.finditer(r'^  > #{2,3} (?:(11\.\d+) )?',raw,re.M)]
bounds=[h[0] for h in heads]+[len(raw)]
for i,(pos,num) in enumerate(heads):
    key=float(num.split(".")[1]) if num else 0
    seg=raw[pos:bounds[i+1]]
    cut=re.search(r'^\+ ## ',seg,re.M)
    if cut: seg=seg[:cut.start()]
    blocks[int(key)]=seg.rstrip()+"\n"
assert set(range(0,37))<=set(blocks), sorted(blocks)

SWAP={ # block -> list of (old,new) applied to its text (cue lines only)
 32:[("> *Leaving Rif — Ólafsvík ahead in nine kilometres.*","> *Coming into Ólafsvík.*")],
 30:[("Passing Rif on the left","Passing Rif on the right")],
 26:[("> *Look left at 9 o'clock — the white tower at Malarrif.*","> *Look right at 3 o'clock — the white tower at Malarrif.*")],
 25:[("> *Look left at 9 o'clock — two dark pinnacles against the sea: Lóndrangar.*","> *Look right at 3 o'clock — two dark pinnacles against the sea: Lóndrangar.*")],
 24:[("> *Look right at 3 o'clock — Snæfellsjökull, if it's showing.*","> *Look left at 9 o'clock — Snæfellsjökull, if it's showing.*")],
 23:[("> *Look left at 9 o'clock — Laugarbrekka, then Hellnar down by the shore.*","> *Look right at 3 o'clock — Hellnar down by the shore, then Laugarbrekka.*")],
 19:[("> *Look ahead at 12 o'clock — the dark pyramid of Stapafell; then right at 3 o'clock, a thin black cleft in th","> *Leaving Arnarstapi — Stapafell over your left shoulder; then at 9 o'clock, a thin black cleft in th")],
 16:[("> *Look left at 9 o'clock — a small black church standing alone on the lava.*","> *Look right at 3 o'clock — a small black church standing alone on the lava.*")],
 14:[("Look left at 9 o'clock — flat pale sand","Look right at 3 o'clock — flat pale sand"),("the cliffs inland on your right are old sea","the cliffs inland on your left are old sea")],
}
def fix36(t):
    t=re.sub(r'  - Which is the theme now: decompression\..*?\n',"",t)
    t=t.replace("🎤 Today ran on tide tables and seal naps. This hour has no schedule at all. Doze if you like — I'll wake you for the city lights.",
                "🎤 A road from 2001 across mountains poured under an ice sheet — and the first waterfall of the day is waiting just over this pass.")
    return t

SELV="""  > ### 💧 Selvallafoss — Script Pending

  > *Turning off at the pass — Selvallafoss below the road.*

  <callout>🎣 This stop is wired into the route and the map — the script block is still to be written. Nothing invented on purpose.</callout>

  - Selvallafoss sits by Selvallavatn on the Vatnaleið road; the block for it is owed by the scripts chat.

  🧵 #pending
"""

SEC=[("🚌 BSÍ Bus Terminal → Borgarnes",[0,1,2,3,4,5,6,7,8]),
     ("📍 Borgarnes",[9]),
     ("🚌 Borgarnes → Selvallafoss",[10,11,12,13,36]),
     ("📍 Selvallafoss",["SELV"]),
     ("🚌 Selvallafoss → Kirkjufell",[35]),
     ("📍 Kirkjufell",[34]),
     ("🚌 Kirkjufell → Ólafsvík",[33]),
     ("📍 Ólafsvík",[32]),
     ("🚌 Ólafsvík → Djúpalónssandur",[30,31,29,28]),
     ("📍 Djúpalónssandur",[27]),
     ("🚌 Djúpalónssandur → Arnarstapi",[26,25,24,23,18]),
     ("📍 Arnarstapi",[20,21,22]),
     ("🚌 Arnarstapi → Ytri-Tunga",[19,17,16]),
     ("📍 Ytri-Tunga",[15]),
     ("🚌 Ytri-Tunga → BSÍ Bus Terminal",[14])]
out=["# 10.0 Snæfellsnes North\n"]
n=0
for title,ids in SEC:
    out.append("\n+ ## %s\n"%title)
    for bid in ids:
        if bid=="SELV": t=SELV
        else:
            t=blocks[bid]
            for old,new in SWAP.get(bid,[]):
                assert old in t,(bid,old[:50]); t=t.replace(old,new)
            if bid==36: t=fix36(t)
        if bid!=0:
            n+=1
            t=re.sub(r'^(  > #{2,3} )(?:11\.\d+ )?',r'\g<1>10.%d '%n,t,count=1,flags=re.M)
        out.append(t+"\n")
open(OUT,"w",encoding="utf-8").write("".join(out))
print("wrote",OUT,os.path.getsize(OUT),"bytes | blocks:",n,"+ intro")
