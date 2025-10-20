"""알림 관련 API 엔드포인트."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from src.database.connection import get_session
from src.models.user import User
from src.security.session import get_current_user_with_csrf

router = APIRouter(tags=["notifications"])


class FCMTokenRequest(BaseModel):
    token: str


@router.post("/notifications/fcm-token")
async def save_fcm_token(
    request: FCMTokenRequest,
    current_user: User = Depends(get_current_user_with_csrf),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """사용자의 FCM 토큰 저장."""
    try:
        # 사용자의 FCM 토큰 업데이트
        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(fcm_token=request.token)
        )
        await session.execute(stmt)
        await session.commit()

        return {"message": "FCM token saved successfully"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save FCM token: {str(e)}"
        )


@router.delete("/notifications/fcm-token")
async def delete_fcm_token(
    current_user: User = Depends(get_current_user_with_csrf),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """사용자의 FCM 토큰 삭제 (로그아웃 시)."""
    try:
        stmt = (
            update(User)
            .where(User.id == current_user.id)
            .values(fcm_token=None)
        )
        await session.execute(stmt)
        await session.commit()

        return {"message": "FCM token deleted successfully"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete FCM token: {str(e)}"
        )
