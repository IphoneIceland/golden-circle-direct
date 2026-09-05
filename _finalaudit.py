#!/usr/bin/env python3
"""Final audit of one tour before it goes on the mic.

Not a rerun of the other tools — this checks the things they do not:
  1. schema completeness, per block, every field
  2. sightline coverage and pin sanity
  3. Threads index integrity
  4. DUPLICATE SUBJECTS — is anything said twice, in different blocks?
  5. repeated distinctive figures, which usually means a fact got copied
  6. Mac vs LIVE byte-identical

Usage: python3 _finalaudit.py 5.0
"""
import json, os, re, subprocess, sys, math, collections

TAG  = sys.argv[1] if len(sys.argv) > 1 else "5.0"
HERE = os.path.dirname(os.path.abspath(__file__))
bad  = []

sc = open(os.path.join(HERE, "script-%s.js" % TAG), encoding="utf-8").read()

# ---------------------------------------------------------------- 1. schema
blocks = []
for m in re.finditer(r'\{id:"(%s\.\d+\.\d+)",' % re.escape(TAG), sc):
    nxt = sc.find('{id:"%s.' % TAG, m.end())
    seg = sc[m.start():nxt if nxt > 0 else len(sc)]
    g = lambda k: re.search(r'\b%s:"((?:[^"\\]|\\.)*)"' % k, seg)
    blocks.append({
        "id": m.group(1),
        "title": (g("title").group(1) if g("title") else ""),
        "cue": (g("cue").group(1) if g("cue") else ""),
        "hook": (g("hook").group(1) if g("hook") else ""),
        "point": (g("point").group(1) if g("point") else ""),
        "mic": (g("mic").group(1) if g("mic") else ""),
        "weather": (g("weather").group(1) if g("weather") else ""),
        "bullets": len(re.findall(r'\n  "', seg)),
        "say": seg.count('["'),
        "seg": seg})
print("%s — %d blocks\n" % (TAG, len(blocks)))

print("1. SCHEMA")
for b in blocks:
    miss = [k for k in ("cue", "hook", "point", "mic", "weather") if not b[k]]
    music = "Music Leg" in b["title"]
    if music:
        miss = [k for k in miss if k in ("cue",)]
    if miss:
        print("   %-11s %-34s missing: %s" % (b["id"], b["title"][:33], ", ".join(miss)))
        bad.append((b["id"], "missing " + ",".join(miss)))
if not any(x[1].startswith("missing") for x in bad):
    print("   every block has cue, hook, point, mic and weather pivot")

# ---------------------------------------------------------------- 2. cues
cu = open(os.path.join(HERE, "cues-%s.js" % TAG), encoding="utf-8").read()
CUES = json.loads(cu[cu.index("["):cu.rindex("]") + 1])
byid = {c["id"]: c for c in CUES}
print("\n2. CUES AND SIGHTLINES")
nocue = [b["id"] for b in blocks if b["id"] not in byid]
nosight = [c["id"] for c in CUES if not c.get("target")]
prev, back = -1, []
for c in CUES:
    if c["progress"] < prev - 0.01:
        back.append(c["id"])
    prev = c["progress"]
print("   %d cues, %d sightlines, no cue: %s, no sightline: %s, backwards: %s"
      % (len(CUES), len(CUES) - len(nosight), nocue or "none",
         [i for i in nosight] or "none", back or "none"))
for i in nosight:
    t = next((b["title"] for b in blocks if b["id"] == i), "?")
    if "Music" not in t:
        bad.append((i, "no sightline")); print("   !! %s %s has no sightline" % (i, t))
if nocue or back:
    bad.append(("cues", "missing or backwards"))

# ---------------------------------------------------------------- 3. threads
print("\n3. THREADS")
secs = re.findall(r'\{title:"([^"]+)", tag:"(#\w+)"', sc)
rows = len(re.findall(r'\["[^"]*","%s\.[\d.]+","' % re.escape(TAG), sc))
tagged = sum(1 for b in blocks if "Music" not in b["title"])
print("   %d sections, %d index rows, %d non-music blocks" % (len(secs), rows, tagged))

# ---------------------------------------------------------------- 4. dupes
print("\n4. DUPLICATE SUBJECTS")
STOP = set("""the a an and or of in on at to for is are was were it its this that with
from by as be been has have had not but they them their we you your our will would
can could one two three about into over under after before then than there here""".split())
words = {}
for b in blocks:
    txt = re.sub(r'[^A-Za-zÀ-ÿÞþÐðÆæÖö ]', ' ', b["seg"]).lower()
    caps = set(w for w in re.findall(r'\b[A-ZÞÐÆÖ][a-zà-ÿþðæö]{4,}\b', b["seg"]))
    words[b["id"]] = (b["title"], caps)
seen = collections.defaultdict(list)
for bid, (title, caps) in words.items():
    for c in caps:
        seen[c].append(bid)
noisy = {"Iceland", "Icelandic", "Reykjavik", "Reykjavík", "Look", "Every", "Behind",
         "Landsvirkjun", "Weather", "Their", "There", "These", "Where", "Which",
         "About", "After", "Before", "Þjórsá", "Route", "South", "North"}
hits = [(c, v) for c, v in seen.items() if len(v) > 2 and c not in noisy]
for c, v in sorted(hits, key=lambda x: -len(x[1]))[:10]:
    names = [words[i][0][:22] for i in v]
    print("   %-18s in %d blocks: %s" % (c, len(v), ", ".join(names)))
if not hits:
    print("   no proper noun appears in more than two blocks")

# ---------------------------------------------------------------- 5. figures
print("\n5. REPEATED DISTINCTIVE FIGURES  (a copied fact usually shows up here)")
fig = collections.defaultdict(set)
for b in blocks:
    for n in re.findall(r'\b\d[\d,\.]{2,}\b', b["seg"]):
        if len(n.replace(",", "").replace(".", "")) >= 3:
            fig[n].add(b["id"])
rep = {k: v for k, v in fig.items() if len(v) > 1}
for k, v in sorted(rep.items(), key=lambda x: -len(x[1]))[:8]:
    print("   %-10s %s" % (k, ", ".join(sorted(v))))
if not rep:
    print("   none")

# ---------------------------------------------------------------- 6. live
print("\n6. MAC vs LIVE")
for f in ("script-%s.js" % TAG, "cues-%s.js" % TAG):
    live = subprocess.run(["curl", "-s", "-H", "Cache-Control: no-cache",
                           "https://www.iguideiceland.is/app/" + f],
                          capture_output=True, text=True).stdout
    mac = open(os.path.join(HERE, f), encoding="utf-8").read()
    ok = live.strip() == mac.strip()
    print("   %-18s %s" % (f, "identical" if ok else "DIFFERS"))
    if not ok:
        bad.append((f, "mac and live differ"))

print("\n%s" % ("PROBLEMS: " + "; ".join("%s %s" % x for x in bad) if bad else "NO PROBLEMS"))
