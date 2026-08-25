# HANDOVER — Golden Circle Direct

**True as of 25 Aug 2026, 15:52 GMT.** Paste this into a fresh chat and you lose nothing.

**Changelog**
- 25 Aug 2026 — **1.0 resynced from the corrected Craft manuscript.** Re-exported the Craft doc and re-ran `build-script.py`; 6 sections / 35 blocks / block ids all unchanged. Five delivery cues were wrong on the bus and are now right — **Hekla** right at **1 o'clock** (was 11, and its weather pivot and pronunciation gloss carried the old clock too), **Rauðhólar left at 9** (was right at 3), **Ölfusárbrú** "we're crossing it now — look down" (was right at 3), **Kjalarnes** left at 9, **ten kilometres off** (was "At Kjalarnes"), **Esja** "left and ahead" (was ahead at 12). Note for the next chat: this `build-script.py` regenerates everything from Craft and **does** import `cue` from each block's italic line, so cues need no separate sync — the older parser that treated `cue` as a protected route fact is gone. Facts fixed: Kjarval's **1968 bequest** replaces "roughly 5,000 works", Kerið is **one of a dozen or so Grímsnes eruptions** and its duplicated scoria/hematite bullets are merged, Hveragerði **~3,350 (3,344 at the start of 2026)** not 2,982, Ölfusá **400 m³/s** not 423, the cave family is **Iceland's** last not Europe's, and it's the **Hreppar block**, not the Hreppar Fault. `sw.js` → `gcd29-v2`. **`golden-circle-direct.html` no longer contains any tour script** — since the multi-tour split, `index.html` loads `script-<id>.js` at runtime, so the single file and the backup gist are the shell only, and the gist is no longer a working offline copy of the script.
- 25 Aug 2026 — **a way home, in words.** There *was* an exit — a dim grey `☰` in the corner of the leg track — and nobody found it, which is the same as there not being one. Two icon-only attempts failed the same test: a gold `‹` sat directly above the outlined block arrows and read as one paginator with a stutter, and an arrow-into-a-bar glyph was just a shape nobody had to decode. **An icon is not a way home.** What shipped is a **top bar**: a solid gold button that says the words — *Choose another tour* / *Andere Tour wählen* / *اختيار جولة أخرى* — with the tour's name on the other end, so you also know where you are. Label and aria-label come from `ui.back`, so it speaks all 21 languages; longest is Russian at **259px of 390**, no overflow anywhere. Under `dir="rtl"` the bar mirrors and the arrow flips. Opening a tour also **pushes a history entry**, so the phone's own back gesture lands on the picker rather than leaving the site. Both paths run one `leaveTour()`: clear `gcd-tour`, `location.replace(location.pathname)` — reloading rather than un-picking `boot()` by hand means no half-torn-down map, and the shell comes straight out of the service worker. Costs **53px** of vertical. Verified headless across en/de/ru/ja/ar and all three tours, zero console errors. `sw.js` -> `gcd31-v1`.
- 25 Aug 2026 — **twenty-one languages, and two of them read backwards.** The welcome, the safety briefing and the UI furniture now exist in **English plus 20**: de, fr, es, it, nl, pt, pl, da, sv, no, fi, is, zh, ja, ko, ru, ar, hi, tr, he. Each `i18n/xx.js` carries `ui` (4 strings), `welcome` (3 items) and `briefing` (11 items) — checked programmatically, all 21 render 3 welcome items and 11 safety items with no console errors. `ar` and `he` carry `rtl:true`, and a new `applyDir()` puts that on `<html dir>` so Arabic and Hebrew actually flip the page instead of just claiming to. **The tour scripts themselves are still English only** — that's the next mountain, roughly 7,000 words x 20 languages x 3 tours. `sw.js` -> `gcd29-v1`.
- 25 Aug 2026 — **one welcome screen, in the order a guest meets it.** Language first, then who we are and how the app works, then safety, then the tours. Languages are a **flag dropdown** rather than 21 buttons eating the screen — `<select>` gets the native phone picker for free, and the choice sticks in `localStorage` under `gcd-lang`. Anything not yet translated shows greyed with "- not yet", so nobody picks a dead end.
- 25 Aug 2026 — **the safety briefing, on the way in.** Eleven items: seatbelts, doors, wind on the door handle, the timings, headcounts, footwear, the weather, the "if you get separated" line. Lives in `briefing.js` as `window.__BRIEFING__`, rendered as icon + heading + body so it scans on a phone instead of reading like terms and conditions.
- 25 Aug 2026 — **iGuide Iceland theme.** Gold `#d4a94a` on near-black `#0d0d0f`, Norse for headings (`fonts/Norse.woff2`, `fonts/NorseBold.woff2`, self-hosted, no CDN), Cormorant Garamond for body, and the stacked logo on the welcome screen. Same palette as the website, so the app doesn't look like a stranger borrowed the bus.
- 25 Aug 2026 — **one app, three tours.** `tours.js` lists them; the picker loads `route-/script-/cues-<id>.js` on demand rather than shipping every tour's payload to every guest. Adding 2.0, 3.0, 4.0 or 7.0 later is three data files and one line. **South Coast 5.0 and 6.0 are live**: 31 blocks, 122 bullets and 139 pronunciations each, 10 sections, routes from OSRM with stops pinned off OpenStreetMap. Both total **417.9 km / 439 min** — genuine coincidence, not a copy-paste: they split at Hvolsvöllur, 5.0 via **Sólheimajökull** (legs 106.6 / 73.8 / 35.2 / 10.9 / 34.6 / 29.4 / 127.4) and 6.0 via **Skógafoss** (106.6 / 48.9 / 34.9 / 10.9 / 38.9 / 50.3 / 127.4), and 1,729 of their 5,873 geometry points differ. `build-any.py` reads **both** Craft export shapes, old and new.
- 25 Aug 2026 — **swipe the story.** Left and right on the text pane moves a block; the trackpad's two-finger swipe does the same. The wheel listener sits on `window` with `capture:true` plus `overscroll-behavior-x:none`, because on `#days` alone the browser ate the gesture and went Back instead.
- 25 Aug 2026 — **this is a guest app, not a guide app.** Off the map: id pills, CUE labels, hashtags, marker emoji, dashed sightlines, target squares. The guide's furniture was never meant for the person in seat 14. Map moved to the **bottom** at a fixed 34% — a stale `order:-1` in the 860px query and a duplicate `#map{flex:1}` had been fighting each other and winning.
- 25 Aug 2026 — **the journey is the navigation.** The two abstract paginators are gone. There's a **leg track** across the top with a dot per part; you can see where you are in the day the way you'd see it out the window.
- 22 Aug 2026 — **the route draws itself as you go.** The map no longer opens with the whole loop already finished, which rather gave the ending away. Geometry is sliced by cumulative distance against each block's `progress` percent, interpolated between anchors and forced monotonic, so the road only ever grows. **Sharper satellite:** Esri has real imagery to **z18** over the route (z19 outside Reykjavík is a flat grey "no data" tile — verified as the identical 2,521-byte file at both Þingvellir and Geysir), so `maxNativeZoom:18` plus `detectRetina` is the honest ceiling. Also: the script pane finally scrolls on a phone (`min-height:0` on the flex child, `100dvh`, safe-area padding) and the drive band sits above an indented block bar so the nesting is obvious.
- 20 Aug 2026 — **content resynced from Craft, and the parser taught the current export shape.** The local export was still 13 July; Craft has since gained ~60 fact bullets and a batch of Tier-1 corrections. `build-script.py` now reads today's Craft format — emoji between number and title, `<callout>` hooks, `-` bullets with no `📖`, `**Name** [**PRON**] — gloss` pronunciations, 🧵 tags last, and the 🌫️ line (used only where the app has no `weather` of its own). All **35 blocks matched by title, none unmatched**; bullets **133 → 193**. Corrections now live: Kerið **5,000–6,000 years** and **gjallgígur/scoria cone** (not an explosion crater), Skálholt's see formally moved in **1801**, Hveragerði's first geothermal greenhouse **1924, Mosfellssveit**. The Norse Expansion keeps its hand-built `heads`/`pre` — now enforced by a `HAND_STRUCTURED` set instead of by luck. New `build-single.py` does the inlining step that produces `golden-circle-direct.html` (verified byte-identical against the previous build before use). `sw.js` → `gcd11-v5`.
- 10 Aug 2026 — **the space belongs to the script now.** Four stacked bars between map and first word — title, section, block, controls, search — cut to **one 86px bar**. `#head` (app name + route line) hidden under 860px; the map and the bar already say where you are. All sections / Hide all / Fit route / A− / A+ / search moved behind a **⋯** button (`#ctl.hid`), which opens with search focused. Fixed a flex bug where `#bnavrow>button` was also matching `#bmid` and pinning the block button to 54px — it read as a squashed "Start …" chip; now `#bprev,#bnext` are targeted explicitly and `#bmid` gets `flex:1 1 auto`. Script starts **532px down a 900px phone instead of ~790px**. `sw.js` → `gcd11-v4`.
- 10 Aug 2026 — **header condensed, and three ways of getting stuck fixed.** The section name was rendering **twice** — once in the nav bar, once as the list's own `.dayhead` — which read as two identical drive sections; `.day.solo` now hides the header whenever a single section is on screen. Two stacked nav bars merged into one (~200px of chrome down to **91px**): section name small on top with its own compact arrows, block arrows big underneath. **Tap the middle of the block bar to fold the block away** and get the map back — there was no way out of a long block before. Block arrows now run off a **flat 35-block index** (`CURS` + `CURB`) instead of being scoped to the current section, so they keep working in *All sections* and after search, where they used to go dead. `sw.js` → `gcd11-v3`.
- 10 Aug 2026 — **block arrows, on a second bar.** `‹ 🎨 Jóhannes Sveinsson Kjarval ›` with `block 2 of 11 · 1.1` under it. Opens that block, closes the last one, scrolls it to the top, flies the map to its pin, and tints the row so you can see where you are. **Runs off the end of a section straight into the next** — one thumb takes you from BSÍ to BSÍ without ever touching the section bar. Tapping a row by hand moves the pointer too, so the arrows carry on from wherever you actually are. Up/down arrow keys mirror the buttons. State is `CURB` (index within `CUR`, `null` = nothing picked yet). `sw.js` → `gcd11-v2`.
- 10 Aug 2026 — **one section at a time.** New `‹ / ›` bar above the controls: section title, `3 of 6`, block count. Arrows step through the six drive/stop sections and **the map fits that section** as you go (`sectionBounds()` off the cue pins and targets, maxZoom 13). Left/right arrow keys work too, unless you're typing in search. The current section opens by default — no tapping a bar to reveal it. **All sections** button returns the full list for prepping at home. Search still spans everything and the bar says how many sections it hit; clear it to drop back where you were. State lives in `CUR` (index, or `null` for all). `sw.js` → `gcd11-v1`.
- 10 Aug 2026 — map pane on narrow screens trimmed **48% → 38%** (min-height 280px → 220px), script gets the other 62%. `sw.js` → `gcd10-v10`.
- 10 Aug 2026 — **`script-1.0.js` is now GENERATED, not hand-kept.** New `build-script.py` parses the Craft export and rewrites the block content — sub, hook, bullets, point, mic, say, tags — matched on **title**, never on id (Craft's numbering and the app's diverge from 1.8 and always will). Route facts — id, emoji, cue, target — stay as the app has them. Brought back **+350 words and +20 pronunciations**, including Kjarval's 1914 Bakkagerði altarpiece, Mosfellsdalur's UCLA dig and Nobel paragraph, Ölfusá's four-systems bullet, and Selfoss's bridge origin. **Run `python3 build-script.py` before every ship.** `--check` reports without writing. One known exception: **The Norse Expansion** stays hand-structured — Craft holds it as a markdown table and a code block, and the app's `heads`/`pre` version reads better on a phone.
- 10 Aug 2026 — **fixed subtitles showing one block late.** They had been keyed on Craft ids; the app has three blocks Craft doesn't (`1.0i`, Gljúfrasteinn, The Sturlung Age), so everything from 1.8 was off by one — Skálholt was advertising Björk on a raft. Now derived from each block's own title. `sw.js` → `gcd10-v8`.
- 10 Aug 2026 — **rebuilt for reading, not for density.** Base type 11–12.5px → **16px** on a `--fs` custom property, line-height **1.8**, 14px between bullets, 13px block padding. Removed the things that fight dyslexic readers: **no italics** (subtitle is upright now), **no letter-spaced ALL-CAPS labels** (sentence case), bold softened 700 → 600 so emphasis means something again, `.blkbody` capped at **66ch** so lines don't run away on desktop. New **A− / A+** buttons step 14–22px and persist in `localStorage` (wrapped in try/catch — preview panes block storage). `sw.js` VERSION → `gcd10-v7`.
- 10 Aug 2026 — **block layout now follows the Craft doc.** Every heading's subtitle (`Kjarval — the cod fisherman who became legal tender`) was being dropped; all **34** are back as a `sub:` field on each block, harvested from `RitchWiki/Tour Scripts/1.0 Golden Circle Direct.md`. 🧵 thread tags moved from the bottom of the body up under the title where Craft has them. Bullets get a **📖 The story** label. Pronunciations re-ordered to Craft's `[PRON] — Name (gloss)`. `sw.js` VERSION → `gcd10-v6`.
- 10 Aug 2026 — **"🗣️ How to say it" is now collapsible**, matching Craft. Rendered as `<details class="say">` with a `<summary>` carrying a rotating chevron and the pronunciation count. Closed by default. `sw.js` VERSION → `gcd10-v5`.
- `de14354` 10 Aug 2026 — narrow screens (phone, and the Claude preview pane) put the **map on top**, script below: `#map{order:-1;height:48%;min-height:280px}`, `#side{height:52%}`. Desktop layout unchanged. `sw.js` VERSION → `gcd10-v4`.

---

## 1. The one link

**https://iphoneiceland.github.io/golden-circle-direct/**

Live, verified by checksum against the local build. That's the link you share and the link you use on the bus. Everything else below is supporting detail.

---

## 2. What this is

The **1.0 Golden Circle Direct** on-mic script — all 35 blocks, verbatim out of Craft — pinned to the road you actually drive. Tap any block and the map flies to **where you say it**, with a dashed line out to **what you point at**.

Structure mirrors the Craft doc exactly: drive → stop → drive → stop → stop → drive.

| Section | Kind | Blocks |
|---|---|---|
| BSÍ Bus Terminal → Þingvellir | 🚌 drive | 11 (1.0i, 1.1–1.10) |
| Þingvellir | 📍 stop | 2 (1.11, 1.12) |
| Þingvellir → Haukadalur Valley | 🚌 drive | 7 (1.13–1.19) |
| Geysir | 📍 stop | 1 (1.20) |
| Gullfoss | 📍 stop | 1 (1.21) |
| Gullfoss → BSÍ | 🚌 drive | 13 (1.22–1.34) |

Every block carries its 🎣 hook, bullets, 🎯 point, 🎤 mic line, 🌫️ weather pivot and 🗣️ pronunciation list. Nothing rewritten, nothing shortened.

Search box hits any word anywhere in the script — `Björk` → 1.26, `tölt` → 1.24, `Sigríður` → 1.21.

**No clock, no drive times, no Google Maps links.** Removed on request.

---

## 3. Where everything lives

### Live
| What | Where |
|---|---|
| **Site (use this)** | https://iphoneiceland.github.io/golden-circle-direct/ |
| Repo | https://github.com/IphoneIceland/golden-circle-direct (public) |
| Backup gist | https://gist.github.com/IphoneIceland/6ace26177d8f304a4dc8d77c5dccba7a (public, 1 file) |

### On the Mac
```
~/Downloads/golden-circle-direct/          ← this project, git repo, remote set, pushed
~/Downloads/golden-circle-hotel-geysir-loop/ ← different project, see §7
~/Downloads/iceland-route-map/             ← the parent week-long map
```

### Files
```
index.html                 the app — welcome, picker, track, script, map. 32 KB
tours.js                   the tour list the picker reads. 1.0, 5.0, 6.0
briefing.js                English welcome (3 items), safety briefing (11 items), the 21-language list
i18n/xx.js                 20 translations of the above + the UI strings. 88 KB the lot
script-1.0.js              Golden Circle Direct — 6 sections, 35 blocks, 208 bullets, 181 pronunciations
route-1.0.js               252.4 km, 8 legs, 4,482 geometry points
cues-1.0.js                35 cues — cue point + target + clock per block
script-5.0.js              South Coast — 10 sections, 31 blocks, 122 bullets, 139 pronunciations
route-5.0.js               417.9 km / 439 min, 7 legs, 5,873 points (via Sólheimajökull)
cues-5.0.js                31 cues
script-6.0.js              South Coast Combo — 10 sections, 31 blocks, 122 bullets, 139 pronunciations
route-6.0.js               417.9 km / 439 min, 7 legs, 5,873 points (via Skógafoss)
cues-6.0.js                31 cues
fonts/                     Norse.woff2, NorseBold.woff2 — self-hosted, no CDN
images/                    iguide-logo-stacked.svg, iguide-logo-line.svg, favicon-64.png
sw.js                      service worker. Cache-first, versioned. **gcd31-v1**
manifest.webmanifest       PWA manifest — installs to the home screen
icon-192.png icon-512.png
vendor/                    Leaflet 1.9.4, vendored. No CDN.
golden-circle-direct.html  the whole app as ONE self-contained file (256 KB) — this is what's in the gist

build-script.py            regenerates script-1.0.js from the Craft export (new format)
build-any.py               regenerates any tour from either Craft format:
                             python3 build-any.py "5.0 South Coast" script-5.0.js
build-route.py             geocodes stops (Nominatim) + routes them (OSRM): python3 build-route.py 5.0
build-single.py            inlines everything into golden-circle-direct.html
```

### Checksums at handover
```
index.html                992928e95436d5ccb53886190026cd8146f2f162daf1eb0f9ed1f08652ba600f
golden-circle-direct.html 825eadf312eb7d163d770f2672575c5f3d98c5443666ab8767936f5419a89b58
tours.js                  9746ab3e217921af8f1712c93511a6b6b2adcd60b3820a0c6caf426fa089f47e
briefing.js               08b59d2574b9ea5b29d5796f01411858ae0a92f0e7ecec5120ef2b4f704c35eb
script-1.0.js             344c9c479cf43d957960a54bf2b9cf72f00341594ca68da0ff12b76a5fed4967
route-1.0.js              e44a25d98d169782e063e72d7ca356c75c6aeb37b6d623519bd9a7078e98087d
cues-1.0.js               fe39b54a9ef0cdb257746bb2c3c93767780a601988f75064b961b3567794bbe2
script-5.0.js             5f790c0f4d2341f919e301a6ca9f8cb0c83dabc3d3274b43fd4b0e3efbe15442
route-5.0.js              c4082022bdcafcf424bf7a8b7b4cafd97ee41452a6994de07299ab93310d9a8d
cues-5.0.js               85fe7febea6cb08cb4fc797f70335d091ac4cbdcb5c051aed3e9d43f8ca2f0d2
script-6.0.js             d1d6f5007461b11274554569acdbc0f4c9911b50cd8afc62cdcd44412f6cdb07
route-6.0.js              c8a40cacddd8f307bdbfd8c5de6f3ec3fa1249f31d1341502b64ac061dfc3b9c
cues-6.0.js               18a420a2a05e83415cb07253029380ac365a0179c7b2dedd1839a07257c85b2b
sw.js                     9aaf6bb230396cb28bdd26efd5915edc0618756071be03a8f220d1bd42fc9d0e
i18n/*.js (rolled up)     1758e332712f12657d00c5fb2907ef0a92ab08782e31f14c8c794935c4350e56
```

### Git
```
SWHASH  sw.js gcd31-v1, single file rebuilt   (HANDOVER commits sit on top of this)
7cbcd4a  A way home that says so in words, at the top of the screen
e9c1f09  Make the way out a different shape from the block arrows
8bdde3d  A way out of a tour: a real back button, and the phone's own back gesture
f40d03b  Resync 1.0 script from corrected Craft manuscript
8844519  Twenty-one languages live for the welcome, safety and UI
e4e9299  Five languages live for the welcome, safety and UI
20da830  Language as a flag dropdown
0f775f5  One welcome screen: language, welcome, safety, then the tours
6c7bff3  iGuide Iceland theme: gold on near-black, Norse headings, logo on the picker
8cf58cd  One app, three tours: picker on launch, data loaded per tour
b8ba091  South Coast 5.0 and 6.0: routes from OSRM, stops pinned from OpenStreetMap
origin → https://github.com/IphoneIceland/golden-circle-direct.git   (pushed, clean)
```

### Keep these three apart
- `golden-circle-direct` — **this** project's own repo + gist `6ace2617…`
- `iceland-route-map` — parent map, gist `908e1337…`
- Scriptable safe box — gist `7ae4b8a9…`, unrelated

---

## 4. The route

**BSÍ → Þingvellir (via Mosfellsdalur) → Geysir → Gullfoss → Friðheimar → Skálholt → Kerið → Selfoss → BSÍ**

**252.4 km**, 4,482 geometry points, coach-legal numbered roads only.

Legs and the roads they use:

| Leg | km | Roads |
|---|---:|---|
| BSÍ → Þingvellir | 46.8 | 49 → 1 → 36 |
| Þingvellir → Geysir | 61.1 | 36 → 365 → 37 → 35 |
| Geysir → Gullfoss | 9.6 | 35 |
| Gullfoss → Friðheimar | 28.7 | 35 |
| Friðheimar → Skálholt | 10.0 | 35 → 31 |
| Skálholt → Kerið | 23.8 | 31 → 35 |
| Kerið → Selfoss | 14.6 | 35 → 1 |
| Selfoss → BSÍ | 57.8 | 1 → 49 |

The route is forced through Mosfellsdalur (blocks 1.6–1.8 need it) and past Laugarvatn (1.16 needs it). **Gullfoss → Friðheimar is pinned to Route 35** — OSRM's default sends it down Routes 358 and 30 to save 2.2 km, which is not a road for a 14 m coach.

---

## 5. Cue points and targets

Each block gets two coordinates:

- **cue** — a point on the route, where you say it
- **target** — the thing out of the window

**29 blocks have a target. 6 do not, deliberately:** 1.0i, 1.9 Norse Expansion, 1.10 Landnám, 1.18 Sturlung Age, 1.24 horses, 1.30 Ingólfur. There is nothing to look at. They read *"no view — tell it anywhere on this stretch."*

Targets are OSM-verified. River blocks (Brúará, Tungufljót, Sog, Ölfusá) use the actual route/river intersection from Overpass geometry, not a river centroid.

---

## 6. ⚠️ Open — things to check before you're on the mic

### Five cue directions don't match the road
Computed from the route heading at closest approach:

| Block | Script says | Actually reads | Distance |
|---|---|---|---|
| 1.34 Rauðhólar | right, 3 o'clock | **left, 9 o'clock** | 0.6 km |
| 1.28 Ölfusá | right, 1–2 o'clock | **8 o'clock** | 0.1 km |
| 1.29 Ölfusárbrú | right, 3 o'clock | **1 o'clock** | 0 m |
| 1.4 Esja | ahead, 12 o'clock | **9 o'clock** at closest approach | 6.3 km |
| 1.15 Hekla | 11 o'clock | **3 o'clock** | 45.8 km |

Esja and Hekla are arguable — the script's direction may be right earlier on the road than at the nearest point. The other three look plain wrong. **Not changed without your say-so.**

### 1.27 "Crossing the Sog" — you don't
This route never crosses the Sog. Nearest approach is 1.4 km. It's a view, not a crossing.

### 1.29 Selfoss bridge dates are impossible
Collapse **Sept 1944**, rebuild "about **five and a half months**", opening **21 Dec 1945**, described as "mid-war". That's 15 months, and Dec 1945 is after the war ended. Two of those three are wrong. **Flagged in red inside the block** so it can't be said by accident.

### Seven more contradictions inside the script itself
1. **Kjarval altarpiece** — intro promises the elf altarpiece "waiting in a valley up the road"; 1.8 says it still hangs at Bakkagerði in the east. Gljúfrasteinn has the *second*, different reject.
2. **Landnám settlers** — 1.10 body says 9,000+; its own weather pivot says 400 filled the island.
3. **Kjalarnesþing** — 1.3 says it was set up at Þingnes; 1.5 and 1.34 say Kjalarnes, moved to Þingnes later.
4. **Settlement date** — 1.9 states 870 flat, 1.10 states 874 flat.
5. **Gljúfrasteinn** called "our next stop" in 1.7, written as a drive-by; 1.18 called "the last stop" in 1.19 with no cue.
6. **Hreppar** is a "Fault" (1.19), a "block" (1.16, 1.20) and a "microplate" (Threads).
7. **Threads index** cites content that isn't in the blocks it points at — six cases.

### Parent project drift, still live
`iceland-route-map` day `d5` still carries the **two wrong pins** and the old *"159.7 km / 2h37, 1 of 120"* figure. Its `index.html` and `i18n.js` also disagree on the d5 pickup time (10:30 vs 10:15) and the Þingvellir window (11:15–12:00 vs 11:15–11:50). Untouched — your call.

---

## 7. The other Golden Circle project

`~/Downloads/golden-circle-hotel-geysir-loop/` is a **different tour**: the Hótel Geysir loop pulled out of the week-long map earlier the same night, with a start-time clock engine, editable dwell times and pinnable bookings. **Never pushed anywhere.** It got renamed out of the way so this project could take the `golden-circle-direct` name.

While building it, two coordinates in the parent map were found to be wrong and were corrected there:
- **Þingvellir** was `64.278608, -21.081941` — the national-park polygon centroid, 3.4 km from the visitor centre, a bare point on Þingvallavegur. Now `64.255561, -21.136075`, car park **P1 Hakið**.
- **Gullfoss** was `64.314452, -20.149556` — the nature-reserve polygon centroid, 2.5 km short of the falls, sitting on Route 35. Now `64.325242, -20.130739`, the visitor centre car park.

Both bad pins came from geocoding a **name** instead of a **feature**. Nominatim hands back polygon centroids for protected areas.

---

## 8. Gotchas — do not relearn these

- **`Cache.put()` throws on an opaque response.** Every cross-origin map tile is opaque. The throw rejected `respondWith` and killed the image. Tiles downloaded fine at 256px and painted nothing. The route line still drew, because SVG isn't a tile. Cost most of an evening.
- **Leaflet's fade animation never flips tiles to opacity 1 behind a service worker.** 52 of 52 tiles loaded, all invisible, no error anywhere. `L.map(el, {fadeAnimation:false})` fixes it. This is why `fadeAnimation:false` is in the code — leave it.
- **A cache-first service worker will serve you your own stale bug.** Two fixes looked like they'd done nothing because the worker kept serving its cached `index.html`. `sw.js` is **network-first** now. Keep it that way.
- **The Claude desktop preview pane blocks all external images.** A map will look broken in it and be fine in a browser. Open in a browser before diagnosing anything.
- **Never run `git` in the Cowork device VM.** No network, and it cannot unlink — every command succeeds and strands a `.git/index.lock` that blocks git on the real Mac.
- **Nominatim returns polygon centroids for protected areas.** Reverse-geocode any pin derived from a place *name* before a coach goes near it.
- **OSRM's fastest line is not always a coach line.** Read the step `ref`s, not just the total.
- **`split(":")` on a value containing a time is a trap.**

---

## 9. Working on it

```bash
cd ~/Downloads/golden-circle-direct && python3 -m http.server 8822
# then http://localhost:8822
```

Needs the server — the service worker won't register off `file://`.

**What to edit where**
- `index.html` — the app: layout, map, interaction
- `script-1.0.js` — the script content. Safe to hand-edit
- `cues-1.0.js` — cue/target coordinates and clock directions. Safe to hand-edit
- `route-1.0.js` — generated geometry. Move a pin and the route needs regenerating
- `sw.js` — **bump `VERSION` on every change to a shell file**, or browsers keep the old one

**Shipping**
```bash
cd ~/Downloads/golden-circle-direct
git add -A && git commit -m "..." && git push
# rebuild takes 1–2 min, then verify rather than trusting it:
curl -s https://iphoneiceland.github.io/golden-circle-direct/index.html | shasum -a 256
shasum -a 256 index.html
# refresh the backup gist
gh gist edit 6ace26177d8f304a4dc8d77c5dccba7a -a golden-circle-direct.html
```

`gh` is authenticated on the Mac as **IphoneIceland** (`gist`, `read:org`, `repo`, `workflow`). Shells older than 8 Aug need `eval "$(/opt/homebrew/bin/brew shellenv zsh)"` first.

---

## 10. What isn't done

- [ ] Five cue directions above — decide and apply
- [ ] Selfoss bridge dates — verify and correct
- [ ] The seven internal contradictions — resolve in Craft, then regenerate `script-1.0.js`
- [ ] 1.16 Laugarvatn's cue point is 19 km from the lake; the cursor logic pushed it past. Cosmetic, worth a nudge
- [ ] Þingvellir and Gullfoss both have a second candidate pin (P5 Valhöll; the marked bus bays 250 m past the visitor centre car park). One-line changes if you want the other one
- [ ] No offline test on an actual phone yet
- [ ] Sections 2.0 Snowmobiling, 3.0 Lagoons and 4.0 Friðheimar exist in Craft and have no map
- [ ] **The tour scripts are English only.** The welcome, safety and UI speak 21 languages; the actual stories speak one. ~7,000 words × 20 languages × 3 tours
- [ ] `build-route.py`'s `PLACES` table only knows the South Coast stops — 2.0, 3.0, 4.0 and 7.0 need entries adding before they can be routed
- [ ] South Coast pins are OSM town/landmark centroids, not the coach bays. Fine for now; worth nudging once you've stood in them
- [ ] The 🧵 in the "Three Names" title comes from the Craft heading itself — a document edit, not an app one
