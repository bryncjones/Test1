// Hang Eleven service worker: keeps the app, survey data and libraries available offline.
// The forecast itself is fetched by the page and saved there, so forecast and map-tile requests pass straight through.
const CACHE = 'hang-eleven-v1';
const CORE = [
  './', './index.html', './privacy.html', './manifest.webmanifest',
  './data/meta.json', './data/terrain.png', './data/imagery.jpg', './data/landcover.png',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png',
];
// The 3D library comes from a CDN; cache it up front so the app starts with no signal.
// Keep this version in step with the import map in index.html.
const THREE_CDN = 'https://cdn.jsdelivr.net/npm/three@0.186.1/';
const LIBS = [THREE_CDN + 'build/three.module.js', THREE_CDN + 'build/three.core.js', THREE_CDN + 'examples/jsm/controls/OrbitControls.js'];
const PASS_THROUGH = /open-meteo\.com|api\.mapbox\.com|api\.maptiler\.com/;

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(async (c) => {
    await c.addAll(CORE);
    // a CDN hiccup shouldn't block install; these are also cached the first time the page loads them
    await Promise.all(LIBS.map((u) => c.add(new Request(u, { mode: 'cors' })).catch(() => {})));
  }).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || PASS_THROUGH.test(req.url)) return;
  if (req.mode === 'navigate') {
    // Pages: network first so updates arrive, cached copy when offline
    e.respondWith(
      fetch(req)
        .then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); return res; })
        .catch(() => caches.match(req).then((r) => r || caches.match('./index.html')))
    );
    return;
  }
  // Everything else (data, three.js, fonts): cached copy at once, refreshed in the background
  e.respondWith(
    caches.open(CACHE).then((c) => c.match(req).then((hit) => {
      const net = fetch(req).then((res) => { if (res.ok || res.type === 'opaque') c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    }))
  );
});
