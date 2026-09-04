#!/usr/bin/env python3
"""List (tag, stop) pairs a document's blocks claim but the Threads index does not carry."""
import re, io, sys
SRC = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/"
NORM = {"#saga": "#literature", "#nature": "#wildlife"}
name = sys.argv[1]
raw = io.open(SRC + name + ".md", encoding="utf-8").read()
parts = re.split(r'^\s*\+? ?#{1,2} 🧵 Threads', raw, maxsplit=1, flags=re.M)
body, thr = parts[0], (parts[1] if len(parts) > 1 else "")

blocks, cur = [], None
for ln in body.split("\n"):
    m = re.match(r'^\s*> ### (\d+\.\d+)\s+(.*)$', ln)
    if m:
        cur = {"no": m.group(1), "title": m.group(2).strip(), "tags": []}
        blocks.append(cur)
    m = re.match(r'^\s*🧵\s+(.*)$', ln)
    if m and cur:
        cur["tags"] = [NORM.get(t, t) for t in re.findall(r'#\w+', m.group(1))]

have, tag = set(), None
for ln in thr.split("\n"):
    m = re.match(r'^\s*### .*?(#\w+)\s*$', ln)
    if m:
        tag = m.group(1); continue
    m = re.match(r'^\s*[-*]\s+(\d+\.\d+)\s', ln)
    if m and tag:
        have.add((tag, m.group(1)))

by_tag = {}
for b in blocks:
    for t in b["tags"]:
        by_tag.setdefault(t, []).append(b)
for t in sorted(by_tag, key=lambda x: -len(by_tag[x])):
    miss = [b for b in by_tag[t] if (t, b["no"]) not in have]
    if miss:
        print("%-14s missing %d:" % (t, len(miss)))
        for b in miss:
            print("     %-7s %s" % (b["no"], b["title"]))
