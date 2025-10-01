"""Donation-related API endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.models.donation import (
    AllocationType,
    DonationMode,
    DonationStatus,
    DonationType,
    SubscriptionCycle,
    SubscriptionStatus,
)

router = APIRouter(tags=["donations"])


class DonationAllocationInput(BaseModel):
    fire_station_id: uuid.UUID
    amount: Decimal = Field(..., ge=0)
    allocation_type: AllocationType = AllocationType.PRIMARY


class DonorInfoInput(BaseModel):
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_anonymous: bool = False
    needs_receipt: bool = False
    id_number: str | None = None


class GroupDonationInput(BaseModel):
    enabled: bool = False
    group_id: uuid.UUID | None = None
    group_code: str | None = None
    group_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class RegularDonationInput(BaseModel):
    enabled: bool = False
    cycle: SubscriptionCycle | None = None
    start_date: date | None = None
    customer_key: str | None = None


class DonationCheckoutRequest(BaseModel):
    mode: DonationMode
    multiple_type: str | None = Field(default=None, pattern="^(split|each|custom)$")
    amount: Decimal = Field(..., ge=Decimal("1000"))
    currency: str = "KRW"
    fire_station_id: uuid.UUID | None = None
    allocations: list[DonationAllocationInput] | None = None
    donor: DonorInfoInput = DonorInfoInput()
    group: GroupDonationInput | None = None
    regular: RegularDonationInput | None = None
    message: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] | None = None
    success_redirect_url: str | None = None
    fail_redirect_url: str | None = None

    def validate_business_rules(self) -> None:
        if self.mode == DonationMode.SINGLE and self.fire_station_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MISSING_STATION")
        if self.mode == DonationMode.MULTIPLE:
            if not self.allocations:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="ALLOCATIONS_REQUIRED"
                )
            if self.multiple_type is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="MULTIPLE_TYPE_REQUIRED"
                )
        if self.regular and self.regular.enabled and self.regular.cycle is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CYCLE_REQUIRED")


class DonationCheckoutResponse(BaseModel):
    donation_id: uuid.UUID
    order_id: str
    payment_url: str | None = None
    billing_auth_url: str | None = None
    subscription_id: uuid.UUID | None = None


class FireStationSummary(BaseModel):
    id: uuid.UUID
    name: str
    region: str
    district: str


class DonationAllocationSummary(BaseModel):
    fire_station: FireStationSummary
    amount: Decimal
    allocation_type: AllocationType


class GroupDonationSummary(BaseModel):
    group_id: uuid.UUID | None
    group_name: str | None
    is_anonymous: bool
    contact_name: str | None


class RegularDonationSummary(BaseModel):
    subscription_id: uuid.UUID | None
    status: SubscriptionStatus | None
    cycle: SubscriptionCycle | None
    next_billing_at: datetime | None


class DonationPaymentInfo(BaseModel):
    method: str | None
    toss_order_id: str | None
    toss_payment_key: str | None


class DonationResponse(BaseModel):
    id: uuid.UUID
    mode: DonationMode
    amount: Decimal
    currency: str
    status: DonationStatus
    message: str | None
    is_anonymous: bool
    needs_receipt: bool
    created_at: datetime
    completed_at: datetime | None
    fire_station: FireStationSummary
    allocations: list[DonationAllocationSummary]
    group: GroupDonationSummary | None
    regular: RegularDonationSummary | None
    payment: DonationPaymentInfo


class DonationDetailResponse(DonationResponse):
    receipt_url: str | None = None
    refund: dict[str, str] | None = None


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    status: SubscriptionStatus
    cycle: SubscriptionCycle
    amount: Decimal
    currency: str
    next_billing_at: datetime | None
    started_at: datetime
    paused_at: datetime | None
    ended_at: datetime | None
    fire_stations: list[FireStationSummary]
    billing_customer_key: str | None
    billing_key: str | None


@router.post("/donations", response_model=DonationCheckoutResponse, status_code=status.HTTP_201_CREATED)
async def create_donation_checkout(
    payload: DonationCheckoutRequest, session: AsyncSession = Depends(get_session)
) -> DonationCheckoutResponse:
    payload.validate_business_rules()
    # TODO: 실제 DonationService 연동 (Step 02 구현 범위에 포함)
    donation_id = uuid.uuid4()
    order_id = f"bodam-{donation_id}"
    payment_url = "https://pay.toss.im/checkout"
    billing_auth_url = (
        "https://pay.toss.im/billing"
        if payload.regular and payload.regular.enabled
        else None
    )
    return DonationCheckoutResponse(
        donation_id=donation_id,
        order_id=order_id,
        payment_url=payment_url if not billing_auth_url else None,
        billing_auth_url=billing_auth_url,
        subscription_id=uuid.uuid4() if billing_auth_url else None,
    )


@router.get("/donations")
async def list_donations(
    page: int = 1,
    limit: int = 20,
    status_filter: DonationStatus | None = None,
) -> dict:
    donation_id = uuid.uuid4()
    station_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    donation = DonationResponse(
        id=donation_id,
        mode=DonationMode.SINGLE,
        amount=Decimal("30000"),
        currency="KRW",
        status=status_filter or DonationStatus.PENDING,
        message="응원합니다",
        is_anonymous=False,
        needs_receipt=True,
        created_at=now,
        completed_at=None,
        fire_station=FireStationSummary(
            id=station_id,
            name="강남소방서",
            region="서울",
            district="강남구",
        ),
        allocations=[
            DonationAllocationSummary(
                fire_station=FireStationSummary(
                    id=station_id,
                    name="강남소방서",
                    region="서울",
                    district="강남구",
                ),
                amount=Decimal("30000"),
                allocation_type=AllocationType.PRIMARY,
            )
        ],
        group=None,
        regular=None,
        payment=DonationPaymentInfo(
            method="card",
            toss_order_id=f"bodam-{donation_id}",
            toss_payment_key=None,
        ),
    )
    return {
        "donations": [donation],
        "total": 1,
        "page": page,
        "limit": limit,
    }


@router.get("/donations/{donation_id}", response_model=DonationDetailResponse)
async def get_donation(donation_id: uuid.UUID) -> DonationDetailResponse:
    now = datetime.now(timezone.utc)
    return DonationDetailResponse(
        id=donation_id,
        mode=DonationMode.SINGLE,
        amount=Decimal("20000"),
        currency="KRW",
        status=DonationStatus.PENDING,
        message="빠른 쾌유를 바랍니다",
        is_anonymous=False,
        needs_receipt=False,
        created_at=now,
        completed_at=None,
        fire_station=FireStationSummary(
            id=uuid.uuid4(),
            name="강남소방서",
            region="서울",
            district="강남구",
        ),
        allocations=[],
        group=GroupDonationSummary(
            group_id=None,
            group_name=None,
            is_anonymous=False,
            contact_name=None,
        ),
        regular=None,
        payment=DonationPaymentInfo(
            method="card",
            toss_order_id=f"bodam-{donation_id}",
            toss_payment_key=None,
        ),
        receipt_url=None,
        refund=None,
    )


@router.get("/donations/{donation_id}/receipt")
async def get_receipt(donation_id: uuid.UUID) -> Response:
    pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    headers = {"Content-Disposition": f"attachment; filename=receipt-{donation_id}.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/donations/{donation_id}/refund", status_code=status.HTTP_201_CREATED)
async def request_refund(donation_id: uuid.UUID, payload: dict) -> dict:
    return {
        "refund_id": str(uuid.uuid4()),
        "status": "pending_review",
        "message": "환불 요청이 접수되었습니다",
    }


@router.get("/subscriptions")
async def list_subscriptions() -> dict:
    now = datetime.now(timezone.utc)
    subscription = SubscriptionResponse(
        id=uuid.uuid4(),
        status=SubscriptionStatus.ACTIVE,
        cycle=SubscriptionCycle.MONTHLY,
        amount=Decimal("15000"),
        currency="KRW",
        next_billing_at=now,
        started_at=now,
        paused_at=None,
        ended_at=None,
        fire_stations=[
            FireStationSummary(
                id=uuid.uuid4(),
                name="강남소방서",
                region="서울",
                district="강남구",
            )
        ],
        billing_customer_key="customer_123",
        billing_key="billing_123",
    )
    return {"subscriptions": [subscription]}


@router.post("/subscriptions/{subscription_id}/pause")
async def pause_subscription(subscription_id: uuid.UUID) -> dict:
    return {"message": "정기 기부가 일시정지되었습니다"}


@router.post("/subscriptions/{subscription_id}/resume")
async def resume_subscription(subscription_id: uuid.UUID) -> dict:
    return {"message": "정기 기부가 재개되었습니다"}


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: uuid.UUID) -> dict:
    return {"message": "정기 기부가 해지되었습니다"}


__all__ = ["router"]
