// _aim.js — what direction IS the thing, according to the road?
//
//   node _aim.js "Rauðhólar"
//
// A block carries ONE target: the landmark's coordinate, the same on every
// tour. What changes per tour is where the coach is when the block fires and
// which way it is pointing. Those two give the clock, so the clock should be
// computed, not typed — and typed is how Gljúfrasteinn ended up saying "look
// left" on three tours that drive past it on the right.
//
// heading  = bearing along the route at the pin, from the geometry either side
// bearing  = pin -> target
// clock    = (bearing - heading), 12 ahead, 3 right, 6 behind, 9 left

const fs = require("fs");
const R = Math.PI / 180;

function bearing(a, b) {
  const y = Math.sin((b.lon - a.lon) * R) * Math.cos(b.lat * R);
  const x = Math.cos(a.lat * R) * Math.sin(b.lat * R) -
            Math.sin(a.lat * R) * Math.cos(b.lat * R) * Math.cos((b.lon - a.lon) * R);
  return (Math.atan2(y, x) / R + 360) % 360;
}
function dist(a, b) {                       // km, haversine
  const dLat = (b.lat - a.lat) * R, dLon = (b.lon - a.lon) * R;
  const s = Math.sin(dLat / 2) ** 2 +
            Math.cos(a.lat * R) * Math.cos(b.lat * R) * Math.sin(dLon / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(s));
}

// The coach's heading at the pin. Resolve the pin by PROGRESS, not by nearest
// point — on an out-and-back tour the nearest point is often the other pass,
// which flips left and right. That trap is already written into CLAUDE.md.
function headingAt(geom, progressPct) {
  let total = 0;
  const cum = [0];
  for (let i = 1; i < geom.length; i++) {
    total += dist({lat: geom[i-1][0], lon: geom[i-1][1]}, {lat: geom[i][0], lon: geom[i][1]});
    cum.push(total);
  }
  const want = total * (progressPct / 100);
  let i = cum.findIndex(c => c >= want);
  if (i < 1) i = 1;
  const span = Math.max(1, Math.round(geom.length / 600));   // smooth over ~0.2% of the road
  const a = geom[Math.max(0, i - span)], b = geom[Math.min(geom.length - 1, i + span)];
  return bearing({lat: a[0], lon: a[1]}, {lat: b[0], lon: b[1]});
}

function clockOf(rel) {
  let h = Math.round(((rel % 360) / 30)) % 12;
  if (h <= 0) h += 12;
  return h;
}
function sideOf(rel) {
  const r = ((rel % 360) + 360) % 360;
  if (r < 15 || r > 345) return "ahead";
  if (r > 165 && r < 195) return "behind";
  return r < 180 ? "right" : "left";
}
module.exports = { bearing, dist, headingAt, clockOf, sideOf };
