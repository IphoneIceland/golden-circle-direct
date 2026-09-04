#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final order for the Fellsfjara -> Vík leg, set by the geometry rather than by
how the blocks happened to get typed: the ridge at Höfðabrekka comes up first
(1 o'clock, 2.4 km), then Katla's ice cap, then Vík itself, where Sveinn
Pálsson actually lived. Renumbers 7.41-7.43 to match."""
import io, json
P = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/7.0 Glacial Lagoon.md"
t = io.open(P, encoding="utf-8").read()
orig = t

a0 = t.index("  > ### 7.41 Katla")
a1 = t.index("  > ### 7.42 🏚️ Höfðabrekka")
a2 = t.index("  > ### 7.43 🧊 Sveinn Pálsson")
a3 = t.index("*******\n+ ## 📍 Vík")
katla, hofda, sveinn = t[a0:a1], t[a1:a2], t[a2:a3]

katla = katla.replace("> ### 7.41 Katla", "> ### 7.42 Katla", 1)
hofda = hofda.replace("> ### 7.42 🏚️ Höfðabrekka", "> ### 7.41 🏚️ Höfðabrekka", 1)
t = t[:a0] + hofda + katla + sveinn + t[a3:]

t = t.replace("- 7.41 Katla — The Sleeping Giant Under the Ice",
              "- 7.42 Katla — The Sleeping Giant Under the Ice")
t = t.replace("- 7.42 Höfðabrekka — the farm that moved uphill",
              "- 7.41 Höfðabrekka — the farm that moved uphill")
assert t != orig
io.open(P, "w", encoding="utf-8").write(t)
print("7.41 Höfðabrekka / 7.42 Katla / 7.43 Sveinn Pálsson")

# ---- cues: pins taken from route points that the checker resolves to themselves
Q = "cues-7.0.js"
c = io.open(Q, encoding="utf-8").read()
s, e = c.index("["), c.rindex("]") + 1
C = json.loads(c[s:e])
C = [x for x in C if x["id"] not in ("7.0.11.2", "7.0.11.3")]
for x in C:
    if x["id"] == "7.0.11.1":          # now Höfðabrekka
        x["progress"] = 74.59
        x["pin"] = {"lat": 63.42886, "lon": -18.88523}
        x["target"] = {"lat": 63.42417, "lon": -18.93361, "name": "Höfðabrekka"}
i = [n for n, x in enumerate(C) if x["id"] == "7.0.11.1"][0]
C = C[:i+1] + [
    {"id": "7.0.11.2", "progress": 75.38, "pin": {"lat": 63.41807, "lon": -19.00183},
     "target": {"lat": 63.66178, "lon": -19.122457, "name": "Mýrdalsjökull (Katla)"}},
    {"id": "7.0.11.3", "progress": 75.38, "pin": {"lat": 63.41812, "lon": -19.00210},
     "target": {"lat": 63.41806, "lon": -19.00611, "name": "Vík í Mýrdal"}},
] + C[i+1:]
pr = [x["progress"] for x in C]
assert pr == sorted(pr), pr
io.open(Q, "w", encoding="utf-8").write(c[:s] + json.dumps(C, ensure_ascii=False) + c[e:])
print("cues-7.0.js rewritten for the new order")
