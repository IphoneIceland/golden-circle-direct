#!/usr/bin/env python3
"""MOCKUP: put the iGuide tours onto the Norse Expansion globe, in its own idiom.

The first attempt threw away everything good about both maps and rebuilt a flat
Leaflet plot in the wrong colours. This does the opposite: it changes nothing
about the globe except adding a fifth arc.

The globe already has all the machinery — ARC_COL / ARC_FOCUS / ARC_ZOOM / ARCS,
a `routes` array of {name, era, cat, coords, routeArc, ...}, and a `themes`
system that spotlights a named set of sites. So the tours go in as:

  * a new arc "T", coloured with the house gold #d4a94a (the Iceland map's own
    --gold, not a new colour), focused on Iceland
  * the ten tour routes as `routes` entries with routeArc "T"
  * a theme, "Standing on it today", listing the eight Norse-world places that
    a tour already stops at — so his existing spotlight UI answers the question
    with no new interface at all

Nothing is redrawn by hand and no layout is touched. Writes a MOCKUP file; the
live norse.html is not touched.
"""
import io, json, os, re, math

REPO = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.expanduser("~/Documents/RitchWiki/outputs/norse/norse-themed.html")
OUT  = os.path.expanduser("~/Documents/RitchWiki/norse-globe-with-tours-MOCKUP.html")
GOLD = "#d4a94a"

tours = json.load(open('/tmp/tours_slim.json'))
s = io.open(SRC, encoding='utf-8', errors='ignore').read()
orig = len(s)

def sub1(pat, repl, why):
    global s
    new, n = re.subn(pat, repl, s, count=1)
    if n != 1:
        raise SystemExit("!! %s — matched %d times, refusing to guess" % (why, n))
    s = new
    print("   ok  %s" % why)

# ---- 1. the arc's colour, focus and zoom -------------------------------
sub1(r'const ARC_COL = \{N:"#5bc0ff", E:"#e3b341", S:"#e2554b", W:"#3ec6a0", HOME:"#c7d0df"\}',
     'const ARC_COL = {N:"#5bc0ff", E:"#e3b341", S:"#e2554b", W:"#3ec6a0", HOME:"#c7d0df", T:"%s"}' % GOLD,
     "ARC_COL gains T (house gold)")
sub1(r'const ARC_FOCUS = \{ N:\[58,-29\], W:\[53,-5\], S:\[39,6\], E:\[49,33\], HOME:\[60,11\] \}',
     'const ARC_FOCUS = { N:[58,-29], W:[53,-5], S:[39,6], E:[49,33], HOME:[60,11], T:[64.6,-19.0] }',
     "ARC_FOCUS gains T (Iceland)")
sub1(r'const ARC_ZOOM  = \{ N:360,      W:300,     S:300,    E:315,     HOME:300 \}',
     'const ARC_ZOOM  = { N:360,      W:300,     S:300,    E:315,     HOME:300, T:150 }',
     "ARC_ZOOM gains T (close on Iceland)")
sub1(r'const ARCS=\{N:false,E:false,S:false,W:false\}',
     'const ARCS={N:false,E:false,S:false,W:false,T:false}',
     "ARCS gains the T toggle")
sub1(r'const anyArc=\(\)=>ARCS\.N\|\|ARCS\.E\|\|ARCS\.S\|\|ARCS\.W;',
     'const anyArc=()=>ARCS.N||ARCS.E||ARCS.S||ARCS.W||ARCS.T;',
     "anyArc() counts T")

# ---- 2. styling, using the tokens the page already declares ------------
sub1(r'(\.tool\.on\[data-arc=W\]\{color:var\(--w\);box-shadow:inset 0 0 14px rgba\(62,198,160,\.28\);\})',
     r'\1\n.tool.on[data-arc=T]{color:var(--tour);box-shadow:inset 0 0 14px rgba(212,169,74,.30);}',
     "toolbar button style for T")
sub1(r'(\.arc-W \.core\{background:var\(--w\);\})',
     r'\1 .arc-T .core{background:var(--tour);} .arc-T.s-tri .core{border-bottom-color:var(--tour);color:var(--tour);}',
     "marker colour for T")
sub1(r'(--n:#5bc0ff; --e:#e3b341; --s:#e2554b; --w:#3ec6a0; --home:#c7d0df;)',
     r'\1 --tour:%s;' % GOLD,
     "--tour token (the Iceland map's own gold)")

# ---- 3. the toolbar button, beside the four directions -----------------
sub1(r'(<div class="tool" data-arc="W"><span class="ic">🌊</span><span class="tx">West</span></div>)',
     r'\1\n  <div class="tool" data-arc="T"><span class="ic">🇮🇸</span><span class="tx">Tours</span></div>',
     "Tours button in the arc toolbar")

# ---- 4. the data: ten tour routes + one theme --------------------------
i = s.index('window.DATA ='); j = s.index('</script>', i)
blob = s[i + len('window.DATA ='):j].strip().rstrip(';')

TOUR_ROUTES = []
for tid, t in sorted(tours.items(), key=lambda kv: float(kv[0])):
    co = t['route'][::3]
    TOUR_ROUTES.append({
        "name": "%s — tour %s" % (t['name'], tid),
        "era": "today",
        "cat": "route",
        "coords": co,
        "from": t['stops'][0]['n'] if t['stops'] else "Reykjavík",
        "to":   t['stops'][-1]['n'] if t['stops'] else "Reykjavík",
        "routeArc": "T",
        "blurb": "A tour that runs today, past %d stops." % len(t['stops']),
        "facts": [["Stops", str(len(t['stops']))], ["Runs", "today, from Reykjavík"]],
        "body": [],
        "teach": "The modern road and the old one answer to the same coast.",
        "img": {},
        "years": [2026],
    })

OVERLAP = ["Þingvellir", "Conversion of Iceland (Kristnitaka 1000)",
           "Þorgeir Þorkelsson (the Lawspeaker 1000)", "Skálholt",
           "Kirkjubæjarklaustur", "Borg (Flóki's second winter)",
           "Egill Skallagrímsson", "Hjörleifshöfði"]
THEME = {
    "id": "standing-on-it",
    "name": "Standing on it today",
    "icon": "🇮🇸",
    "volume": "iGuide Iceland — where the tours and the sagas share ground",
    "blurb": "Eight places on this globe are stops on a tour that runs today. "
             "Not near — the same ground.",
    "body": [],
    "facts": [["Places", "8"], ["Tours involved", "4.0, 5.0, 7.0, 9.0"]],
    "teach": "Þingvellir is not a ruin you read about. It is a car park, a path, "
             "and the exact spot where the country changed religion in the year 1000.",
    "sites": OVERLAP,
    "img": {},
}

patch = ("""
;(function(){
  // MOCKUP injection — tours as a fifth arc. Data only; no layout, no timers.
  var D = window.DATA;
  D.routes = D.routes.concat(%s);
  D.themes = [%s].concat(D.themes);
})();
""" % (json.dumps(TOUR_ROUTES, ensure_ascii=False), json.dumps(THEME, ensure_ascii=False)))

s = s[:j] + patch + s[j:]
io.open(OUT, 'w', encoding='utf-8').write(s)
print("\nwrote %s" % OUT)
print("  %.1f MB (source %.1f MB)" % (len(s)/1e6, orig/1e6))
print("  + %d tour routes on a new gold 'Tours' arc" % len(TOUR_ROUTES))
print("  + 1 theme 'Standing on it today' with %d sites" % len(OVERLAP))
