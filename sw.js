/* iGuide - Iceland — service worker.
   Two caches, on purpose:
     SHELL  cache-first, versioned. The app itself. Bump VERSION to ship an update.
     TILES  stale-while-revalidate, capped. Map imagery you have already looked at.
   Load the page once on hotel wifi, pan the loop, and the whole day survives
   the dead patch past Laugarvatn. */
const VERSION = "gcd81-v1";
const SHELL   = VERSION + "-shell";
const TILES   = VERSION + "-tiles";
const TILE_CAP = 900;

const SHELL_FILES = [
  "./", "./index.html", "./tours.js", "./briefing.js", "./images/hero-road.webp", "./images/logo-crest.webp",
  "./i18n/de.js", "./i18n/fr.js", "./i18n/es.js", "./i18n/it.js", "./i18n/nl.js",
  "./i18n/pt.js", "./i18n/pl.js", "./i18n/da.js", "./i18n/sv.js", "./i18n/no.js",
  "./i18n/fi.js", "./i18n/is.js", "./i18n/zh.js", "./i18n/ja.js", "./i18n/ko.js",
  "./i18n/ru.js", "./i18n/ar.js", "./i18n/hi.js", "./i18n/tr.js", "./i18n/he.js",
  "./route-1.0.js", "./script-1.0.js", "./cues-1.0.js", "./route-2.0.js", "./script-2.0.js", "./cues-2.0.js", "./route-3.0.js", "./script-3.0.js", "./cues-3.0.js",
  "./route-4.0.js", "./script-4.0.js", "./cues-4.0.js", "./route-5.0.js", "./script-5.0.js", "./cues-5.0.js", "./route-6.0.js", "./script-6.0.js", "./cues-6.0.js",
  "./route-7.0.js", "./script-7.0.js", "./cues-7.0.js", "./route-10.0.js", "./script-10.0.js", "./cues-10.0.js", "./route-11.0.js", "./script-11.0.js", "./cues-11.0.js",
  "./vendor/leaflet.js", "./vendor/leaflet.css",
  "./vendor/images/marker-icon.png", "./vendor/images/marker-shadow.png",
  "./vendor/images/layers.png", "./vendor/images/layers-2x.png",
  "./fonts/Norse.woff2", "./fonts/NorseBold.woff2",
  "./images/iguide-logo-stacked.svg", "./images/iguide-logo-line.svg", "./images/favicon-64.png",
  "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"
];

// The twenty tour translations are ~3 MB all told. They are cached best-effort
// AFTER the shell lands: a guest who boards without signal and picks Japanese
// still gets a Japanese tour, but one flaky download on hotel wifi can no
// longer take the whole install down with it.
const TOUR_TR = ["de","fr","es","it","nl","pt","pl","da","sv","no",
                 "fi","is","zh","ja","ko","ru","ar","hi","tr","he"]
                .map(l => "./i18n/tours/" + l + ".js");

self.addEventListener("install", e=>{
  e.waitUntil(caches.open(SHELL)
    .then(c => c.addAll(SHELL_FILES)
                .then(() => Promise.all(TOUR_TR.map(u => c.add(u).catch(()=>null)))))
    .then(()=>self.skipWaiting()));
});

self.addEventListener("activate", e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(
    ks.filter(k=>k!==SHELL && k!==TILES).map(k=>caches.delete(k))
  )).then(()=>self.clients.claim()));
});

function isTile(url){
  return /arcgisonline\.com|tile\.opentopomap\.org|basemaps\.cartocdn\.com/.test(url.hostname);
}

async function trimTiles(){
  const c = await caches.open(TILES);
  const keys = await c.keys();
  if(keys.length <= TILE_CAP) return;
  for(const k of keys.slice(0, keys.length - TILE_CAP)) await c.delete(k);
}

self.addEventListener("fetch", e=>{
  const req = e.request;
  if(req.method !== "GET") return;
  const url = new URL(req.url);

  if(isTile(url)){
    e.respondWith((async ()=>{
      const c = await caches.open(TILES);
      const hit = await c.match(req);
      // Cache.put() throws TypeError on an opaque (status 0) response, and a cross-origin
      // tile fetched without CORS is always opaque. The throw rejected respondWith, which
      // killed the image — so every satellite tile silently failed while the route line,
      // being SVG, drew fine. Only cache what is safely cacheable; pass the rest through.
      const net = fetch(req).then(res=>{
        if(res && res.ok && res.type !== "opaque"){
          try { c.put(req, res.clone()); trimTiles(); } catch(e){ /* not cacheable */ }
        }
        return res;
      }).catch(()=>null);
      return hit || (await net) || new Response("", {status:504});
    })());
    return;
  }

  if(url.origin !== location.origin) return;

  // NETWORK-FIRST for the app's own files, cache only as the offline fallback.
  // Cache-first bit hard: a fixed index.html sat on disk while the worker kept serving
  // the broken copy out of its cache, so the fix looked like it had not worked at all.
  // The shell is ~100 KB on a hotel wifi; freshness is worth more than the millisecond.
  e.respondWith((async ()=>{
    const c = await caches.open(SHELL);
    try{
      const res = await fetch(req, {cache:"no-store"});
      if(res && res.ok){ try{ c.put(req, res.clone()); }catch(_){} }
      return res;
    }catch(err){
      return (await c.match(req, {ignoreSearch:true}))
          || (await c.match("./index.html"))
          || new Response("Offline", {status:503});
    }
  })());
});
