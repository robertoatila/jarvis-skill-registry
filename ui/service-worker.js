'use strict';

const CACHE_NAME = 'jarvis-mark-liv-shell-v3';
const STATIC_SHELL = [
  '/',
  '/index.html',
  '/jarvis.css',
  '/workspace.css',
  '/mark-liv.css',
  '/chat-session.js',
  '/jarvis.js',
  '/workspace.js',
  '/mark-liv-cockpit.js',
];

const REMOTE_OWNED_PATHS = new Set([
  '/remote-companion.css',
  '/remote-companion.js',
  '/remote-service-worker.js',
  '/manifest.webmanifest',
]);

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => Promise.all(
      names
        .filter((name) => name.startsWith('jarvis-mark-liv-shell-') && name !== CACHE_NAME)
        .map((name) => caches.delete(name))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);

  // Runtime truth must always come from the PC. Never replay API cache as live state.
  if (requestUrl.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // The dedicated Remote Companion owns /remote/ and its shell assets.
  // Do not cache, rewrite, or provide desktop fallbacks for that surface here.
  if (
    requestUrl.pathname === '/remote'
    || requestUrl.pathname.startsWith('/remote/')
    || REMOTE_OWNED_PATHS.has(requestUrl.pathname)
  ) {
    return;
  }

  if (event.request.method !== 'GET') return;

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put('/index.html', copy));
          }
          return response;
        })
        .catch(() => caches.match('/index.html'))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
      if (response && response.ok && requestUrl.origin === self.location.origin) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
      }
      return response;
    }))
  );
});
