#!/usr/bin/env python3
"""Which shared blocks still disagree between tours?  _mergecheck.py [--list]

The job Ritchie set on 17 Sep: every block that appears on more than one tour
must say THE SAME THING on all of them. This is the scoreboard for that, and
the audit that proves a merge actually landed.

What counts as "the same": the bullets, hook, point, mic, weather line and
pronunciation list. NOT the cue line and NOT the block id — the cue is the
sightline instruction, which is legitimately per-tour and is Ritchie's to set,
and ids are positional. A block whose only difference is its cue is MERGED.

Music legs are skipped: they are playlist markers, deliberately different.

Exit code is the number of blocks still unmerged, so it can gate a deploy.
"""
import re, io, os, glob, sys, unicodedata, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))

def norm_title(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = t.replace("þ", "th").replace("ð", "d").replace("æ", "ae")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 &]", " ", t)).strip()

def blocks(path):
    s = io.open(path, encoding="utf-8").read()
    ms = list(re.finditer(r'\{id:"([\d.]+)", title:"((?:[^"\\]|\\.)*)"', s))
    out = []
    # The LAST block in a file has no next block to stop at, so "to end of file"
    # swept the whole threads index into its body — and since every tour's
    # threads index is different, the last block on 1.0/2.0/3.0 could never hash
    # equal to the same block mid-file on 4.0-7.0. Rauðhólar reported "7 tours,
    # 4 versions, word spread 0" on 17 Sep: identical text, four hashes, purely
    # this artefact. Stop at the threads block instead.
    tail = s.find("\nthreadsIntro:")
    if tail < 0:
        tail = s.find("\nthreads:")
    if tail < 0:
        tail = len(s)
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else tail
        body = s[m.start():min(end, tail)]
        body = re.sub(r'cue:"(?:[^"\\]|\\.)*",', "", body)     # per-tour by design
        body = re.sub(r'\{id:"[\d.]+", ', "", body)            # ids are positional
        # ...and the LAST block of a SECTION carries that section's closing
        # "]}," / "]," while the same block mid-section does not. Structure, not
        # content. Trim any trailing run of pure punctuation/whitespace lines.
        body = re.sub(r'(?:\n[\s\]\},]*)+$', "", body)
        # ...and the last block of a section is followed by the NEXT SECTION'S
        # opener, `{title:"Geysir", kind:"stop", blocks:[`. That is the tour's
        # route structure, not the block, and it made Haukadalur report as
        # "4 tours, 2 versions, word spread 0" when all four were byte-identical.
        # Third variant of the same artefact. Cut at the section opener too.
        body = re.split(r'\n\{title:"', body)[0]
        body = re.sub(r'(?:\n[\s\]\},]*)+$', "", body)
        bl = re.search(r"bullets:\[(.*?)\n\s*\]", body, re.S)
        words = len(re.findall(r"\w+", bl.group(1))) if bl else 0
        sm = re.search(r'sub:"((?:[^"\\]|\\.)*)"', body)
        key = norm_title(m.group(2))
        if key in SPLIT_BY_SUB:
            key += " | " + norm_title(sm.group(1) if sm else "")
        out.append((key, m.group(2), hashlib.sha1(body.encode()).hexdigest()[:8], words))
    return out

# Two tours can title a block the same and mean COMPLETELY different things.
# "🐦 Vestmannaeyjar — Puffins, Ports and Plumes" on 5.0/6.0/7.0 is the 1973
# Eldfell eruption seen from the mainland. "🏝️ Vestmannaeyjar — The Isles of the
# West Men" on 8.0 is the Landnámabók naming story: Hjörleifur, the ox, the ten
# Gaels. Same word, different block. Grouping them made the scoreboard report a
# 558-word "spread" that no merge could ever close, because there is nothing to
# merge. For titles listed here, split the group by SUBTITLE as well.
# Add to this list only when the blocks are genuinely different subjects — not
# when they are the same subject with drifted subtitles, which IS merge work.
# 17 Sep 2026: "reykjavik" added for a DIFFERENT reason — not two tours meaning
# different things, but ONE tour carrying two genuinely different blocks with the
# same name. 14.0 opens with "🏛️ Reykjavík — The Brook, The Hill And The
# Forty-Five Years Of Silence" (Arnarhóll, the culverted Lækurinn, Alþingi's
# 1800-1845 closure, Hallgrímskirkja) at 14.1, and closes with
# "🏙️ Reykjavík — The Smoky Bay" (the name, the geothermal heat, tying off the
# day) at 14.28. Departure block and arrival block. There is nothing to merge and
# the 290-word "spread" between them could never be closed.
# ⚠️ SEPARATE ISSUE, NOT FIXED HERE: photoKey() strips the emoji, so BOTH of
# those titles key as "reykjavik" and the two blocks necessarily share one photo.
# That is a content decision for Ritchie, not a scoreboard bug.
SPLIT_BY_SUB = {"vestmannaeyjar", "reykjavik"}

shared = {}
for f in sorted(glob.glob(os.path.join(HERE, "script-*.js"))):
    if ".bak" in f:
        continue
    tour = os.path.basename(f)[7:-3]
    for key, title, h, w in blocks(f):
        shared.setdefault(key, []).append((tour, title, h, w))

unmerged, merged, solo = [], [], 0
for key, v in shared.items():
    if len(v) < 2:
        solo += 1
        continue
    if "music leg" in key:
        continue
    (unmerged if len({x[2] for x in v}) > 1 else merged).append((key, v))

unmerged.sort(key=lambda r: (-len(r[1]), -(max(x[3] for x in r[1]) - min(x[3] for x in r[1]))))

if "--list" in sys.argv:
    print(f"{'block':34s} {'tours':>5s} {'vers':>4s}  {'words min-max':>13s}  spread  on")
    print("-" * 104)
    for key, v in unmerged:
        ws = [x[3] for x in v]
        print(f"{v[0][1][:34]:34s} {len(v):5d} {len({x[2] for x in v}):4d}  "
              f"{min(ws):5d}-{max(ws):<7d} {max(ws)-min(ws):6d}  "
              f"{','.join(sorted({x[0] for x in v}))}")

print()
print(f"blocks on 2+ tours, already identical : {len(merged)}")
print(f"blocks on 2+ tours, still differing   : {len(unmerged)}")
print(f"blocks unique to one tour             : {solo}")
tot = len(merged) + len(unmerged)
if tot:
    print(f"merged: {len(merged)}/{tot}  ({100*len(merged)//tot}%)")
sys.exit(len(unmerged))
