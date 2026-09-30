// frontend/src/services/pushNotifications.js

const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY;

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('[PUSH] Not supported in this browser');
    return null;
  }
  try {
    return await navigator.serviceWorker.register('/sw.js');
  } catch (err) {
    console.error('[PUSH] Service worker registration failed:', err);
    return null;
  }
}

export async function askPermission() {
  const permission = await Notification.requestPermission();
  return permission === 'granted';
}

export async function subscribeUser(phoneNumber) {
  if (!VAPID_PUBLIC_KEY) {
    console.warn('[PUSH] VAPID public key missing');
    return null;
  }

  const registration = await registerServiceWorker();
  if (!registration) return null;

  const granted = await askPermission();
  if (!granted) return null;

  try {
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
    });

    const subJson = subscription.toJSON();
    // Use the shared axios instance so it respects VITE_API_BASE_URL
    const { default: api } = await import('./api');
    await api.post('/subscribe-push/', {
      phone_number: phoneNumber,
      endpoint: subJson.endpoint,
      p256dh: subJson.keys.p256dh,
      auth: subJson.keys.auth,
    });

    console.log('[PUSH] Subscribed successfully');
    return subscription;
  } catch (err) {
    console.error('[PUSH] Subscribe failed:', err);
    return null;
  }
}