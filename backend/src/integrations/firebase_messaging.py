"""Firebase Cloud Messaging 통합."""

import os
from typing import Optional
import firebase_admin
from firebase_admin import credentials, messaging


class FirebaseMessagingService:
    """Firebase Cloud Messaging 서비스."""

    def __init__(self):
        """Firebase Admin SDK 초기화."""
        if not firebase_admin._apps:
            # firebase-service-account.json 파일 경로
            cred_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "firebase-service-account.json"
            )

            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                print(f"Warning: Firebase credentials not found at {cred_path}")

    async def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
        url: Optional[str] = None
    ) -> bool:
        """
        FCM 푸시 알림 전송.

        Args:
            token: FCM 디바이스 토큰
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터
            url: 클릭 시 이동할 URL

        Returns:
            전송 성공 여부
        """
        try:
            notification_data = data or {}
            if url:
                notification_data["url"] = url

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=notification_data,
                token=token,
            )

            response = messaging.send(message)
            print(f"Successfully sent message: {response}")
            return True

        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return False

    async def send_multicast_notification(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
        url: Optional[str] = None
    ) -> tuple[int, int]:
        """
        여러 디바이스에 FCM 푸시 알림 전송.

        Args:
            tokens: FCM 디바이스 토큰 리스트
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터
            url: 클릭 시 이동할 URL

        Returns:
            (성공 개수, 실패 개수)
        """
        try:
            notification_data = data or {}
            if url:
                notification_data["url"] = url

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=notification_data,
                tokens=tokens,
            )

            response = messaging.send_multicast(message)
            print(f"Successfully sent {response.success_count} messages")
            print(f"Failed to send {response.failure_count} messages")

            return response.success_count, response.failure_count

        except Exception as e:
            print(f"Error sending multicast FCM notification: {e}")
            return 0, len(tokens)


# 전역 인스턴스
firebase_service = FirebaseMessagingService()
