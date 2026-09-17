// _aimdata.js — where every block would land on every tour, and which way you look.
//
//   node _aimdata.js            # summary
//   node _aimdata.js --write    # writes aim.json for the back office
//
// The back office lets you tick a block onto a tour. The question that
// immediately follows is "and where does it go?" — which is not a thing to
// type, it is a thing to work out from the road.
//
// For a block's target and a tour's geometry:
//   * closest approach  — the point on that road nearest the landmark
//   * progress          — how far along the tour that is, so the block can be
//                         slotted into the running order
//   * side + clock      — computed at that point, from the coach's heading
//   * km                — how far off the road it is, so a 60 km "sightline"
//                         can be seen for what it is
//
// Targets come from the cue files: a block's target is the same coordinate on
// every tour that already carries it, so it is a property of the block.

const fs = require("fs");
const A = require("./_aim.js");
const WRITE = process.argv.includes("--write");

function load(f) { global.window = {}; eval(fs.readFileSync(f, "utf8")); return global.window; }

const TOURS = load("tours.js").__TOURS__.filter(t => t.ready !== false);
const BOOK = JSON.parse(fs.readFileSync("_blocks/blocks.json", "utf8"));

// ── every target we know about, keyed by block title ──────────────────────
const TARGET = {};                 // title -> {lat, lon, name}
const disagree = [];
for (const t of TOURS) {
  let S, C;
  try { S = load("script-" + t.id + ".js").__SCRIPT__; } catch (e) { continue; }
  try { C = load("cues-" + t.id + ".js").__CUES__; } catch (e) { continue; }
  const byId = {}; C.forEach(c => byId[c.id] = c);
  S.sections.forEach(sec => sec.blocks.forEach(b => {
    const c = byId[b.id];
    if (!c || !c.target) return;
    const k = b.title.trim();
    if (!TARGET[k]) { TARGET[k] = { ...c.target, from: t.id }; return; }
    const d = A.dist(TARGET[k], c.target);
    if (d > 0.5) disagree.push({ block: k, a: TARGET[k].from, b: t.id, km: +d.toFixed(2) });
  }));
}

// ── each tour's road, measured once ───────────────────────────────────────
const ROADS = {};
for (const t of TOURS) {
  let R;
  try { R = load("route-" + t.id + ".js").__ROUTE__; } catch (e) { continue; }
  const g = R.geometry, cum = [0];
  let total = 0;
  for (let i = 1; i < g.length; i++) {
    total += A.dist({ lat: g[i-1][0], lon: g[i-1][1] }, { lat: g[i][0], lon: g[i][1] });
    cum.push(total);
  }
  ROADS[t.id] = { g, cum, total };
}

// Closest approach of a road to a point. Walks the whole line — an out-and-back
// tour passes some landmarks twice and BOTH passes are real, so keep the best
// of each direction rather than silently picking one. That two-pass trap is
// what put a 7.0 pin on the outbound carriageway and flipped left for right.
function approaches(road, tgt) {
  const { g, cum, total } = road;
  const hits = [];
  let best = null;
  for (let i = 0; i < g.length; i++) {
    const d = A.dist({ lat: g[i][0], lon: g[i][1] }, tgt);
    if (!best || d < best.d) best = { d, i };
    // a local minimum that is meaningfully closer than its neighbours = a pass
    if (i > 1 && i < g.length - 1) {
      const dPrev = A.dist({ lat: g[i-1][0], lon: g[i-1][1] }, tgt);
      const dNext = A.dist({ lat: g[i+1][0], lon: g[i+1][1] }, tgt);
      if (d <= dPrev && d <= dNext) hits.push({ d, i });
    }
  }
  if (!hits.length && best) hits.push(best);
  // keep passes that are distinct stretches of road, nearest first
  hits.sort((a, b) => a.d - b.d);
  const keep = [];
  for (const h of hits) {
    if (keep.every(k => Math.abs(cum[k.i] - cum[h.i]) > total * 0.05)) keep.push(h);
    if (keep.length === 3) break;
  }
  return keep.map(h => {
    const pin = { lat: g[h.i][0], lon: g[h.i][1] };
    const progress = 100 * cum[h.i] / total;
    const head = A.headingAt(g, progress);
    const rel = (A.bearing(pin, tgt) - head + 360) % 360;
    return { km: +h.d.toFixed(2), progress: +progress.toFixed(3),
             pin: { lat: +pin.lat.toFixed(5), lon: +pin.lon.toFixed(5) },
             side: A.sideOf(rel), clock: A.clockOf(rel) };
  });
}

// ── PLACELESS BLOCKS ──────────────────────────────────────────────────────
// A block about an idea has nowhere to point, and that is not a fault to fix.
// The two playlists go on whatever tour wants them; Landnám happened to the
// whole country. Marking them keeps them out of the "no target" count, so the
// red rings on the map stay meaning "this one needs a target" instead of
// slowly filling up with things that never will.
const PLACELESS = new Set([
  "\ud83c\udfa7 Iceland Through the Years",
  "\ud83c\udfa7 Rícharður's Mix",
  "\ud83c\udfa7 Music Leg",
  "\ud83e\uddf5 Three Names to Keep in Your Pocket",
  "\ud83d\udea2 The Norse Expansion (793–1066 CE)",
  "\ud83c\udfd8\ufe0f Landnám",
  "\u2696\ufe0f Kristnitaka",
  "\u2696\ufe0f The Sturlung Age",
  "\ud83c\uddee\ud83c\uddf8 17 June 1944",
  "\ud83d\udc0e Icelandic Horses",
]);
const isPlaceless = t => PLACELESS.has(t.trim());

// ── the location code ─────────────────────────────────────────────────────
// "Where is this block?" answered at a glance, off the real coordinate rather
// than a number somebody has to keep in order. Compass octant from BSÍ plus
// the distance in km: SE10 is ten kilometres south-east of the bus station.
// Nothing to renumber, nothing to collide, and it stays true when a block
// moves between tours — because the landmark has not moved.
const ORIGIN = (() => {
  const g = ROADS["1.0"] && ROADS["1.0"].g;                 // BSÍ, first point of tour 1.0
  return g ? { lat: g[0][0], lon: g[0][1] } : { lat: 64.13768, lon: -21.93434 };
})();
const OCT = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
function codeOf(tgt) {
  const km = A.dist(ORIGIN, tgt);
  const brg = A.bearing(ORIGIN, tgt);
  const oct = OCT[Math.round(brg / 45) % 8];
  return km < 3 ? "RVK" : oct + Math.round(km);
}

// ── the table the back office wants ───────────────────────────────────────
const out = { builtAt: new Date().toISOString(), origin: ORIGIN,
              tours: TOURS.map(t => t.id), blocks: {} };
let withTarget = 0, noTarget = [];

// A block with a pin but no target still has a place on the road, and the
// whole point of the map is to SEE the gaps. So it goes on, marked as
// unaimed, at the pin — where the coach is when it fires.
const PIN = {};
for (const t of TOURS) {
  let S, C;
  try { S = load("script-" + t.id + ".js").__SCRIPT__; } catch (e) { continue; }
  try { C = load("cues-" + t.id + ".js").__CUES__; } catch (e) { continue; }
  const byId = {}; C.forEach(c => byId[c.id] = c);
  S.sections.forEach(sec => sec.blocks.forEach(b => {
    const c = byId[b.id];
    if (c && c.pin && !PIN[b.title.trim()]) PIN[b.title.trim()] = { ...c.pin, from: t.id };
  }));
}

BOOK.forEach(e => {
  const tgt = TARGET[e.title.trim()];
  if (isPlaceless(e.title)) {
    out.blocks[e.title] = { placeless: true, on: {} };
    return;
  }
  if (!tgt) {
    const pin = PIN[e.title.trim()];
    noTarget.push(e.title);
    if (pin) {
      out.blocks[e.title] = {
        unaimed: true,
        code: codeOf(pin), kmFromRvk: +A.dist(ORIGIN, pin).toFixed(1),
        target: { lat: pin.lat, lon: pin.lon, name: e.title + " (pin, no target)" },
        on: {}
      };
    }
    return;
  }
  withTarget++;
  const row = { code: codeOf(tgt), kmFromRvk: +A.dist(ORIGIN, tgt).toFixed(1),
                target: { lat: tgt.lat, lon: tgt.lon, name: tgt.name || e.title }, on: {} };
  TOURS.forEach(t => {
    const road = ROADS[t.id];
    if (!road) return;
    const passes = approaches(road, tgt);
    if (!passes.length) return;
    row.on[t.id] = { best: passes[0], passes: passes.length > 1 ? passes.slice(1) : undefined,
                     used: e.usedBy.includes(t.id) };
  });
  out.blocks[e.title] = row;
});

console.log("BLOCKS            " + BOOK.length + " in the library");
console.log("  with a target   " + withTarget);
const plottedUnaimed = Object.values(out.blocks).filter(b => b.unaimed).length;
console.log("  no target yet   " + noTarget.length + "   (" + plottedUnaimed
            + " still mapped at their pin, " + (noTarget.length - plottedUnaimed) + " with no pin either)");
console.log("  placeless       " + Object.values(out.blocks).filter(b => b.placeless).length
            + "   (ideas and playlists — nowhere to point, and that is fine)");
console.log("TOURS             " + Object.keys(ROADS).length + " with road geometry");

if (disagree.length) {
  console.log("\nSAME BLOCK, DIFFERENT TARGET on different tours — one of them is wrong:");
  disagree.slice(0, 15).forEach(d =>
    console.log("   " + d.km + " km apart   " + d.block + "   (" + d.a + " vs " + d.b + ")"));
  if (disagree.length > 15) console.log("   …and " + (disagree.length - 15) + " more");
}

// how far the nearest road passes — a block nobody can see is worth knowing about
const far = [];
Object.entries(out.blocks).forEach(([k, v]) => {
  const best = Math.min(...Object.values(v.on).map(o => o.best.km));
  if (best > 25) far.push([k, best]);
});
if (far.length) {
  console.log("\nNO TOUR GETS WITHIN 25 km:");
  far.sort((a, b) => b[1] - a[1]).slice(0, 10).forEach(([k, d]) =>
    console.log("   " + d.toFixed(1) + " km   " + k));
}

if (WRITE) {
  fs.writeFileSync("aim.json", JSON.stringify(out));
  fs.writeFileSync("_blocks/aim.json", JSON.stringify(out, null, 1));
  console.log("\nwrote aim.json (" + (fs.statSync("aim.json").size / 1024 | 0) + " KB) and _blocks/aim.json");
}
