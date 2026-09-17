#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_applyplan.py — apply a tour-plan.json from the backoffice matrix.

WHAT THIS IS FOR
The backoffice has a block x tour matrix: tick a box and that block is on that
tour. Saving downloads `tour-plan.json` whose own note says
"Apply with: python3 _applyplan.py tour-plan.json" — and until 17 Sep 2026 that
script did not exist, so every plan was a dead end. This is the missing half.

  python3 _applyplan.py tour-plan.json            # dry run, shows every edit
  python3 _applyplan.py tour-plan.json --write    # apply, backing each file up

WHAT IT DOES
  add    render the library's copy of the block into that tour's manuscript,
         in that file's own indentation, and renumber the tour
  remove cut the block out of that manuscript and renumber the tour

THE PER-TOUR VOICE IS RESPECTED. A block carries `overrides` for the hook, point,
mic and subtitle, and `cuePerTour` for the look-here line, because a tour that
STOPS somewhere words it differently from one that drives past. Adding a block
to a new tour inherits the shared base; it never copies another tour's staging.
The new tour's cue is left as a TODO marker rather than invented — a sightline is
Ritchie's call and guessing one would put "look left" on the wrong window.

WHAT IT REFUSES TO DO
  - add a block to a tour that already has it
  - remove a block that is not there
  - touch a manuscript that does not parse cleanly afterwards
Every file is re-parsed after the edit and the block count checked before the
write is kept. Edits are collected and applied in REVERSE line order, because
every write that changes the number of lines invalidates every index after it
(_blocklib's founding law).
"""
import json, os, re, shutil, sys, glob, datetime

sys.path.insert(0, "/Users/ritchiej/Documents/iGuide-deploy")
import _blocklib as B

GCD   = "/Users/ritchiej/Documents/golden-circle-direct/"
MS    = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/"
STAMP = ".bak-applyplan-" + datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
WRITE = "--write" in sys.argv
args  = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    sys.exit(__doc__)

plan = json.load(open(args[0], encoding="utf-8"))
BOOK = json.load(open(GCD + "_blocks/blocks.json", encoding="utf-8"))
BYTITLE = {e["title"]: e for e in BOOK}

TODO_CUE = "*TODO — sightline for this tour. Which window, and at what o'clock?*"


def manuscript(tag):
    hits = [p for p in glob.glob(MS + "*.md")
            if os.path.basename(p).startswith(tag + " ")]
    return hits[0] if hits else None


def render(entry, tag, indent):
    """The library entry as manuscript markdown, in this file's indentation."""
    b = dict(entry["block"])
    for k, v in ((entry.get("overrides") or {}).get(tag) or {}).items():
        b[k] = v
    cue = (entry.get("cuePerTour") or {}).get(tag)

    L = []
    head = b.get("title", "")
    if b.get("sub"):
        head += " — " + b["sub"]
    L.append("> ### {N} " + head)
    L.append("")
    L.append("> *%s*" % cue if cue else "> " + TODO_CUE)
    L.append("")
    if b.get("hook"):
        L.append("<callout>🎣 %s</callout>" % b["hook"])
        L.append("")
    for bl in b.get("bullets") or []:
        L.append("- " + bl)
    if b.get("bullets"):
        L.append("")
    if b.get("point"):
        L.append("🎯 " + b["point"]); L.append("")
    if b.get("mic"):
        L.append("🎤 " + b["mic"]); L.append("")
    if b.get("weather"):
        L.append("🌫️ " + b["weather"]); L.append("")
    if b.get("say"):
        L.append("+ ### 🗣️ How to say it:")
        for row in b["say"]:
            name, phon, gloss = (list(row) + ["", ""])[:3]
            L.append("  - **%s** [%s]%s" % (name, phon, (" — " + gloss) if gloss else ""))
        L.append("")
    if b.get("tags"):
        L.append("🧵 " + " ".join(b["tags"])); L.append("")
    return [(indent + x) if x else "" for x in L]


def file_indent(lines):
    for (s, e, ind, num, head) in B.regions(lines):
        return ind
    return ""


def renumber(lines, tag):
    """Block numbers are positional: 12.1, 12.2, 12.3 in running order."""
    major = tag.split(".")[0]
    edits, n = [], 0
    for (s, e, ind, num, head) in B.regions(lines):
        n += 1
        new = re.sub(r'(>\s*###\s+)[\d.]+(\s)', r'\g<1>%s.%d\g<2>' % (major, n), head, count=1)
        if new != head:
            edits.append((s, s + 1, [new.rstrip("\n")]))
    return edits, n


def apply_to(tag, adds, removes):
    p = manuscript(tag)
    if not p:
        print("   %-6s NO MANUSCRIPT — skipped" % tag); return None
    lines = open(p, encoding="utf-8").read().split("\n")
    ind = file_indent(lines)
    regs = B.regions(lines)
    have = {}
    for (s, e, i2, num, head) in regs:
        t = re.sub(r'^\s*>\s*###\s+[\d.]+\s*', '', head).strip()
        t = t.split("—")[0].strip()
        have[t] = (s, e)

    edits = []
    for title in removes:
        base = title.split("—")[0].strip()
        if base not in have:
            print("   %-6s remove %-34s NOT PRESENT — skipped" % (tag, base[:34])); continue
        s, e = have[base]
        while e < len(lines) and lines[e].strip() in ("", "*******"):
            e += 1
        edits.append((s, e, []))
        print("   %-6s remove %-34s lines %d-%d" % (tag, base[:34], s + 1, e))

    for title in adds:
        base = title.split("—")[0].strip()
        if base in have:
            print("   %-6s add    %-34s ALREADY THERE — skipped" % (tag, base[:34])); continue
        e = BYTITLE.get(title)
        if not e:
            print("   %-6s add    %-34s NOT IN LIBRARY — skipped" % (tag, base[:34])); continue
        body = render(e, tag, ind)
        at = regs[-1][1] if regs else len(lines)
        edits.append((at, at, body + [ind + "*******", ""]))
        cue = "inherits its own cue" if (e.get("cuePerTour") or {}).get(tag) else "CUE LEFT AS TODO"
        print("   %-6s add    %-34s %d lines at %d   (%s)"
              % (tag, base[:34], len(body), at + 1, cue))

    if not edits:
        return None
    out = B.apply(lines, edits)
    ren, n = renumber(out, tag)
    out = B.apply(out, ren)
    after = len(B.regions(out))
    if after != n:
        print("   %-6s ABORT: reparsed to %d blocks, expected %d" % (tag, after, n)); return None
    print("   %-6s -> %d blocks after renumbering" % (tag, n))
    return p, out


byt = {}
for c in plan.get("changes", []):
    byt.setdefault(c["tour"], {"add": [], "remove": []})[c["action"]].append(c["block"])

print("plan built %s — %d changes across %d tours\n"
      % (plan.get("builtAt", "?"), len(plan.get("changes", [])), len(byt)))

results = []
for tag, ops in sorted(byt.items()):
    r = apply_to(tag, ops["add"], ops["remove"])
    if r: results.append(r)

print("\n%s" % ("WRITING" if WRITE else "DRY RUN — nothing written. re-run with --write"))
for p, out in results:
    if WRITE:
        shutil.copy2(p, p + STAMP)
        open(p, "w", encoding="utf-8").write("\n".join(out))
        print("   wrote %s  (backup %s)" % (os.path.basename(p), STAMP))
if WRITE and results:
    print("\nNow rebuild the touched tours, regenerate the library, and redeploy:")
    for p, _ in results:
        print("   python3 build-any.py \"%s\" script-<id>.js" % os.path.basename(p)[:-3])
    print("   python3 _onecopy.py --write")
