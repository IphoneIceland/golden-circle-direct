// _aimaudit.js — every block, every tour: what the words say vs what the road says.
//
//   node _aimaudit.js            # summary + the disagreements
//   node _aimaudit.js --all      # every row
//   node _aimaudit.js --json     # machine-readable, for the back office
//
// A block has ONE target. The clock is a property of where the coach is and
// which way it points, so it is computed here rather than typed once per tour.
// Typed is how Gljúfrasteinn told three tours to look left at a house on the
// right.
//
// A row is only a disagreement if the CUE NAMES a direction. Plenty of cues
// are positional ("driving under it now", "pulling into") and those are left
// alone — that rule is already in _clockcheck.py and it is here too.

const fs = require("fs");
const A = require("./_aim.js");
const ALL = process.argv.includes("--all");
const JSONOUT = process.argv.includes("--json");

function load(f) { global.window = {}; eval(fs.readFileSync(f, "utf8")); return global.window; }

const TOURS = load("tours.js").__TOURS__.filter(t => t.ready !== false).map(t => t.id);

// what the words claim
const SIDE = [
  [/\b(\d{1,2})\s*o.?clock\b/i, m => ({ clock: +m[1] })],
  [/\blook (back|behind)\b|\bbehind us\b/i, () => ({ side: "behind" })],
  [/\blook left\b|\bon your left\b|\bto your left\b|\bleft at\b/i, () => ({ side: "left" })],
  [/\blook right\b|\bon your right\b|\bto your right\b|\bright at\b/i, () => ({ side: "right" })],
  [/\blook ahead\b|\bahead of us\b|\bin front of us\b|\bstraight ahead\b/i, () => ({ side: "ahead" })],
];
// cues that describe position, not direction — never counted as wrong
const POSITIONAL = /\bdriving (under|through|past|into)\b|\bcrossing\b|\bpulling in(to)?\b|\bwe are on\b|\ball around\b|\bunderneath\b|\bboth sides\b/i;

function claimOf(cue) {
  if (!cue) return null;
  const out = {};
  for (const [re, f] of SIDE) { const m = cue.match(re); if (m) Object.assign(out, f(m)); }
  if (!Object.keys(out).length) return null;
  if (out.clock && !out.side) {
    out.side = out.clock === 12 ? "ahead" : out.clock === 6 ? "behind"
             : out.clock < 6 ? "right" : "left";
  }
  return out;
}

const rows = [];
for (const id of TOURS) {
  let S, C, Rt;
  try { S = load("script-" + id + ".js").__SCRIPT__; } catch (e) { continue; }
  try { C = load("cues-" + id + ".js").__CUES__; } catch (e) { C = []; }
  try { Rt = load("route-" + id + ".js").__ROUTE__; } catch (e) { continue; }
  const geom = Rt.geometry;
  const byId = {}; C.forEach(c => byId[c.id] = c);

  S.sections.forEach(sec => sec.blocks.forEach(b => {
    const c = byId[b.id];
    if (!c || !c.pin || !c.target) return;
    const head = A.headingAt(geom, c.progress);
    const brg = A.bearing(c.pin, c.target);
    const rel = (brg - head + 360) % 360;
    const km = A.dist(c.pin, c.target);
    const road = { side: A.sideOf(rel), clock: A.clockOf(rel) };
    const said = claimOf(b.cue);
    const positional = POSITIONAL.test(b.cue || "");

    let verdict = "no claim";
    if (said && !positional) {
      const sideOk = !said.side || said.side === road.side;
      // a clock is allowed to be one hour out; the coach is moving and the
      // guest is looking out of a window, not sighting a rifle
      const clockOk = !said.clock ||
        Math.min((said.clock - road.clock + 12) % 12, (road.clock - said.clock + 12) % 12) <= 1;
      verdict = (sideOk && clockOk) ? "agrees" : (sideOk ? "clock out" : "WRONG SIDE");
    } else if (positional) verdict = "positional";

    rows.push({ tour: id, block: b.title.trim(), id: b.id, cue: b.cue || "",
                road, said, km: +km.toFixed(2), kind: sec.kind, verdict });
  }));
}

if (JSONOUT) { console.log(JSON.stringify(rows, null, 1)); process.exit(0); }

const tally = {};
rows.forEach(r => tally[r.verdict] = (tally[r.verdict] || 0) + 1);
console.log("EVERY BLOCK WITH A PIN AND A TARGET: " + rows.length + " across " + TOURS.length + " tours\n");
["agrees", "clock out", "WRONG SIDE", "positional", "no claim"].forEach(v => {
  if (tally[v]) console.log("  " + String(tally[v]).padStart(4) + "  " + v);
});

const bad = rows.filter(r => r.verdict === "WRONG SIDE" || r.verdict === "clock out");
if (bad.length) {
  console.log("\n─── the words and the road disagree ───\n");
  const by = {};
  bad.forEach(r => (by[r.block] = by[r.block] || []).push(r));
  Object.entries(by).sort((a, b) => b[1].length - a[1].length).forEach(([blk, rs]) => {
    console.log(blk + "   (" + rs.length + " tour" + (rs.length === 1 ? "" : "s") + ")");
    rs.forEach(r => {
      console.log("   " + r.tour.padEnd(6) + r.verdict.padEnd(12) +
        ("road says " + r.road.side + " " + r.road.clock + "h").padEnd(24) +
        (r.km + " km").padEnd(10) + r.cue.slice(0, 70));
    });
    console.log();
  });
}
if (ALL) {
  console.log("\n─── everything ───");
  rows.forEach(r => console.log(r.tour.padEnd(6) + r.verdict.padEnd(12) +
    (r.road.side + " " + r.road.clock + "h").padEnd(14) + (r.km + "km").padEnd(9) + r.block));
}
