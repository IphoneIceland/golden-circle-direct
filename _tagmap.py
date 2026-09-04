#!/usr/bin/env python3
import re, io
SRC = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/"
for name in ("9.0 Snæfellsnes North", "10.0 Snæfellsnes South"):
    raw = io.open(SRC + name + ".md", encoding="utf-8").read()
    body = re.split(r'^\s*\+? ?#{1,2} 🧵 Threads', raw, maxsplit=1, flags=re.M)[0]
    cur = None
    out = {}
    for ln in body.split("\n"):
        m = re.match(r'^\s*> ### (\d+\.\d+)\s+(.*)$', ln)
        if m:
            cur = (m.group(1), m.group(2).strip())
        m = re.match(r'^\s*🧵\s+(.*)$', ln)
        if m and cur:
            for tg in re.findall(r'#\w+', m.group(1)):
                out.setdefault(tg, []).append(cur)
    print("=" * 8, name)
    for tg in ("#saga", "#nature", "#food", "#film", "#history", "#language", "#safety", "#statehood"):
        if tg in out:
            print(tg, "->", "; ".join("%s %s" % x for x in out[tg]))
