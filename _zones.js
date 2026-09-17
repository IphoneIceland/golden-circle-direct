// _zones.js — group the blocks into places, from where they actually are.
//
//   node _zones.js            # propose zones
//   node _zones.js --write    # writes zones.json
//
// SE10 meant nothing on the mic. A zone does: Þingvellir, Ölfus, Snæfellsnes.
// So rather than draw boundaries on a map and argue about them, the zones are
// grown from the blocks themselves — single-link clustering with a distance
// threshold, then each cluster is named after the block in it that is closest
// to the cluster's centre. The names therefore come out of Ritchie's own
// content and can be corrected by hand where they read wrong.

const fs = require("fs");
const A = require("./_aim.js");
const WRITE = process.argv.includes("--write");
const LINK = +(process.argv.find(a => a.startsWith("--link=")) || "--link=18").split("=")[1];

const AIM = JSON.parse(fs.readFileSync("aim.json", "utf8"));
const pts = Object.entries(AIM.blocks).map(([title, v]) => ({ title, ...v.target }));

// single-link: two blocks are in the same zone if you can walk between them in
// hops of LINK km or less. A road's worth of blocks chains into one place;
// a 60 km gap starts a new one.
const parent = pts.map((_, i) => i);
const find = i => parent[i] === i ? i : (parent[i] = find(parent[i]));
const union = (a, b) => { a = find(a); b = find(b); if (a !== b) parent[b] = a; };
for (let i = 0; i < pts.length; i++)
  for (let j = i + 1; j < pts.length; j++)
    if (A.dist(pts[i], pts[j]) <= LINK) union(i, j);

const groups = {};
pts.forEach((p, i) => (groups[find(i)] = groups[find(i)] || []).push(p));

const zones = Object.values(groups).map(members => {
  const lat = members.reduce((a, p) => a + p.lat, 0) / members.length;
  const lon = members.reduce((a, p) => a + p.lon, 0) / members.length;
  const centre = { lat, lon };
  // name it after the member nearest the middle — that is usually the place
  // the whole cluster is about
  const named = members.slice().sort((a, b) => A.dist(centre, a) - A.dist(centre, b))[0];
  const span = Math.max(...members.map(p => A.dist(centre, p)));
  return { name: named.title.replace(/^[^\p{L}]+/u, "").split("&")[0].split("—")[0].trim(),
           centre: { lat: +lat.toFixed(4), lon: +lon.toFixed(4) },
           spanKm: +span.toFixed(1), count: members.length,
           members: members.map(m => m.title) };
}).sort((a, b) => b.count - a.count);

console.log("link distance " + LINK + " km  ->  " + zones.length + " zones, "
            + pts.length + " blocks placed\n");
zones.forEach(z => {
  console.log("  " + String(z.count).padStart(3) + "  " + z.name.padEnd(28)
              + "span " + String(z.spanKm).padStart(5) + " km");
});
const orphans = zones.filter(z => z.count === 1);
if (orphans.length) console.log("\n  " + orphans.length + " zone(s) of one block — probably want folding into a neighbour");

if (WRITE) {
  const byBlock = {};
  zones.forEach(z => z.members.forEach(m => byBlock[m] = z.name));
  fs.writeFileSync("zones.json", JSON.stringify({ builtAt: new Date().toISOString(), linkKm: LINK,
    zones: zones.map(({ members, ...z }) => z), byBlock }, null, 1));
  console.log("\nwrote zones.json");
}
