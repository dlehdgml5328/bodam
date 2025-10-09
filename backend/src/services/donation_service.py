"""Donation domain service with Toss Payments integration hooks."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Iterable, Protocol, Sequence, runtime_checkable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.donation import (
    AllocationType,
    Donation,
    DonationAllocation,
    DonationMode,
    DonationStatus,
    DonationSubscription,
    DonationType,
    SubscriptionCycle,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckoutSession:
    order_id: str
    payment_url: str


@dataclass(frozen=True)
class BillingAuthorization:
    billing_auth_url: str | None
    customer_key: str | None = None
    billing_key: str | None = None


@dataclass(frozen=True)
class PaymentConfirmation:
    payment_key: str
    method: str
    approved_at: datetime


@dataclass(frozen=True)
class AllocationSpec:
    fire_station_id: uuid.UUID
    amount: Decimal
    allocation_type: AllocationType = AllocationType.PRIMARY


@dataclass(frozen=True)
class DonorInfoSpec:
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_anonymous: bool = False
    needs_receipt: bool = False
    id_number: str | None = None


@dataclass(frozen=True)
class GroupInfoSpec:
    group_id: uuid.UUID | None = None
    group_code: str | None = None
    group_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_anonymous: bool = False


@dataclass(frozen=True)
class RegularDonationSpec:
    cycle: SubscriptionCycle
    start_date: date | None = None
    customer_key: str | None = None


@dataclass(frozen=True)
class CheckoutIntent:
    donation: Donation
    subscription: DonationSubscription | None
    payment_url: str | None
    billing_auth_url: str | None


@runtime_checkable
class PaymentsGateway(Protocol):
    async def create_checkout(
        self,
        *,
        amount: Decimal,
        order_id: str,
        customer_name: str,
        success_url: str | None,
        fail_url: str | None,
        metadata: dict[str, Any] | None = None,
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

    async def create_billing_authorization(
        self,
        *,
        customer_key: str | None,
        success_url: str | None,
        fail_url: str | None,
    ) -> BillingAuthorization: ...


class DonationNotFoundError(Exception):
    """Raised when a donation cannot be located."""


class SubscriptionNotFoundError(Exception):
    """Raised when a subscription cannot be located."""


class DonationService:
    def __init__(self, session: AsyncSession, payments: PaymentsGateway) -> None:
        self._session = session
        self._payments = payments

    async def prepare_donation_checkout(
        self,
        *,
        user_id: uuid.UUID,
        mode: DonationMode,
        amount: Decimal,
        currency: str,
        fire_station_id: uuid.UUID | None,
        allocations: Sequence[AllocationSpec] | None,
        donor: DonorInfoSpec,
        group: GroupInfoSpec | None,
        regular: RegularDonationSpec | None,
        message: str | None,
        metadata: dict[str, Any] | None,
        success_url: str | None,
        fail_url: str | None,
    ) -> CheckoutIntent:
        if mode == DonationMode.SINGLE and fire_station_id is None:
            raise ValueError("Single mode donation requires fire_station_id")
        if mode == DonationMode.MULTIPLE:
            if not allocations:
                raise ValueError("Multiple mode donation requires allocations")
            if not any(a.amount > 0 for a in allocations):
                raise ValueError("At least one allocation must have a positive amount")

        primary_station_id = fire_station_id
        if mode == DonationMode.MULTIPLE and allocations:
            primary_station_id = _resolve_primary_station_id(allocations)

        order_id = f"bodam-{uuid.uuid4()}"
        donation = Donation(
            user_id=user_id,
            fire_station_id=primary_station_id,
            group_id=group.group_id if (group and group.group_id) else None,
            mode=mode,
            amount=amount,
            currency=currency,
            type=DonationType.RECURRING if (regular and regular.cycle) else DonationType.ONE_TIME,
            message=message,
            donor_display_name=donor.display_name,
            is_anonymous=donor.is_anonymous,
            needs_receipt=donor.needs_receipt,
            is_group_anonymous=group.is_anonymous if group else False,
            metadata_json=metadata,
            toss_order_id=order_id,
        )
        self._session.add(donation)

        if allocations:
            for spec in allocations:
                allocation = DonationAllocation(
                    donation=donation,
                    fire_station_id=spec.fire_station_id,
                    amount=spec.amount,
                    allocation_type=spec.allocation_type,
                )
                self._session.add(allocation)

        subscription: DonationSubscription | None = None
        billing_auth_url: str | None = None
        if regular and regular.cycle:
            subscription = DonationSubscription(
                user_id=user_id,
                origin_donation=donation,
                status=SubscriptionStatus.ACTIVE,
                cycle=regular.cycle,
                amount=amount,
                currency=currency,
                next_billing_at=_combine_date_with_utc(regular.start_date),
                toss_customer_key=regular.customer_key,
            )
            self._session.add(subscription)
            donation.subscription = subscription

            billing_auth_url = await self._maybe_create_billing_authorization(
                subscription=subscription,
                success_url=success_url,
                fail_url=fail_url,
            )

        checkout_session: CheckoutSession | None = None
        if billing_auth_url is None:
            checkout_session = await self._payments.create_checkout(
                amount=amount,
                order_id=order_id,
                customer_name=donor.display_name or str(user_id),
                success_url=success_url,
                fail_url=fail_url,
                metadata={}
                if metadata is None
                else metadata,
            )

        await self._session.flush()

        return CheckoutIntent(
            donation=donation,
            subscription=subscription,
            payment_url=checkout_session.payment_url if checkout_session else None,
            billing_auth_url=billing_auth_url,
        )

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

    async def list_subscriptions_for_user(
        self, user_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> list[DonationSubscription]:
        result = await self._session.execute(
            select(DonationSubscription)
            .where(DonationSubscription.user_id == user_id)
            .order_by(DonationSubscription.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars())

    async def pause_subscription(self, subscription_id: uuid.UUID) -> DonationSubscription:
        subscription = await self._session.get(DonationSubscription, subscription_id)
        if subscription is None:
            raise SubscriptionNotFoundError(str(subscription_id))
        subscription.status = SubscriptionStatus.PAUSED
        subscription.paused_at = datetime.now(timezone.utc)
        await self._session.flush()
        return subscription

    async def resume_subscription(self, subscription_id: uuid.UUID) -> DonationSubscription:
        subscription = await self._session.get(DonationSubscription, subscription_id)
        if subscription is None:
            raise SubscriptionNotFoundError(str(subscription_id))
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.paused_at = None
        await self._session.flush()
        return subscription

    async def cancel_subscription(self, subscription_id: uuid.UUID) -> DonationSubscription:
        subscription = await self._session.get(DonationSubscription, subscription_id)
        if subscription is None:
            raise SubscriptionNotFoundError(str(subscription_id))
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.ended_at = datetime.now(timezone.utc)
        await self._session.flush()
        return subscription

    async def _maybe_create_billing_authorization(
        self,
        *,
        subscription: DonationSubscription,
        success_url: str | None,
        fail_url: str | None,
    ) -> str | None:
        if not hasattr(self._payments, "create_billing_authorization"):
            return None

        billing = await self._payments.create_billing_authorization(
            customer_key=subscription.toss_customer_key,
            success_url=success_url,
            fail_url=fail_url,
        )
        if billing.customer_key and not subscription.toss_customer_key:
            subscription.toss_customer_key = billing.customer_key
        if billing.billing_key:
            subscription.toss_billing_key = billing.billing_key
        return billing.billing_auth_url


def _resolve_primary_station_id(allocations: Iterable[AllocationSpec]) -> uuid.UUID:
    for spec in allocations:
        if spec.allocation_type == AllocationType.PRIMARY:
            return spec.fire_station_id
    # fallback: first allocation entry
    first = next(iter(allocations))
    return first.fire_station_id


def _combine_date_with_utc(value: date | None) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


__all__ = [
    "DonationService",
    "DonationNotFoundError",
    "SubscriptionNotFoundError",
    "PaymentsGateway",
    "CheckoutSession",
    "BillingAuthorization",
    "PaymentConfirmation",
    "AllocationSpec",
    "DonorInfoSpec",
    "GroupInfoSpec",
    "RegularDonationSpec",
    "CheckoutIntent",
]
