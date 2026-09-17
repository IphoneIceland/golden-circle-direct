#!/usr/bin/env python3
"""Build the combined-map MOCKUP: the Norse world and the tour routes on one Leaflet map.

Everything on it is real:
  - 337 Norse-world places lifted out of Norse-Expansion-16K-v39.html (name, lat, lon,
    year, category, blurb, teach line)
  - the ten tour routes and 86 stop pins, straight from route-*.js and cues-*.js
  - the 8 places that appear in BOTH, computed by distance, not by hand

Leaflet is inlined from the app's own vendor copy so the file opens with no network
for everything except the tiles.

Writes ~/Documents/RitchWiki/norse-tours-mockup.html
"""
import io, json, os, math

REPO = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.expanduser("~/Documents/RitchWiki/norse-tours-mockup.html")

raids = json.load(open('/tmp/raids_slim.json'))
tours = json.load(open('/tmp/tours_slim.json'))
lf_js  = io.open(os.path.join(REPO, 'vendor/leaflet.js'),  encoding='utf-8').read()
lf_css = io.open(os.path.join(REPO, 'vendor/leaflet.css'), encoding='utf-8').read()

def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a); dl = math.radians(d - b)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(x))

stops = [(t, s['n'], s['la'], s['lo']) for t, v in tours.items() for s in v['stops']]
for r in raids:
    best = None
    for t, n, la, lo in stops:
        d = hav(r['la'], r['lo'], la, lo)
        if best is None or d < best[0]: best = (d, t, n)
    if best and best[0] < 12:
        r['ov'] = {'km': round(best[0], 1), 'tour': best[1], 'stop': best[2]}
n_ov = sum(1 for r in raids if 'ov' in r)

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Norse world + iGuide tours — combined map mockup</title>
<style>__LFCSS__</style>
<style>
:root{--gold:#d4a94a;--ink:#0e0e10;--panel:#16161a;--line:#2a2a31;--txt:#e9e6df;--mut:#9a958c}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--ink);color:var(--txt);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif}
#map{position:absolute;inset:0}
.leaflet-container{background:#0b0f14}
#hud{position:absolute;z-index:500;top:12px;left:12px;width:310px;max-height:calc(100% - 24px);
  overflow:auto;background:rgba(22,22,26,.94);border:1px solid var(--line);border-radius:12px;
  padding:14px 14px 12px;backdrop-filter:blur(8px)}
h1{font-size:15px;margin:0 0 2px;color:var(--gold);letter-spacing:.02em}
.sub{color:var(--mut);font-size:12px;margin-bottom:12px}
h2{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);
  margin:14px 0 6px;font-weight:600}
label{display:flex;align-items:center;gap:8px;padding:3px 0;cursor:pointer;font-size:13px}
input[type=checkbox]{accent-color:var(--gold)}
.dot{width:10px;height:10px;border-radius:50%;flex:0 0 10px}
.count{margin-left:auto;color:var(--mut);font-size:11px;font-variant-numeric:tabular-nums}
#yearwrap{margin-top:6px}
#year{width:100%;accent-color:var(--gold)}
#yearlab{color:var(--gold);font-variant-numeric:tabular-nums;font-size:13px}
.btn{display:inline-block;padding:6px 10px;margin:4px 4px 0 0;border:1px solid var(--line);
  border-radius:8px;background:#1d1d22;color:var(--txt);font-size:12px;cursor:pointer}
.btn:hover{border-color:var(--gold);color:var(--gold)}
#info{position:absolute;z-index:500;right:12px;bottom:12px;width:320px;
  background:rgba(22,22,26,.96);border:1px solid var(--line);border-radius:12px;padding:14px;display:none}
#info h3{margin:0 0 2px;font-size:14px;color:var(--gold)}
#info .meta{color:var(--mut);font-size:11px;margin-bottom:8px}
#info p{margin:0 0 8px;font-size:13px}
#info .teach{border-left:2px solid var(--gold);padding-left:9px;color:#cfc9bd;font-size:12.5px}
#info .ov{margin-top:9px;padding-top:9px;border-top:1px solid var(--line);
  color:var(--gold);font-size:12px}
.x{position:absolute;top:8px;right:10px;color:var(--mut);cursor:pointer;font-size:16px;line-height:1}
.note{margin-top:12px;padding-top:10px;border-top:1px solid var(--line);color:var(--mut);font-size:11.5px}
.stop{color:var(--gold);font-weight:600}
</style></head><body>
<div id="map"></div>
<div id="hud">
  <h1>Norse world + iGuide tours</h1>
  <div class="sub">Mockup — one map, two datasets, real coordinates.</div>

  <h2>Layers</h2>
  <label><input type="checkbox" id="L_tour" checked><span class="dot" style="background:#d4a94a"></span>Tour routes<span class="count" id="c_tour"></span></label>
  <label><input type="checkbox" id="L_stop" checked><span class="dot" style="background:#fff"></span>Tour stops<span class="count" id="c_stop"></span></label>
  <label><input type="checkbox" id="L_settlement" checked><span class="dot" style="background:#4da3ff"></span>Settlements<span class="count" id="c_settlement"></span></label>
  <label><input type="checkbox" id="L_battle" checked><span class="dot" style="background:#e2564a"></span>Battles &amp; raids<span class="count" id="c_battle"></span></label>
  <label><input type="checkbox" id="L_person" checked><span class="dot" style="background:#b98cff"></span>People<span class="count" id="c_person"></span></label>
  <label><input type="checkbox" id="L_event" checked><span class="dot" style="background:#4ad2a8"></span>Events<span class="count" id="c_event"></span></label>
  <label><input type="checkbox" id="L_ov" checked><span class="dot" style="background:#d4a94a;box-shadow:0 0 0 3px rgba(212,169,74,.3)"></span>On a tour stop<span class="count" id="c_ov"></span></label>

  <h2>Year <span id="yearlab"></span></h2>
  <div id="yearwrap"><input type="range" id="year" min="700" max="1450" step="5" value="1450"></div>

  <h2>Jump</h2>
  <div>
    <span class="btn" data-view="world">The Norse world</span>
    <span class="btn" data-view="iceland">Iceland</span>
    <span class="btn" data-view="gc">Golden Circle</span>
  </div>

  <div class="note" id="note"></div>
</div>
<div id="info"><span class="x" onclick="document.getElementById('info').style.display='none'">×</span>
  <h3 id="i_n"></h3><div class="meta" id="i_m"></div>
  <p id="i_b"></p><div class="teach" id="i_t"></div><div class="ov" id="i_o"></div></div>

<script>__LFJS__</script>
<script>
const RAIDS = __RAIDS__;
const TOURS = __TOURS__;
const COL = {settlement:'#4da3ff', battle:'#e2564a', person:'#b98cff', event:'#4ad2a8'};

const map = L.map('map',{zoomControl:true, worldCopyJump:true}).setView([59,-8],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  {maxZoom:19, attribution:'&copy; OpenStreetMap &copy; CARTO'}).addTo(map);

// ---- tour routes and stops, straight from the app's own route/cue files
const tourLayer = L.layerGroup().addTo(map);
const stopLayer = L.layerGroup().addTo(map);
let nStops = 0;
for (const id in TOURS){
  const t = TOURS[id];
  L.polyline(t.route, {color:'#d4a94a', weight:2, opacity:.55}).addTo(tourLayer);
  t.stops.forEach(s=>{
    nStops++;
    L.circleMarker([s.la,s.lo],{radius:3.5,color:'#fff',weight:1,fillColor:'#fff',fillOpacity:.9})
      .bindTooltip(t.name+' — '+s.n,{direction:'top'}).addTo(stopLayer);
  });
}

// ---- the Norse world
const groups = {settlement:L.layerGroup().addTo(map), battle:L.layerGroup().addTo(map),
                person:L.layerGroup().addTo(map), event:L.layerGroup().addTo(map)};
const ovLayer = L.layerGroup().addTo(map);
const marks = [];
RAIDS.forEach(r=>{
  const c = COL[r.c] || '#888';
  const m = L.circleMarker([r.la,r.lo], {radius: r.ov?7:4, color:c, weight: r.ov?2:1,
      fillColor:c, fillOpacity:.75, className: r.ov?'ovmark':''});
  m.bindTooltip(r.n + (r.y? ' · '+r.y : ''), {direction:'top'});
  m.on('click', ()=>show(r));
  m._r = r;
  marks.push(m);
  (r.ov ? ovLayer : groups[r.c] || groups.event).addLayer(m);
});

function show(r){
  document.getElementById('i_n').textContent = r.n;
  document.getElementById('i_m').textContent =
    [r.y?('c. '+r.y):null, r.c].filter(Boolean).join(' · ');
  document.getElementById('i_b').textContent = r.b || '';
  document.getElementById('i_t').textContent = r.t || '';
  document.getElementById('i_o').innerHTML = r.ov
    ? 'Already a stop on tour <span class="stop">'+r.ov.tour+'</span> — '+r.ov.stop+
      ' <span style="color:var(--mut)">('+r.ov.km+' km away)</span>'
    : '';
  document.getElementById('i_o').style.display = r.ov ? 'block':'none';
  document.getElementById('info').style.display = 'block';
}

// ---- year filter
const yr = document.getElementById('year'), yl = document.getElementById('yearlab');
function applyYear(){
  const y = +yr.value;
  yl.textContent = y >= 1450 ? 'all' : '≤ ' + y;
  marks.forEach(m=>{
    const r = m._r, on = (r.y == null) || r.y <= y || y >= 1450;
    m.setStyle({opacity: on?1:0.06, fillOpacity: on?0.75:0.04});
  });
  count();
}
yr.addEventListener('input', applyYear);

// ---- layer toggles
function bind(id, layer){
  document.getElementById(id).addEventListener('change', e=>{
    e.target.checked ? map.addLayer(layer) : map.removeLayer(layer);
  });
}
bind('L_tour', tourLayer); bind('L_stop', stopLayer); bind('L_ov', ovLayer);
for (const k in groups) bind('L_'+k, groups[k]);

function count(){
  const y = +yr.value;
  const vis = r => (r.y == null) || r.y <= y || y >= 1450;
  const by = {settlement:0,battle:0,person:0,event:0,ov:0};
  RAIDS.forEach(r=>{ if(!vis(r)) return; if(r.ov) by.ov++; else by[r.c]=(by[r.c]||0)+1; });
  for (const k in by) { const el = document.getElementById('c_'+k); if (el) el.textContent = by[k]; }
  document.getElementById('c_tour').textContent = Object.keys(TOURS).length;
  document.getElementById('c_stop').textContent = nStops;
}

// ---- views
const VIEWS = {world:[[35,-60],[70,45]], iceland:[[63.2,-24.6],[66.6,-13.4]], gc:[[63.9,-21.99],[64.42,-20.1]]};
document.querySelectorAll('.btn').forEach(b=>b.addEventListener('click',()=>{
  map.fitBounds(VIEWS[b.dataset.view], {padding:[20,20]});
}));

document.getElementById('note').innerHTML =
  '<b>__NOV__ of the 337</b> Norse-world places sit on ground a tour already stops at — '+
  'gold rings. Everything here is lifted from the existing files: places from the Norse '+
  'Expansion globe, routes and stops from the tour app. Nothing was redrawn by hand.';
applyYear(); count();
map.fitBounds(VIEWS.world,{padding:[20,20]});
</script></body></html>"""

html = (HTML.replace('__LFCSS__', lf_css)
            .replace('__LFJS__',  lf_js)
            .replace('__RAIDS__', json.dumps(raids, ensure_ascii=False))
            .replace('__TOURS__', json.dumps(tours, ensure_ascii=False))
            .replace('__NOV__',   str(n_ov)))
io.open(OUT, 'w', encoding='utf-8').write(html)
print("wrote %s  %.1f MB" % (OUT, len(html)/1e6))
print("  %d Norse-world places, %d on a tour stop" % (len(raids), n_ov))
print("  %d tours, %d stops" % (len(tours), len(stops)))
