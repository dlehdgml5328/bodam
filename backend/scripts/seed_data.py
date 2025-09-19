"""Simple data seeding scaffold for local development."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from src.database.connection import SessionLocal
from src.models.fire_station import FireStation, StationStatus
from src.models.user import User, UserRole


async def seed() -> None:
    async with SessionLocal() as session:  # type: ignore[arg-type]
        user = User(
            email="admin@bodam.local",
            password_hash="not-secure",
            name="로컬 관리자",
            role=UserRole.ADMIN,
        )
        station = FireStation(
            name="강남소방서",
            address="서울특별시 강남구 테헤란로 000",
            location="SRID=4326;POINT(127.028 37.498)",
            phone="02-000-0000",
            station_code="GN001",
            region="서울",
            district="강남구",
            status=StationStatus.ACTIVE,
            total_received=Decimal("0"),
            donor_count=0,
        )
        session.add_all([user, station])
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
