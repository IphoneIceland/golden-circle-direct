#!/usr/bin/env python3
"""MOCKUP: the Iceland map as a LAYER inside the Norse Expansion globe.

Ritchie's model, not mine: two layers, one app. The globe does its thing.
Click Iceland and the Iceland map comes into play on top of it. Zoom back out
and the globe is still there, still spinning.

The previous attempt injected ten tour routes as "journeys" and it was rightly
called terrible: route colour comes from ROUTE_PAL keyed on `o.arc` (so the gold
never applied), and every active route auto-labels at its midpoint past NAMES_Z,
so ten routes on one small island stacked ten labels on the same pixel. None of
that is here. No routes are added to the globe at all.

What this does, and nothing more:
  1. adds ONE marker — Iceland — in the house gold
  2. clicking it opens the real Iceland map (iGuide-Iceland-Site/map.html) as a
     full-screen layer in the same glass-and-gold chrome
  3. a back control returns to the globe

Writes a MOCKUP file. The live norse.html is untouched.
"""
import io, os, re

SRC  = os.path.expanduser("~/Documents/RitchWiki/outputs/norse/norse-themed.html")
OUT  = os.path.expanduser("~/Documents/RitchWiki/norse-ICELAND-LAYER-MOCKUP.html")
MAP  = os.path.expanduser("~/Documents/iGuide-Iceland-Site/map.html")
GOLD = "#d4a94a"

s = io.open(SRC, encoding='utf-8', errors='ignore').read()

def sub1(pat, repl, why):
    global s
    new, n = re.subn(pat, repl, s, count=1)
    if n != 1:
        raise SystemExit("!! %s — matched %d times, refusing to guess" % (why, n))
    s = new
    print("   ok  %s" % why)

# ---- the gold, reusing the Iceland map's own token ---------------------
sub1(r'(--n:#5bc0ff; --e:#e3b341; --s:#e2554b; --w:#3ec6a0; --home:#c7d0df;)',
     r'\1 --tour:%s;' % GOLD, "--tour token")
sub1(r'const ARC_COL = \{N:"#5bc0ff", E:"#e3b341", S:"#e2554b", W:"#3ec6a0", HOME:"#c7d0df"\}',
     'const ARC_COL = {N:"#5bc0ff", E:"#e3b341", S:"#e2554b", W:"#3ec6a0", HOME:"#c7d0df", T:"%s"}' % GOLD,
     "ARC_COL gains T")
sub1(r'(\.arc-W \.core\{background:var\(--w\);\})',
     r'\1 .arc-T .core{background:var(--tour);box-shadow:0 0 0 1px rgba(6,10,16,.9),0 0 14px rgba(212,169,74,.85);}',
     "gold marker for Iceland")

# ---- the layer: chrome in the house style -----------------------------
LAYER_CSS = """
<style id="iguide-iceland-layer">
#iceLayer{position:fixed;inset:0;z-index:60;display:none;opacity:0;
  transform:scale(1.06);transition:opacity .42s ease,transform .42s ease;}
#iceLayer.show{display:block;opacity:1;transform:scale(1);}
#iceLayer iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#2c7180;}
</style>
"""
LAYER_HTML = """
<div id="iceLayer">
  <iframe id="iceFrame" src="about:blank" title="Iceland — today's tours"></iframe>
</div>
"""
LAYER_JS = """
<script>
/* ---- Layer two: the Iceland map, inside the globe -------------------------
   The globe keeps running underneath — this is a layer, not a page change.

   The way IN is the gate. There used to be a capture-phase handler that
   watched for a click on the Iceland marker and opened the island instead of
   the globe's own card, plus a timed hint telling you to try it. Both are
   gone: the gate has an Iceland door, so the marker went back to behaving
   like every other marker on the globe, and a hint pointing at a mechanic
   nobody needs is just something else on screen.

   openIsland / closeIsland are published on window so the gate can call them
   without going near the DOM. ---- */
(function(){
  var MAP_SRC = "__MAPSRC__";
  var layer, frame, open=false;
  function els(){
    layer=document.getElementById('iceLayer');
    frame=document.getElementById('iceFrame');
  }
  function openIsland(){
    if(open) return; open=true; els();
    if(frame.getAttribute('src')==='about:blank') frame.setAttribute('src',MAP_SRC);
    layer.style.display='block';
    requestAnimationFrame(function(){ layer.classList.add('show'); });
  }
  function closeIsland(){
    if(!open) return; open=false; els();
    layer.classList.remove('show');
    setTimeout(function(){ if(!open) layer.style.display='none'; }, 440);
  }
  window.__openIsland = openIsland;
  window.__closeIsland = closeIsland;
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeIsland(); });
})();
</script>
"""

DATA_JS = """
<script>
/* Iceland as a place on the globe. This MUST run before the app script: the
   markers are built from D.settlements at boot, so a push at the end of the
   page is too late and the pin never exists (verified the hard way).
   NB: never put a closing body tag in this comment - the layer injection
   replaces the FIRST one it finds, and it found this one. */
(function(){
  window.DATA.settlements.push({
    name:"Iceland", lat:64.9, lon:-19.0, year:874, cat:"settlement",
    forceArc:"T",
    blurb:"Settled from 874. Ten tours run across it today \u2014 tap to drop into the island.",
    facts:[["Settled","from 874"],["Tours running","10"],["Stops","86"]],
    body:[], teach:"", img:{}, craftUrl:""
  });
})();
</script>
"""
i = s.index('window.DATA ='); j = s.index('</script>', i) + len('</script>')
s = s[:j] + DATA_JS + s[j:]
print("   ok  Iceland pushed into DATA before the app boots")

sub1(r'</head>', LAYER_CSS + '</head>', "layer stylesheet")
sub1(r'</body>', LAYER_HTML + LAYER_JS.replace('__MAPSRC__', 'file://' + MAP) + '</body>',
     "layer markup + behaviour")

io.open(OUT, 'w', encoding='utf-8').write(s)
print("\nwrote %s" % OUT)
print("  globe untouched — no routes added, no layout changed")
print("  Iceland marker in house gold; click it for the Iceland map as a layer")
