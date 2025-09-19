"""Notification model for multi-channel alerts."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class NotificationType(str, enum.Enum):
    DONATION_SUCCESS = "donation_success"
    INCIDENT_ALERT = "incident_alert"
    SYSTEM = "system"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    related_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    channels: Mapped[list[str]] = mapped_column(ARRAY(String(20)), nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notification_status"),
        nullable=False,
        default=NotificationStatus.PENDING,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"Notification(id={self.id}, type={self.type})"
