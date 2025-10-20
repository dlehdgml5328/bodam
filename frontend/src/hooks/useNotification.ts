import { useEffect, useState } from 'react';
import { requestNotificationPermission } from '@/lib/firebase';
import { apiRequest } from '@/lib/api';

export function useNotification() {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [fcmToken, setFcmToken] = useState<string | null>(null);

  useEffect(() => {
    // 현재 알림 권한 상태 확인
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }

    // Service Worker 등록
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/firebase-messaging-sw.js')
        .then((registration) => {
          console.log('Service Worker registered:', registration);
        })
        .catch((error) => {
          console.error('Service Worker registration failed:', error);
        });
    }

    // 포그라운드 메시지 리스너 (페이지가 열려있을 때)
    if (typeof window !== 'undefined') {
      import('@/lib/firebase').then(({ messaging }) => {
        if (messaging) {
          const { onMessage } = require('firebase/messaging');
          onMessage(messaging, (payload: any) => {
            console.log('Received foreground message:', payload);

            // 브라우저 알림 표시
            if (Notification.permission === 'granted') {
              const notificationTitle = payload.notification?.title || '보담 알림';
              const notificationOptions = {
                body: payload.notification?.body || '',
                icon: '/icon-192x192.png',
                badge: '/icon-192x192.png',
                data: payload.data,
                tag: payload.data?.type || 'default',
              };

              new Notification(notificationTitle, notificationOptions);
            }
          });
        }
      });
    }
  }, []);

  const requestPermission = async () => {
    try {
      const token = await requestNotificationPermission();

      if (token) {
        setFcmToken(token);
        setPermission('granted');

        // 서버에 FCM 토큰 저장
        try {
          await apiRequest('/notifications/fcm-token', {
            method: 'POST',
            body: JSON.stringify({ token }),
          });
          console.log('FCM token saved to server');
        } catch (error) {
          console.error('Failed to save FCM token to server:', error);
        }
      } else {
        setPermission('denied');
      }
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      setPermission('denied');
    }
  };

  return {
    permission,
    fcmToken,
    requestPermission,
  };
}
