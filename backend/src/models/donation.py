"""Donation and subscription domain models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
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


class DonationMode(str, enum.Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"


class AllocationType(str, enum.Enum):
    PRIMARY = "primary"
    SPLIT = "split"
    EACH = "each"
    CUSTOM = "custom"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class SubscriptionCycle(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


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
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[DonationMode] = mapped_column(
        SAEnum(
            DonationMode,
            name="donation_mode",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=DonationMode.SINGLE,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="KRW")
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
    billing_customer_key: Mapped[str | None] = mapped_column(String(120))
    billing_key: Mapped[str | None] = mapped_column(String(120))
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donation_subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    message: Mapped[str | None] = mapped_column(String(500))
    donor_display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    needs_receipt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_group_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    receipt_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", backref="donations")
    fire_station = relationship("FireStation", backref="donations")
    group = relationship("Group", backref="donations")
    allocations: Mapped[list["DonationAllocation"]] = relationship(
        "DonationAllocation",
        back_populates="donation",
        cascade="all, delete-orphan",
    )
    subscription: Mapped["DonationSubscription | None"] = relationship(
        "DonationSubscription",
        back_populates="origin_donation",
        foreign_keys=[subscription_id],
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"Donation(id={self.id}, amount={self.amount}, mode={self.mode.value})"


class DonationAllocation(Base):
    __tablename__ = "donation_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donations.id", ondelete="CASCADE"), nullable=False
    )
    fire_station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fire_stations.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    allocation_type: Mapped[AllocationType] = mapped_column(
        SAEnum(
            AllocationType,
            name="donation_allocation_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=AllocationType.PRIMARY,
    )

    donation = relationship("Donation", back_populates="allocations")
    fire_station = relationship("FireStation")

    def __repr__(self) -> str:
        return (
            f"DonationAllocation(id={self.id}, donation_id={self.donation_id}, "
            f"fire_station_id={self.fire_station_id}, amount={self.amount})"
        )


class DonationSubscription(Base):
    __tablename__ = "donation_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    origin_donation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donations.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(
            SubscriptionStatus,
            name="donation_subscription_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )
    cycle: Mapped[SubscriptionCycle] = mapped_column(
        SAEnum(
            SubscriptionCycle,
            name="donation_subscription_cycle",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="KRW")
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    toss_customer_key: Mapped[str | None] = mapped_column(String(120))
    toss_billing_key: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )

    user = relationship("User", backref="donation_subscriptions")
    origin_donation: Mapped["Donation | None"] = relationship(
        "Donation",
        foreign_keys=[origin_donation_id],
        remote_side="Donation.id",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"DonationSubscription(id={self.id}, status={self.status.value}, "
            f"cycle={self.cycle.value})"
        )


__all__ = [
    "Donation",
    "DonationAllocation",
    "DonationSubscription",
    "DonationType",
    "DonationStatus",
    "DonationMode",
    "AllocationType",
    "SubscriptionStatus",
    "SubscriptionCycle",
]
