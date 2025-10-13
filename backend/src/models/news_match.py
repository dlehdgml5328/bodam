"""
뉴스-사고 매칭 모델
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import Base


class NewsMatch(Base):
    """뉴스와 화재 사고 매칭 정보"""

    __tablename__ = "news_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(50), ForeignKey("fire_incidents.id", ondelete="CASCADE"), nullable=False)
    news_type = Column(String(20), nullable=False)  # 'naver', 'youtube'
    news_id = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=True)  # 유사도 점수 (0.0 ~ 1.0)
    matched_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    incident = relationship("FireIncident", back_populates="news_matches")

    __table_args__ = (
        UniqueConstraint("incident_id", "news_type", "news_id", name="idx_news_matches_unique"),
    )

    def __repr__(self) -> str:
        return f"<NewsMatch(id={self.id}, incident_id={self.incident_id}, news_type={self.news_type})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "news_type": self.news_type,
            "news_id": self.news_id,
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "thumbnail_url": self.thumbnail_url,
            "similarity_score": self.similarity_score,
            "matched_at": self.matched_at.isoformat() if self.matched_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Indexes
Index("idx_news_matches_incident", NewsMatch.incident_id)
Index("idx_news_matches_news_id", NewsMatch.news_id)
Index("idx_news_matches_type", NewsMatch.news_type)
