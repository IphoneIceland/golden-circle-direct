#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_pairdiff.py — read-only. Show what actually differs between two tours' copies
of the same block, body only, with the per-tour cue stripped out.

  python3 _pairdiff.py 12.0 13.0            # every shared subject that differs
  python3 _pairdiff.py 12.0 13.0 grindavik  # just one

The cue is per-tour by design and is never a difference worth merging, so it is
removed before comparing. What is left is the part that must agree: the hook,
the facts, the point, the mic line and the pronunciation list.
"""
import re, sys, difflib, unicodedata, glob, os
sys.path.insert(0, "/Users/ritchiej/Documents/iGuide-deploy")
import _blocklib

DIR = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/"
A, B = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3].lower() if len(sys.argv) > 3 else None

def path_for(tag):
    hits = [p for p in glob.glob(DIR + "*.md") if os.path.basename(p).startswith(tag + " ")]
    if not hits: sys.exit("no manuscript for " + tag)
    return hits[0]

def key(t):
    t = re.sub(r'^\s*>\s*###\s+[\d.]+\s*', '', t).strip()
    t = re.sub(r'[\s📜🔀🌍🎣]+$', '', t)
    t = t.split("—")[0]
    k = "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if c.isalnum() or c == " ")
    return re.sub(r'\s+', ' ', k).strip()

def load(tag):
    p = path_for(tag)
    L = open(p, encoding="utf-8").read().split("\n")
    out = {}
    for (s, e, ind, num, head) in _blocklib.regions(L):
        body = []
        for x in L[s+1:e]:
            t = x.strip()
            if not t: continue
            if t.startswith("> *") or t.startswith("*(") : continue   # the cue / provenance
            body.append(t)
        out[key(head)] = {"num": num, "head": head.strip(), "body": body}
    return out

a, b = load(A), load(B)
shared = [k for k in a if k in b]
diff = [k for k in shared if a[k]["body"] != b[k]["body"]]
print("%s: %d blocks | %s: %d blocks | shared %d | body differs on %d"
      % (A, len(a), B, len(b), len(shared), len(diff)))
for k in diff:
    if ONLY and ONLY not in k: continue
    print("\n" + "=" * 72)
    print("%s  |  %s   vs   %s" % (k, a[k]["num"], b[k]["num"]))
    print("=" * 72)
    for l in difflib.unified_diff(a[k]["body"], b[k]["body"], A, B, lineterm="", n=0):
        if l.startswith("@@"): continue
        print(l)
