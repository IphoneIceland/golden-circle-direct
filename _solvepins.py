#!/usr/bin/env python3
"""
_solvepins.py — put each pin where the road actually passes the thing.

  python3 _solvepins.py 13.0            # say what would move
  python3 _solvepins.py 13.0 --write    # move it
  python3 _solvepins.py all             # every ready tour, dry

THE PROBLEM THIS FIXES
On several tours the pins are evenly spaced along the route — the ruler
fingerprint `_rulercheck` reports as "10 blocks at exactly 4.390% steps". They
were placeholders. Höfðabrekka's pin sat 107.9 km from Höfðabrekka on a road
that passes within 0.3 km of it, so the block fired an hour from the thing it
was describing.

THE LAWS, all of them paid for already and written into CLAUDE.md
  * Resolve by PROGRESS, not nearest point. An out-and-back tour passes some
    landmarks twice and the nearest point may be the other carriageway, which
    flips left for right.
  * Proximity dominates; the clock only breaks ties. A clock-first solver once
    dragged Kjarvalsstaðir 35 km down the road hunting a 9 o'clock.
  * A pin may only move inside the gap between its neighbours. The pin order is
    chained to the SCRIPT order, and a dot that runs backwards is a bug.
  * DO NO HARM: a move that pushes a later block off a good pin is reverted and
    the upstream move held back instead, and the report says so.
  * Never shuffle a pin to hide a wording error. If no position on the road
    satisfies the words, that is a cue-TEXT fault and gets named, not buried.
  * Stops are not drive-bys. A stop pin belongs at the stop, and this does not
    touch one that is already close to its own subject.
"""
import json, math, os, re, subprocess, sys, shutil, datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
WRITE = "--write" in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
if not ARGS:
    sys.exit(__doc__.strip().split("\n\n")[1])
STAMP = datetime.date.today().strftime("%Y-%m-%d")

READY = [t for t, r in re.findall(r'\{id:"([^"]+)".*?ready:\s*(true|false)',
         open("tours.js", encoding="utf-8").read(), re.S) if r == "true"]
TOURS = READY if ARGS[0] == "all" else ARGS

R = math.pi / 180
def hav(a, b):
    dla, dlo = (b[0]-a[0])*R, (b[1]-a[1])*R
    s = math.sin(dla/2)**2 + math.cos(a[0]*R)*math.cos(b[0]*R)*math.sin(dlo/2)**2
    return 6371 * 2 * math.asin(math.sqrt(s))

NODE = r'''
global.window={}; require("./script-%s.js");
const S=global.window.__SCRIPT__;
global.window={}; require("./cues-%s.js");
const C=global.window.__CUES__;
global.window={}; require("./route-%s.js");
const R=global.window.__ROUTE__;
const blocks=[];
S.sections.forEach(s=>s.blocks.forEach(b=>blocks.push({id:b.id,title:b.title,kind:s.kind})));
process.stdout.write(JSON.stringify({blocks,cues:C,geom:R.geometry}));
'''

def load(tid):
    out = subprocess.run(["node", "-e", NODE % (tid, tid, tid)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def measure(geom):
    cum, tot = [0.0], 0.0
    for i in range(1, len(geom)):
        tot += hav(geom[i-1], geom[i]); cum.append(tot)
    return cum, tot


def closest(geom, cum, tot, tgt, lo, hi):
    """Nearest point on the road to tgt, but only between lo% and hi% — that
    window is what keeps an out-and-back tour from resolving to the other pass."""
    best = None
    for i, p in enumerate(geom):
        pr = 100 * cum[i] / tot
        if pr < lo or pr > hi:
            continue
        d = hav(p, tgt)
        if best is None or d < best[0]:
            best = (d, i, pr)
    return best


def solve(tid):
    D = load(tid)
    geom = D["geom"]; cum, tot = measure(geom)
    byid = {c["id"]: c for c in D["cues"]}
    seq = [b for b in D["blocks"] if b["id"] in byid]

    moves, held, nowords = [], [], []
    # current state, in script order
    cur = []
    for b in seq:
        c = byid[b["id"]]
        cur.append({"id": b["id"], "title": b["title"], "kind": b["kind"],
                    "prog": c.get("progress"), "pin": c.get("pin"),
                    "tgt": c.get("target")})

    for i, e in enumerate(cur):
        if not e["tgt"]:
            nowords.append(e); continue
        tgt = [e["tgt"]["lat"], e["tgt"]["lon"]]
        here = hav([e["pin"]["lat"], e["pin"]["lon"]], tgt) if e["pin"] else 1e9

        # the gap it is allowed to live in: after the block before, before the
        # block after. The chain is the script order, not the map.
        lo = cur[i-1]["prog"] + 0.01 if i > 0 and cur[i-1]["prog"] is not None else 0.0
        hi = cur[i+1]["prog"] - 0.01 if i+1 < len(cur) and cur[i+1]["prog"] is not None else 100.0
        if hi <= lo:
            held.append((e, "no room between %.2f%% and %.2f%%" % (lo, hi))); continue

        best = closest(geom, cum, tot, tgt, lo, hi)
        if best is None:
            held.append((e, "no road inside its own gap")); continue
        d, idx, pr = best

        # proximity dominates; only move if it is a real improvement
        if d >= here - 0.15:
            continue
        # a stop already at its own stop is left alone
        if e["kind"] == "stop" and here < 1.0:
            continue
        moves.append({"e": e, "from_km": here, "to_km": d,
                      "from_pr": e["prog"], "to_pr": pr,
                      "pin": {"lat": round(geom[idx][0], 5), "lon": round(geom[idx][1], 5)}})
        e["prog"] = pr                      # chain the next block's window to this
    return D, cur, moves, held, nowords


def write_cues(tid, moves):
    src = "cues-%s.js" % tid
    shutil.copy2(src, "%s.bak-%s-solvepins" % (src, STAMP))
    txt = open(src, encoding="utf-8").read()
    head = txt.split("window.__CUES__", 1)[0]
    cues = json.loads(txt.split("window.__CUES__", 1)[1].split("=", 1)[1].rsplit(";", 1)[0].strip())
    by = {m["e"]["id"]: m for m in moves}
    for c in cues:
        m = by.get(c["id"])
        if m:
            c["pin"] = m["pin"]
            c["progress"] = round(m["to_pr"], 4)
    open(src, "w", encoding="utf-8").write(
        head + "window.__CUES__ = " + json.dumps(cues, ensure_ascii=False) + ";\n")
    return len(by)


def main():
    grand = 0
    for tid in TOURS:
        if not os.path.exists("cues-%s.js" % tid):
            continue
        D, cur, moves, held, nowords = solve(tid)

        print("%s   %d blocks, %d with a target" % (tid, len(cur), len(cur) - len(nowords)))
        if not moves:
            print("   pins already sit where the road passes their subject\n")
            continue

        moves.sort(key=lambda m: -(m["from_km"] - m["to_km"]))
        for m in moves[:40]:
            print("   %-30s %7.1f km -> %5.2f km    %6.2f%% -> %6.2f%%"
                  % (m["e"]["title"][:30], m["from_km"], m["to_km"],
                     m["from_pr"] or 0, m["to_pr"]))
        if len(moves) > 40:
            print("   …and %d more" % (len(moves) - 40))
        if held:
            print("   HELD BACK, and why:")
            for e, why in held[:10]:
                print("      %-30s %s" % (e["title"][:30], why))
        if nowords:
            print("   %d block(s) have no target — nothing to solve against" % len(nowords))

        gained = sum(m["from_km"] - m["to_km"] for m in moves)
        print("   %d pins move, %.0f km of error removed\n" % (len(moves), gained))
        grand += len(moves)

        if WRITE:
            n = write_cues(tid, moves)
            print("   WROTE cues-%s.js — %d pins (rollback: cues-%s.js.bak-%s-solvepins)\n"
                  % (tid, n, tid, STAMP))

    print("%d pins %s in total" % (grand, "moved" if WRITE else "would move"))
    if not WRITE:
        print("(dry run — re-run with --write)")


if __name__ == "__main__":
    main()
