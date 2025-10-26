"""Public API endpoints for firefighter support messages."""

from __future__ import annotations

from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session
from src.models.donation import Donation
from src.models.fire_station import FireStation

# 한국 시간대 (UTC+9)
KST = timezone(timedelta(hours=9))

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageResponse(BaseModel):
    name: str
    message: str
    date: str
    location: str


@router.get("", response_model=list[MessageResponse])
async def list_messages(
    limit: int = Query(default=4, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> list[MessageResponse]:
    """응원 메시지 목록 조회 - 실제 기부 데이터에서 가져옴."""

    # 메시지가 있고, 익명이 아닌 최근 기부 조회
    stmt = (
        select(Donation, FireStation)
        .join(FireStation, Donation.fire_station_id == FireStation.id)
        .where(Donation.message.isnot(None))
        .where(Donation.message != "")
        .where(Donation.is_anonymous.is_(False))
        .order_by(Donation.created_at.desc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    messages = []
    for donation, fire_station in rows:
        # UTC를 KST로 변환
        kst_time = donation.created_at.replace(tzinfo=timezone.utc).astimezone(KST)

        messages.append(
            MessageResponse(
                name=donation.donor_display_name or "익명",
                message=donation.message or "",
                date=kst_time.strftime("%Y-%m-%d %H:%M"),
                location=f"{fire_station.region} {fire_station.district}" if fire_station.district else fire_station.region,
            )
        )

    return messages


__all__ = ["router"]
