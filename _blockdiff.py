#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_blockdiff.py "<title>" 9.0 10.0 [...]  — show what actually differs between
two or more tours' versions of the same block, in the BUILT js.

Slicing rules copied from _mergecheck.py, because getting them wrong is how you
convince yourself a block differs when it does not:
  * cut at the next block opener
  * ALSO cut at the next SECTION opener  ('\\n{title:"')
  * strip trailing close-punctuation
  * ignore the id field (each tour numbers its own blocks)
"""
import re, sys, difflib

BLOCK = re.compile(r'\{id:"([\d.]+)",\s*title:"((?:[^"\\]|\\.)*)"')


def blocks(n):
    s = open("script-%s.js" % n, encoding="utf-8").read()
    out = {}
    ms = list(BLOCK.finditer(s))
    for k, m in enumerate(ms):
        i = m.start()
        j = ms[k + 1].start() if k + 1 < len(ms) else len(s)
        body = s[i:j]
        body = re.split(r'\n\{title:"', body)[0]
        body = re.sub(r'(?:[\s\]\},]*)$', "", body)
        out[m.group(2)] = re.sub(r'^\{id:"[^"]*",\s*', "{", body)
    return out


if __name__ == "__main__":
    title = sys.argv[1]
    tours = sys.argv[2:]
    got = {}
    for t in tours:
        b = blocks(t)
        if title not in b:
            print("%s: NOT PRESENT" % t)
        else:
            got[t] = b[title]
    ref = tours[0]
    for t in tours[1:]:
        if t not in got or ref not in got:
            continue
        if got[t] == got[ref]:
            print("%s == %s  (identical)" % (ref, t))
            continue
        print("\n===== %s vs %s =====" % (ref, t))
        for line in difflib.unified_diff(got[ref].split(",\n"), got[t].split(",\n"),
                                         ref, t, lineterm="", n=0):
            print(line[:500])
