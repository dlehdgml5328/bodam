"""
화재 사고 영상 매칭 모델
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base


class IncidentVideoMatch(Base):
    """화재 사고 영상 매칭 정보"""

    __tablename__ = "incident_video_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(String(255), ForeignKey("fire_incidents.id", ondelete="CASCADE"), nullable=False)
    video_url = Column(Text, nullable=False)
    video_title = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship
    incident = relationship("FireIncident", back_populates="video_matches")

    def __repr__(self) -> str:
        return f"<IncidentVideoMatch(id={self.id}, incident_id={self.incident_id}, title={self.video_title})>"
