const CACHE_NAME = 'pulsehr-v1';
const OFFLINE_URL = '/offline.html';
const ASSETS_TO_CACHE = [
  OFFLINE_URL
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      await cache.addAll(ASSETS_TO_CACHE);
    })()
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)));
      await clients.claim();
    })()
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          const networkResponse = await fetch(event.request);
          return networkResponse;
        } catch (error) {
          const cache = await caches.open(CACHE_NAME);
          const cachedResponse = await cache.match(OFFLINE_URL);
          return cachedResponse;
        }
      })(),
    );
  } else if (ASSETS_TO_CACHE.includes(new URL(event.request.url).pathname)) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        return cachedResponse || fetch(event.request);
      }),
    );
  }
});

