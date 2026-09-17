#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_leakcheck.py — find EDITORIAL NOTES that are shipping to the guide's screen.

Three of these were found by hand on 17 Sep 2026, all inside `bullets:[...]`,
all therefore rendered in the app and read aloud:

  Víkurkirkja (7.0)  "(You will see “about 15 minutes” quoted for the run-up;
                      no Icelandic official source states it, so leave the
                      number out and keep the instruction.)"
  Keldur (7.0)       "(No weather pivot for this one: Keldur is never in view
                      from Route 1 in any weather. ...)" — printed directly
                      under the weather pivot it says does not exist.
  Keldur (6.0)       "...which is as precise as the published record gets, so
                      treat any exact felling year you hear as a guess."

A note to the writer is not a sentence for a bus. This scans the BUILT js —
what actually reaches the screen — because a note in the manuscript that
build-any drops is harmless, and a note in a bullet is not.

Usage:  python3 _leakcheck.py            # all script-*.js next to this file
        python3 _leakcheck.py 5.0 7.0    # named tours only
Exit code = number of suspect lines, so it can gate a deploy.
"""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Phrases that only ever appear when somebody is talking to the writer,
# not to a passenger.
PATTERNS = [
    r"you will (?:see|hear) [^.\"]{0,60}quoted",
    r"no (?:Icelandic )?(?:official )?source",
    r"leave the number out",
    r"treat (?:any|that|this)[^.\"]{0,40}as a guess",
    r"no weather pivot",
    r"\bunverified\b",
    r"\bnot verified\b",
    r"needs? (?:a )?(?:source|citation|checking)",
    r"\bTODO\b|\bFIXME\b|\bXXX\b",
    r"as precise as the published record gets",
    r"is as (?:accurate|precise) as",
    r"so the story has to carry itself",
    r"\bcheck this\b|\bverify (?:this|before)\b",
    r"\bplaceholder\b",
    r"\[\s*(?:source|cite|ref)\s*\]",
    r"\(sic\)",
]
RX = [re.compile(p, re.I) for p in PATTERNS]

FIELD = re.compile(r'(bullets|hook|point|mic|weather|sub):', re.I)
BLOCK = re.compile(r'\{id:"([\d.]+)",\s*title:"((?:[^"\\]|\\.)*)"')


def scan(path):
    s = open(path, encoding="utf-8").read()
    heads = list(BLOCK.finditer(s))
    hits = []
    for i, line in enumerate(s.split("\n")):
        for rx in RX:
            m = rx.search(line)
            if not m:
                continue
            # which block is this line in?
            off = sum(len(x) + 1 for x in s.split("\n")[:i])
            title = "?"
            bid = "?"
            for h in heads:
                if h.start() <= off:
                    bid, title = h.group(1), h.group(2)
                else:
                    break
            hits.append((bid, title, m.group(0), line.strip()[:160]))
            break
    return hits


def main(argv):
    tours = argv or None
    files = sorted(glob.glob(os.path.join(HERE, "script-*.js")))
    if tours:
        files = [f for f in files
                 if any(os.path.basename(f) == "script-%s.js" % t for t in tours)]
    total = 0
    for f in files:
        hits = scan(f)
        if not hits:
            continue
        print("=" * 70)
        print(os.path.basename(f))
        for bid, title, frag, line in hits:
            total += 1
            print("  %-10s %-34s  <%s>" % (bid, title[:34], frag))
            print("      %s" % line)
    print()
    print("suspect editorial lines reaching the screen: %d" % total)
    return total


if __name__ == "__main__":
    sys.exit(min(main(sys.argv[1:]), 120))
