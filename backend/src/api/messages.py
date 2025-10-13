"""Public API endpoints for firefighter support messages."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageResponse(BaseModel):
    name: str
    message: str
    date: str
    location: str


_MESSAGES: list[MessageResponse] = [
    MessageResponse(
        name="김민서",
        message="언제나 시민의 안전을 위해 애써주셔서 진심으로 감사합니다. 힘든 순간마다 여러분의 용기를 기억하겠습니다.",
        date=datetime(2024, 7, 18, 9, 30).strftime("%Y-%m-%d %H:%M"),
        location="서울특별시 마포구",
    ),
    MessageResponse(
        name="이정훈",
        message="최근 화재 현장에서의 활약을 보고 깊이 감동했습니다. 여러분 덕분에 우리 가족이 더욱 안전한 일상을 누립니다.",
        date=datetime(2024, 7, 12, 14, 5).strftime("%Y-%m-%d %H:%M"),
        location="부산광역시 해운대구",
    ),
    MessageResponse(
        name="박지영",
        message="무더운 여름에도 최선을 다해 주셔서 고맙습니다. 여러분의 노력을 응원하며 작은 기부로 마음을 전합니다.",
        date=datetime(2024, 7, 5, 20, 10).strftime("%Y-%m-%d %H:%M"),
        location="대구광역시 수성구",
    ),
    MessageResponse(
        name="정우진",
        message="현장에서 만난 소방관님들의 밝은 미소가 아직도 기억에 남아요. 늘 건강하시고 안전 활동 기원합니다!",
        date=datetime(2024, 6, 29, 11, 42).strftime("%Y-%m-%d %H:%M"),
        location="강원특별자치도 춘천시",
    ),
    MessageResponse(
        name="최서연",
        message="밤낮없이 출동하시는 모습에 존경과 감사의 마음만이 가득합니다. 작은 응원이 힘이 되길 바랍니다.",
        date=datetime(2024, 6, 21, 16, 55).strftime("%Y-%m-%d %H:%M"),
        location="경기도 수원시",
    ),
]


@router.get("", response_model=list[MessageResponse])
async def list_messages(limit: int = Query(default=4, ge=1, le=50)) -> list[MessageResponse]:
    """응원 메시지 목록 조회."""
    return _MESSAGES[:limit]


__all__ = ["router"]
