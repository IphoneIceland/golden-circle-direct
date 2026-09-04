#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Put the two new 7.0 blocks in the order the road actually passes them, and
give each a cue the geometry agrees with. Westbound across Mýrdalssandur you
meet Höfðabrekka's ridge first and Vík last, so Sveinn Pálsson — who lived in
Vík — belongs at the end of the leg, not the middle of the sand."""
import io, re
P = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/7.0 Glacial Lagoon.md"
t = io.open(P, encoding="utf-8").read()
orig = t

a0 = t.index("  > ### 7.42 🧊 Sveinn Pálsson")
a1 = t.index("  > ### 7.43 🏚️ Höfðabrekka")
a2 = t.index("*******\n+ ## 📍 Vík")
sveinn, hofda = t[a0:a1], t[a1:a2]

# swap the numbers with the blocks
sveinn = sveinn.replace("> ### 7.42 🧊 Sveinn Pálsson", "> ### 7.43 🧊 Sveinn Pálsson", 1)
hofda  = hofda.replace("> ### 7.43 🏚️ Höfðabrekka",  "> ### 7.42 🏚️ Höfðabrekka", 1)

# cues the geometry backs: Höfðabrekka 1 o'clock right at 2.4 km, Vík dead ahead at 1.4 km
sveinn = sveinn.replace("  > *Look right — Mýrdalsjökull over the black sand.*",
                        "  > *Look ahead — Vík. He lived down there, at Suður-Vík, from 1809.*", 1)
hofda  = hofda.replace("  > *Look right — the slope above the black sand, just before Vík.*",
                       "  > *Look right at 1 o'clock — the ridge above the sand, with the farm up on top.*", 1)
assert "Suður-Vík, from 1809" in sveinn and "1 o'clock" in hofda

t = t[:a0] + hofda + sveinn + t[a2:]

# Threads index follows the blocks
t = t.replace("- 7.42 Sveinn Pálsson — the country doctor who worked out how glaciers move",
              "- 7.43 Sveinn Pálsson — the country doctor who worked out how glaciers move")
t = t.replace("- 7.43 Höfðabrekka — the farm that moved uphill",
              "- 7.42 Höfðabrekka — the farm that moved uphill")

assert t != orig
io.open(P, "w", encoding="utf-8").write(t)
print("7.42/7.43 swapped, cues re-aimed")
