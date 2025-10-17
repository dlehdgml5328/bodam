"""
fire_incidents 데이터에서 소방서 정보를 추출하여 fire_stations 테이블에 삽입하는 스크립트
"""
import asyncio
import re
import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os


def extract_region(address: str) -> tuple[str, str]:
    """주소에서 시/도와 시/군/구 추출"""
    # 시/도 추출
    region_match = re.match(
        r'^(서울특별시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시|세종특별자치시|경기도|강원특별자치도|충청북도|충청남도|전북특별자치도|전라남도|경상북도|경상남도|제주특별자치도)',
        address
    )
    region = region_match.group(1) if region_match else '기타'

    # 시도명 단순화
    region = region.replace('특별시', '').replace('광역시', '').replace('특별자치시', '').replace('특별자치도', '').replace('도', '')

    # 시/군/구 추출
    district_match = re.search(r'\s+([가-힣]+시|[가-힣]+군|[가-힣]+구)', address)
    district = district_match.group(1) if district_match else ''

    return region, district


async def main():
    # 데이터베이스 연결
    database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://bodam:bodam@db:5432/bodam')
    engine = create_async_engine(database_url, echo=True)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. fire_incidents에서 유니크한 소방서 정보 추출
        query = text("""
            SELECT DISTINCT
                title as name,
                location_address
            FROM fire_incidents
            WHERE title IS NOT NULL
              AND location_address IS NOT NULL
            ORDER BY title
        """)

        result = await session.execute(query)
        incidents = result.fetchall()

        print(f"Found {len(incidents)} unique fire stations from incidents")

        # 2. 각 소방서 정보를 fire_stations 테이블에 삽입
        inserted_count = 0
        skipped_count = 0

        for incident in incidents:
            name = incident.name
            address = incident.location_address
            region, district = extract_region(address)

            # station_code 생성 (region_name 형식)
            station_code = f"{region}_{name}"

            # 이미 존재하는지 확인
            check_query = text("SELECT id FROM fire_stations WHERE station_code = :code")
            exists = await session.execute(check_query, {"code": station_code})
            if exists.fetchone():
                skipped_count += 1
                continue

            # 기본 위치 좌표 (0,0) - 추후 지오코딩으로 업데이트
            station_id = uuid.uuid4()

            insert_query = text("""
                INSERT INTO fire_stations (
                    id, name, address, location, phone, station_code,
                    region, district, status, total_received, donor_count,
                    created_at, updated_at
                ) VALUES (
                    :id, :name, :address, ST_SetSRID(ST_MakePoint(0, 0), 4326),
                    '000-0000-0000', :station_code, :region, :district,
                    'active', 0.00, 0, NOW(), NOW()
                )
            """)

            try:
                await session.execute(insert_query, {
                    "id": str(station_id),
                    "name": name,
                    "address": address,
                    "station_code": station_code,
                    "region": region,
                    "district": district
                })
                inserted_count += 1
                print(f"✓ Inserted: {name} ({region} {district})")
            except Exception as e:
                print(f"✗ Failed to insert {name}: {e}")
                skipped_count += 1

        await session.commit()

        print(f"\n=== Summary ===")
        print(f"Total unique stations: {len(incidents)}")
        print(f"Inserted: {inserted_count}")
        print(f"Skipped: {skipped_count}")

        # 3. 결과 확인
        count_query = text("SELECT COUNT(*) as count FROM fire_stations")
        count_result = await session.execute(count_query)
        total = count_result.fetchone()[0]
        print(f"\nTotal fire_stations in database: {total}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
