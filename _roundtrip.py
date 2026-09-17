#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_roundtrip.py — read-only. PROVE the library can rebuild every tour before
anything is allowed to depend on it.

THE GOAL BEHIND THIS (Ritchie, 17 Sep 2026)
"One copy. Six tours point at it. Fix it once, it changes everywhere."

THE HONEST ORDER OF WORK
You do not switch a live system onto a new source of truth and find out
afterwards whether it was complete. So: take blocks.json plus a per-tour
manifest (the ordered list of block ids each tour uses), rebuild each tour's
script FROM THOSE ALONE, and compare it against the script the manuscript
actually produces today.

  identical  -> the library holds everything the manuscripts hold, and the
                builder can safely be pointed at it
  different  -> the library is LOSSY, and the diff names exactly what it drops

Nothing is written. Nothing is deployed. This only answers the question.

  python3 _roundtrip.py            # every tour, summary
  python3 _roundtrip.py 12.0 -v    # one tour, show the first differences
"""
import json, os, subprocess, sys, collections

os.chdir(os.path.dirname(os.path.abspath(__file__)))
VERBOSE = "-v" in sys.argv
want = [a for a in sys.argv[1:] if not a.startswith("-")]

BOOK = json.load(open("_blocks/blocks.json", encoding="utf-8"))

def built(tag):
    """The script the manuscript produces today — the thing we must reproduce."""
    out = subprocess.run(["node", "-e",
        'global.window={};eval(require("fs").readFileSync(process.argv[1],"utf8"));'
        'process.stdout.write(JSON.stringify(window.__SCRIPT__))',
        "script-%s.js" % tag], capture_output=True, text=True).stdout
    return json.loads(out)

# index the library by the subject key _onecopy.py used, per tour
BY = {}
for e in BOOK:
    for t in e["usedBy"]:
        BY.setdefault(t, {})[e["block"]["title"]] = e

def subject_of(block_title):
    """Index by the block's own title, exactly as the library stores it.

    An earlier version normalised the title (strip emoji, casefold, drop
    punctuation) and looked up `entry["subject"]`. That reported 22 to 37 blocks
    per tour as "not in library" — which was a lookup failure on this side, not a
    gap in the library. `entry["block"]["title"]` and the built script's
    `block.title` are the same string; use it. (17 Sep 2026)
    """
    return block_title


FIELDS = ("title", "sub", "cue", "hook", "point", "mic", "bullets", "say", "tags")

def from_library(tag, shape):
    """Rebuild the tour using ONLY the library entry + this tour's overrides.

    The manuscript supplies nothing here except the running order and the
    section headings — which is exactly what a manifest would hold.
    """
    lib = BY.get(tag, {})
    out = {"title": shape["title"], "sections": [], 
           "threadsIntro": shape.get("threadsIntro"), "threads": shape.get("threads")}
    misses = []
    for sec in shape["sections"]:
        blocks = []
        for b in sec["blocks"]:
            e = lib.get(subject_of(b["title"]))
            if not e:
                misses.append(b["title"]); blocks.append(b); continue
            nb = dict(e["block"])
            nb["id"] = b["id"]                      # position, not content
            ov = (e.get("overrides") or {}).get(tag) or {}
            for k, v in ov.items():
                nb[k] = v
            cpt = e.get("cuePerTour") or {}
            if tag in cpt:
                nb["cue"] = cpt[tag]
            blocks.append({k: nb.get(k) for k in FIELDS if k in b or k in nb})
        out["sections"].append({"title": sec["title"], "kind": sec["kind"],
                                "blocks": blocks})
    return out, misses

TOURS = [l.split('"')[1] for l in open("tours.js", encoding="utf-8") if 'id:"' in l]
tags = want or TOURS
tot_b = tot_bad = 0
worst = collections.Counter()

for tag in tags:
    if not os.path.exists("script-%s.js" % tag):
        print("%-6s no built script" % tag); continue
    real = built(tag)
    rebuilt, misses = from_library(tag, real)
    nb = bad = 0
    diffs = []
    for s_real, s_new in zip(real["sections"], rebuilt["sections"]):
        for b_real, b_new in zip(s_real["blocks"], s_new["blocks"]):
            nb += 1
            for f in FIELDS:
                if b_real.get(f) != b_new.get(f):
                    bad += 1; worst[f] += 1
                    diffs.append((b_real.get("id"), f, b_real.get(f), b_new.get(f)))
                    break
    tot_b += nb; tot_bad += bad
    flag = "OK" if bad == 0 and not misses else "%d of %d blocks differ" % (bad, nb)
    print("%-6s %3d blocks   %s%s" % (tag, nb, flag,
          "   (%d not in library)" % len(misses) if misses else ""))
    if VERBOSE and diffs:
        for bid, f, a, c in diffs[:4]:
            print("      %s  field %r" % (bid, f))
            print("         manuscript: %s" % str(a)[:150])
            print("         library   : %s" % str(c)[:150])

print("\n%d blocks checked, %d differ" % (tot_b, tot_bad))
if worst:
    print("fields that differ most: %s"
          % ", ".join("%s×%d" % (f, n) for f, n in worst.most_common(6)))
print("\nidentical everywhere = the library is complete and the builder can be"
      "\npointed at it. Anything else names what the library still drops.")
