#!/usr/bin/env python3
"""
Split the corpus into even chunks for translation, one file per chunk.

  python3 i18n-chunks.py --missing [n]   # DEFAULT WAY TO USE THIS. Chunks only
                                         # the ids no existing chunk covers,
                                         # into FRESH chunk numbers. Safe.
  python3 i18n-chunks.py [n] --force     # re-partition the WHOLE corpus into
                                         # chunk-1..n. Destructive, see below.

Even by WORDS, not by count — a chunk of 200 one-line glosses and a chunk of
200 fact bullets are not the same job.

WHY --force EXISTS AND WHY YOU ALMOST NEVER WANT IT (17 Sep 2026)
Translated output lives in _tr/out/<lang>-<chunk>.jsonl and i18n-build.py
validates each output line against the id ORDER of the chunk file it claims to
come from. Re-partitioning chunk-1..3 therefore invalidates every <lang>-1..3
output at once: the build reports "N ids not from this chunk — corrupt file"
for all twenty languages and refuses to write. Nothing is actually corrupt —
the chunk file moved underneath the translations. Recovered with
`git checkout -- _tr/chunks/chunk-1.json ...`, but only because this is a repo.
Chunk files are append-only history, not a scratch partition. Add work as NEW
chunk numbers; never rewrite one a translator has already answered.
"""
import json, os, sys, glob

os.chdir(os.path.dirname(os.path.abspath(__file__)))
args    = [a for a in sys.argv[1:] if not a.startswith("--")]
MISSING = "--missing" in sys.argv
FORCE   = "--force"   in sys.argv
N = int(args[0]) if args else 3

corpus = json.load(open("_tr/corpus.json", encoding="utf-8"))
existing = sorted(int(p.split("-")[-1][:-5]) for p in glob.glob("_tr/chunks/chunk-*.json"))

if MISSING:
    covered = set()
    for n in existing:
        for e in json.load(open("_tr/chunks/chunk-%d.json" % n, encoding="utf-8")):
            covered.add(e["id"])
    corpus = [e for e in corpus if e["id"] not in covered]
    first  = (max(existing) + 1) if existing else 1
    if not corpus:
        print("nothing unchunked — every corpus id is already in a chunk file")
        sys.exit(0)
    print("%d unchunked strings -> new chunks starting at %d" % (len(corpus), first))
else:
    first = 1
    clash = [n for n in existing if n <= N]
    if clash and not FORCE:
        sys.exit("REFUSING: this would overwrite chunk-%s, which translations in "
                 "_tr/out already answer. Use --missing to chunk only new strings, "
                 "or --force if you really mean to re-partition everything."
                 % ", chunk-".join(str(n) for n in clash))

total  = sum(len(e["en"].split()) for e in corpus)
target = total / N
chunks, cur, cw = [], [], 0
for e in corpus:
    cur.append(e)
    cw += len(e["en"].split())
    if cw >= target and len(chunks) < N - 1:
        chunks.append(cur); cur, cw = [], 0
chunks.append(cur)

os.makedirs("_tr/chunks", exist_ok=True)
for i, c in enumerate(chunks, first):
    p = "_tr/chunks/chunk-%d.json" % i
    with open(p, "w", encoding="utf-8") as f:
        json.dump([{"id": e["id"], "ctx": e["ctx"], "en": e["en"]} for e in c],
                  f, ensure_ascii=False, indent=1)
    print("%s  %3d strings  %5d words" % (p, len(c), sum(len(e["en"].split()) for e in c)))
