"""
출동 이벤트 모델
"""
from datetime import datetime
from uuid import UUID
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from .base import Base


class DispatchEvent(Base):
    """소방서 출동 이벤트"""

    __tablename__ = "dispatch_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(50), ForeignKey("fire_incidents.id", ondelete="CASCADE"), nullable=False)
    fire_station_id = Column(PGUUID(as_uuid=True), ForeignKey("fire_stations.id"), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=False)
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    cleared_at = Column(DateTime(timezone=True), nullable=True)
    units_count = Column(Integer, default=1)  # 출동 차량 수
    personnel_count = Column(Integer, default=0)  # 출동 인원
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    incident = relationship("FireIncident", back_populates="dispatch_events")
    fire_station = relationship("FireStation", foreign_keys=[fire_station_id])

    def __repr__(self) -> str:
        return f"<DispatchEvent(id={self.id}, incident_id={self.incident_id}, station_id={self.fire_station_id})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "fire_station_id": self.fire_station_id,
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else None,
            "arrived_at": self.arrived_at.isoformat() if self.arrived_at else None,
            "cleared_at": self.cleared_at.isoformat() if self.cleared_at else None,
            "units_count": self.units_count,
            "personnel_count": self.personnel_count,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Indexes
Index("idx_dispatch_events_incident", DispatchEvent.incident_id)
Index("idx_dispatch_events_station", DispatchEvent.fire_station_id)
Index("idx_dispatch_events_dispatched_at", DispatchEvent.dispatched_at.desc())
