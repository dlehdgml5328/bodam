"""Unit tests covering donation service scenarios for QA checklist."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from src.models.donation import (
    AllocationType,
    DonationMode,
    SubscriptionCycle,
    SubscriptionStatus,
    DonationStatus,
    DonationType,
)
from src.services.donation_service import (
    AllocationSpec,
    BillingAuthorization,
    CheckoutIntent,
    CheckoutSession,
    DonationService,
    DonorInfoSpec,
    GroupInfoSpec,
    PaymentsGateway,
    RegularDonationSpec,
)


pytestmark = pytest.mark.asyncio


class FakeAsyncSession:
    """Minimal async session stub to capture added SQLAlchemy models."""

    def __init__(self) -> None:
        self._pending: list[Any] = []
        self._store: dict[type[Any], dict[uuid.UUID, Any]] = {}

    def add(self, obj: Any) -> None:
        self._pending.append(obj)

    async def flush(self) -> None:  # noqa: D401 - follows AsyncSession API
        for obj in self._pending:
            if hasattr(obj, "id") and getattr(obj, "id", None) is None:
                setattr(obj, "id", uuid.uuid4())
            if hasattr(obj, "id"):
                obj_id = getattr(obj, "id")
                self._store.setdefault(type(obj), {})[obj_id] = obj
        self._pending.clear()

    async def get(self, model: type[Any], obj_id: uuid.UUID) -> Any | None:
        return self._store.get(model, {}).get(obj_id)

    # Helper for tests to pre-populate entities
    def store(self, obj: Any) -> None:
        if hasattr(obj, "id") and getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid.uuid4())
        if hasattr(obj, "id"):
            self._store.setdefault(type(obj), {})[obj.id] = obj


@dataclass
class SimpleDonation:
    user_id: uuid.UUID
    fire_station_id: uuid.UUID | None
    group_id: uuid.UUID | None = None
    mode: DonationMode = DonationMode.SINGLE
    amount: Decimal = Decimal("0")
    currency: str = "KRW"
    type: DonationType = DonationType.ONE_TIME
    status: DonationStatus = DonationStatus.PENDING
    message: str | None = None
    donor_display_name: str | None = None
    is_anonymous: bool = False
    needs_receipt: bool = False
    is_group_anonymous: bool = False
    metadata_json: dict[str, Any] | None = None
    toss_order_id: str = ""
    toss_payment_key: str | None = None
    payment_method: str | None = None
    receipt_url: str | None = None
    subscription: "SimpleSubscription | None" = None  # type: ignore[name-defined]
    allocations: list["SimpleAllocation"] = field(default_factory=list)  # type: ignore[name-defined]
    id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    refunded_at: datetime | None = None


@dataclass
class SimpleAllocation:
    donation: SimpleDonation
    fire_station_id: uuid.UUID
    amount: Decimal
    allocation_type: AllocationType
    id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        self.donation.allocations.append(self)


@dataclass
class SimpleSubscription:
    user_id: uuid.UUID
    origin_donation: SimpleDonation | None
    status: SubscriptionStatus
    cycle: SubscriptionCycle
    amount: Decimal
    currency: str
    next_billing_at: datetime | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    paused_at: datetime | None = None
    ended_at: datetime | None = None
    toss_customer_key: str | None = None
    toss_billing_key: str | None = None
    id: uuid.UUID | None = None

    def __post_init__(self) -> None:
        if self.origin_donation is not None:
            self.origin_donation.subscription = self


@pytest.fixture(autouse=True)
def patch_domain_models(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.services.donation_service.Donation", SimpleDonation)
    monkeypatch.setattr(
        "src.services.donation_service.DonationAllocation",
        SimpleAllocation,
    )
    monkeypatch.setattr(
        "src.services.donation_service.DonationSubscription",
        SimpleSubscription,
    )


@dataclass
class StubGateway(PaymentsGateway):
    checkout_result: CheckoutSession = CheckoutSession(
        order_id="bodam-test-order",
        payment_url="https://pay.mock/test-order",
    )
    billing_result: BillingAuthorization = BillingAuthorization(
        billing_auth_url="https://pay.mock/billing/customer-test",
        customer_key="customer-test",
        billing_key="billing-test",
    )

    def __post_init__(self) -> None:
        self.checkout_calls: list[dict[str, Any]] = []
        self.billing_calls: list[dict[str, Any]] = []

    async def create_checkout(
        self,
        *,
        amount: Decimal,
        order_id: str,
        customer_name: str,
        success_url: str | None,
        fail_url: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        self.checkout_calls.append(
            {
                "amount": amount,
                "order_id": order_id,
                "customer_name": customer_name,
                "success_url": success_url,
                "fail_url": fail_url,
                "metadata": metadata,
            }
        )
        return self.checkout_result

    async def confirm_payment(
        self,
        *,
        payment_key: str,
        order_id: str,
        amount: Decimal,
    ) -> Any:
        raise NotImplementedError

    async def request_refund(
        self,
        *,
        payment_key: str,
        amount: Decimal,
        reason: str,
    ) -> None:
        return None

    async def create_billing_authorization(
        self,
        *,
        customer_key: str | None,
        success_url: str | None,
        fail_url: str | None,
    ) -> BillingAuthorization:
        self.billing_calls.append(
            {
                "customer_key": customer_key,
                "success_url": success_url,
                "fail_url": fail_url,
            }
        )
        return self.billing_result


def _build_service(session: FakeAsyncSession, gateway: StubGateway | None = None) -> DonationService:
    return DonationService(session, gateway or StubGateway())


async def test_single_donation_checkout_returns_payment_url() -> None:
    session = FakeAsyncSession()
    gateway = StubGateway()
    service = _build_service(session, gateway)

    donor = DonorInfoSpec(
        display_name="김보담",
        email="kim@example.com",
        phone="010-1234-5678",
        is_anonymous=False,
        needs_receipt=True,
    )

    intent = await service.prepare_donation_checkout(
        user_id=uuid.uuid4(),
        mode=DonationMode.SINGLE,
        amount=Decimal("10000"),
        currency="KRW",
        fire_station_id=uuid.uuid4(),
        allocations=None,
        donor=donor,
        group=None,
        regular=None,
        message="고생하십니다",
        metadata={"source": "unit-test"},
        success_url="https://frontend/success",
        fail_url="https://frontend/fail",
    )

    assert isinstance(intent, CheckoutIntent)
    assert intent.subscription is None
    assert intent.payment_url == gateway.checkout_result.payment_url
    assert intent.billing_auth_url is None
    assert intent.donation.needs_receipt is True
    assert gateway.checkout_calls, "create_checkout should be invoked for one-time donations"


async def test_multiple_split_donation_creates_allocations() -> None:
    session = FakeAsyncSession()
    service = _build_service(session)

    allocations = [
        AllocationSpec(
            fire_station_id=uuid.uuid4(),
            amount=Decimal("20000"),
            allocation_type=AllocationType.PRIMARY,
        ),
        AllocationSpec(
            fire_station_id=uuid.uuid4(),
            amount=Decimal("10000"),
            allocation_type=AllocationType.SPLIT,
        ),
    ]

    intent = await service.prepare_donation_checkout(
        user_id=uuid.uuid4(),
        mode=DonationMode.MULTIPLE,
        amount=Decimal("30000"),
        currency="KRW",
        fire_station_id=None,
        allocations=allocations,
        donor=DonorInfoSpec(email="donor@example.com"),
        group=None,
        regular=None,
        message=None,
        metadata=None,
        success_url=None,
        fail_url=None,
    )

    assert intent.payment_url is not None
    assert len(intent.donation.allocations) == 2
    assert {alloc.allocation_type for alloc in intent.donation.allocations} == {
        AllocationType.PRIMARY,
        AllocationType.SPLIT,
    }


async def test_multiple_custom_donation_persists_custom_amounts() -> None:
    session = FakeAsyncSession()
    service = _build_service(session)

    first_station = uuid.uuid4()
    second_station = uuid.uuid4()

    allocations = [
        AllocationSpec(
            fire_station_id=first_station,
            amount=Decimal("15000"),
            allocation_type=AllocationType.PRIMARY,
        ),
        AllocationSpec(
            fire_station_id=second_station,
            amount=Decimal("5000"),
            allocation_type=AllocationType.CUSTOM,
        ),
    ]

    intent = await service.prepare_donation_checkout(
        user_id=uuid.uuid4(),
        mode=DonationMode.MULTIPLE,
        amount=Decimal("20000"),
        currency="KRW",
        fire_station_id=None,
        allocations=allocations,
        donor=DonorInfoSpec(email="custom@example.com"),
        group=None,
        regular=None,
        message=None,
        metadata=None,
        success_url=None,
        fail_url=None,
    )

    assert intent.donation.amount == Decimal("20000")
    by_station = {alloc.fire_station_id: alloc.amount for alloc in intent.donation.allocations}
    assert by_station[first_station] == Decimal("15000")
    assert by_station[second_station] == Decimal("5000")


async def test_group_donation_sets_group_metadata() -> None:
    session = FakeAsyncSession()
    service = _build_service(session)

    group_id = uuid.uuid4()
    intent = await service.prepare_donation_checkout(
        user_id=uuid.uuid4(),
        mode=DonationMode.SINGLE,
        amount=Decimal("12000"),
        currency="KRW",
        fire_station_id=uuid.uuid4(),
        allocations=None,
        donor=DonorInfoSpec(email="leader@example.com", display_name="대표"),
        group=GroupInfoSpec(group_id=group_id, is_anonymous=True),
        regular=None,
        message=None,
        metadata=None,
        success_url=None,
        fail_url=None,
    )

    assert intent.donation.group_id == group_id
    assert intent.donation.is_group_anonymous is True


async def test_regular_donation_creates_subscription_and_billing_authorization() -> None:
    session = FakeAsyncSession()
    gateway = StubGateway(
        billing_result=BillingAuthorization(
            billing_auth_url="https://pay.mock/billing/customer-regular",
            customer_key="customer-regular",
            billing_key="billing-regular",
        )
    )
    service = _build_service(session, gateway)

    intent = await service.prepare_donation_checkout(
        user_id=uuid.uuid4(),
        mode=DonationMode.SINGLE,
        amount=Decimal("55000"),
        currency="KRW",
        fire_station_id=uuid.uuid4(),
        allocations=None,
        donor=DonorInfoSpec(email="regular@example.com"),
        group=None,
        regular=RegularDonationSpec(
            cycle=SubscriptionCycle.MONTHLY,
            start_date=date(2025, 5, 1),
            customer_key=None,
        ),
        message="한 달 한 번",
        metadata=None,
        success_url="https://frontend/success",
        fail_url="https://frontend/fail",
    )

    assert intent.subscription is not None
    assert intent.payment_url is None, "Regular donations should skip immediate checkout"
    assert intent.billing_auth_url == "https://pay.mock/billing/customer-regular"
    assert intent.subscription.toss_customer_key == "customer-regular"
    assert intent.subscription.toss_billing_key == "billing-regular"
    assert not gateway.checkout_calls, "No checkout should occur when billing auth is issued"


async def test_multiple_donation_without_allocations_raises_error() -> None:
    session = FakeAsyncSession()
    service = _build_service(session)

    with pytest.raises(ValueError):
        await service.prepare_donation_checkout(
            user_id=uuid.uuid4(),
            mode=DonationMode.MULTIPLE,
            amount=Decimal("30000"),
            currency="KRW",
            fire_station_id=None,
            allocations=None,
            donor=DonorInfoSpec(email="donor@example.com"),
            group=None,
            regular=None,
            message=None,
            metadata=None,
            success_url=None,
            fail_url=None,
        )


async def test_multiple_donation_requires_positive_allocation() -> None:
    session = FakeAsyncSession()
    service = _build_service(session)

    with pytest.raises(ValueError):
        await service.prepare_donation_checkout(
            user_id=uuid.uuid4(),
            mode=DonationMode.MULTIPLE,
            amount=Decimal("0"),
            currency="KRW",
            fire_station_id=None,
            allocations=[
                AllocationSpec(
                    fire_station_id=uuid.uuid4(),
                    amount=Decimal("0"),
                    allocation_type=AllocationType.PRIMARY,
                )
            ],
            donor=DonorInfoSpec(email="donor@example.com"),
            group=None,
            regular=None,
            message=None,
            metadata=None,
            success_url=None,
            fail_url=None,
        )


async def test_subscription_pause_resume_cancel_flows() -> None:
    session = FakeAsyncSession()
    gateway = StubGateway()
    service = _build_service(session, gateway)

    subscription = SimpleSubscription(
        user_id=uuid.uuid4(),
        origin_donation=None,
        status=SubscriptionStatus.ACTIVE,
        cycle=SubscriptionCycle.MONTHLY,
        amount=Decimal("15000"),
        currency="KRW",
        next_billing_at=datetime.now(timezone.utc),
    )
    session.store(subscription)

    paused = await service.pause_subscription(subscription.id)
    assert paused.status is SubscriptionStatus.PAUSED
    assert paused.paused_at is not None

    resumed = await service.resume_subscription(subscription.id)
    assert resumed.status is SubscriptionStatus.ACTIVE
    assert resumed.paused_at is None

    cancelled = await service.cancel_subscription(subscription.id)
    assert cancelled.status is SubscriptionStatus.CANCELLED
    assert cancelled.ended_at is not None
