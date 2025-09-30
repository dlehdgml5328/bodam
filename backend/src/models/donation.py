"""Donation model capturing financial transactions."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DonationType(str, enum.Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class DonationStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    fire_station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fire_stations.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[DonationType] = mapped_column(
        SAEnum(
            DonationType,
            name="donation_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    frequency: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[DonationStatus] = mapped_column(
        SAEnum(
            DonationStatus,
            name="donation_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=DonationStatus.PENDING,
    )
    payment_method: Mapped[str | None] = mapped_column(String(50))
    toss_payment_key: Mapped[str | None] = mapped_column(String(120))
    toss_order_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    message: Mapped[str | None] = mapped_column(String(500))
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    receipt_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", backref="donations")
    fire_station = relationship("FireStation", backref="donations")

    def __repr__(self) -> str:
        return f"Donation(id={self.id}, amount={self.amount})"
