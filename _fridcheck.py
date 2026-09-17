#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prove the Friðheimar block is byte-identical across 1.0-4.0 in the BUILT js,
ignoring only the id field (each tour numbers its own blocks).

Trap this file exists to avoid: slicing to the next '{id:"' runs past the end of
the block when the block is the LAST in its section — you then pick up the
section-closing braces and the next section's opener. Cut at the next SECTION
opener too, and strip trailing close-punctuation, exactly like _mergecheck.py.
"""
import re, hashlib, difflib

bodies = {}
for n in ["1.0", "2.0", "3.0", "4.0"]:
    s = open("script-%s.js" % n, encoding="utf-8").read()
    i = s.find("Reykholt & Friðheimar")
    if i < 0:
        print(n, "NOT FOUND")
        continue
    j = s.rfind('{id:"', 0, i)
    k = s.find('{id:"', i)
    body = s[j:k if k > 0 else len(s)]
    body = re.sub(r'^\{id:"[^"]*",', "{", body)
    body = re.split(r'\n\{title:"', body)[0]
    body = re.sub(r'(?:[\s\]\},]*)$', "", body)
    bodies[n] = body
    print(n, len(body), hashlib.sha256(body.encode("utf-8")).hexdigest()[:16])

ref = bodies["1.0"]
for n, b in bodies.items():
    if b != ref:
        print("\n--- %s differs from 1.0 ---" % n)
        for line in difflib.unified_diff(ref.split(","), b.split(","),
                                         "1.0", n, lineterm="", n=1):
            print(line[:300])
