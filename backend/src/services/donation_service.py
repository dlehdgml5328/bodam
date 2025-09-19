"""Donation domain service with Toss Payments integration hooks."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Protocol, runtime_checkable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.donation import Donation, DonationStatus, DonationType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckoutSession:
    order_id: str
    payment_url: str


@dataclass(frozen=True)
class PaymentConfirmation:
    payment_key: str
    method: str
    approved_at: datetime


@runtime_checkable
class PaymentsGateway(Protocol):
    async def create_checkout(
        self,
        *,
        amount: Decimal,
        order_id: str,
        customer_name: str,
        success_url: str,
        fail_url: str,
    ) -> CheckoutSession: ...

    async def confirm_payment(
        self,
        *,
        payment_key: str,
        order_id: str,
        amount: Decimal,
    ) -> PaymentConfirmation: ...

    async def request_refund(
        self,
        *,
        payment_key: str,
        amount: Decimal,
        reason: str,
    ) -> None: ...


class DonationNotFoundError(Exception):
    """Raised when a donation cannot be located."""


class DonationService:
    def __init__(self, session: AsyncSession, payments: PaymentsGateway) -> None:
        self._session = session
        self._payments = payments

    async def create_donation(
        self,
        *,
        user_id: uuid.UUID,
        fire_station_id: uuid.UUID,
        amount: Decimal,
        donation_type: DonationType,
        success_url: str,
        fail_url: str,
        frequency: str | None = None,
        message: str | None = None,
        is_anonymous: bool = False,
    ) -> tuple[Donation, CheckoutSession]:
        order_id = f"bodam-{uuid.uuid4()}"
        donation = Donation(
            user_id=user_id,
            fire_station_id=fire_station_id,
            amount=amount,
            type=donation_type,
            frequency=frequency,
            message=message,
            is_anonymous=is_anonymous,
            toss_order_id=order_id,
        )
        self._session.add(donation)
        await self._session.flush()

        checkout = await self._payments.create_checkout(
            amount=amount,
            order_id=order_id,
            customer_name=str(user_id),
            success_url=success_url,
            fail_url=fail_url,
        )
        return donation, checkout

    async def confirm_donation(
        self,
        *,
        donation_id: uuid.UUID,
        payment_key: str,
    ) -> Donation:
        donation = await self._session.get(Donation, donation_id)
        if donation is None:
            raise DonationNotFoundError(str(donation_id))

        confirmation = await self._payments.confirm_payment(
            payment_key=payment_key,
            order_id=donation.toss_order_id,
            amount=donation.amount,
        )
        donation.status = DonationStatus.COMPLETED
        donation.toss_payment_key = confirmation.payment_key
        donation.payment_method = confirmation.method
        donation.completed_at = confirmation.approved_at
        await self._session.flush()
        return donation

    async def get_donation(self, donation_id: uuid.UUID) -> Donation:
        donation = await self._session.get(Donation, donation_id)
        if donation is None:
            raise DonationNotFoundError(str(donation_id))
        return donation

    async def list_donations_for_user(
        self, user_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> list[Donation]:
        result = await self._session.execute(
            select(Donation)
            .where(Donation.user_id == user_id)
            .order_by(Donation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars())

    async def request_refund(
        self,
        *,
        donation_id: uuid.UUID,
        reason: str,
    ) -> Donation:
        donation = await self.get_donation(donation_id)
        if donation.status != DonationStatus.COMPLETED:
            raise ValueError("Refunds can only be requested for completed donations")
        if not donation.toss_payment_key:
            raise ValueError("Donation does not have a payment key yet")

        await self._payments.request_refund(
            payment_key=donation.toss_payment_key,
            amount=donation.amount,
            reason=reason,
        )
        donation.status = DonationStatus.REFUNDED
        donation.refunded_at = datetime.now(timezone.utc)
        await self._session.flush()
        return donation


__all__ = [
    "DonationService",
    "DonationNotFoundError",
    "PaymentsGateway",
    "CheckoutSession",
    "PaymentConfirmation",
]
