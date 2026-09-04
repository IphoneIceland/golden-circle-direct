#!/usr/bin/env python3
"""Write _tr/out/<lang>-15.jsonl from the per-language lists in _tr15_<batch>.py.
Order must match _tr/chunks/chunk-15.json exactly."""
import json, io, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
IDS = [e["id"] for e in json.load(open("_tr/chunks/chunk-15.json", encoding="utf-8"))]
EN = {e["id"]: e["en"] for e in json.load(open("_tr/chunks/chunk-15.json", encoding="utf-8"))}

def write(lang, lines):
    assert len(lines) == len(IDS), "%s: %d lines, want %d" % (lang, len(lines), len(IDS))
    p = "_tr/out/%s-15.jsonl" % lang
    with io.open(p, "w", encoding="utf-8") as f:
        for i, t in zip(IDS, lines):
            assert t.strip(), "%s: empty for %s" % (lang, i)
            f.write(json.dumps({"id": i, "t": t}, ensure_ascii=False) + "\n")
    print("wrote", p, len(lines))
