#!/usr/bin/env python3
"""Adds the entry gate to the two-layer mockup: three doors and nothing else.

    The Norse Expansion   -> the globe
    Iceland               -> the Iceland map layer
    iGuide Iceland        -> back out to iguideiceland.is

All three doors share ONE anatomy, the site's own brandmark lockup:
44px round emblem + gold Cormorant name + letterspaced uppercase sub.
No glass cards, no emoji, no paragraphs - three of the same object.

Emblems (all gold, all 1.5px-equivalent stroke at 44px, no vegvisir):
  Norse   - a knarr under sail, drawn as a fine line engraving to sit beside
            the crest rather than shout over it: sheer, keel, two clinker
            strakes, tapering stem and stern posts, and the rope lattice that
            reinforced a Norse square sail (Gotland picture stones, Bayeux
            Tapestry). The ocean-going cargo ship, not a longship.
            Drawn from Skuldelev 1 at the Viking Ship Museum, Roskilde - the
            museum's own words are "a rounded form that gives it a high loading
            capacity and great seaworthiness on the North Atlantic", with
            "decks fore and aft as well as an open hold amidships". Ottar, its
            reconstruction, is 15.80 m x 4.80 m, 1.20 m draught, 90 m2 of sail
            and only FOUR oars - so the sail is the story, and the hull is
            drawn deep and full at roughly its real 3.3:1 length-to-beam.
            https://www.vikingeskibsmuseet.dk/en/professions/the-boat-collection/ottar
  Iceland - the real coastline, Natural Earth 10m, RDP-simplified to 186 points
  Site    - the real logo-crest.webp, round-masked as everywhere else

Every word on screen is lifted from the apps themselves, nothing invented:
  "Norse Expansion" / "The Viking world - 793-1200"  -> globe #brand
  "Interactive Map of Iceland"                       -> map.html <h1>
  "iGuide Iceland"                                   -> map.html brandmark
The one word NOT lifted is this door's sub: the brandmark says "Local guide"
everywhere else, but on the gate this door leaves for the website, so it says
"Website". A label on a door names where the door goes.

The globe loads while the gate is up but is NOT shown behind it - Ritchie's
call, and he is right: three doors on a spinning Earth is a busy place to make
a choice. It is faded, not removed, because a WebGL canvas pulled out of layout
can lose its drawing buffer and it must be ready the moment a door is picked. The stylesheet goes in the HEAD and
`gate-up` is stamped straight onto the body tag, so the globe's own controls are
hidden from the first paint - added by script at the end of the body they got a
frame or two on screen first, and the play button and timeline visibly dissolved
on every refresh. Run _twolayer.py first; this patches
its output.

WARNING: never put a literal closing-body tag in a comment in this file - the
patcher matches the first one it finds and will inject the gate into the note.
"""
import base64, io, os, re

SITE  = os.path.expanduser("~/Documents/iGuide-Iceland-Site")
TARGET = os.path.expanduser("~/Documents/RitchWiki/norse-ICELAND-LAYER-MOCKUP.html")

# Iceland coastline: Natural Earth 10m admin-0, mainland ring only (3063 pts),
# equirectangular x*cos(65.0N), Douglas-Peucker eps 0.022 deg -> 442 points,
# normalised into a 0-100 box. Islets dropped - they are noise at 44px.
ICELAND_PATH = "M90.4,19.3 L86.5,21.5 L86.9,23.5 L84.8,25.2 L85.8,25.6 L85.7,26.6 L87.8,26.8 L89.0,26.1 L89.9,27.7 L89.6,30.1 L87.4,32.8 L88.4,32.1 L87.8,33.4 L92.5,32.4 L91.9,33.7 L93.0,34.7 L90.4,38.4 L92.6,35.2 L93.8,35.6 L93.3,34.9 L95.2,36.1 L96.7,35.9 L97.3,37.8 L98.1,37.2 L99.0,38.2 L98.5,41.1 L97.0,41.4 L97.9,42.2 L95.4,43.2 L98.3,42.7 L99.4,43.6 L98.6,44.5 L95.2,45.0 L98.9,45.0 L98.7,45.8 L97.8,46.1 L98.9,47.0 L99.8,45.6 L100.0,47.5 L99.3,49.1 L97.5,49.5 L95.2,47.5 L95.2,48.4 L93.4,48.5 L96.2,49.0 L98.0,50.6 L97.9,51.2 L95.0,50.7 L97.4,51.9 L97.0,53.0 L95.8,52.8 L97.0,53.6 L95.4,53.6 L95.6,54.9 L93.0,55.8 L90.8,53.6 L93.0,56.8 L91.0,56.7 L91.8,57.7 L90.3,58.0 L90.7,58.9 L92.4,57.8 L90.6,62.1 L88.7,62.6 L90.3,61.9 L89.0,61.6 L86.9,63.9 L87.5,64.8 L87.1,65.2 L85.5,64.4 L84.4,65.1 L84.6,64.4 L83.8,63.7 L83.5,64.3 L82.1,62.3 L83.1,63.6 L82.8,65.0 L77.4,67.8 L73.1,73.0 L70.3,73.9 L70.2,75.2 L69.3,73.8 L69.1,75.1 L68.9,73.8 L68.6,75.5 L68.6,72.6 L68.3,75.3 L66.4,74.9 L63.2,76.3 L63.3,75.5 L61.8,77.3 L62.7,76.4 L61.8,75.6 L59.6,77.9 L61.1,78.0 L60.5,79.0 L59.5,79.1 L60.5,79.3 L59.6,81.2 L57.5,82.3 L58.2,81.0 L56.4,80.7 L56.8,82.4 L57.6,82.5 L52.6,84.0 L47.6,83.0 L43.5,80.7 L39.5,80.8 L36.1,77.1 L36.6,76.0 L38.3,76.7 L37.1,75.5 L37.4,74.4 L35.9,77.1 L34.2,75.8 L35.6,75.9 L34.6,75.6 L34.9,73.9 L33.7,75.6 L30.5,73.6 L30.3,72.4 L31.7,72.1 L29.9,71.9 L29.4,72.7 L30.2,73.4 L28.9,73.4 L28.7,74.2 L26.1,74.5 L24.9,73.7 L22.4,74.5 L20.0,73.9 L16.7,75.0 L16.4,73.3 L17.3,72.0 L16.4,71.5 L16.7,69.0 L18.3,71.4 L22.6,69.8 L23.3,69.3 L22.7,68.5 L23.8,68.2 L22.6,67.5 L24.8,67.9 L24.7,67.2 L25.7,66.8 L25.2,67.0 L25.6,66.3 L24.7,65.8 L23.7,65.8 L25.2,63.4 L26.6,62.7 L28.1,63.0 L28.0,62.3 L26.4,62.2 L23.4,64.5 L22.1,64.1 L24.3,62.5 L22.6,62.1 L23.2,60.0 L25.0,59.2 L24.7,58.7 L25.7,57.7 L27.6,58.6 L26.8,57.6 L25.9,57.6 L27.4,56.8 L25.7,57.3 L26.1,56.5 L22.9,59.5 L22.7,58.7 L21.5,61.0 L20.7,60.4 L20.8,58.5 L19.9,58.9 L19.0,56.5 L19.7,57.0 L21.3,54.9 L19.4,56.3 L20.1,54.6 L19.1,54.3 L19.3,53.1 L17.0,54.3 L16.9,53.6 L16.0,53.6 L16.3,54.1 L11.7,52.9 L9.8,53.7 L8.9,53.2 L7.8,54.9 L6.4,55.2 L5.4,54.5 L4.3,51.6 L6.3,50.8 L8.2,51.5 L10.4,50.0 L11.6,50.9 L12.4,48.8 L13.2,49.0 L12.5,50.3 L13.0,51.0 L13.8,49.0 L14.5,49.6 L16.5,47.6 L16.2,48.7 L17.8,49.7 L17.3,49.0 L18.1,48.2 L24.6,48.5 L25.1,44.8 L22.7,46.8 L18.4,45.9 L18.0,45.6 L18.9,45.3 L18.0,45.3 L20.2,42.7 L25.8,39.5 L23.2,39.8 L23.1,38.3 L22.4,38.8 L22.0,37.8 L20.7,39.9 L19.5,38.6 L21.5,37.6 L22.0,36.4 L20.8,37.7 L19.9,37.8 L20.2,37.1 L18.7,38.3 L18.1,35.6 L18.1,37.2 L17.7,37.7 L17.3,37.0 L17.1,37.9 L16.8,35.8 L16.1,35.7 L16.4,38.4 L15.0,37.6 L15.7,36.3 L15.3,35.9 L14.8,37.0 L14.4,36.1 L14.1,37.4 L13.3,37.6 L12.3,36.8 L11.9,38.7 L10.3,38.2 L5.8,40.5 L5.0,40.2 L5.0,39.0 L0.0,38.3 L2.1,35.5 L5.9,38.0 L6.6,37.7 L4.1,35.2 L6.6,36.1 L4.2,34.0 L4.1,31.9 L8.3,34.0 L8.9,36.0 L11.4,34.6 L9.8,34.5 L9.1,33.6 L11.7,33.3 L12.2,32.4 L11.1,32.9 L7.3,32.5 L6.1,30.3 L6.7,29.2 L12.1,31.0 L8.7,29.7 L6.6,27.4 L7.1,26.0 L10.1,27.0 L10.6,27.9 L7.9,25.1 L9.6,24.9 L10.4,25.5 L8.5,24.5 L9.8,23.2 L12.6,24.5 L13.0,26.0 L13.7,25.3 L14.2,26.9 L13.4,28.4 L14.6,26.6 L14.8,27.5 L15.4,27.2 L14.5,28.8 L15.6,27.6 L15.6,29.6 L16.1,26.6 L16.8,26.4 L17.8,28.2 L17.1,31.2 L18.3,28.2 L19.0,29.7 L19.2,29.3 L19.1,31.0 L19.7,29.4 L18.6,27.0 L19.6,25.5 L18.6,26.0 L15.2,24.2 L14.2,22.6 L16.2,22.0 L18.0,22.9 L17.9,22.3 L19.7,21.7 L18.1,21.7 L18.6,20.7 L16.6,21.3 L17.5,19.6 L15.6,20.8 L15.5,19.9 L14.5,21.1 L12.7,20.6 L12.4,19.8 L13.5,19.9 L13.7,19.2 L12.7,18.3 L14.7,18.0 L15.1,18.5 L14.4,17.6 L16.7,18.6 L17.8,17.6 L19.1,18.4 L19.1,17.6 L21.2,20.4 L21.0,21.8 L23.2,21.7 L23.7,22.4 L23.1,23.0 L25.3,23.6 L26.0,27.2 L26.3,25.8 L27.1,25.5 L27.2,27.1 L29.1,27.5 L26.6,28.5 L28.4,28.4 L28.1,29.1 L29.3,29.0 L29.1,31.8 L27.8,32.7 L29.1,33.3 L28.1,34.3 L26.8,34.3 L25.9,32.6 L25.0,32.7 L26.5,35.4 L28.3,35.5 L27.7,37.1 L29.2,36.3 L29.2,38.0 L27.8,39.6 L29.2,38.9 L30.2,39.8 L31.3,45.7 L31.2,39.6 L32.8,41.9 L32.2,38.3 L32.8,36.3 L35.0,34.3 L35.3,37.3 L35.6,36.5 L36.8,38.6 L37.3,37.4 L36.3,36.8 L37.4,36.4 L37.6,37.8 L38.7,34.9 L37.1,27.0 L37.4,25.7 L40.3,24.8 L42.2,29.7 L43.8,30.4 L44.5,33.0 L45.1,33.4 L45.5,32.8 L46.1,33.5 L46.6,31.2 L45.6,28.5 L46.4,27.5 L46.2,26.2 L49.0,25.4 L49.7,26.1 L49.6,24.1 L50.7,23.5 L50.9,24.4 L51.8,23.3 L52.0,24.6 L53.0,24.0 L53.6,24.8 L53.3,25.7 L54.3,25.9 L54.4,28.2 L56.1,28.7 L57.3,30.5 L58.7,35.3 L58.6,31.3 L56.6,27.3 L56.6,23.8 L60.0,24.4 L63.3,29.6 L63.1,28.2 L63.8,27.9 L62.8,27.8 L64.2,27.8 L64.6,28.5 L65.1,25.6 L67.0,22.9 L68.4,23.3 L69.0,25.3 L70.5,24.4 L70.6,25.2 L71.0,24.5 L72.0,25.5 L71.2,24.1 L72.6,23.3 L71.7,24.1 L72.7,23.8 L73.5,24.5 L72.5,16.7 L72.8,17.1 L73.5,16.4 L73.6,17.2 L74.1,16.5 L74.5,17.2 L75.9,16.1 L77.2,16.0 L78.4,16.9 L77.9,18.5 L80.0,19.1 L80.3,20.2 L79.4,21.4 L80.1,22.6 L81.6,22.7 L83.0,24.4 L83.4,22.0 L85.5,21.6 L87.1,19.3 L90.4,19.3 Z"

def datauri(path, mime):
    return "data:%s;base64,%s" % (mime, base64.b64encode(open(path, "rb").read()).decode())

VEGVISIR = io.open(os.path.expanduser("~/Documents/RitchWiki/_vegvisir.svg"),
                   encoding="utf-8").read()

crest = datauri(os.path.join(SITE, "images/logo-crest.webp"), "image/webp")
norse = datauri(os.path.join(SITE, "fonts/Norse.woff2"), "font/woff2")
norseb = datauri(os.path.join(SITE, "fonts/NorseBold.woff2"), "font/woff2")

s = io.open(TARGET, encoding="utf-8", errors="ignore").read()
if 'id="gate"' in s:
    raise SystemExit("gate already present - rebuild with _twolayer.py first")

GATE_CSS = """
<style id="iguide-gate">
@font-face{font-family:'NorseG';src:url('__NORSE__') format('woff2');font-weight:400;font-display:swap;}
@font-face{font-family:'NorseG';src:url('__NORSEB__') format('woff2');font-weight:700;font-display:swap;}
#gate{position:fixed;inset:0;z-index:90;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:8px;
  background:radial-gradient(120% 90% at 50% 42%, #16161c 0%, #0d0d0f 58%, #08080b 100%);
  transition:opacity .55s ease, visibility .55s;}
#gate.gone{opacity:0;visibility:hidden;pointer-events:none;}

/* the ground: one enormous ghosted vegvisir, Ritchie's own traced artwork.
   0.07 at 74vmin - measured against 0.05 (vanishes in a bright room) and 0.10
   (competes with the doors), and against 58/92vmin for size. */
#gateMark{position:absolute;left:50%;top:50%;width:74vmin;height:74vmin;
  transform:translate(-50%,-50%);color:#d4a94a;opacity:.07;pointer-events:none;
  animation:vegTurn 240s linear infinite;}
#gateMark svg{width:100%;height:100%;display:block;}
@keyframes vegTurn{from{transform:translate(-50%,-50%) rotate(0deg);}
                   to{transform:translate(-50%,-50%) rotate(360deg);}}
@media (prefers-reduced-motion:reduce){ #gateMark{animation:none;} }

/* Nothing has been chosen yet, so none of the globe's own controls belong on
   screen. Hide every UI container while the gate is up and fade them in once a
   door is picked. #scene / #routefx stay - the spinning globe IS the backdrop.
   (Ids taken from the page itself, not guessed.) */
/* the globe is faded, not removed: a WebGL canvas taken out of layout can
   lose its drawing buffer, and it has to be ready the moment a door is picked */
body.gate-up #scene{opacity:0!important;}
#scene{transition:opacity .5s ease;}
body.gate-up #eras, body.gate-up #brand, body.gate-up #count,
body.gate-up #legend, body.gate-up #journeys, body.gate-up #bar,
body.gate-up #cultureTool, body.gate-up #timeline, body.gate-up #search,
body.gate-up #bl-controls, body.gate-up #themePanel, body.gate-up #card,
body.gate-up #tabbar, body.gate-up #eraSub{
  opacity:0!important;visibility:hidden!important;pointer-events:none!important;
  transition:none!important;}
/* the fade belongs to the way OUT, never the way in. Scoping it to
   :not(.gate-up) is what stops the play button and the timeline dissolving
   on screen for half a second on every single refresh. */
body:not(.gate-up) #eras, body:not(.gate-up) #brand, body:not(.gate-up) #count,
body:not(.gate-up) #legend, body:not(.gate-up) #journeys, body:not(.gate-up) #bar,
body:not(.gate-up) #cultureTool, body:not(.gate-up) #timeline,
body:not(.gate-up) #search, body:not(.gate-up) #bl-controls,
body:not(.gate-up) #tabbar{
  transition:opacity .45s ease .05s;}

/* ---- ONE lockup, used three times. Rules lifted from map.html verbatim so
   the crest reads the way it does everywhere else: round-masked (the raw .webp
   has a black square baked in - the 50% radius is what hides it), wordmark
   beside it, gold Cormorant name, letterspaced uppercase sub. ---- */
/* the three doors share one left edge - a lockup family, not three loose
   labels. .doors is inline so it stays centred; the locks stretch inside it. */
#gate .doors{display:inline-flex;flex-direction:column;align-items:stretch;gap:2px;}
#gate .lock{display:flex;align-items:center;gap:16px;cursor:pointer;
  padding:11px 22px;border-radius:999px;border:1px solid transparent;
  transition:transform .18s ease,background .18s ease,border-color .18s ease;
  -webkit-tap-highlight-color:transparent;}
#gate .lock:hover{transform:translateY(-2px);background:rgba(212,169,74,0.07);
  border-color:rgba(212,169,74,0.26);}
#gate .lock:active{transform:translateY(0);}
#gate .bm-crest{width:64px;height:64px;border-radius:50%;object-fit:cover;background:#000;flex:none;}
#gate .bm-mark{width:64px;height:64px;border-radius:50%;flex:none;
  display:flex;align-items:center;justify-content:center;
  background:rgba(8,10,15,0.72);box-shadow:inset 0 0 0 1px rgba(212,169,74,0.30);
  color:#d4a94a;}
#gate .bm-mark svg{width:45px;height:45px;display:block;overflow:visible;}
#gate .lock:hover .bm-mark{box-shadow:inset 0 0 0 1px rgba(212,169,74,0.62),0 0 16px rgba(212,169,74,.20);}
#gate .bm-word{display:flex;flex-direction:column;line-height:1;text-align:left;}
#gate .bm-name{font-family:"Cormorant Garamond",Georgia,"Times New Roman",serif;
  font-size:1.58rem;font-weight:500;letter-spacing:0.01em;color:#d4a94a;white-space:nowrap;}
#gate .bm-sub{margin-top:4px;font-size:0.68rem;letter-spacing:0.3em;text-transform:uppercase;
  color:#cbc4b0;white-space:nowrap;}

/* a hairline between the two map doors and the way back to the website */
#gate .rule{width:auto;height:1px;margin:13px 8px 5px;
  background:linear-gradient(90deg,rgba(212,169,74,0) 0%,rgba(212,169,74,.34) 50%,rgba(212,169,74,0) 100%);}

@media (max-width:560px){
  #gate .bm-crest,#gate .bm-mark{width:50px;height:50px;}
  #gate .bm-mark svg{width:35px;height:35px;}
  #gate .bm-name{font-size:1.26rem;}
  #gate .bm-sub{font-size:0.6rem;letter-spacing:0.24em;}
  #gate .lock{gap:13px;padding:9px 16px;}
}
</style>
"""

# the app's own picture: a globe with a voyage arc springing off it
MARK_NORSE = """<svg viewBox="-3 -3 106 106" fill="none" stroke="currentColor" stroke-width="3.1"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <!-- mast and yard -->
  <path d="M50 14 V70"/>
  <path d="M28 22 H72"/>
  <!-- the square sail, drawing full. The FOOT ARCHES UP in the middle - that
       one curve is the whole trick: with the foot curving down it reads as a
       bucket, with it curving up it reads as a sail pulling. -->
  <path d="M29 23 C41 27 59 27 71 23 C72 35 71 45 70 52
           C61 44 39 44 30 52 C29 45 28 35 29 23 Z"/>
  <!-- the rope lattice that reinforced a Norse square sail, as shown on the
       Gotland picture stones and the Bayeux Tapestry. Only legible now the
       emblem is 64px - at 44px it turned the sail into a grille. -->
  <path d="M50 25.5 V47.5" opacity=".4"/>
  <path d="M39.5 25.6 C39.8 33 40 41 40.6 47.6" opacity=".33"/>
  <path d="M60.5 25.6 C60.2 33 60 41 59.4 47.6" opacity=".33"/>
  <path d="M29.4 33 C41 36.5 59 36.5 70.6 33" opacity=".33"/>
  <path d="M29.9 42 C41 45 59 45 70.1 42" opacity=".33"/>
  <!-- hull: long and shallow, not a bowl -->
  <path d="M9 64 C26 72 74 72 91 64"/>
  <path d="M13 68 C27 82 73 82 87 68"/>
  <path d="M10.6 66 C26.5 76 73.5 76 89.4 66" opacity=".55"/>
  <!-- stem and stern posts, curling inward - the Viking gesture -->
  <path d="M91 64 C99 48 96 33 86 31 C81 30 79 34 82 37"/>
  <path d="M9 64 C1 48 4 33 14 31 C19 30 21 34 18 37"/>
</svg>"""

MARK_ICELAND = """<svg viewBox="-4 12 108 76" aria-hidden="true">
  <path d="__ICEPATH__" fill="rgba(212,169,74,0.10)" stroke="currentColor"
    stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
</svg>"""

GATE_HTML = """
<div id="gate">
  <div id="gateMark" aria-hidden="true">__VEGVISIR__</div>
  <div class="doors">
  <div class="lock" id="goNorse">
    <span class="bm-mark">__MARK_NORSE__</span>
    <span class="bm-word">
      <span class="bm-name">Norse Expansion</span>
      <span class="bm-sub">The Viking world &middot; 793&ndash;1200</span>
    </span>
  </div>
  <div class="lock" id="goIceland">
    <span class="bm-mark">__MARK_ICELAND__</span>
    <span class="bm-word">
      <span class="bm-name">Iceland</span>
      <span class="bm-sub">Interactive map</span>
    </span>
  </div>
  <div class="rule"></div>
  <div class="lock" id="goSite" title="Back to iguideiceland.is">
    <img class="bm-crest" src="__CREST__" alt="">
    <span class="bm-word">
      <span class="bm-name">iGuide Iceland</span>
      <span class="bm-sub">Website</span>
    </span>
  </div>
  </div>
</div>
"""

GATE_JS = """
<script>
/* The gate: three doors on a plain ground, nothing else. The globe still
   loads while you are looking at this - it is just not shown, so the doors do
   not sit on a busy moving picture. */
(function(){
  var gate=document.getElementById('gate');
  document.body.classList.add('gate-up');
  function drop(){ gate.classList.add('gone'); document.body.classList.remove('gate-up'); }
  /* the gate IS the home page, so every map needs a way back up to it */
  window.__raiseGate = function(){
    /* the island's own bar is gone - close it properly instead of faking a
       click on a control that no longer exists */
    if(typeof window.__closeIsland==='function') window.__closeIsland();
    document.body.classList.remove('island-open');
    gate.classList.remove('gone');
    document.body.classList.add('gate-up');
  };
  /* The island asks to come home by postMessage. It cannot call __raiseGate
     across the frame: both documents are file:// URLs, which WebKit treats as
     opaque origins, so the property read throws. A message always crosses. */
  window.addEventListener('message', function(e){
    if(e && e.data && e.data.iguide === 'home') window.__raiseGate();
  });
  document.getElementById('goNorse').addEventListener('click', drop);
  document.getElementById('goIceland').addEventListener('click', function(){
    /* Order matters. Claim the screen for the island BEFORE the gate lets go:
       the globe is hidden by `island-open`, the island starts rising behind
       the still-opaque gate, and the gate then fades away to reveal it. Drop
       the gate first and there is a half-second window with nothing over the
       globe, which is exactly the flash Ritchie saw. */
    document.body.classList.add('island-open');
    if(typeof window.__openIsland==='function') window.__openIsland();
    else console.warn('gate: __openIsland missing - is _twolayer.py stale?');
    drop();
  });
  document.getElementById('goSite').addEventListener('click', function(){
    window.location.href='https://www.iguideiceland.is';
  });
})();
</script>
"""

head_tag = "</" + "head>"
body_tag = "</" + "body>"
css = GATE_CSS.replace("__NORSE__", norse).replace("__NORSEB__", norseb)
rest = (GATE_HTML.replace("__CREST__", crest)
                 .replace("__VEGVISIR__", VEGVISIR)
                 .replace("__MARK_NORSE__", MARK_NORSE)
                 .replace("__MARK_ICELAND__", MARK_ICELAND.replace("__ICEPATH__", ICELAND_PATH))
        + GATE_JS)

new, n = re.subn(re.escape(head_tag), css + head_tag, s, count=1)
if n != 1:
    raise SystemExit("!! could not find the closing head tag exactly once")
new, n = re.subn(re.escape(body_tag), rest + body_tag, new, count=1)
if n != 1:
    raise SystemExit("!! could not find the closing body tag exactly once")
opener = "<" + "body>"
if new.count(opener) != 1:
    raise SystemExit("!! expected exactly one bare opening body tag")
new = new.replace(opener, "<" + 'body class="gate-up">', 1)
io.open(TARGET, "w", encoding="utf-8").write(new)
print("gate added to %s" % TARGET)
print("  three doors, one lockup each: Norse Expansion / Iceland / iGuide Iceland")
print("  Iceland emblem = real coastline, %d chars of path" % len(ICELAND_PATH))
