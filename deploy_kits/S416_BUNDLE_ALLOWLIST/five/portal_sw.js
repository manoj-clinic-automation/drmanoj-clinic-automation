/* portal_sw.js -- kit S366_RING_POPUP (session 279, 22-Sep-2026)
 * The Clinic app's service worker: shows the ring-time pop-up the server pushes, replaces it when someone
 * answers, closes it when the call ends, and opens the Call Tracker (already signed in) on tap.
 * It caches nothing and intercepts no request -- the portal keeps working exactly as before without it. */
self.addEventListener('install', function (e) { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });

self.addEventListener('push', function (e) {
  var d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = { kind: 'ring', title: 'Clinic', body: e.data ? e.data.text() : '' }; }
  var tag = String(d.tag || 'clinic');
  if (d.kind === 'close') {
    e.waitUntil(self.registration.getNotifications({ tag: tag }).then(function (list) { list.forEach(function (n) { n.close(); }); }));
    return;
  }
  var opts = {
    body: String(d.body || ''),
    tag: tag,
    renotify: d.renotify !== false,
    requireInteraction: !!d.requireInteraction,
    icon: '/portal/pwa-icon-192.png',
    badge: '/portal/pwa-icon-192.png',
    vibrate: d.kind === 'ring' ? [200, 100, 200, 100, 200] : [100],
    timestamp: d.ts || Date.now(),
    data: { url: d.url || '/portal', kind: d.kind || '', mobile: d.mobile || '' }
  };
  e.waitUntil(self.registration.showNotification(String(d.title || 'Clinic'), opts));
});

self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  var url = (e.notification.data && e.notification.data.url) || '/portal';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      if (c.url && c.url.indexOf('/portal') >= 0 && 'focus' in c) { return c.focus().then(function (w) { return w && w.navigate ? w.navigate(url) : w; }); }
    }
    return self.clients.openWindow(url);
  }));
});
