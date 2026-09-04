#!/usr/bin/env python3
import json, io, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
CH = json.load(open("_tr/chunks/chunk-16.json", encoding="utf-8"))
IDS = [e["id"] for e in CH]
EN = {e["id"]: e["en"] for e in CH}

def write(lang, lines):
    assert len(lines) == len(IDS), "%s: %d lines, want %d" % (lang, len(lines), len(IDS))
    bad = []
    for i, t in zip(IDS, lines):
        assert t.strip(), "%s: empty %s" % (lang, i)
        if EN[i].count("**") != t.count("**"):
            bad.append("%s bold %d vs %d" % (i, EN[i].count("**"), t.count("**")))
        if any(ch.isdigit() for ch in EN[i]) and not any(ch.isdigit() for ch in t):
            bad.append("%s lost its numbers" % i)
    assert not bad, "%s: %s" % (lang, "; ".join(bad))
    with io.open("_tr/out/%s-16.jsonl" % lang, "w", encoding="utf-8") as f:
        for i, t in zip(IDS, lines):
            f.write(json.dumps({"id": i, "t": t}, ensure_ascii=False) + "\n")
    print("wrote _tr/out/%s-16.jsonl" % lang, len(lines))
