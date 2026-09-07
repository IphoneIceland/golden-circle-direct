#!/usr/bin/env python3
"""Does each Craft EXPORT still list its stops in the order the app ships?

The gcd197 reorder put eleven stops the way the road actually passes them. That
change lives in the exports and in script-*.js. Craft itself was NOT reordered --
a stop there is a flat heading whose content follows as siblings, so moving one
means recreating ~17 styled blocks, and getting a callout or toggle marker subtly
wrong silently breaks the build for that stop.

So the risk is a future re-export from Craft quietly restoring the old order. This
turns that from silent rot into a loud failure: it compares the stop order in each
export against the order of blocks in the shipped script, and shouts if they part.

Run it with the other audits. If it fails after a re-export, re-apply the eleven
swaps with _swapmd.py and _renumthreads.py, or reorder in Craft first.
"""
import re, io, os, sys, unicodedata

SRC = os.path.expanduser("~/Documents/RitchWiki/Tour Scripts")
HERE = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    s = re.sub(r"[*_`]", "", s)
    s = "".join(c for c in s if not unicodedata.category(c).startswith("S"))
    return re.sub(r"\s+", " ", s).strip().lower()

ids = re.findall(r'\{id:"([^"]+)"[^}]*?ready:\s*true',
                 io.open(os.path.join(HERE, "tours.js"), encoding="utf-8").read())
bad = 0
for tid in ids:
    hit = [f[:-3] for f in os.listdir(SRC)
           if f.endswith(".md") and f.startswith(tid + " ")]
    if len(hit) != 1:
        print("%-6s no single export (%s)" % (tid, hit)); bad += 1; continue
    raw = io.open("%s/%s.md" % (SRC, hit[0]), encoding="utf-8").read()
    body = re.split(r"^\s*\+? ?#{1,2} 🧵 Threads", raw, maxsplit=1, flags=re.M)[0]
    exp = [norm(m.group(2)).split(" — ")[0].split(" – ")[0]
           for m in re.finditer(r"(?m)^\s*>? ?#{3}\s+(\d+\.\d+)\s+(.*)$", body)]
    sc = io.open(os.path.join(HERE, "script-%s.js" % tid), encoding="utf-8").read()
    app = [norm(m.group(1)) for m in
           re.finditer(r'\{id:"[\d.]+"[^}]*?title:"((?:[^"\\\\]|\\\\.)*)"', sc)]
    app = [a for a in app if a]
    # Match on EXACT normalised title. Substring matching produced two false
    # alarms first time out -- "olfusa" also matches "olfusa intro", and
    # "reykjavik" matches half of 14.0 -- so an export heading that does not
    # resolve to exactly one app block is skipped rather than guessed at.
    seq, order = [], []
    for e in exp:
        hits = [i for i, a in enumerate(app) if a == e]
        if len(hits) == 1:
            seq.append(e); order.append(hits[0])
    slips = [i for i in range(1, len(order)) if order[i] < order[i-1]]
    if slips:
        bad += len(slips)
        print("%-6s EXPORT ORDER DIVERGED from the shipped script at %d point(s)" % (tid, len(slips)))
        for i in slips:
            print("        export has %r before %r; the app ships them the other way"
                  % (seq[i-1], seq[i]))
    else:
        print("%-6s ok (%d stops, order matches the app)" % (tid, len(seq)))
print("\ndivergences: %d" % bad)
sys.exit(1 if bad else 0)
