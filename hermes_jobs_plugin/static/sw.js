// Minimal service worker: cache the static shell only. API responses
// (/api/*) are ALWAYS network-first and never cached -- a stale job list
// on a control panel like this is actively harmful, not a convenience.
"use strict";

const CACHE_NAME = "hermes-jobs-shell-v5";
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
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
    );
    await self.clients.claim();
    // A shell deploy only becomes visible after the old cache-first page is
    // replaced. Reload open tabs once when a new service worker activates so
    // users do not have to hard-refresh a control panel to see new controls.
    const clients = await self.clients.matchAll({ type: "window" });
    clients.forEach((client) => client.navigate(client.url).catch(() => {}));
  })());
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  if (url.pathname.startsWith("/api/")) {
    // Network-only. Let it fail visibly offline rather than serve stale
    // job state -- the app.js toast on fetch failure communicates this.
    return;
  }

  // Network-first for the shell so a UI deploy shows up on the next load;
  // the cache is an offline fallback only, never a stale first answer.
  event.respondWith(
    fetch(event.request)
      .then((resp) => {
        if (resp.ok) {
          const copy = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        }
        return resp;
      })
      .catch(() => caches.match(event.request).then(
        (cached) => cached || new Response("Offline", { status: 503 })
      ))
  );
});
