// Minimal service worker: cache the static shell only. API responses
// (/api/*) are ALWAYS network-first and never cached -- a stale job list
// on a control panel like this is actively harmful, not a convenience.
"use strict";

const CACHE_NAME = "hermes-jobs-shell-v1";
const SHELL_FILES = [
  "/", "/index.html", "/style.css", "/app.js", "/manifest.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  if (url.pathname.startsWith("/api/")) {
    // Network-only. Let it fail visibly offline rather than serve stale
    // job state -- the app.js toast on fetch failure communicates this.
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const network = fetch(event.request)
        .then((resp) => {
          if (resp.ok) {
            const copy = resp.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return resp;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
