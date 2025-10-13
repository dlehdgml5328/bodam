"""Rankings API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.models.donation import Donation
from src.models.user import User
from src.models.group import Group

router = APIRouter(prefix="/rankings", tags=["rankings"])


class RankingItem(BaseModel):
    """랭킹 아이템"""
    rank: int
    name: str
    amount: int
    cups: int


class RankingsResponse(BaseModel):
    """랭킹 응답"""
    individual: list[RankingItem]
    group: list[RankingItem]
    company: list[RankingItem]


@router.get("", response_model=RankingsResponse)
async def get_rankings(
    limit: int = Query(default=10, le=100),
    session: AsyncSession = Depends(get_session),
) -> RankingsResponse:
    """
    기부 랭킹 조회

    Args:
        limit: 반환할 랭킹 개수 (기본 10개, 최대 100개)

    Returns:
        RankingsResponse: 개인/단체/기업 랭킹
    """
    # 개인 기부 랭킹
    individual_query = (
        select(
            User.name,
            func.sum(Donation.amount).label("total_amount"),
            func.count(Donation.id).label("donation_count"),
        )
        .join(Donation, Donation.user_id == User.id)
        .where(Donation.group_id.is_(None))
        .group_by(User.id, User.name)
        .order_by(desc("total_amount"))
        .limit(limit)
    )
    individual_result = await session.execute(individual_query)
    individual_data = individual_result.all()

    individual_rankings = [
        RankingItem(
            rank=idx + 1,
            name=row.name,
            amount=int(row.total_amount or 0),
            cups=int(row.total_amount or 0) // 3000,
        )
        for idx, row in enumerate(individual_data)
    ]

    # 단체 기부 랭킹 (그룹별 총 기부액)
    group_query = (
        select(
            Group.name,
            func.sum(Donation.amount).label("total_amount"),
            func.count(Donation.id).label("donation_count"),
        )
        .join(Donation, Donation.group_id == Group.id)
        .group_by(Group.id, Group.name)
        .order_by(desc("total_amount"))
        .limit(limit)
    )
    group_result = await session.execute(group_query)
    group_data = group_result.all()

    group_rankings = [
        RankingItem(
            rank=idx + 1,
            name=row.name,
            amount=int(row.total_amount or 0),
            cups=int(row.total_amount or 0) // 3000,
        )
        for idx, row in enumerate(group_data)
    ]

    # 기업 랭킹 (일단 빈 배열, 나중에 구분 로직 추가)
    company_rankings = []

    return RankingsResponse(
        individual=individual_rankings,
        group=group_rankings,
        company=company_rankings,
    )


__all__ = ["router"]
