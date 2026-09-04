#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""7.42 Sveinn Pálsson carried two things that were simply not true — "1793"
and "Iceland's first university-trained doctor". Rewritten against Vísindavefur
and Læknablaðið. 7.43 Höfðabrekka gains the exact dates the University of
Iceland report gives, and both cues are turned to the side the bus is on."""
import io
P = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/7.0 Glacial Lagoon.md"
t = io.open(P, encoding="utf-8").read()
orig = t
I = "  "

start = t.index(I + "> ### 7.42 🧊 Sveinn Pálsson")
end   = t.index(I + "> ### 7.44 Vík í Mýrdal")
NEW = """  > ### 7.42 🧊 Sveinn Pálsson — The Country Doctor Who Worked Out How Glaciers Move

  > *Look right — Mýrdalsjökull over the black sand.*

  <callout>🎣 In **1794** a country doctor stood in front of a glacier tongue and worked out something nobody in Europe had: **glaciers flow.** They are not frozen still. **They move like something thick and half-melted** — and he was about a century early.</callout>

  - **Sveinn Pálsson**, **1762–1840.** He took a **natural-sciences degree in Copenhagen in the spring of 1791** — the first person in Denmark to sit that exam — and went home meaning to come back and finish the medical half. He never did finish it. He doctored anyway, for the rest of his life.
  - In **1799** a new medical district was created covering **Árnessýsla, Rangárvallasýsla, Vestur-Skaftafellssýsla and the Westman Islands.** He took it up in **1800**, moved to **Suður-Vík in Mýrdalur in 1809** — the village we are driving into — and stayed there until he died in **1840.**
  - The glaciers were his own time, not the job. At **Kvíárjökull in 1794** he looked at the curved cracks running across the ice and wrote that it had moved *"hálfbráðinn eða sem þykkt seigfljótandi efni"* — **half-melted, like a thick viscous substance.** That is the modern answer: ice deforms under its own weight and creeps downhill.
  - Europe never got to read it. His ***Ferðabók*** and the glacier treatise ***Jöklaritið*** **stayed in manuscript and were not printed until 1945**, translated by **Jón Eyþórsson, Pálmi Hannesson and Steindór Steindórsson**; the English edition came in **2004.** By 1945 the credit for glacier flow had long gone elsewhere.
  - And be accurate about the one guides get wrong: **he was not Iceland's first doctor.** That was his father-in-law, **Bjarni Pálsson**, the first *landlæknir*. Sveinn stood in as acting *landlæknir* himself, briefly, in **1803–04.**

  🎯 The right answer about moving ice, written down in 1794 by a district doctor, and printed **105 years after he died.**

  🎤 He worked out how glaciers move while riding between farms in this weather — and the world got round to reading it in 1945.

  🌫️ Weather pivot (if the ice is hidden): "It is all in there under the cloud. He was out in exactly this, on a horse, with a notebook."

  + ### 🗣️ How to say it:
    - **Sveinn Pálsson** [**SVAYN POWL**-son] — the district doctor at Vík, 1762–1840
    - **Kvíárjökull** [**KVEE**-ow-**YEU**-kutl] — the glacier tongue he described in 1794
    - **Jöklaritið** [**YEU**-kla-ri-tith] — his glacier treatise, printed 1945
    - **Suður-Vík** [**SOO**-thur-**VEEK**] — the farm in Vík he lived on from 1809

  🧵 #geology #technology


  > ### 7.43 🏚️ Höfðabrekka — The Farm That Moved Uphill

  > *Look right — the slope above the black sand, just before Vík.*

  <callout>🎣 A farm that got picked up and moved because **the volcano kept aiming at it** — and the flood that did it is recorded almost hour by hour.</callout>

  - **Höfðabrekka** stood on the low ground below this slope. On **3 November 1660** Katla's flood reached it — *"kom fram að Höfðabrekku jöklagangur með ofurmáta miklum vatnsþunga"* — and on the **8th–9th of November** the biggest wave *"sópaði burtu kirkju og bæjarhúsum að mestu"*: **it took the church and most of the farm buildings.**
  - They rebuilt it **up on the ridge itself** — where it still is, and where you are looking. The farm kept its name and changed its address.
  - That is the pattern along this whole coast, and it is worth naming: people here do not abandon a place, they **move it upslope and carry on.**
  - Everything between here and the sea is the reason — **Mýrdalssandur**, a black plain that exists because Katla has repeatedly emptied a glacier across it.

  🎯 The volcano took the church and the farm in November 1660, so they rebuilt it further up the hill and stayed.

  🎤 In most countries a flood like that ends the settlement. Here it just changes the postcode.

  🌫️ Weather pivot (if the slope is hidden): "The farm is up in that murk somewhere — which is exactly the point. It was deliberately put up out of the water's way."

  + ### 🗣️ How to say it:
    - **Höfðabrekka** [**HUV**-tha-**BREK**-ka] — the farm rebuilt uphill after the 1660 flood
    - **Mýrdalssandur** [**MEER**-dals-**SAN**-dur] — the black flood-plain Katla built
    - **jökulhlaup** [**YEU**-kul-hloyp] — the glacial flood that took it

  🧵 #geology #migration


"""
t = t[:start] + NEW + t[end:]
assert t != orig
io.open(P, "w", encoding="utf-8").write(t)
print("7.42 / 7.43 rewritten")
