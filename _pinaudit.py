#!/usr/bin/env python3
"""PIN AUDIT — are the map pins and sightlines where they are supposed to be?

WINDOWED, and that is the whole point. 5.0 is an out-and-back: Sólheimajökull to
Vík is driven twice, and BSÍ is both the first and the last point on the line.
A naive nearest-point search over the whole geometry therefore resolves a
return-leg pin to its outbound pass and screams "42 km backwards" about a cue
that is perfectly fine. Every lookup here is constrained to a window around the
cue's own stated progress. (Repo law, learned on 4.0 and re-learned here.)

Checks, per cue:
  1. is the pin ON the road?
  2. does the pin actually sit where its progress says it does?
  3. do the pins run in route order?
  4. is the pin BEFORE the target's closest approach, within the window?
  5. is the target close enough for a human to see?
Then: clumps, and silences split into OUTBOUND (a real gap) and RETURN
(same road already covered outbound — not a gap, per Ritchie's dedupe rule).

Usage: python3 _pinaudit.py 5.0
"""
import json, re, sys, math, os

TAG    = sys.argv[1] if len(sys.argv) > 1 else "5.0"
HERE   = os.path.dirname(os.path.abspath(__file__))
WINDOW = 8.0          # % of route either side of the stated progress

def km(a, b):
    dy = (a[0] - b[0]) * 111.32
    dx = (a[1] - b[1]) * 111.32 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)

rt = open(os.path.join(HERE, "route-%s.js" % TAG), encoding="utf-8").read()
pts = [(float(a), float(b)) for a, b in
       re.findall(r"\[\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\]", rt)]
if pts and abs(pts[0][0]) < 30:
    pts = [(b, a) for a, b in pts]
cum = [0.0]
for i in range(1, len(pts)):
    cum.append(cum[-1] + km(pts[i - 1], pts[i]))
TOTAL = cum[-1]
PROG  = [c / TOTAL * 100 for c in cum]

cu   = open(os.path.join(HERE, "cues-%s.js" % TAG), encoding="utf-8").read()
CUES = json.loads(cu[cu.index("["):cu.rindex("]") + 1])
sc   = open(os.path.join(HERE, "script-%s.js" % TAG), encoding="utf-8").read()

KINDBYID = {}
for m in re.finditer(r'\{title:"[^"]+", kind:"(\w+)", blocks:\[', sc):
    seg = sc[m.end():]
    n = seg.find('{title:"')
    seg = seg[:n] if n > 0 else seg
    for b in re.findall(r'\{id:"(%s\.\d+\.\d+)"' % re.escape(TAG), seg):
        KINDBYID[b] = m.group(1)

BLOCK = {}
for m in re.finditer(r'\{id:"(%s\.\d+\.\d+)"' % re.escape(TAG), sc):
    seg = sc[m.start():m.start() + 900]
    t = re.search(r'title:"([^"]*)"', seg)
    c = re.search(r'cue:"((?:[^"\\]|\\.)*)"', seg)
    BLOCK[m.group(1)] = (t.group(1) if t else "?", c.group(1) if c else "")

def near_win(p, prog):
    """Nearest route index to p, searched ONLY within +/-WINDOW% of prog."""
    lo = next((i for i, q in enumerate(PROG) if q >= prog - WINDOW), 0)
    hi = next((i for i in range(len(PROG) - 1, -1, -1) if PROG[i] <= prog + WINDOW),
              len(PROG) - 1)
    if hi < lo:
        lo, hi = 0, len(PROG) - 1
    best, bi = 1e9, lo
    for i in range(lo, hi + 1):
        d = km(p, pts[i])
        if d < best:
            best, bi = d, i
    return best, bi

print("route %.1f km | %d points | %d cues | window +/-%.0f%%\n"
      % (TOTAL, len(pts), len(CUES), WINDOW))
print("%-11s %-31s %6s %7s %7s %-8s %s"
      % ("id", "title", "prog", "pin→rd", "tgt km", "abeam", "notes"))
print("-" * 120)

rows, prev, problems = [], -1, []
for c in CUES:
    bid = c["id"]
    title, cue = BLOCK.get(bid, ("?", ""))
    prog = c["progress"]
    off, pi = near_win((c["pin"]["lat"], c["pin"]["lon"]), prog)
    notes = []
    if off > 0.12:
        notes.append("PIN %dm OFF-ROAD" % int(off * 1000))
    drift = PROG[pi] - prog
    if abs(drift) > 1.5:
        notes.append("pin sits at %.1f%%, progress says %.1f%% (%.0f km out)"
                     % (PROG[pi], prog, abs(drift) / 100 * TOTAL))
    if prog < prev - 0.01:
        notes.append("PROGRESS GOES BACKWARDS")
    prev = prog

    tk, ab, tg = "-", "-", c.get("target")
    if tg:
        tp = (tg["lat"], tg["lon"])
        td = km((c["pin"]["lat"], c["pin"]["lon"]), tp)
        tk = "%.1f" % td
        _, ai = near_win(tp, prog)
        # The before-abeam law is about a MOVING bus: a pin placed past its
        # subject draws the arrow out of the back window. At a stop the coach is
        # parked and the guest can turn round, so the rule does not apply.
        stationary = KINDBYID.get(bid) == "stop"
        ab = "n/a" if stationary else ("ok" if pi <= ai + 3 else "PAST")
        if pi > ai + 3 and not stationary:
            notes.append("pin %.1f km PAST closest approach — arrow points backwards"
                         % (cum[pi] - cum[ai]))
        if td > 30:
            notes.append("target %.0f km off — visible?" % td)
    rows.append(dict(id=bid, title=title, cue=cue, prog=prog,
                     pin_off_road_m=round(off * 1000),
                     pin_actual_prog=round(PROG[pi], 2),
                     target=(tg or {}).get("name"),
                     target_km=(float(tk) if tk != "-" else None),
                     abeam=ab, notes=notes))
    if notes:
        problems.append(bid)
    print("%-11s %-31s %5.1f%% %6dm %7s %-8s %s"
          % (bid, title[:30], prog, int(off * 1000), tk, ab, "; ".join(notes)))

print("\n" + "=" * 78)
print("CLUMPS — blocks firing within 0.15%% (%.1f km) of each other"
      % (0.15 / 100 * TOTAL))
print("=" * 78)
for i in range(1, len(CUES)):
    g = CUES[i]["progress"] - CUES[i - 1]["progress"]
    if g < 0.15:
        print("  %.2f%%  %-11s %-27s + %-11s %s"
              % (g, CUES[i - 1]["id"], BLOCK.get(CUES[i - 1]["id"], ("", ""))[0][:26],
                 CUES[i]["id"], BLOCK.get(CUES[i]["id"], ("", ""))[0][:26]))

# outbound = up to the furthest point of the route (max distance from start)
far = max(range(len(pts)), key=lambda i: km(pts[0], pts[i]))
TURN = PROG[far]
print("\nturnaround (furthest point from BSÍ) at %.1f%% of the route" % TURN)
print("=" * 78)
print("SILENCES >= 12 km  —  OUTBOUND ones are real gaps, RETURN ones retrace")
print("=" * 78)
for i in range(1, len(CUES)):
    a, b = CUES[i - 1]["progress"], CUES[i]["progress"]
    d = (b - a) / 100 * TOTAL
    if d >= 12:
        leg = "OUTBOUND" if b <= TURN + 1 else ("RETURN  " if a >= TURN - 1 else "SPANS   ")
        print("  %-8s %6.1f km  %5.1f%% → %5.1f%%   %-28s → %s"
              % (leg, d, a, b, BLOCK.get(CUES[i - 1]["id"], ("", ""))[0][:27],
                 BLOCK.get(CUES[i]["id"], ("", ""))[0][:27]))

print("\ncues with something to answer for: %d of %d" % (len(problems), len(CUES)))
json.dump({"tag": TAG, "total_km": round(TOTAL, 1), "turnaround_pct": round(TURN, 1),
           "rows": rows},
          open(os.path.join(HERE, "_pinaudit-%s.json" % TAG), "w"),
          ensure_ascii=False, indent=1)
print("wrote _pinaudit-%s.json" % TAG)
