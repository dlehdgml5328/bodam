export async function subscribePush(): Promise<PushSubscription | null> {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    return null;
  }

  const registration = await navigator.serviceWorker.register('/sw.js');
  return registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: process.env.NEXT_PUBLIC_WEB_PUSH_KEY,
  });
}
