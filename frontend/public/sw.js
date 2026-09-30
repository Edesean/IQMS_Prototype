// frontend/public/sw.js

self.addEventListener('push', function (event) {
  console.log('[SW] Push event received');

  let data = {};
  try {
    data = event.data ? event.data.json() : {};
    console.log('[SW] Parsed JSON payload:', data);
  } catch (e) {
    console.error('[SW] Failed to parse JSON, using text:', e);
    data = { title: 'IQMS', body: event.data ? event.data.text() : 'New notification' };
  }

  const title = data.title || 'IQMS Notification';
  const options = {
    body: data.body || 'You have a new update.',
    icon: '/vite.svg',
    badge: '/vite.svg',
    tag: data.ticket_number || 'iqms',
    requireInteraction: true,
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
      .then(() => console.log('[SW] Notification shown successfully'))
      .catch(err => console.error('[SW] showNotification error:', err))
  );
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then(function (clientList) {
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url.includes('/check-status') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('/check-status');
      }
    })
  );
});