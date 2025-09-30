"""NewsContent model representing analyzed articles."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List

from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ContentStatus(str, enum.Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


class NewsContent(Base):
    __tablename__ = "news_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )
    embedding: Mapped[List[float]] = mapped_column(Vector(1536))
    relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String(50)), nullable=False, default=list)
    status: Mapped[ContentStatus] = mapped_column(
        SAEnum(
            ContentStatus,
            name="content_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ContentStatus.PENDING_REVIEW,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"NewsContent(id={self.id}, source={self.source!r})"
