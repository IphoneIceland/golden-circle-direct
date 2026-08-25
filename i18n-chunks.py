#!/usr/bin/env python3
"""
Split the corpus into even chunks for translation, one file per chunk.

  python3 i18n-chunks.py [n]        # default 3

Even by WORDS, not by count — a chunk of 200 one-line glosses and a chunk of
200 fact bullets are not the same job.
"""
import json, os, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
corpus = json.load(open("_tr/corpus.json", encoding="utf-8"))

total = sum(len(e["en"].split()) for e in corpus)
target = total / N
chunks, cur, cw = [], [], 0
for e in corpus:
    cur.append(e)
    cw += len(e["en"].split())
    if cw >= target and len(chunks) < N - 1:
        chunks.append(cur); cur, cw = [], 0
chunks.append(cur)

os.makedirs("_tr/chunks", exist_ok=True)
for i, c in enumerate(chunks, 1):
    p = "_tr/chunks/chunk-%d.json" % i
    with open(p, "w", encoding="utf-8") as f:
        json.dump([{"id": e["id"], "ctx": e["ctx"], "en": e["en"]} for e in c],
                  f, ensure_ascii=False, indent=1)
    print("%s  %3d strings  %5d words" % (p, len(c), sum(len(e["en"].split()) for e in c)))
