"""관리자 환불 처리 API 엔드포인트."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.integrations.toss_payments import TossPaymentsClient
from src.models.refund import Refund
from src.services.refund_service import BulkRefundResult, RefundService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/api/refunds", tags=["admin", "refunds"])


# Pydantic 모델 정의
class BulkApproveRequest(BaseModel):
    """대량 환불 승인 요청"""

    refund_ids: list[uuid.UUID] = Field(..., max_length=100, min_length=1)
    admin_note: str = Field(..., min_length=5, max_length=500)


class BulkRejectRequest(BaseModel):
    """대량 환불 거부 요청"""

    refund_ids: list[uuid.UUID] = Field(..., max_length=100, min_length=1)
    rejection_reason: str = Field(..., min_length=10, max_length=500)


class ApproveRequest(BaseModel):
    """단일 환불 승인 요청"""

    admin_note: str | None = Field(None, max_length=500)


class RejectRequest(BaseModel):
    """단일 환불 거부 요청"""

    rejection_reason: str = Field(..., min_length=10, max_length=500)


class RefundFailureResponse(BaseModel):
    """환불 실패 응답"""

    refund_id: uuid.UUID
    reason: str


class BulkRefundResponse(BaseModel):
    """대량 환불 처리 응답"""

    approved: int
    rejected: int
    failed: list[RefundFailureResponse]


class RefundDetailResponse(BaseModel):
    """환불 상세 응답"""

    id: uuid.UUID
    donation_id: uuid.UUID
    reason: str
    amount: str
    status: str
    reviewer_id: uuid.UUID | None
    reviewed_at: str | None
    created_at: str


# Dependency: 관리자 ID (임시 - 실제로는 JWT에서 추출)
async def get_admin_id() -> uuid.UUID:
    """관리자 ID 가져오기 (임시 구현)"""
    # TODO: JWT 토큰에서 관리자 ID 추출
    # 현재는 임시 UUID 반환
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


# Dependency: RefundService
async def get_refund_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RefundService:
    """RefundService 의존성 주입"""
    payments_client = TossPaymentsClient()
    return RefundService(session=session, payments_client=payments_client)


@router.post("/bulk-approve", response_model=BulkRefundResponse, status_code=status.HTTP_200_OK)
async def bulk_approve_refunds(
    request: BulkApproveRequest,
    service: Annotated[RefundService, Depends(get_refund_service)],
    admin_id: Annotated[uuid.UUID, Depends(get_admin_id)],
) -> BulkRefundResponse:
    """
    대량 환불 승인
    - 최대 100개까지 일괄 처리
    - 부분 성공 지원 (일부 실패해도 성공한 건은 처리)
    - Toss Payments API 호출하여 실제 환불 처리
    """
    try:
        result: BulkRefundResult = await service.bulk_approve(
            refund_ids=request.refund_ids,
            admin_id=admin_id,
            admin_note=request.admin_note,
        )

        return BulkRefundResponse(
            approved=result.approved,
            rejected=result.rejected,
            failed=[
                RefundFailureResponse(refund_id=f.refund_id, reason=f.reason) for f in result.failed
            ],
        )

    except ValueError as e:
        logger.error("Bulk approve validation error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.exception("Bulk approve unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during bulk approval",
        ) from e


@router.post("/bulk-reject", response_model=BulkRefundResponse, status_code=status.HTTP_200_OK)
async def bulk_reject_refunds(
    request: BulkRejectRequest,
    service: Annotated[RefundService, Depends(get_refund_service)],
    admin_id: Annotated[uuid.UUID, Depends(get_admin_id)],
) -> BulkRefundResponse:
    """
    대량 환불 거부
    - 최대 100개까지 일괄 처리
    - 부분 성공 지원
    - Toss Payments API 호출 없음 (내부 상태만 변경)
    """
    try:
        result: BulkRefundResult = await service.bulk_reject(
            refund_ids=request.refund_ids,
            admin_id=admin_id,
            rejection_reason=request.rejection_reason,
        )

        return BulkRefundResponse(
            approved=result.approved,
            rejected=result.rejected,
            failed=[
                RefundFailureResponse(refund_id=f.refund_id, reason=f.reason) for f in result.failed
            ],
        )

    except ValueError as e:
        logger.error("Bulk reject validation error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.exception("Bulk reject unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during bulk rejection",
        ) from e


@router.post("/{refund_id}/approve", status_code=status.HTTP_200_OK)
async def approve_refund(
    refund_id: uuid.UUID,
    request: ApproveRequest,
    service: Annotated[RefundService, Depends(get_refund_service)],
    admin_id: Annotated[uuid.UUID, Depends(get_admin_id)],
) -> dict:
    """단일 환불 승인"""
    try:
        refund = await service.approve_refund(
            refund_id=refund_id,
            admin_id=admin_id,
            admin_note=request.admin_note,
        )

        return {
            "refund_id": str(refund.id),
            "status": refund.status.value,
            "message": "Refund approved successfully",
        }

    except ValueError as e:
        logger.error("Approve refund validation error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.exception("Approve refund unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during approval",
        ) from e


@router.post("/{refund_id}/reject", status_code=status.HTTP_200_OK)
async def reject_refund(
    refund_id: uuid.UUID,
    request: RejectRequest,
    service: Annotated[RefundService, Depends(get_refund_service)],
    admin_id: Annotated[uuid.UUID, Depends(get_admin_id)],
) -> dict:
    """단일 환불 거부"""
    try:
        refund = await service.reject_refund(
            refund_id=refund_id,
            admin_id=admin_id,
            rejection_reason=request.rejection_reason,
        )

        return {
            "refund_id": str(refund.id),
            "status": refund.status.value,
            "message": "Refund rejected successfully",
        }

    except ValueError as e:
        logger.error("Reject refund validation error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.exception("Reject refund unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during rejection",
        ) from e


@router.get("/{refund_id}", response_model=RefundDetailResponse, status_code=status.HTTP_200_OK)
async def get_refund_detail(
    refund_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RefundDetailResponse:
    """환불 상세 조회"""
    refund = await session.get(Refund, refund_id)

    if refund is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund not found")

    return RefundDetailResponse(
        id=refund.id,
        donation_id=refund.donation_id,
        reason=refund.reason,
        amount=str(refund.amount),
        status=refund.status.value,
        reviewer_id=refund.reviewer_id,
        reviewed_at=refund.reviewed_at.isoformat() if refund.reviewed_at else None,
        created_at=refund.created_at.isoformat(),
    )


@router.get("/audit-logs/refunds", status_code=status.HTTP_200_OK)
async def get_refund_audit_logs(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 50,
) -> dict:
    """
    환불 감사 로그 조회
    TODO: 실제 감사 로그 테이블이 구현되면 해당 테이블에서 조회
    현재는 Refund 테이블의 reviewed 기록만 반환
    """
    stmt = (
        select(Refund)
        .where(Refund.reviewer_id.isnot(None))
        .order_by(desc(Refund.reviewed_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    refunds = result.scalars().all()

    logs = [
        {
            "refund_id": str(r.id),
            "donation_id": str(r.donation_id),
            "reviewer_id": str(r.reviewer_id) if r.reviewer_id else None,
            "status": r.status.value,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "amount": str(r.amount),
        }
        for r in refunds
    ]

    return {"logs": logs, "total": len(logs)}


__all__ = ["router"]
