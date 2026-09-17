#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_factclash.py — read-only. Of the blocks two tours both carry, separate the
differences that are FACTS from the differences that are STAGING.

Two tours can legitimately word the same block differently when one of them
stops there and the other drives past: "our late-morning stop" belongs in the
tour that actually goes, and must never be pushed into the transfer. That is
not drift, it is correct authorship.

What is never legitimate is the two copies disagreeing about a NUMBER. So this
pulls every figure out of each side and reports only where the sets differ.

  python3 _factclash.py 12.0 13.0
"""
import re, sys, glob, os, unicodedata
sys.path.insert(0, "/Users/ritchiej/Documents/iGuide-deploy")
import _blocklib

DIR = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/"
A, B = sys.argv[1], sys.argv[2]
NUM = re.compile(r'\d[\d.,]*\s?(?:km²|km|m²|m|%|°C|MW|CE|BCE)?')
STAGING = re.compile(r'today|later|before lunch|our .*stop|this morning|this afternoon|we will|you will|stay on|weather pivot', re.I)

def key(t):
    t = re.sub(r'^\s*>\s*###\s+[\d.]+\s*', '', t).strip()
    t = re.sub(r'[\s📜🔀🌍🎣]+$', '', t).split("—")[0]
    k = "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if c.isalnum() or c == " ")
    return re.sub(r'\s+', ' ', k).strip()

def load(tag):
    p = [q for q in glob.glob(DIR + "*.md") if os.path.basename(q).startswith(tag + " ")][0]
    L = open(p, encoding="utf-8").read().split("\n")
    out = {}
    for (s, e, ind, num, head) in _blocklib.regions(L):
        body = [x.strip() for x in L[s+1:e]
                if x.strip() and not x.strip().startswith("> *")]
        out[key(head)] = body
    return out

a, b = load(A), load(B)
clash = staged = clean = 0
for k in sorted(set(a) & set(b)):
    if a[k] == b[k]:
        clean += 1; continue
    na = set(m.group(0).strip() for m in NUM.finditer(" ".join(a[k])))
    nb = set(m.group(0).strip() for m in NUM.finditer(" ".join(b[k])))
    onlyA, onlyB = na - nb, nb - na
    if not onlyA and not onlyB:
        staged += 1
        print("STAGING ONLY  %-34s  same figures, different delivery" % k[:34])
        continue
    clash += 1
    print("\nFIGURES DIFFER  %s" % k)
    print("   only in %s : %s" % (A, ", ".join(sorted(onlyA)) or "-"))
    print("   only in %s : %s" % (B, ", ".join(sorted(onlyB)) or "-"))
    for side, other, tag in ((a[k], b[k], A), (b[k], a[k], B)):
        for l in side:
            if l in other: continue
            if not NUM.search(l): continue
            if STAGING.search(l): continue
            print("   [%s] %s" % (tag, l[:150]))
print("\n%d identical, %d differ by staging only, %d have figure differences"
      % (clean, staged, clash))
