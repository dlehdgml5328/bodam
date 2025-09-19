"""Notification orchestration service (DB + WebSocket broadcast)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.event_bus import EventBus
from src.models.notification import Notification, NotificationStatus, NotificationType

logger = logging.getLogger(__name__)


class WebSocketBroadcaster(Protocol):
    async def send_notification(self, user_id: uuid.UUID, payload: dict) -> None: ...


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        broadcaster: WebSocketBroadcaster,
        event_bus: EventBus | None = None,
    ) -> None:
        self._session = session
        self._broadcaster = broadcaster
        self._event_bus = event_bus

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        channels: list[str] | None = None,
        related_id: uuid.UUID | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            channels=channels or ["websocket"],
            related_id=related_id,
        )
        self._session.add(notification)
        await self._session.flush()

        await self._broadcast(notification)
        return notification

    async def mark_as_read(self, notification_id: uuid.UUID) -> Notification:
        notification = await self._session.get(Notification, notification_id)
        if notification is None:
            raise ValueError(f"Notification {notification_id} not found")
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await self._session.flush()
        return notification

    async def list_user_notifications(
        self, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[Notification]:
        result = await self._session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars())

    async def _broadcast(self, notification: Notification) -> None:
        if "websocket" not in notification.channels:
            logger.debug("Notification %s does not target websocket channel", notification.id)
            return

        payload = {
            "type": "notification",
            "id": str(notification.id),
            "title": notification.title,
            "message": notification.message,
            "status": notification.status.value,
        }
        try:
            await self._broadcaster.send_notification(notification.user_id, payload)
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            if self._event_bus:
                await self._event_bus.publish("notification.sent", payload)
        except Exception:  # pragma: no cover - defensive log
            logger.exception("Failed to broadcast notification %s", notification.id)
            notification.status = NotificationStatus.FAILED
        finally:
            await self._session.flush()


__all__ = ["NotificationService", "WebSocketBroadcaster"]
