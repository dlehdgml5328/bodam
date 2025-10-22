"""Donation-related API endpoints."""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone, timedelta
import os
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.integrations.toss_payments import TossPaymentsClient
from src.models.donation import (
    AllocationType,
    Donation,
    DonationMode,
    DonationStatus,
    DonationSubscription,
    SubscriptionCycle,
    SubscriptionStatus,
)
from src.models.user import User
from src.security.session import get_current_user_from_bearer, get_current_user_with_csrf, get_optional_user_from_bearer
from src.services.donation_service import (
    AllocationSpec,
    BillingAuthorization,
    CheckoutSession,
    DonationService,
    DonorInfoSpec,
    GroupInfoSpec,
    PaymentConfirmation,
    PaymentsGateway,
    RegularDonationSpec,
)
from src.services.user_service import UserNotFoundError, UserService

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
    is_anonymous: bool = False


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
    fire_station_id: uuid.UUID | str | None = None  # UUID 또는 소방서 이름 모두 허용
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
    donor_name: str | None = None
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


async def _resolve_fire_station_id(fire_station_id: uuid.UUID | str | None, session: AsyncSession) -> uuid.UUID | None:
    """소방서 ID 또는 이름을 UUID로 변환"""
    if fire_station_id is None:
        return None

    # 이미 UUID면 그대로 반환
    if isinstance(fire_station_id, uuid.UUID):
        return fire_station_id

    # 문자열이면 UUID 파싱 시도
    try:
        return uuid.UUID(fire_station_id)
    except ValueError:
        pass

    # UUID가 아니면 소방서 이름으로 간주하고 검색
    from sqlalchemy import select
    from src.models.fire_station import FireStation

    result = await session.execute(
        select(FireStation).where(FireStation.name == fire_station_id)
    )
    fire_station = result.scalar_one_or_none()

    if fire_station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fire station not found: {fire_station_id}"
        )

    return fire_station.id


@router.post("/donations", response_model=DonationCheckoutResponse, status_code=status.HTTP_201_CREATED)
async def create_donation_checkout(
    payload: DonationCheckoutRequest,
    current_user: User | None = Depends(get_optional_user_from_bearer),
    session: AsyncSession = Depends(get_session),
) -> DonationCheckoutResponse:
    # 소방서 ID 변환 (이름이면 UUID로 변환)
    fire_station_uuid = await _resolve_fire_station_id(payload.fire_station_id, session)

    payload.validate_business_rules()

    # 비회원 기부: 이메일 필수
    if current_user is None:
        if not payload.donor.email:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="EMAIL_REQUIRED_FOR_GUEST")
        donor_email = payload.donor.email
        # 비회원 기부를 위한 임시 게스트 사용자 생성 또는 이메일만 사용
        user_service = UserService(session)
        try:
            user = await user_service.get_user_by_email(donor_email)
        except UserNotFoundError:
            # 게스트 기부용 임시 사용자 생성
            from src.security.passwords import hash_password
            import secrets
            # 랜덤 패스워드 생성 (게스트는 로그인 불가)
            random_password = secrets.token_urlsafe(32)
            user = User(
                email=donor_email,
                password_hash=hash_password(random_password),
                name=payload.donor.display_name or "Guest",
                is_active=True,
            )
            session.add(user)
            await session.flush()
    else:
        # 로그인된 사용자 기부
        incoming_email = payload.donor.email
        if incoming_email and incoming_email.lower() != current_user.email.lower():
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="EMAIL_MISMATCH")
        donor_email = incoming_email or current_user.email
        user = current_user

    donor_spec = DonorInfoSpec(
        display_name=payload.donor.display_name,
        email=donor_email,
        phone=payload.donor.phone,
        is_anonymous=payload.donor.is_anonymous,
        needs_receipt=payload.donor.needs_receipt,
        id_number=payload.donor.id_number,
    )

    allocations = (
        [
            AllocationSpec(
                fire_station_id=item.fire_station_id,
                amount=item.amount,
                allocation_type=item.allocation_type,
            )
            for item in payload.allocations or []
        ]
        or None
    )

    group_spec = (
        GroupInfoSpec(
            group_id=payload.group.group_id if payload.group.group_id else None,
            group_code=payload.group.group_code,
            group_name=payload.group.group_name,
            contact_name=payload.group.contact_name,
            contact_email=payload.group.contact_email,
            contact_phone=payload.group.contact_phone,
            is_anonymous=payload.group.is_anonymous,
        )
        if payload.group and payload.group.enabled
        else None
    )

    regular_spec = (
        RegularDonationSpec(
            cycle=payload.regular.cycle,
            start_date=payload.regular.start_date,
            customer_key=payload.regular.customer_key,
        )
        if payload.regular and payload.regular.enabled and payload.regular.cycle
        else None
    )

    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        intent = await service.prepare_donation_checkout(
            user_id=user.id,
            mode=payload.mode,
            amount=payload.amount,
            currency=payload.currency,
            fire_station_id=fire_station_uuid,
            allocations=allocations,
            donor=donor_spec,
            group=group_spec,
            regular=regular_spec,
            message=payload.message,
            metadata=payload.metadata,
            success_url=payload.success_redirect_url,
            fail_url=payload.fail_redirect_url,
        )

    return DonationCheckoutResponse(
        donation_id=intent.donation.id,
        order_id=intent.donation.toss_order_id,
        payment_url=intent.payment_url,
        billing_auth_url=intent.billing_auth_url,
        subscription_id=intent.subscription.id if intent.subscription else None,
    )


@router.get("/donations/recent")
async def list_recent_donations(
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """공개 API: 최근 기부 내역 조회 (실시간 기부 현황용)"""
    from sqlalchemy import select, desc
    from sqlalchemy.orm import selectinload

    # 완료된 기부만 최신순으로 조회 (eager loading 적용)
    stmt = (
        select(Donation)
        .options(
            selectinload(Donation.user),
            selectinload(Donation.fire_station),
            selectinload(Donation.allocations).selectinload(DonationAllocation.fire_station),
            selectinload(Donation.group),
            selectinload(Donation.subscription),
        )
        .where(Donation.status == DonationStatus.COMPLETED)
        .order_by(desc(Donation.created_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    donations = result.scalars().all()

    return {
        "donations": [_map_donation_response(d) for d in donations],
        "total": len(donations),
    }


@router.get("/donations")
async def list_donations(
    page: int = 1,
    limit: int = 20,
    status_filter: DonationStatus | None = None,
    donor_email: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if donor_email is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMAIL_REQUIRED")

    user_service = UserService(session)
    try:
        user = await user_service.get_user_by_email(donor_email)
    except UserNotFoundError:
        return {"donations": [], "total": 0, "page": page, "limit": limit}

    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        donations = await service.list_donations_for_user(
            user.id, limit=limit, offset=(page - 1) * limit
        )
    if status_filter is not None:
        donations = [d for d in donations if d.status == status_filter]

    return {
        "donations": [_map_donation_response(d) for d in donations],
        "total": len(donations),
        "page": page,
        "limit": limit,
    }


@router.get("/donations/{donation_id}", response_model=DonationDetailResponse)
async def get_donation(
    donation_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> DonationDetailResponse:
    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        try:
            donation = await service.get_donation(donation_id)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND") from exc

    response = _map_donation_response(donation)
    return DonationDetailResponse(**response.model_dump(), receipt_url=donation.receipt_url, refund=None)


@router.get("/donations/{donation_id}/receipt")
async def get_receipt(
    donation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """기부 영수증 PDF 다운로드"""
    from src.services.receipt_service import ReceiptService, ReceiptData

    # 기부 정보 조회
    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        donation = await service.get_donation(donation_id)

    # 영수증 발급 가능 여부 확인
    if donation.status != DonationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="완료된 기부만 영수증을 발급받을 수 있습니다"
        )

    # 영수증 데이터 준비
    user = donation.user
    fire_station = donation.fire_station

    receipt_data = ReceiptData(
        donor_name=user.name if user else "익명",
        donor_email=user.email if user else None,
        fire_station_name=fire_station.name,
        fire_station_region=fire_station.region,
        amount=float(donation.amount),
        currency=donation.currency,
        issue_date=donation.completed_at or donation.created_at,
        receipt_number=str(donation.id),
        toss_order_id=donation.toss_order_id,
    )

    # PDF 생성
    receipt_service = ReceiptService()
    pdf_bytes = receipt_service.render_pdf(receipt_data)

    # 응답 헤더 설정
    headers = {"Content-Disposition": f"attachment; filename=receipt-{donation_id}.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


class RefundRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


@router.post("/donations/{donation_id}/refund", status_code=status.HTTP_201_CREATED)
async def request_refund(
    donation_id: uuid.UUID,
    payload: RefundRequest,
    current_user: User = Depends(get_current_user_with_csrf),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """기부 환불 요청"""
    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        try:
            # 기부 조회
            donation = await service.get_donation(donation_id)

            # 권한 확인 (본인의 기부인지)
            if donation.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="본인의 기부만 환불 요청할 수 있습니다."
                )

            # 환불 처리
            refunded_donation = await service.request_refund(
                donation_id=donation_id,
                reason=payload.reason,
            )

            await session.commit()

            return {
                "donation_id": str(refunded_donation.id),
                "status": "refunded",
                "message": "환불이 완료되었습니다",
                "refunded_at": refunded_donation.refunded_at.isoformat() if refunded_donation.refunded_at else None,
            }

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc)
            ) from exc
        except Exception as exc:
            logger.exception("환불 처리 중 오류 발생")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="환불 처리 중 오류가 발생했습니다."
            ) from exc


@router.get("/subscriptions")
async def list_subscriptions(
    donor_email: str | None = None, session: AsyncSession = Depends(get_session)
) -> dict:
    if donor_email is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMAIL_REQUIRED")

    user_service = UserService(session)
    try:
        user = await user_service.get_user_by_email(donor_email)
    except UserNotFoundError:
        return {"subscriptions": []}

    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        subscriptions = await service.list_subscriptions_for_user(user.id)
    return {"subscriptions": [_map_subscription_response(s) for s in subscriptions]}


@router.post("/subscriptions/{subscription_id}/pause")
async def pause_subscription(
    subscription_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user_with_csrf),
) -> dict:
    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        await service.pause_subscription(subscription_id)
    return {"message": "정기 기부가 일시정지되었습니다"}


@router.post("/subscriptions/{subscription_id}/resume")
async def resume_subscription(
    subscription_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user_with_csrf),
) -> dict:
    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        await service.resume_subscription(subscription_id)
    return {"message": "정기 기부가 재개되었습니다"}


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user_with_csrf),
) -> dict:
    async with _payments_gateway() as gateway:
        service = DonationService(session, gateway)
        await service.cancel_subscription(subscription_id)
    return {"message": "정기 기부가 해지되었습니다"}


@asynccontextmanager
async def _payments_gateway() -> PaymentsGateway:
    secret = os.getenv("TOSS_SECRET_KEY")
    client = os.getenv("TOSS_CLIENT_KEY")
    if secret and client:
        gateway: PaymentsGateway = TossPaymentsClient()
        try:
            yield gateway
        finally:
            if hasattr(gateway, "close"):
                await gateway.close()  # type: ignore[attr-defined]
    else:
        yield _MockPaymentsGateway()


class _MockPaymentsGateway(PaymentsGateway):
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
        return CheckoutSession(order_id=order_id, payment_url=f"https://pay.mock/{order_id}")

    async def confirm_payment(
        self,
        *,
        payment_key: str,
        order_id: str,
        amount: Decimal,
    ) -> PaymentConfirmation:
        return PaymentConfirmation(
            payment_key=payment_key,
            method="card",
            approved_at=datetime.now(timezone.utc),
        )

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
        key = customer_key or f"customer_{uuid.uuid4()}"
        return BillingAuthorization(
            billing_auth_url=f"https://pay.mock/billing/{key}",
            customer_key=key,
            billing_key=None,
        )


def _map_donation_response(donation: Donation) -> DonationResponse:
    fire_station = donation.fire_station
    allocations = donation.allocations or []
    group = donation.group
    subscription = donation.subscription

    # 한국 시간대 (UTC+9)로 변환
    KST = timezone(timedelta(hours=9))
    created_at_kst = donation.created_at.replace(tzinfo=timezone.utc).astimezone(KST)
    completed_at_kst = donation.completed_at.replace(tzinfo=timezone.utc).astimezone(KST) if donation.completed_at else None

    # 기부자 이름 (user가 있으면 user.name, 없으면 None)
    donor_name = None
    if donation.user:
        donor_name = donation.user.name

    return DonationResponse(
        id=donation.id,
        mode=donation.mode,
        amount=donation.amount,
        currency=donation.currency,
        status=donation.status,
        message=donation.message,
        is_anonymous=donation.is_anonymous,
        needs_receipt=donation.needs_receipt,
        donor_name=donor_name,
        created_at=created_at_kst,
        completed_at=completed_at_kst,
        fire_station=_map_fire_station_summary(fire_station),
        allocations=[
            DonationAllocationSummary(
                fire_station=_map_fire_station_summary(allocation.fire_station),
                amount=allocation.amount,
                allocation_type=allocation.allocation_type,
            )
            for allocation in allocations
        ],
        group=(
            GroupDonationSummary(
                group_id=group.id,
                group_name=group.name,
                is_anonymous=donation.is_group_anonymous,
                contact_name=None,
            )
            if group
            else None
        ),
        regular=(
            RegularDonationSummary(
                subscription_id=subscription.id,
                status=subscription.status,
                cycle=subscription.cycle,
                next_billing_at=subscription.next_billing_at,
            )
            if subscription
            else None
        ),
        payment=DonationPaymentInfo(
            method=donation.payment_method,
            toss_order_id=donation.toss_order_id,
            toss_payment_key=donation.toss_payment_key,
        ),
    )


def _map_fire_station_summary(station: Any) -> FireStationSummary:
    return FireStationSummary(
        id=station.id,
        name=station.name,
        region=station.region,
        district=station.district,
    )


def _map_subscription_response(subscription: DonationSubscription) -> SubscriptionResponse:
    fire_stations = [
        _map_fire_station_summary(allocation.fire_station)
        for allocation in subscription.origin_donation.allocations
    ] or [
        _map_fire_station_summary(subscription.origin_donation.fire_station)
    ]
    return SubscriptionResponse(
        id=subscription.id,
        status=subscription.status,
        cycle=subscription.cycle,
        amount=subscription.amount,
        currency=subscription.currency,
        next_billing_at=subscription.next_billing_at,
        started_at=subscription.started_at,
        paused_at=subscription.paused_at,
        ended_at=subscription.ended_at,
        fire_stations=fire_stations,
        billing_customer_key=subscription.toss_customer_key,
        billing_key=subscription.toss_billing_key,
    )


__all__ = ["router"]
