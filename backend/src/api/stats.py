"""Statistics API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.models.donation import Donation
from src.models.fire_station import FireStation
from src.models.group import Group
from src.models.user import User

router = APIRouter(prefix="/stats", tags=["stats"])


class DashboardStats(BaseModel):
    """대시보드 통계 응답"""
    total_amount: int
    total_cups: int
    total_fire_stations: int
    total_users: int
    total_groups: int
    total_companies: int


@router.get("", response_model=DashboardStats)
async def get_dashboard_stats(session: AsyncSession = Depends(get_session)) -> DashboardStats:
    """
    대시보드 통계 조회

    Returns:
        DashboardStats: 총 기부금액, 커피잔수, 소방서 수, 참여자 수 등
    """
    # 총 기부금액
    total_amount_result = await session.execute(
        select(func.coalesce(func.sum(Donation.amount), 0))
    )
    total_amount = total_amount_result.scalar()

    # 총 기부된 커피 잔수 (기부금액 / 3000원 = 1잔으로 계산)
    total_cups = total_amount // 3000 if total_amount else 0

    # 지원한 소방서 수 (기부가 있는 소방서)
    total_fire_stations_result = await session.execute(
        select(func.count(distinct(Donation.fire_station_id)))
        .where(Donation.fire_station_id.isnot(None))
    )
    total_fire_stations = total_fire_stations_result.scalar()

    # 참여한 시민 수 (개인 기부자)
    total_users_result = await session.execute(
        select(func.count(distinct(Donation.user_id)))
        .where(Donation.user_id.isnot(None))
        .where(Donation.group_id.is_(None))
    )
    total_users = total_users_result.scalar()

    # 참여한 단체 수 (모든 그룹)
    total_groups_result = await session.execute(
        select(func.count(Group.id))
    )
    total_groups = total_groups_result.scalar()

    # 참여한 기업 수 (일단 0으로, 나중에 구분 로직 추가)
    total_companies = 0

    return DashboardStats(
        total_amount=total_amount or 0,
        total_cups=total_cups or 0,
        total_fire_stations=total_fire_stations or 0,
        total_users=total_users or 0,
        total_groups=total_groups or 0,
        total_companies=total_companies or 0,
    )


__all__ = ["router"]
