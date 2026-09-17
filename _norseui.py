#!/usr/bin/env python3
"""Puts the Norse globe into the Iceland map's UI language.

Before: six separate pieces of floating chrome (era pills, an emoji tool row, a
brand card with two more buttons, a play bar, a zoom box, a search field) in the
globe's own cold blue-grey glass. It read as a different project.

After: ONE command menu, the same object as the Iceland map's Vegvisir — a
vertical column pinned top-left, headed by a grip you click to fold, gold
24x24 stroked icons, Norse display labels, warm house glass. The two bars that
genuinely are not menu items (the timeline scrubber, the zoom box) stay where
they are and get the house treatment.

HOW IT WORKS — and why it is safe. The globe's own controls are NOT rewritten.
Every row in the new menu is a PROXY: it calls .click() on the original control,
which is still in the DOM, just hidden. The globe's handlers never know anything
changed. A MutationObserver copies the original's `on` class back onto the row,
so the lit state stays true even when the globe lights something itself.

The one exception is the era chips: those are MOVED into a sub-panel rather than
proxied, because moving a node keeps its listeners and there are seven of them.

The four direction colours are DATA, not decoration - N blue, E amber, S red,
W green, straight off ARC_COL. So the icons sit gold like every other icon in
the house until a direction is lit, and then that row takes its own arc colour.
Both systems get to keep what they meant.

Values are lifted from map.html, not eyeballed:
  icons     viewBox 0 0 24 24, fill none, stroke currentColor, width 2-2.2,
            round caps and joins
  panel     var(--sheen) over var(--glass), var(--blur), 1px var(--hair),
            var(--shadow) + var(--ring), radius 32/22
  rows      42px tall, 12px gap, icon 22px, label var(--display) 16px 700
            uppercase 0.06em, line-height clamped to 1 (Norse has huge vertical
            metrics and every row inflates without it)
  lit       color var(--gold), background rgba(212,169,74,0.18),
            drop-shadow(0 0 7px rgba(212,169,74,.55))
  grip      rgba(212,169,74,0.10), hover .20, 1px bottom hair at .22

Run order:  _twolayer.py  ->  _norseui.py  ->  _gate.py
"""
import io, os, re

TARGET = os.path.expanduser("~/Documents/RitchWiki/norse-ICELAND-LAYER-MOCKUP.html")

s = io.open(TARGET, encoding="utf-8", errors="ignore").read()
if 'id="tabbar"' in s:
    raise SystemExit("command menu already present - rebuild with _twolayer.py first")
if 'id="gate"' in s:
    raise SystemExit("run this BEFORE _gate.py, not after")

def sub1(pat, rep, label):
    global s
    s2, n = re.subn(pat, rep, s, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("!! no single match for: " + label)
    s = s2
    print("   ok  %s" % label)

# ---------------------------------------------------------------- icons
# Drawn in the Iceland map's own hand: 24x24, stroked, round joins, no fill.
I = {
 # a compass needle swung north
 "N": '<path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/><circle cx="12" cy="12" r="6.6"/><path d="M12 8.2l2 5.6-2-1.4-2 1.4z"/>',
 # a sun coming up over a line - east
 "E": '<path d="M3 19h18"/><path d="M6.5 15.5a5.5 5.5 0 0 1 11 0"/><path d="M12 5v2.4M5.6 8.1l1.7 1.7M18.4 8.1l-1.7 1.7"/>',
 # a sun high - south
 "S": '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.6v2.6M12 18.8v2.6M2.6 12h2.6M18.8 12h2.6M5.3 5.3l1.9 1.9M16.8 16.8l1.9 1.9M18.7 5.3l-1.9 1.9M7.2 16.8l-1.9 1.9"/>',
 # open water - west
 "W": '<path d="M2 8.5c2.6 0 2.6 2 5.3 2s2.7-2 5.4-2 2.6 2 5.3 2 3-2 3-2"/><path d="M2 13.5c2.6 0 2.6 2 5.3 2s2.7-2 5.4-2 2.6 2 5.3 2 3-2 3-2"/><path d="M2 18.5c2.6 0 2.6 2 5.3 2s2.7-2 5.4-2"/>',
 # a sailed track between two landfalls
 "R": '<circle cx="4.6" cy="18.4" r="2.1"/><circle cx="19.4" cy="5.6" r="2.1"/><path d="M6.4 17C9 14 8 10.6 11 9.2c2.6-1.2 4.6.4 6.6-1.8" stroke-dasharray="3 3"/>',
 # a raised banner - realms held
 "M": '<path d="M6 21V4"/><path d="M6 5.2c3.4-1.7 6.8 1.7 10.2 0v7.6c-3.4 1.7-6.8-1.7-10.2 0z"/>',
 # a valknut-ish knot for life and culture
 "C": '<path d="M12 3.2l7.4 12.9H4.6z"/><path d="M12 8.6l4.2 7.3H7.8z"/>',
 # an hourglass - the eras
 "T": '<path d="M6.5 3h11M6.5 21h11"/><path d="M7.6 3c0 5 4.4 6.2 4.4 9s-4.4 4-4.4 9"/><path d="M16.4 3c0 5-4.4 6.2-4.4 9s4.4 4 4.4 9"/>',
 # a key to the map
 "L": '<rect x="3.2" y="4.2" width="17.6" height="15.6" rx="2.4"/><path d="M3.2 9.4h17.6"/><path d="M6.6 13h3M6.6 16.4h3M13 13h4.4M13 16.4h4.4"/>',
 # out of the app altogether, to the website
 "S": '<path d="M13.4 4.2H19.8V10.6"/><path d="M19.8 4.2 11.2 12.8"/><path d="M16.6 14.4v4.6a1.8 1.8 0 0 1-1.8 1.8H5a1.8 1.8 0 0 1-1.8-1.8V9.2A1.8 1.8 0 0 1 5 7.4h4.6"/>',
 # the way back out to the three doors
 "H": '<path d="M3.6 11.2L12 4l8.4 7.2"/><path d="M5.8 10v9.4h12.4V10"/><path d="M9.8 19.4v-5.2h4.4v5.2"/>',
 # a longship track - the journeys
 "J": '<path d="M3 15.5c3 2 15 2 18 0"/><path d="M5.2 17.6c2.6 2.2 11 2.2 13.6 0"/><path d="M12 4v9"/><path d="M7.4 6.4h9.2c0 3-1 5-1.6 6.2H9c-.6-1.2-1.6-3.2-1.6-6.2z"/>',
}
def svg(k, w="2"):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="%s" '
            'stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (w, I[k]))

# rows:  key, label, icon, the original control this proxies, arc colour or None
ROWS = [
 ("home",    "Maps",     "H", None,                        None),
 ("website", "Website",  "S", None,                        None),
 ("north",   "North",    "N", '.tool[data-arc="N"]',       "var(--n,#5bc0ff)"),
 ("east",    "East",     "E", '.tool[data-arc="E"]',       "var(--e,#e3b341)"),
 ("south",   "South",    "S", '.tool[data-arc="S"]',       "var(--s,#e2554b)"),
 ("west",    "West",     "W", '.tool[data-arc="W"]',       "var(--w,#3ec6a0)"),
 ("routes",  "Routes",   "R", '.tool[data-routes]',        None),
 ("realms",  "Realms",   "M", '.tool[data-realms]',        None),
 ("culture", "Culture",  "C", '#cultureTool',              None),
 ("eras",    "Eras",     "T", None,                        None),
 ("legend",  "Legend",   "L", '#legendBtn',                None),
 ("journeys","Journeys", "J", '#journeysBtn',              None),
]

rows_html = "".join(
  '<button class="tab" data-nav="%s"%s><span class="ti">%s</span>'
  '<span class="tl">%s</span></button>' % (
     k, (' data-proxy=\'%s\'' % p) if p else '', svg(ic), lbl)
  for k, lbl, ic, p, _ in ROWS)

arc_css = "".join(
  '#tabbar .tab[data-nav="%s"].on{color:%s;}'
  '#tabbar .tab[data-nav="%s"].on .ti svg{color:%s;'
  'filter:drop-shadow(0 0 7px %s);}\n' % (k, c, k, c, c)
  for k, _, _, _, c in ROWS if c)

VEGVISIR = io.open(
    os.path.expanduser("~/Documents/RitchWiki/_vegvisir.svg"), encoding="utf-8").read()

NAV = """
<nav id="tabbar" aria-label="Command menu">
  <div class="tabs">
    <div id="menuGrip" title="Fold the menu">
      <span class="vg-mark" aria-hidden="true">__VEGVISIR__</span>
      <span class="grip-runes">Vegv&iacute;sir</span>
      <svg class="vg-caret" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 9l7 7 7-7"/></svg>
    </div>
    __ROWS__
  </div>
  <div id="eraSub" class="vg-sub"></div>
</nav>
""".replace("__ROWS__", rows_html)

CSS = """
<style id="norse-house-ui">
/* ============================================================
   ONE command menu, in the Iceland map's language.
   Every value here is lifted from map.html, not eyeballed.
   ============================================================ */

/* the globe's own scattered chrome steps aside - the controls stay in the DOM
   because the new menu clicks them, they just stop being furniture */
html body #bar, html body #eras, html body .brandbtns{
  display:none!important;}
/* the zoom box and the Find field go entirely - scroll zooms, drag turns, and
   the menu is the way in. They stay in the DOM so nothing that references
   them throws; they just stop being furniture. */
html body #bl-controls{display:none!important;}

/* ---- the column ---- */
#tabbar{position:fixed;left:14px;top:14px;z-index:1003;
  display:flex;flex-direction:column;align-items:flex-start;gap:8px;
  max-width:calc(100vw - 28px);}
#tabbar .tabs{display:flex;flex-direction:column;align-items:stretch;gap:2px;padding:8px;
  border-radius:22px;min-width:244px;
  background:var(--sheen), var(--glass);
  backdrop-filter:var(--blur);-webkit-backdrop-filter:var(--blur);
  border:1px solid var(--hair);box-shadow:var(--shadow), var(--ring);
  max-height:min(78vh,620px);overflow-y:auto;overflow-x:hidden;scrollbar-width:none;}
#tabbar .tabs::-webkit-scrollbar{display:none;}

/* ---- the grip: the closed state has to look like a control, not a badge ---- */
/* Ritchie's traced vegvisir, the same file the Iceland map draws from */
#menuGrip .vg-mark{flex:0 0 auto;display:inline-flex;width:24px;height:24px;
  color:var(--gold);pointer-events:none;}
#menuGrip .vg-mark svg{width:24px;height:24px;display:block;}
#menuGrip{flex:none;display:flex;align-items:center;gap:9px;
  cursor:pointer;user-select:none;padding:9px 12px 8px;border-radius:14px;margin:-2px 0 6px;
  background:rgba(212,169,74,0.10);border-bottom:1px solid rgba(212,169,74,0.22);}
#menuGrip:hover{background:rgba(212,169,74,0.20);}
#menuGrip .grip-runes{flex:1 1 auto;font-family:var(--display);font-weight:700;font-size:19px;
  line-height:1;height:19px;letter-spacing:0.05em;text-transform:uppercase;color:var(--gold);
  pointer-events:none;}
#menuGrip .vg-caret{flex:0 0 auto;width:12px;height:12px;color:var(--gold);opacity:.75;
  transition:transform .22s ease, opacity .22s ease;transform:rotate(180deg);pointer-events:none;}
body.menu-hidden #menuGrip .vg-caret{transform:rotate(0deg);opacity:.9;}
body.menu-hidden #tabbar .tabs{min-width:0;max-height:none;}
body.menu-hidden #tabbar .tab{display:none!important;}
body.menu-hidden #menuGrip{margin:0;border-bottom:none;background:transparent;}
body.menu-hidden #eraSub{display:none!important;}

/* ---- the rows ---- */
#tabbar .tab{display:flex;flex-direction:row;align-items:center;gap:12px;
  border:none;background:transparent;color:var(--tx);cursor:pointer;
  width:100%;height:42px;min-height:42px;box-sizing:border-box;
  padding:0 12px;border-radius:14px;font:inherit;text-align:left;
  transition:color .18s, background .18s;}
#tabbar .tab:hover{background:rgba(244,240,230,0.05);}
#tabbar .tab .ti{width:22px;height:22px;flex:none;display:grid;place-items:center;color:var(--gold);}
#tabbar .tab .ti svg{width:22px;height:22px;display:block;}
/* Norse has huge vertical metrics - clamp the line box or every row inflates */
#tabbar .tab .tl{font-family:var(--display);font-weight:700;font-size:16px;
  letter-spacing:0.06em;text-transform:uppercase;line-height:1;height:16px;
  margin:0;display:block;white-space:nowrap;}
/* THE RULE: rows above the hairline LEAVE, rows below it ACT on the map.
   Maps and Website are the two exits, in that order, on both maps. */
#tabbar .tab[data-nav="website"]{margin-bottom:6px;padding-bottom:0;
  border-bottom:1px solid rgba(212,169,74,0.18);border-radius:0 0 14px 14px;}
#tabbar .tab.on{color:var(--gold);background:rgba(212,169,74,0.18);
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.16);}
#tabbar .tab.on .ti svg{filter:drop-shadow(0 0 7px rgba(212,169,74,0.55));}

/* the four directions are DATA. Gold until lit, then their own arc colour. */
__ARCCSS__

/* ---- the era sub-panel, hung off the column like map.html's .vg-sub ---- */
#eraSub{display:none;position:fixed;z-index:1002;
  flex-wrap:wrap;gap:6px;padding:10px;border-radius:18px;width:236px;
  background:var(--sheen), var(--glass);
  backdrop-filter:var(--blur);-webkit-backdrop-filter:var(--blur);
  border:1px solid var(--hair);box-shadow:var(--shadow), var(--ring);}
#eraSub.open{display:flex;}
#eraSub .chip{position:static!important;font-family:var(--display)!important;font-weight:700!important;
  font-size:13px!important;letter-spacing:.05em!important;text-transform:uppercase!important;
  padding:7px 12px!important;border-radius:999px!important;cursor:pointer;
  color:var(--tx2)!important;border:1px solid var(--hair)!important;background:transparent!important;}
#eraSub .chip:hover{color:var(--tx)!important;}
#eraSub .chip.on{color:var(--gold)!important;background:rgba(212,169,74,0.18)!important;
  border-color:rgba(212,169,74,0.55)!important;}


/* ============================================================
   THE PANELS THE MENU OPENS
   Legend and Journeys were absolutely positioned inside #brand, bottom-left,
   opening upward off a button that no longer exists. They now hang off the
   command menu the way map.html's sub-panels hang off the Vegvisir, and wear
   the same glass.
   ============================================================ */
html body #legend, html body #journeys{
  position:fixed!important;left:14px!important;top:auto!important;right:auto!important;
  bottom:auto!important;margin:0!important;z-index:1002!important;
  width:250px!important;max-height:min(56vh,440px)!important;overflow-y:auto!important;
  padding:12px 14px!important;border-radius:18px!important;
  background:var(--sheen), var(--glass)!important;
  backdrop-filter:var(--blur)!important;-webkit-backdrop-filter:var(--blur)!important;
  border:1px solid var(--hair)!important;box-shadow:var(--shadow), var(--ring)!important;}
/* every panel flies out BESIDE its own row, the way Iceland's do. The script
   sets these two per panel at open time - the column's height changes, so a
   fixed offset would be a guess. */
html body #legend, html body #journeys, html body #eraSub{
  left:var(--sub-x,214px)!important;top:var(--sub-y,88px)!important;}

/* headers in the house voice */
html body #legend .hdr, html body #journeys .hdr{
  font-family:var(--display)!important;font-weight:700!important;font-size:13px!important;
  letter-spacing:.06em!important;text-transform:uppercase!important;line-height:1!important;
  color:var(--gold)!important;opacity:1!important;margin:12px 0 6px!important;}
html body #legend .hdr:first-child, html body #journeys .hdr:first-child{margin-top:0!important;}
html body #legend .row, html body #journeys .jrow{
  color:var(--tx2)!important;font-size:12px!important;line-height:1.35!important;}
html body #legend .row b{color:var(--tx)!important;}
html body #journeys .jrow{border-radius:10px!important;padding:6px 8px!important;}

/* Culture: a centred sheet, house glass, Norse heading, a proper close control */
html body #themePanel{border-radius:22px!important;padding:18px 20px!important;
  background:var(--sheen), var(--glass)!important;
  backdrop-filter:var(--blur)!important;-webkit-backdrop-filter:var(--blur)!important;
  border:1px solid var(--hair)!important;box-shadow:var(--shadow), var(--ring)!important;}
html body #themePanel .thead{font-family:var(--display)!important;font-weight:700!important;
  font-size:19px!important;letter-spacing:.06em!important;text-transform:uppercase!important;
  color:var(--gold)!important;margin-bottom:14px!important;}
html body #themePanel .thead em{font-family:var(--serif),Georgia,serif!important;
  font-size:12.5px!important;letter-spacing:0!important;text-transform:none!important;
  color:var(--tx2)!important;}
html body #themePanel .x2{background:rgba(212,169,74,0.14)!important;color:var(--gold)!important;
  border:1px solid var(--hair)!important;}
html body #themePanel .x2:hover{background:rgba(212,169,74,0.28)!important;}

/* the info card */
html body #card{border-radius:20px!important;overflow:hidden!important;
  background:var(--sheen), var(--glass)!important;
  backdrop-filter:var(--blur)!important;-webkit-backdrop-filter:var(--blur)!important;
  border:1px solid var(--hair)!important;box-shadow:var(--shadow), var(--ring)!important;}
html body #card .hd{font-family:var(--display)!important;font-weight:700!important;
  letter-spacing:.05em!important;text-transform:uppercase!important;color:var(--gold)!important;}
html body #card .sites .site{background:rgba(212,169,74,0.12)!important;
  border:1px solid var(--hair)!important;color:var(--tx)!important;}
html body #card .sites .site:hover{background:rgba(212,169,74,0.26)!important;}

/* ---- the title becomes a pill, the same object as the Iceland map's ---- */
html body #brand{width:auto!important;max-width:none!important;height:auto!important;
  padding:9px 18px 10px!important;border-radius:999px!important;
  display:inline-flex!important;flex-direction:column!important;align-items:flex-start!important;
  gap:0!important;left:14px!important;bottom:14px!important;}
html body #brand h1{font-size:18px!important;}
html body #brand .sub{margin-top:3px!important;font-size:9.5px!important;
  letter-spacing:0.3em!important;text-transform:uppercase!important;color:var(--tx2)!important;}
html body #count{margin-top:5px!important;font-size:11px!important;color:var(--tx2)!important;}

/* ============================================================
   WHEN THE ISLAND IS UP, THE GLOBE'S FURNITURE GETS OFF THE SCREEN.
   The Iceland map has its own Vegvisir inside the frame. Two command menus
   stacked on top of each other was the single worst thing on screen.
   ============================================================ */
/* #scene included: without it the globe faded back in during the handover and
   you saw it arrive and get covered. */
html body.island-open #scene,
html body.island-open #tabbar, html body.island-open #eraSub,
html body.island-open #brand, html body.island-open #timeline,
html body.island-open #bl-controls, html body.island-open #legend,
html body.island-open #journeys, html body.island-open #card,
html body.island-open #themePanel{
  opacity:0!important;visibility:hidden!important;pointer-events:none!important;}


/* ---- while the globe is being turned, the furniture yields ---- */
html body.vg-yield #tabbar, html body.vg-yield #eraSub,
html body.vg-yield #timeline, html body.vg-yield #bl-controls, html body.vg-yield #brand,
html body.vg-yield #legend, html body.vg-yield #journeys{
  opacity:.12!important;pointer-events:none!important;transition:opacity .16s ease-out!important;}
#tabbar,#eraSub,#timeline,#bl-controls,#brand{transition:opacity .28s ease;}

/* ---- the timeline is the one bar that is not a menu item ---- */
/* it belongs at the FOOT of the globe, not over the top of it */
html body #timeline{
  top:auto!important;bottom:calc(18px + env(safe-area-inset-bottom))!important;
  transform:translateX(-50%) scale(var(--ui,1))!important;transform-origin:50% 100%!important;
  border-radius:999px!important;
  background:var(--sheen), var(--glass)!important;border:1px solid var(--hair)!important;
  box-shadow:var(--shadow), var(--ring)!important;}
html body #play{background:var(--gold)!important;color:#0d0d0f!important;border:none!important;}
html body #yr{font-family:var(--display)!important;font-weight:700!important;font-size:13px!important;
  letter-spacing:.06em!important;text-transform:uppercase!important;color:var(--gold)!important;}
html body #fill{background:var(--gold)!important;}
html body #knob{background:var(--gold)!important;box-shadow:0 0 10px rgba(212,169,74,.6)!important;}
html body #bl-controls{border-radius:22px!important;
  background:var(--sheen), var(--glass)!important;border:1px solid var(--hair)!important;
  box-shadow:var(--shadow), var(--ring)!important;}
html body .zbtn{color:var(--tx)!important;}
html body .zbtn:hover{color:var(--gold)!important;}
html body #search .si{filter:grayscale(1) brightness(1.6);opacity:.55;}
html body #q{font-family:var(--serif,inherit)!important;color:var(--tx)!important;}

/* the title card loses its buttons, so it becomes a plain plaque */
html body #brand{border-radius:22px!important;}

@media (max-width:560px){
  #tabbar{left:10px;top:10px;}
  #tabbar .tabs{min-width:212px;}
  #tabbar .tab{height:40px;min-height:40px;}
  #tabbar .tab .tl{font-size:14px;height:14px;}
}
</style>
""".replace("__ARCCSS__", arc_css)

JS = """
<script>
/* The command menu is a PROXY, never a rewrite. Each row clicks the globe's own
   control - still in the DOM, just no longer furniture - so none of the globe's
   handlers know anything changed, and a MutationObserver copies the original's
   `on` class back onto the row so the lit state stays true even when the globe
   lights something by itself. */
(function(){
  var nav=document.getElementById('tabbar');
  var grip=document.getElementById('menuGrip');
  var sub=document.getElementById('eraSub');
  if(!nav||!grip||!sub) return;

  /* the era chips are MOVED, not proxied - moving a node keeps its listeners
     and there are seven of them */
  var eras=document.getElementById('eras');
  if(eras){ while(eras.firstChild){ sub.appendChild(eras.firstChild); } }

  function src(row){
    var q=row.getAttribute('data-proxy');
    return q ? document.querySelector(q) : null;
  }

  nav.querySelectorAll('.tab').forEach(function(row){
    if(row.getAttribute('data-nav')==='website'){
      row.addEventListener('click', function(){
        window.location.href='https://www.iguideiceland.is/';
      });
      return;
    }
    if(row.getAttribute('data-nav')==='home'){
      row.addEventListener('click', function(){
        /* the gate is the home page. _gate.py hands us the way back up. */
        if(typeof window.__raiseGate==='function') window.__raiseGate();
      });
      return;
    }
    if(row.getAttribute('data-nav')==='eras'){
      row.addEventListener('click', function(){
        var willOpen = !sub.classList.contains('open');
        closeSubs('eras');
        sub.classList.toggle('open', willOpen);
        setTimeout(syncSubs, 10);
      });
      return;
    }
    var el=src(row);
    if(!el){ row.style.display='none'; return; }
    row.addEventListener('click', function(){
      var k=row.getAttribute('data-nav');
      if(SUBS[k]) closeSubs(k);
      el.click();
      if(SUBS[k]) setTimeout(syncSubs, 10);
    });
    /* mirror the original's lit state, whoever changed it */
    var mirror=function(){ row.classList.toggle('on', el.classList.contains('on')); };
    mirror();
    new MutationObserver(mirror).observe(el,{attributes:true,attributeFilter:['class']});
  });

  /* ---- Iceland's sub-menu manners, on the globe ----------------------
     A row flies its panel out BESIDE itself, only ever one is open, and a tap
     on the globe folds it away. Measured at open time: the column's height
     changes with the menu's state, so any fixed offset would be a guess. */
  var SUBS = {
    eras:     {el: sub,                                  cls: 'open'},
    legend:   {el: document.getElementById('legend'),    cls: 'show'},
    journeys: {el: document.getElementById('journeys'),  cls: 'show'}
  };
  function isOpen(k){
    var S=SUBS[k]; return !!(S && S.el && S.el.classList.contains(S.cls));
  }
  function place(k){
    var S=SUBS[k]; if(!S || !S.el) return;
    var row=nav.querySelector('.tab[data-nav="'+k+'"]'); if(!row) return;
    var r=nav.getBoundingClientRect(), q=row.getBoundingClientRect();
    var h=S.el.offsetHeight || 220;
    S.el.style.setProperty('--sub-x', Math.round(r.right+8)+'px');
    S.el.style.setProperty('--sub-y',
      Math.round(Math.max(8, Math.min(q.top, window.innerHeight-h-14)))+'px');
  }
  function closeSubs(except){
    Object.keys(SUBS).forEach(function(k){
      if(k===except) return;
      var S=SUBS[k]; if(!S || !S.el) return;
      if(S.el.classList.contains(S.cls)){
        if(k==='eras') S.el.classList.remove('open');
        else { var btn=document.querySelector(k==='legend'?'#legendBtn':'#journeysBtn');
               if(btn) btn.click(); else S.el.classList.remove('show'); }
      }
      var row=nav.querySelector('.tab[data-nav="'+k+'"]'); if(row) row.classList.remove('on');
    });
  }
  function syncSubs(){
    Object.keys(SUBS).forEach(function(k){
      var row=nav.querySelector('.tab[data-nav="'+k+'"]');
      var on=isOpen(k);
      if(row) row.classList.toggle('on', on);
      if(on) place(k);
    });
  }
  Object.keys(SUBS).forEach(function(k){
    var S=SUBS[k]; if(!S || !S.el) return;
    new MutationObserver(function(){ syncSubs(); })
      .observe(S.el, {attributes:true, attributeFilter:['class']});
  });
  window.__closeSubs = function(){ closeSubs(null); };
  window.__placeSubs = syncSubs;
  window.addEventListener('resize', syncSubs);
  syncSubs();

  /* the island layer opening is the globe's cue to clear the screen */
  var iceLayer=document.getElementById('iceLayer');
  if(iceLayer){
    var seen=function(){
      var up = iceLayer.classList.contains('show') ||
               (iceLayer.style.display && iceLayer.style.display!=='none');
      document.body.classList.toggle('island-open', !!up);
      if(up){ closeSubs(null); setTimeout(syncSubs, 10); }
    };
    seen();
    new MutationObserver(seen).observe(iceLayer,{attributes:true,attributeFilter:['class','style']});
  }

  /* fold the column down to the grip */
  grip.addEventListener('click', function(){
    document.body.classList.toggle('menu-hidden');
  });

  /* while the globe is being turned the furniture gets out of the way, and a
     tap on the globe folds the era panel - the map is the point, the menus
     are the tools */
  var scene=document.getElementById('scene')||document.body, t=null;
  function yield_(){
    document.body.classList.add('vg-yield');
    clearTimeout(t); t=setTimeout(function(){
      document.body.classList.remove('vg-yield'); }, 700);
  }
  scene.addEventListener('pointerdown', function(e){
    if(e.target.closest && e.target.closest('#tabbar,#eraSub,#timeline,#bl-controls,#brand,#card,#gate')) return;
    yield_(); closeSubs(null); setTimeout(syncSubs, 10);
  }, true);
  scene.addEventListener('wheel', yield_, {passive:true});
})();
</script>
"""

head = "</" + "head>"
body = "</" + "body>"
sub1(re.escape(head), CSS + head, "house UI stylesheet into the head")
sub1(re.escape(body), NAV.replace("__VEGVISIR__", VEGVISIR) + JS + body,
     "command menu markup + proxy behaviour")

io.open(TARGET, "w", encoding="utf-8").write(s)
print("\nthe globe now speaks the Iceland map's UI language")
print("  one command menu, %d rows, gold stroked icons, Norse labels" % len(ROWS))
print("  #bar, #eras and the brand buttons hidden - the controls themselves are untouched")
print("  timeline and zoom box restyled to house glass")
