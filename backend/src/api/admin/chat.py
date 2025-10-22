"""
Admin Llama Chat API 엔드포인트

Llama AI 채팅 서비스를 위한 REST API
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.admin.llama_chat.service import LlamaChatService
from src.monitoring.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/api/chat", tags=["admin-chat"])


# Pydantic 모델
class ChatQueryRequest(BaseModel):
    """채팅 쿼리 요청"""
    query: str = Field(..., min_length=1, max_length=500, description="사용자 질문")
    session_id: str = Field(..., description="세션 ID")
    max_results: int = Field(default=10, ge=1, le=100, description="최대 결과 개수")
    explain: bool = Field(default=False, description="SQL 쿼리 노출 여부")


class ChatQueryResponse(BaseModel):
    """채팅 쿼리 응답"""
    response: str = Field(..., description="자연어 응답")
    sources: List[dict] = Field(default_factory=list, description="데이터 소스")
    execution_time_ms: float = Field(..., description="실행 시간 (ms)")
    cached: bool = Field(..., description="캐시 히트 여부")
    sql_query: Optional[str] = Field(None, description="SQL 쿼리 (explain=True일 때)")
    query_type: Optional[str] = Field(None, description="쿼리 타입 (statistics/search/analysis)")


class ChatHistoryResponse(BaseModel):
    """대화 기록 응답"""
    session_id: str = Field(..., description="세션 ID")
    messages: List[dict] = Field(default_factory=list, description="대화 메시지 목록")
    total: int = Field(..., description="총 메시지 수")


class SessionCreateResponse(BaseModel):
    """세션 생성 응답"""
    session_id: str = Field(..., description="생성된 세션 ID")


class SuccessResponse(BaseModel):
    """성공 응답"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field(..., description="메시지")


# 전역 서비스 인스턴스
_chat_service: Optional[LlamaChatService] = None


def get_chat_service() -> LlamaChatService:
    """채팅 서비스 싱글톤 인스턴스 반환"""
    global _chat_service
    if _chat_service is None:
        _chat_service = LlamaChatService()
    return _chat_service


@router.post("/query", response_model=ChatQueryResponse)
async def query_chat(request: ChatQueryRequest) -> ChatQueryResponse:
    """
    채팅 쿼리 실행

    자연어 질문을 받아 Knowledge Graph를 조회하고 결과를 반환합니다.

    **Example Request**:
    ```json
    {
        "query": "서울에 있는 소방서는 몇 개인가요?",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "max_results": 10,
        "explain": false
    }
    ```

    **Example Response**:
    ```json
    {
        "response": "서울에는 총 25개의 소방서가 있습니다.",
        "sources": [...],
        "execution_time_ms": 1234.56,
        "cached": false,
        "sql_query": null,
        "query_type": "statistics"
    }
    ```

    **Features**:
    - Semantic Cache (유사도 > 0.95): < 500ms
    - SQL Injection 방지 (SELECT만 허용)
    - 대화 컨텍스트 유지 (최대 20개 메시지)
    """
    try:
        logger.info(f"[ChatAPI] Query received: session={request.session_id}, query={request.query[:50]}...")

        service = get_chat_service()
        result = await service.query(
            user_query=request.query,
            session_id=request.session_id,
            max_results=request.max_results,
            explain=request.explain
        )

        return ChatQueryResponse(
            response=result.response,
            sources=result.sources,
            execution_time_ms=result.execution_time_ms,
            cached=result.cached,
            sql_query=result.sql_query,
            query_type=result.query_type
        )

    except ValueError as e:
        logger.error(f"[ChatAPI] Validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"[ChatAPI] Query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="쿼리 처리 중 오류가 발생했습니다."
        ) from e


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_history(session_id: str) -> ChatHistoryResponse:
    """
    대화 기록 조회

    특정 세션의 대화 기록을 조회합니다.

    **Example Response**:
    ```json
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "messages": [
            {
                "role": "user",
                "content": "서울에 있는 소방서는 몇 개인가요?",
                "timestamp": "2025-10-17T14:30:00Z"
            },
            {
                "role": "assistant",
                "content": "서울에는 총 25개의 소방서가 있습니다.",
                "timestamp": "2025-10-17T14:30:02Z"
            }
        ],
        "total": 2
    }
    ```
    """
    try:
        logger.info(f"[ChatAPI] Get history: session={session_id}")

        service = get_chat_service()
        messages = await service.get_history(session_id)

        return ChatHistoryResponse(
            session_id=session_id,
            messages=messages,
            total=len(messages)
        )

    except Exception as e:
        logger.error(f"[ChatAPI] Get history failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 기록 조회 중 오류가 발생했습니다."
        ) from e


@router.post("/clear/{session_id}", response_model=SuccessResponse)
async def clear_history(session_id: str) -> SuccessResponse:
    """
    대화 기록 초기화

    특정 세션의 대화 기록을 삭제합니다.

    **Example Response**:
    ```json
    {
        "success": true,
        "message": "대화 기록이 초기화되었습니다."
    }
    ```
    """
    try:
        logger.info(f"[ChatAPI] Clear history: session={session_id}")

        service = get_chat_service()
        await service.clear_history(session_id)

        return SuccessResponse(
            success=True,
            message="대화 기록이 초기화되었습니다."
        )

    except Exception as e:
        logger.error(f"[ChatAPI] Clear history failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 기록 초기화 중 오류가 발생했습니다."
        ) from e


@router.post("/session", response_model=SessionCreateResponse)
async def create_session() -> SessionCreateResponse:
    """
    새 세션 생성

    새로운 채팅 세션을 생성하고 세션 ID를 반환합니다.

    **Example Response**:
    ```json
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    """
    try:
        logger.info("[ChatAPI] Create session")

        service = get_chat_service()
        session_id = await service.create_session()

        return SessionCreateResponse(session_id=session_id)

    except Exception as e:
        logger.error(f"[ChatAPI] Create session failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 생성 중 오류가 발생했습니다."
        ) from e


@router.delete("/session/{session_id}", response_model=SuccessResponse)
async def delete_session(session_id: str) -> SuccessResponse:
    """
    세션 삭제

    특정 세션과 관련된 모든 데이터를 삭제합니다.

    **Example Response**:
    ```json
    {
        "success": true,
        "message": "세션이 삭제되었습니다."
    }
    ```
    """
    try:
        logger.info(f"[ChatAPI] Delete session: session={session_id}")

        service = get_chat_service()
        await service.delete_session(session_id)

        return SuccessResponse(
            success=True,
            message="세션이 삭제되었습니다."
        )

    except Exception as e:
        logger.error(f"[ChatAPI] Delete session failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 삭제 중 오류가 발생했습니다."
        ) from e


__all__ = ["router"]
