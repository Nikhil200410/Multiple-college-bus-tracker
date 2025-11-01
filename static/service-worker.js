const CACHE_NAME = "bus-tracker-cache-v3";
const urlsToCache = [
  "/",
  "/role",
  "/sender",
  "/manifest.json",
  "/static/icon-192.png",
  "/static/icon-512.png"
];

// Install event
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
  self.skipWaiting();
});

// Activate event
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      )
    )
  );
  self.clients.claim();
});

// Fetch event
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response =>
      response ||
      fetch(event.request).catch(() =>
        new Response("⚠️ You are offline. Please reconnect.", {
          headers: { "Content-Type": "text/plain" }
        })
      )
    )
  );
});
