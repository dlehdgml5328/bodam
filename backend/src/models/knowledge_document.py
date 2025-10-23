"""
Knowledge Document 모델

RAG(Retrieval-Augmented Generation)을 위한 문서 저장 모델
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class KnowledgeDocument(Base):
    """
    지식 문서 모델

    내부 크롤링·매칭 파이프라인이 생성하는 설명형 리포트,
    운영 매뉴얼/프로세스, 회의 요약 등 비정형 텍스트를 저장
    """

    __tablename__ = "knowledge_documents"

    # 기본 필드
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
        comment="문서 출처 (파일명, URL 등)",
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="문서 제목",
    )

    section: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="문서 섹션/챕터",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="문서 내용 (청크)",
    )

    doc_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",  # DB 컬럼명은 metadata, Python 속성명은 doc_metadata
        JSON,
        nullable=True,
        comment="추가 메타데이터 (파일 해시, 페이지 번호 등)",
    )

    # pgvector 임베딩
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(1024),  # BAAI/bge-large-en-v1.5 임베딩 차원
        nullable=True,
        comment="문서 임베딩 벡터 (1024차원)",
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="청크 인덱스 (같은 문서의 여러 청크를 구분)",
    )

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeDocument(id={self.id}, "
            f"source={self.source!r}, "
            f"title={self.title!r}, "
            f"chunk_index={self.chunk_index})>"
        )


__all__ = ["KnowledgeDocument"]
