"""
ErrorEvent model - pgvector embedding 포함
FR-015, FR-016: 중요 에러 저장 및 유사도 검색
"""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from src.models.base import Base


class ErrorEvent(Base):
    __tablename__ = "error_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    level = Column(String(10), nullable=False, index=True)
    message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    service = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    trace_id = Column(String(32), nullable=True, index=True)
    span_id = Column(String(16), nullable=True)
    context = Column(JSONB, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    resolution_status = Column(String(20), nullable=False, default="new", index=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_error_events_timestamp_level", "timestamp", "level"),
        Index("ix_error_events_service_timestamp", "service", "timestamp"),
    )
