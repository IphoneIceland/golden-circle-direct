#!/usr/bin/env python3
"""Apply weather pivots to the .md manuscripts, keyed by block title.

Two sources:
  1. pivots already written on another tour — copied across verbatim, so the
     same stop reads the same way whichever tour a guest is on
  2. _wxnew.tsv, one "title<TAB>line" per row, for blocks that had none anywhere

The line goes in after the 🎤 mic drop, at the document's own indentation.
Blocks that already have one, and Music Legs, are never touched.

Usage: python3 _wxapply.py [--write]
"""
import os, re, sys, shutil, collections

WRITE = "--write" in sys.argv
HERE  = os.path.dirname(os.path.abspath(__file__))
D     = os.path.expanduser("~/Documents/RitchWiki/Tour Scripts")

DOC = {"1.0": "1.0 Golden Circle Direct", "2.0": "2.0 Golden Circle Snowmobiling",
       "3.0": "3.0 Golden Circle Lagoons", "4.0": "4.0 Golden Circle Friðheimar",
       "5.0": "5.0 South Coast", "6.0": "6.0 South Coast Combo",
       "7.0": "7.0 Glacial Lagoon", "9.0": "9.0 Snæfellsnes North",
       "10.0": "10.0 Snæfellsnes South", "14.0": "14.0 Reykjanes South Loop"}

def indent_of(s):
    """Manuscripts are indented 0, 2, 4 or 6 spaces depending on when they were
    written. Read it off the headings rather than assuming."""
    m = re.search(r'^([ \t]*)> ### ', s, re.M)
    return m.group(1) if m else ""

def key(title):
    return re.sub(r'^[^\wÀ-ÿÞþÐðÆæÖö]+', '', title).split(" — ")[0].strip()

# ---- harvest every pivot that already exists anywhere -------------------
WX = {}
for t, name in DOC.items():
    p = os.path.join(D, name + ".md")
    if not os.path.exists(p):
        continue
    s = open(p, encoding="utf-8").read()
    ind = indent_of(s)
    for m in re.finditer(r'^%s> ### (?:[\d.]+ )?(.*)$' % re.escape(ind), s, re.M):
        nxt = s.find("\n%s> ### " % ind, m.end())
        body = s[m.end():nxt if nxt > 0 else len(s)]
        w = re.search(r'^%s🌫️ (.*)$' % re.escape(ind), body, re.M)
        if w:
            WX.setdefault(key(m.group(1)), w.group(1).strip())
print("harvested %d existing pivots" % len(WX))

tsv = os.path.join(HERE, "_wxnew.tsv")
if os.path.exists(tsv):
    n = 0
    for line in open(tsv, encoding="utf-8"):
        if "\t" not in line:
            continue
        k, v = line.rstrip("\n").split("\t", 1)
        if k.strip() and k.strip() not in WX:
            WX[k.strip()] = 'Weather pivot: "%s"' % v.strip().strip('"')
            n += 1
    print("loaded %d new pivots from _wxnew.tsv" % n)

# ---- apply ---------------------------------------------------------------
total = 0
for t, name in DOC.items():
    p = os.path.join(D, name + ".md")
    if not os.path.exists(p):
        continue
    s = open(p, encoding="utf-8").read()
    ind = indent_of(s)
    added, missing = 0, []
    for m in list(re.finditer(r'^%s> ### (?:[\d.]+ )?(.*)$' % re.escape(ind), s, re.M))[::-1]:
        title = m.group(1)
        nxt = s.find("\n%s> ### " % ind, m.end())
        end = nxt if nxt > 0 else len(s)
        body = s[m.end():end]
        if "🌫️" in body or "Music Leg" in title:
            continue
        k = key(title)
        if k not in WX:
            missing.append(k)
            continue
        mm = re.search(r'^%s🎤 .*$' % re.escape(ind), body, re.M)
        if not mm:
            missing.append(k + " (no mic line)")
            continue
        at = m.end() + mm.end()
        s = s[:at] + "\n\n" + ind + "🌫️ " + WX[k] + s[at:]
        added += 1
    total += added
    print("  %-30s +%d%s" % (name, added,
          ("   still none: %d" % len(missing)) if missing else ""))
    if WRITE and added:
        shutil.copy2(p, p + ".bak-2026-09-05-wx")
        open(p, "w", encoding="utf-8").write(s)
print("\n%d pivots applied%s" % (total, "" if WRITE else "  (dry run)"))
