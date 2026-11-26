const CACHE_NAME = 'fitmate-tcm-v2';
const STATIC_ASSETS = [
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/favicon.ico',
];

const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Offline — FitMate TCM</title>
</head>
<body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#F7F4EE;color:#211C17;font-family:system-ui,-apple-system,sans-serif;padding:24px;text-align:center;">
  <main style="max-width:420px;background:#FFFFFF;border:1px solid rgba(33,28,23,0.12);border-radius:16px;padding:28px;">
    <h1 style="margin:0 0 10px;font-size:20px;">Anda Sedang Offline</h1>
    <p style="margin:0;font-size:14px;line-height:1.6;color:#4A4238;">
      FitMate TCM memerlukan koneksi internet untuk memuat halaman dan menganalisis komposisi herbal. Periksa jaringan Anda lalu coba muat ulang.
    </p>
  </main>
</body>
</html>`;

function isStaticAsset(url) {
  if (url.origin !== self.location.origin) return false;
  return (
    url.pathname.startsWith('/icons/') ||
    url.pathname.startsWith('/_next/static/') ||
    url.pathname === '/manifest.json' ||
    url.pathname === '/favicon.ico'
  );
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.map((key) => {
            if (key !== CACHE_NAME) {
              return caches.delete(key);
            }
            return Promise.resolve();
          })
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Never intercept non-http(s) schemes
  if (url.protocol !== 'http:' && url.protocol !== 'https:') {
    return;
  }

  // Never cache admin routes, API calls, or Next.js RSC payloads
  if (
    url.pathname.startsWith('/admin') ||
    url.pathname.startsWith('/api') ||
    url.searchParams.has('_rsc')
  ) {
    return;
  }

  // Navigation requests: network-first with explicit Indonesian offline fallback
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(OFFLINE_HTML, {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 'Content-Type': 'text/html; charset=utf-8' },
        })
      )
    );
    return;
  }

  // Stale-while-revalidate strictly for known static assets
  if (!isStaticAsset(url)) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request)
        .then((networkResponse) => {
          if (
            networkResponse &&
            networkResponse.status === 200 &&
            networkResponse.type === 'basic'
          ) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(() => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return new Response('Aset tidak tersedia saat offline.', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
          });
        });

      return cachedResponse || fetchPromise;
    })
  );
});
