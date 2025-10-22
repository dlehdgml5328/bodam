"""
SQLAdmin 커스텀 페이지 - Llama AI 채팅

Knowledge Graph 기반 자연어 쿼리 인터페이스
"""

from __future__ import annotations

from pathlib import Path

from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from src.monitoring.logging import get_logger

logger = get_logger(__name__)

# 템플릿 디렉토리 설정
TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class LlamaChatPage(BaseView):
    """
    Llama AI 채팅 커스텀 페이지

    Features:
    - 자연어 → SQL 변환 (SELECT만 허용)
    - Knowledge Graph 쿼리 실행
    - Semantic Cache (코사인 유사도 > 0.95)
    - 대화 컨텍스트 관리 (최대 20개 메시지)
    """

    name = "Llama AI 채팅"
    icon = "fa-solid fa-robot"

    @expose("/llama-chat", methods=["GET"])
    async def chat_page(self, request: Request) -> HTMLResponse:
        """
        채팅 페이지 렌더링

        Args:
            request: Starlette Request 객체

        Returns:
            HTML 응답
        """
        logger.info("[LlamaChatPage] Rendering chat page")

        return templates.TemplateResponse(
            "llama_chat.html",
            {
                "request": request
            }
        )


__all__ = ["LlamaChatPage"]
