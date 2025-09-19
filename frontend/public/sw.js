self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {};
  const title = data.title || 'BoDam 알림';
  const options = {
    body: data.message,
    icon: '/icons/icon-192.png'
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow('/notifications'));
});
