"""FireStation domain model with spatial metadata and live status snapshots."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class StationStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    MERGED = "merged"


class FireStation(Base):
    __tablename__ = "fire_stations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    station_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[StationStatus] = mapped_column(
        SAEnum(
            StationStatus,
            name="station_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=StationStatus.ACTIVE,
    )
    total_received: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0.00")
    )
    donor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_incident_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    status_snapshot: Mapped["FireStationStatus | None"] = relationship(
        "FireStationStatus",
        back_populates="station",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"FireStation(id={self.id}, name={self.name!r})"


class LiveStatus(str, enum.Enum):
    DISPATCHING = "dispatching"
    SUPPRESSING = "suppressing"
    STANDBY = "standby"
    MAINTENANCE = "maintenance"


class EmergencyPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FireStationStatus(Base):
    __tablename__ = "fire_station_statuses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fire_stations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    status: Mapped[LiveStatus] = mapped_column(
        SAEnum(
            LiveStatus,
            name="fire_station_live_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    priority: Mapped[EmergencyPriority] = mapped_column(
        SAEnum(
            EmergencyPriority,
            name="emergency_priority_level",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=EmergencyPriority.MEDIUM,
    )
    status_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    station: Mapped[FireStation] = relationship(
        "FireStation", back_populates="status_snapshot", lazy="joined"
    )
    active_incidents: Mapped[list["FireStationActiveIncident"]] = relationship(
        "FireStationActiveIncident",
        back_populates="status",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"FireStationStatus(id={self.id}, station_id={self.station_id}, "
            f"status={self.status.value})"
        )


class FireStationActiveIncident(Base):
    __tablename__ = "fire_station_active_incidents"

    status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fire_station_statuses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("news_content.id", ondelete="CASCADE"),
        primary_key=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[FireStationStatus] = relationship(
        "FireStationStatus", back_populates="active_incidents"
    )
    incident: Mapped["NewsContent | None"] = relationship("NewsContent")

    def __repr__(self) -> str:
        return (
            f"FireStationActiveIncident(status_id={self.status_id}, "
            f"incident_id={self.incident_id})"
        )


__all__ = [
    "FireStation",
    "FireStationStatus",
    "FireStationActiveIncident",
    "StationStatus",
    "LiveStatus",
    "EmergencyPriority",
]
