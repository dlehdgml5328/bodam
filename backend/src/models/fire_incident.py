"""
화재 사고 정보 모델
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Float,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.orm import relationship
from .base import Base


class FireIncident(Base):
    """화재 사고 정보"""

    __tablename__ = "fire_incidents"

    id = Column(String(50), primary_key=True)  # 예: "F2025001"
    title = Column(String(500), nullable=False)
    location_address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False)  # dispatching, suppressing, contained, resolved
    severity = Column(String(20), nullable=True)  # critical, high, medium, low
    casualties_injured = Column(Integer, default=0)
    casualties_dead = Column(Integer, default=0)
    estimated_damage = Column(BigInteger, nullable=True)  # 예상 피해액 (원)
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dispatch_events = relationship("DispatchEvent", back_populates="incident", cascade="all, delete-orphan")
    news_matches = relationship("NewsMatch", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FireIncident(id={self.id}, title={self.title}, status={self.status})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "location_address": self.location_address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "status": self.status,
            "severity": self.severity,
            "casualties_injured": self.casualties_injured,
            "casualties_dead": self.casualties_dead,
            "estimated_damage": self.estimated_damage,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Indexes
Index("idx_fire_incidents_occurred_at", FireIncident.occurred_at.desc())
Index("idx_fire_incidents_status", FireIncident.status)
# Note: Spatial index for lat/lng requires PostGIS extension
