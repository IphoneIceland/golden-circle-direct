#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_dupecheck.py — find the SAME TOPIC living under TWO DIFFERENT TITLES.

`_mergecheck.py` groups blocks by title. That is correct for what it does, but
it means a subject written up twice under two different names is INVISIBLE to it
and will drift apart forever with nothing complaining.

That is not hypothetical. On 17 Sep 2026:

    "🏞️ Elliðaárdalur — The Valley That Runs the City"   on 1.0 2.0 3.0 4.0
    "🏞️ Elliðaárdalur & Paradísardalur"                  on 5.0 6.0 7.0

Same valley. The scoreboard never compared them, the Golden Circle version was
corrected hours before the South Coast one, and for those hours three tours said
"1,500-2,500 salmon" while four said, correctly, that 2,500 is a batch of smolts.
It was found by accident. This finds the rest on purpose.

Method: take every distinct block title in the built JS, normalise it the way
_mergecheck does, and report any pair where one normalised title is a PREFIX of
the other, or where they share a leading word that is a proper noun. Then a human
decides — some are genuinely different blocks (14.0's two Reykjavík blocks are
the tour's opening and closing) and some are duplication.

Exit code = number of suspect pairs, so it can gate a deploy.
"""
import glob, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = re.compile(r'\{id:"([\d.]+)",\s*title:"((?:[^"\\]|\\.)*)"')

# words that carry no topic information on their own
STOP = {"the", "and", "of", "a", "an", "at", "in", "on", "to"}


def norm(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = t.replace("þ", "th").replace("ð", "d").replace("æ", "ae")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def main():
    titles = {}                       # normalised -> (raw, {tours})
    for f in sorted(glob.glob(os.path.join(HERE, "script-*.js"))):
        if ".bak" in f:
            continue
        tour = os.path.basename(f)[7:-3]
        s = open(f, encoding="utf-8").read()
        for m in BLOCK.finditer(s):
            raw = m.group(2)
            k = norm(raw)
            if not k:
                continue
            titles.setdefault(k, [raw, set()])[1].add(tour)

    keys = sorted(titles)
    suspects = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            wa = [w for w in a.split() if w not in STOP]
            wb = [w for w in b.split() if w not in STOP]
            if not wa or not wb:
                continue
            # one title's whole word-set contained in the other, or a shared
            # first significant word of 5+ characters (a place name, basically)
            shared_head = wa[0] == wb[0] and len(wa[0]) >= 5
            contained = set(wa) <= set(wb) or set(wb) <= set(wa)
            if shared_head or contained:
                suspects.append((a, b))

    for a, b in suspects:
        ra, ta = titles[a]
        rb, tb = titles[b]
        print("-" * 72)
        print("  %-46s  %s" % (ra[:46], ",".join(sorted(ta))))
        print("  %-46s  %s" % (rb[:46], ",".join(sorted(tb))))
        if ta & tb:
            print("  ^^ SAME TOUR carries both — opening/closing pair, or a dupe")
        else:
            print("  ^^ DIFFERENT TOURS — if it is the same topic, it WILL drift")

    print()
    print("suspect same-topic pairs: %d" % len(suspects))
    print("(this is a prompt for a human, not a verdict — some pairs are correct)")
    return len(suspects)


if __name__ == "__main__":
    sys.exit(min(main(), 120))
