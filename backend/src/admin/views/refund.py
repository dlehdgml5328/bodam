"""환불 관리 Admin View"""

import logging
import uuid

from sqladmin import ModelView, action

# from sqladmin.actions import action  # sqladmin 0.16.0에서는 actions 미지원
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.integrations.toss_payments import TossPaymentsClient
from src.models.refund import Refund, RefundStatus
from src.services.refund_service import RefundService

logger = logging.getLogger(__name__)


class RefundAdmin(ModelView, model=Refund):
    """환불 요청 관리 Admin View

    Refund 모델을 기반으로 환불 요청을 관리합니다.
    대량 승인/거부 액션 제공
    """

    # 기본 설정
    name = "환불 요청"
    name_plural = "환불 요청 목록"
    icon = "fa-solid fa-rotate-left"

    # 목록 페이지 설정
    column_list = [
        Refund.id,
        Refund.donation_id,
        Refund.amount,
        Refund.status,
        Refund.reviewer_id,
        Refund.reviewed_at,
        Refund.created_at,
    ]

    # 정렬 가능 필드
    column_sortable_list = [Refund.created_at, Refund.reviewed_at, Refund.amount]

    # 검색 가능 필드
    column_searchable_list = [Refund.reason]

    # 필터 설정
    column_filters = [Refund.status]

    # 기본 정렬 (created_at DESC)
    column_default_sort = [(Refund.created_at, True)]

    # 상세 페이지 설정
    column_details_list = [
        Refund.id,
        Refund.donation_id,
        Refund.reason,
        Refund.amount,
        Refund.status,
        Refund.reviewer_id,
        Refund.reviewed_at,
        Refund.created_at,
    ]

    # 폼 설정 (환불 요청은 생성/수정 불가 - API로만 처리)
    form_columns = [
        Refund.status,
    ]

    # 권한 설정
    can_create = False  # API로만 생성
    can_edit = False  # API로만 수정
    can_delete = False  # 삭제 비활성화

    # 페이지네이션
    page_size = 50

    # 컬럼 라벨 한글화
    column_labels = {
        Refund.id: "환불 ID",
        Refund.donation_id: "기부 ID",
        Refund.reason: "환불 사유",
        Refund.amount: "환불 금액",
        Refund.status: "상태",
        Refund.reviewer_id: "검토자 ID",
        Refund.reviewed_at: "검토일시",
        Refund.created_at: "요청일시",
    }

    def _redirect_to_list(self, request: Request) -> RedirectResponse:
        url = request.url_for("admin:list", identity=self.identity)
        return RedirectResponse(url=url, status_code=302)

    @action(
        name="approve",
        label="선택 환불 승인",
        confirmation_message="선택한 환불 요청을 승인하시겠습니까?",
    )
    async def action_approve(self, request: Request) -> RedirectResponse:
        """
        대량 환불 승인 액션
        - 선택된 환불 요청들을 일괄 승인
        - Toss Payments API 호출하여 실제 환불 처리
        """
        raw_ids = request.query_params.getlist("pks")
        tokenized: list[str] = []
        for raw in raw_ids:
            tokenized.extend([value for value in raw.split(",") if value])

        if not tokenized:
            return self._redirect_to_list(request)

        refund_ids = [uuid.UUID(rid) for rid in tokenized]
        admin_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        async with self.session_maker(expire_on_commit=False) as session:  # type: ignore[attr-defined]
            payments_client = TossPaymentsClient()
            service = RefundService(session=session, payments_client=payments_client)

            try:
                result = await service.bulk_approve(
                    refund_ids=refund_ids,
                    admin_id=admin_id,
                    admin_note="SQLAdmin bulk approve action",
                )

                logger.info(
                    "Bulk approve completed: approved=%d, failed=%d",
                    result.approved,
                    len(result.failed),
                )
                await session.commit()
            except ValueError as e:
                logger.error("Bulk approve validation error: %s", str(e))
                await session.rollback()
            except Exception:  # pragma: no cover
                logger.exception("Bulk approve unexpected error")
                await session.rollback()

        return self._redirect_to_list(request)

    @action(
        name="reject",
        label="선택 환불 거절",
        confirmation_message="선택한 환불 요청을 거절하시겠습니까?",
    )
    async def action_reject(self, request: Request) -> RedirectResponse:
        """
        대량 환불 거부 액션
        - 선택된 환불 요청들을 일괄 거부
        - Toss Payments API 호출 없음 (내부 상태만 변경)
        """
        raw_ids = request.query_params.getlist("pks")
        tokenized: list[str] = []
        for raw in raw_ids:
            tokenized.extend([value for value in raw.split(",") if value])

        if not tokenized:
            return self._redirect_to_list(request)

        refund_ids = [uuid.UUID(rid) for rid in tokenized]
        admin_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        async with self.session_maker(expire_on_commit=False) as session:  # type: ignore[attr-defined]
            payments_client = TossPaymentsClient()
            service = RefundService(session=session, payments_client=payments_client)

            try:
                result = await service.bulk_reject(
                    refund_ids=refund_ids,
                    admin_id=admin_id,
                    rejection_reason="SQLAdmin bulk reject action",
                )

                logger.info(
                    "Bulk reject completed: rejected=%d, failed=%d",
                    result.rejected,
                    len(result.failed),
                )
                await session.commit()
            except ValueError as e:
                logger.error("Bulk reject validation error: %s", str(e))
                await session.rollback()
            except Exception:  # pragma: no cover
                logger.exception("Bulk reject unexpected error")
                await session.rollback()

        return self._redirect_to_list(request)

    # PENDING 상태 환불만 표시 (승인/거부 대기 중)
    def get_query(self):
        """대기 중인 환불 요청만 조회"""
        query = super().get_query()
        return query.filter(Refund.status == RefundStatus.PENDING)

    def get_count_query(self):
        """대기 중인 환불 요청 개수 조회"""
        query = super().get_count_query()
        return query.filter(Refund.status == RefundStatus.PENDING)
