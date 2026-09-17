"""End-of-session check: rebuild from scratch and prove every decision survived."""
import io

s = io.open("/Users/ritchiej/Documents/RitchWiki/norse-ICELAND-LAYER-MOCKUP.html",
            encoding="utf-8").read()
m = io.open("/Users/ritchiej/Documents/iGuide-Iceland-Site/map.html",
            encoding="utf-8").read()

checks = [
 ("gate, three doors",        'id="gate"' in s and s.count('class="lock"') == 3),
 ("vegvisir ground 74vmin",   'id="gateMark"' in s and "width:74vmin" in s),
 ("globe hidden on the gate", "body.gate-up #scene{opacity:0!important;}" in s),
 ("globe hidden on island",   "html body.island-open #scene" in s),
 ("crest door says Website",  'bm-sub">Website<' in s),
 ("menu on the globe",        'id="tabbar"' in s),
 ("twelve rows",              s.count('class="tab" data-nav') == 12),
 ("globe: Maps exit",         'data-nav="home"' in s),
 ("globe: Website exit",      'data-nav="website"' in s),
 ("globe: exits above line",  '#tabbar .tab[data-nav="website"]' in s),
 ("menu 244px",               "min-width:244px" in s),
 ("grip wears the glyph",     "vg-mark" in s),
 ("one sub-panel at a time",  "function closeSubs" in s),
 ("island opener published",  "window.__openIsland" in s),
 ("gate calls it",            "window.__openIsland()" in s),
 ("gate hears postMessage",   "e.data.iguide === 'home'" in s),
 ("no island back bar",       "iceBar" not in s and "iceBack" not in s),
 ("no tap-Iceland hint",      "iceHint" not in s and "Tap Iceland" not in s),
 ("no zoom / Find box",       "html body #bl-controls{display:none!important;}" in s),
 ("map: MIRROR block",        "MIRROR-START" in m),
 ("map: menu 200px",          "width:200px" in m),
 ("map: Maps exit",           "vgHome" in m),
 ("map: Website exit",        "vgSite" in m),
 ("map: exits above line",    ".vg-site{margin-bottom" in m),
 ("map: info plaque",         "id='mapinfo'" in m),
 ("map: Maps below the grip", "grip.nextSibling" in m),
 ("map: brandmark retired",   "#brandmark{display:none!important;}" in m),
]
for name, ok in checks:
    print(("  OK    " if ok else "  FAIL  ") + name)
bad = [n for n, ok in checks if not ok]
print()
print("ALL GREEN — %d checks" % len(checks) if not bad
      else "FAILURES: " + ", ".join(bad))
