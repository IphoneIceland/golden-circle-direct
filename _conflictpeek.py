#!/usr/bin/env python3
"""Throwaway: how DIFFERENT are the conflicting versions, really?
If they're 95% the same sentence, that's rot to be merged, not a choice to make."""
import os, sys, collections, difflib, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0]]
import importlib.util
spec = importlib.util.spec_from_file_location("cons", "_consolidate.py")
cons = importlib.util.module_from_spec(spec); spec.loader.exec_module(cons)

src = cons.load()
subs = collections.OrderedDict()
for tid in cons.READY:
    for sec in src[tid]["sections"]:
        for b in sec["blocks"]:
            subs.setdefault(b["title"].strip(), []).append((tid, b))

def flat(v):
    if v is None: return ""
    if isinstance(v, str): return v
    return "\n".join(flat(x) for x in v)

buckets = collections.Counter()
examples = {}
for t, ins in subs.items():
    if len(ins) < 2: continue
    for f in cons.PROSE + cons.LISTS:
        v, c, d = cons.classify([(tid, b.get(f)) for tid, b in ins])
        if v != "conflict" or f == "cue": continue
        vals = [flat(b.get(f)) for tid, b in ins if b.get(f)]
        worst = 1.0
        for i in range(len(vals)):
            for j in range(i+1, len(vals)):
                worst = min(worst, difflib.SequenceMatcher(None, vals[i], vals[j]).ratio())
        band = ("≥95% same" if worst >= .95 else "85-95%" if worst >= .85
                else "60-85%" if worst >= .60 else "<60% — really different")
        buckets[band] += 1
        examples.setdefault(band, (t, f, round(worst, 2), vals[:2]))

print("HOW DIFFERENT ARE THE 174 CONFLICTS (worst pair per field):")
for b in ["≥95% same", "85-95%", "60-85%", "<60% — really different"]:
    print("  %-26s %3d" % (b, buckets[b]))
for b, (t, f, r, vals) in examples.items():
    print("\n--- example: %s  (%s / %s, ratio %.2f)" % (b, t, f, r))
    for v in vals: print("    " + v[:200].replace("\n", " ⏎ "))
