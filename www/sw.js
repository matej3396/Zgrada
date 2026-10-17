/* Zgrada : tout fonctionne hors ligne. Monter CACHE à chaque version. */
var CACHE = "zgrada-v1";
var CORE = ["./", "index.html", "manifest.webmanifest", "icon.svg", "icon-192.png", "icon-512.png"];
self.addEventListener("install", function (e) { e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(CORE); }).then(function () { return self.skipWaiting(); })); });
self.addEventListener("activate", function (e) { e.waitUntil(caches.keys().then(function (k) { return Promise.all(k.filter(function (x) { return x !== CACHE; }).map(function (x) { return caches.delete(x); })); }).then(function () { return self.clients.claim(); })); });
self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  var url = new URL(e.request.url);
  if (url.origin === location.origin && e.request.mode === "navigate") {
    /* Réseau d'abord pour la page (nouvelle version), cache si hors ligne */
    e.respondWith(fetch(e.request).then(function (r) { var c = r.clone(); caches.open(CACHE).then(function (x) { x.put("index.html", c); }); return r; }).catch(function () { return caches.match("index.html"); }));
    return;
  }
  /* Le reste (icônes, polices) : cache d'abord */
  e.respondWith(caches.match(e.request).then(function (hit) { return hit || fetch(e.request).then(function (r) { if (r.ok || r.type === "opaque") { var c = r.clone(); caches.open(CACHE).then(function (x) { x.put(e.request, c); }); } return r; }); }));
});
