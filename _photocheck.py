#!/usr/bin/env python3
"""Does every drive block that COULD have a photo actually get one?  _photocheck.py

Written 16 Sep 2026 because I made the same mistake twice.

A photo is matched by photoKey() of the BLOCK TITLE. If one tour titles a block
"Kjalarnesþing" and another titles the same subject "Kjalarnes", the second gets
no picture and NOTHING SAYS SO — the card just renders without one. That is how
images/drive/ellidaardalur.webp sat unused for six days, and how kjalarnes.webp
shipped to four tours and missed the two that drive through the place.

Checking the tour you happen to be working on is not enough. This checks all of
them, every time, and shouts about three separate failures:

  1. a photo key that matches no block anywhere        (dead entry)
  2. a drive block with no photo whose title is a NEAR MATCH for a key that
     does exist                                        (the silent miss)
  3. a file in images/ that no key points at           (orphan file)
"""
import re, io, os, glob, unicodedata, sys

HERE = os.path.dirname(os.path.abspath(__file__))

def photo_key(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = t.replace("þ","th").replace("ð","d").replace("æ","ae")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 -]", " ", t)).strip()

h = io.open(os.path.join(HERE,"index.html"), encoding="utf-8").read()
seg = h[h.index("const STOPPHOTOS={"):]
seg = seg[:seg.index("};")]
KEYS = {m.group(1): m.group(2) for m in re.finditer(r'"([^"]+)":\s*\{src:"([^"]+)"', seg)}

blocks = {}   # key -> [(tour, title, kind)]
for f in sorted(glob.glob(os.path.join(HERE,"script-*.js"))):
    if ".bak" in f: continue
    tour = os.path.basename(f)[7:-3]
    s = io.open(f, encoding="utf-8").read()
    secs = [(m.group(1), m.group(2), m.start())
            for m in re.finditer(r'\{title:"((?:[^"\\]|\\.)*)",\s*kind:"(\w+)"', s)]
    for i,(st,kind,pos) in enumerate(secs):
        end = secs[i+1][2] if i+1 < len(secs) else len(s)
        for m in re.finditer(r'\{id:"([\d.]+)", title:"((?:[^"\\]|\\.)*)"', s[pos:end]):
            blocks.setdefault(photo_key(m.group(2)), []).append((tour, m.group(2), kind))

bad = 0

dead = [k for k in KEYS if k not in blocks]
if dead:
    bad += len(dead)
    print("DEAD PHOTO KEYS — match no block on any tour:")
    for k in dead: print("   %-32s -> %s" % (k, KEYS[k]))

print()
# Deliberate, checked, and NOT faults:
#   krysuvikurkirkja  - a different church from Vikurkirkja; must not share a photo
#   olfusa intro      - same river as the Olfusa block two stops later; dedupe on purpose
#   hvolsvollur.webp  - a STOP block on 5.0/6.0/7.0, and photos are drive-only by design
ACCEPTED = {"krysuvikurkirkja", "olfusa intro"}
ACCEPTED_ORPHANS = {"images/stops/hvolsvollur.webp"}

near = []
for k, v in sorted(blocks.items()):
    if k in KEYS or k in ACCEPTED: continue
    drives = sorted(set(x[0] for x in v if x[2] == "drive"))
    if not drives: continue
    for kk in KEYS:
        if k == kk: continue
        if k in kk or kk in k:
            near.append((k, drives, kk, KEYS[kk]))
            break
if near:
    print("SILENT MISSES — a drive block with no photo, next to a key that nearly matches:")
    for k, drives, kk, src in near:
        bad += 1
        print('   "%s" on %s has NO photo' % (k, ", ".join(drives)))
        print('        nearest key "%s" -> %s' % (kk, src))
else:
    print("SILENT MISSES: none")

print()
used = set(os.path.basename(v) for v in KEYS.values())
orphans = []
for d in ("images/drive", "images/stops"):
    p = os.path.join(HERE, d)
    if not os.path.isdir(p): continue
    for fn in sorted(os.listdir(p)):
        if fn.endswith(".webp") and fn not in used and (d+"/"+fn) not in ACCEPTED_ORPHANS:
            orphans.append(d + "/" + fn)
if orphans:
    bad += len(orphans)
    print("ORPHAN IMAGES — on disk, no key points at them:")
    for o in orphans: print("   ", o)
else:
    print("ORPHAN IMAGES: none")

print()
drive_total = sum(1 for v in blocks.values() for x in v if x[2] == "drive")
drive_with  = sum(1 for k,v in blocks.items() if k in KEYS for x in v if x[2] == "drive")
print("drive blocks across all tours: %d   with a photo: %d" % (drive_total, drive_with))
print("problems:", bad)
sys.exit(1 if bad else 0)
