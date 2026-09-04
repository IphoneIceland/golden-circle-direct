#!/usr/bin/env python3
"""Threads index vs headings: does every cited number point at the stop the
index claims it does? build-any.py only checks the number exists, so a
renumber can silently repoint an entry at the wrong stop."""
import re, io, os, sys, unicodedata

SRC = os.path.expanduser("~/Documents/RitchWiki/Tour Scripts")
DOCS = ["1.0 Golden Circle Direct", "2.0 Golden Circle Snowmobiling",
        "3.0 Golden Circle Lagoons", "4.0 Golden Circle Friðheimar",
        "5.0 South Coast", "6.0 South Coast Combo", "7.0 Glacial Lagoon",
        "9.0 Snæfellsnes North", "10.0 Snæfellsnes South"]

def norm(s):
    s = re.sub(r'[\*_`]', '', s)
    s = "".join(c for c in s if not unicodedata.category(c).startswith("S"))
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s

bad = 0
for name in DOCS:
    raw = io.open("%s/%s.md" % (SRC, name), encoding="utf-8").read()
    parts = re.split(r'^\s*\+? ?#{1,2} 🧵 Threads', raw, maxsplit=1, flags=re.M)
    body, thr = parts[0], (parts[1] if len(parts) > 1 else "")
    heads = {}
    for m in re.finditer(r'(?m)^\s*>? ?#{3}\s+(\d+\.\d+)\s+(.*)$', body):
        heads[m.group(1)] = m.group(2).strip()
    if not thr:
        print("%-24s NO THREADS INDEX (%d stops)" % (name, len(heads)))
        continue
    probs = []
    for m in re.finditer(r'(?m)^\s*[-*]\s+(\d+\.\d+)\s+([^—–]+)[—–]', thr):
        no, label = m.group(1), m.group(2).strip()
        if no not in heads:
            probs.append("%s DEAD" % no); continue
        h = norm(heads[no]).split(" — ")[0].split(" – ")[0]
        if norm(label) not in h and h not in norm(label):
            probs.append("%s index=%r heading=%r" % (no, label, heads[no]))
    if probs:
        bad += len(probs)
        print("%-24s %d MISMATCH" % (name, len(probs)))
        for p in sorted(set(probs)): print("      ", p)
    else:
        print("%-24s ok" % name)
print("total mismatches: %d" % bad)
