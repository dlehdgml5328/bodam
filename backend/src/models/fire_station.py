"""FireStation domain model with spatial metadata."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum as SAEnum, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

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
    location: Mapped[str] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
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

    def __repr__(self) -> str:
        return f"FireStation(id={self.id}, name={self.name!r})"
