#!/usr/bin/env python3
"""Consolidate: old packs (h32-keyed) + agent jsonl outputs -> canonical per-chunk out/<L>-<n>.jsonl"""
import json, os, glob, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)

def h32(s):
    x = 0x811c9dc5
    for b in s.encode("utf-8"):
        x ^= b
        x = (x * 0x01000193) & 0xFFFFFFFF
    return format(x, "08x")

corpus = json.load(open(f"{ROOT}/corpus.json"))
EN = {e["id"]: e["en"] for e in corpus}

chunks = {}
for f in sorted(glob.glob(f"{ROOT}/chunks/chunk-*.json")):
    n = int(re.search(r"chunk-(\d+)", f).group(1))
    chunks[n] = [e["id"] for e in json.load(open(f))]

LANGS = sorted({os.path.basename(p).split("-")[0]
                for p in glob.glob(f"{ROOT}/agentdone/*.jsonl")}
               | {os.path.basename(p)[:-3] for p in glob.glob(f"{REPO}/i18n/tours/*.js")})

report = []
for L in LANGS:
    m = {}
    # 1. seed from existing built pack, keyed by h32(en)
    pk = f"{REPO}/i18n/tours/{L}.js"
    if os.path.exists(pk):
        s = open(pk).read()
        mm = re.search(r"window\.__TR__\.[A-Za-z_-]+\s*=\s*", s)
        start = s.index("{", mm.end())
        pack = json.loads(s[start: s.rindex("}") + 1])
        for cid, en in EN.items():
            t = pack.get(h32(en))
            if t:
                m[cid] = t
    # 2. overlay existing out/*.jsonl (id-keyed, from earlier rounds)
    for f in sorted(glob.glob(f"{ROOT}/out/{L}-*.jsonl")):
        for line in open(f):
            line = line.strip()
            if not line: continue
            d = json.loads(line)
            if d.get("t"): m[d["id"]] = d["t"]
    # 3. overlay this run's agent outputs (highest priority)
    for f in sorted(glob.glob(f"{ROOT}/agentdone/{L}-p*.jsonl")):
        for line in open(f):
            line = line.strip()
            if not line: continue
            d = json.loads(line)
            if d.get("t"): m[d["id"]] = d["t"]
    # 4. emit chunk-aligned canonical files
    total = 0
    for n, ids in sorted(chunks.items()):
        rows = [{"id": i, "t": m[i]} for i in ids if i in m]
        total += len(rows)
        with open(f"{ROOT}/out/{L}-{n}.jsonl", "w") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    cov = 100.0 * total / len(corpus)
    report.append((L, total, len(corpus), cov))
    print(f"{L}: {total}/{len(corpus)}  {cov:.1f}%")

print()
bad = [r for r in report if r[3] < 100.0]
print("BELOW 100%:", [(r[0], r[1], f"{r[3]:.1f}%") for r in bad] or "none")
