# Cue pins that fire too early — for whoever owns pins

Found 17 Sep 2026 while auditing drive sections. **I did not touch any pin.**

A cue's `pin` is where the coach is when the block fires. Its `target` is the thing
being pointed at. The gap between them should be what you can see. Where it is tens
of kilometres, the block fires long before the thing is in the window — and the
sightline maths in the back office computes left/right from the pin, so a wrong pin
gives a confidently wrong answer.

Verified against OpenStreetMap: **Bjarnarhöfn** (64.9974, -22.9633) and **Vatnaleið**
(64.8926, -22.8363) both have the RIGHT target and the WRONG pin. The pin moved, not the place.

| tour | cues with target >15 km from the bus |
|---|---|
| 1.0 | **2 of 33** |
| 2.0 | **3 of 34** |
| 3.0 | **2 of 34** |
| 4.0 | **2 of 33** |
| 5.0 | **2 of 35** |
| 6.0 | **2 of 35** |
| 7.0 | **29 of 48** |
| 11.0 | **5 of 33** |
| 10.0 | **13 of 33** |

Some of this is correct — Hekla at 62 km and Vestmannaeyjar at 28 km are things you
genuinely point at from a distance. The ones below are not.


## 7.0

| block | km from bus | pin | target |
|---|---|---|---|
| 🏚️ Höfðabrekka | 108 | 63.9736, -17.0948 | 63.4266, -18.9049 |
| 🧭 Ingólfur Arnarson | 61 | 63.9456, -20.7603 | 64.1478, -21.9329 |
| 🛡️ Markarfljót & Hlíðarendi | 49 | 63.5697, -19.8654 | 63.9514, -19.3586 |
| 🌋 Katla | 47 | 63.7551, -18.1353 | 63.6333, -19.0500 |
| 🏡 Keldur | 44 | 63.7511, -20.2230 | 63.9565, -19.4440 |
| 🛡️ Hjörleifshöfði | 36 | 63.6848, -18.3577 | 63.4151, -18.7434 |
| ⛪ Víkurkirkja | 34 | 63.6041, -18.4629 | 63.4205, -19.0029 |
| 🌊 Reynisfjara & Reynisdrangar | 31 | 63.5154, -18.4828 | 63.4044, -19.0588 |
| 🐦 Vestmannaeyjar | 28 | 63.6777, -20.1549 | 63.4267, -20.2699 |
| 🧭 Ingólfshöfði | 27 | 64.0109, -16.3876 | 63.8006, -16.6472 |
| 🚪 Dýrhólaey | 25 | 63.4539, -18.6451 | 63.3988, -19.1266 |
| ⛰️ Rauðhólar | 25 | 64.0178, -21.2802 | 64.0953, -21.7553 |
| Orustuhóll | 23 | 63.9402, -17.3694 | 63.8594, -17.8117 |
| 🏞️ Elliðaárdalur & Paradísardalur | 22 | 64.0189, -21.4037 | 64.1128, -21.7999 |

## 11.0

| block | km from bus | pin | target |
|---|---|---|---|
| 🧙 Mávahlíð | 121 | 64.8959, -23.7085 | 64.1333, -21.9094 |
| ⛰️ Stapafell & Rauðfeldsgjá | 113 | 64.8303, -23.5020 | 63.9076, -22.5221 |
| ⛪ Búðir | 98 | 64.8044, -23.0803 | 64.0890, -21.9016 |
| 🦅 Löngufjörur | 46 | 64.3973, -21.8727 | 64.7538, -22.3724 |
| 🪨 Gerðuberg | 16 | 64.8486, -22.6842 | 64.8631, -22.3575 |

## 10.0

| block | km from bus | pin | target |
|---|---|---|---|
| 🦈 Bjarnarhöfn | 107 | 64.1377, -21.9343 | 64.9974, -22.9633 |
| ⛰️ Vatnaleið | 94 | 64.1377, -21.9343 | 64.8926, -22.8363 |
| 🌊 Kolgrafarfjörður | 93 | 64.3407, -21.8229 | 64.9601, -23.1213 |
| 💪 Djúpalónssandur & Dritvík | 78 | 64.7651, -22.2670 | 64.7521, -23.9032 |
| ⛪ Hellissandur, Ingjaldshóll & the Columbus Story | 76 | 64.7888, -22.2666 | 64.9078, -23.8524 |
| 🧙 Mávahlíð | 73 | 64.7693, -22.2669 | 64.1333, -21.9094 |
| ⚓ Ólafsvík | 70 | 64.7693, -22.2669 | 64.8942, -23.7108 |
| 🛁 Bárðarlaug | 67 | 64.7720, -22.2669 | 64.7589, -23.6799 |
| 🔪 Axlar-Björn | 57 | 64.7720, -22.2669 | 64.8267, -23.4553 |
| 🪨 Berserkjahraun | 55 | 64.6502, -22.0634 | 64.9631, -22.9711 |
| ⛰️ Kirkjufell | 53 | 64.7693, -22.2669 | 64.9399, -23.3075 |
| 🌋 Eldborg | 39 | 64.7720, -22.2669 | 64.8030, -23.0810 |
| 🐚 Búlandshöfði | 28 | 64.9372, -22.9020 | 64.9437, -23.4872 |

## The clearest faults

- **10.0** — Bjarnarhöfn, Helgafell and Vatnaleið are all pinned at **64.1377, -21.9343**, which is BSÍ Bus Terminal. They fire as the coach pulls out of Reykjavík, about 180 km early.
- **10.0** — Ólafsvík, Mávahlíð and Kirkjufell share one pin roughly 70 km short of all three.
- **11.0** — Mávahlíð's target is **64.1333, -21.9094**, in Reykjavík, 120 km from the bus. Stapafell & Rauðfeldsgjá points at **63.9076, -22.5221**, on the Reykjanes peninsula.
- **7.0** — Höfðabrekka fires near Skaftafell and points 108 km back to Vík.

## How to check your work

```
python3 _sightline.py 10.0        # side and o'clock at the pin AND beside the thing
python3 _pinaudit.py 10.0         # drop-one test: what each waypoint costs the route
```

`_sightline.py` prints two answers per cue. When they disagree the pin is early, and it says by how many km. When the pins are right those two answers agree.
