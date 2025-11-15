#!/usr/bin/env python3
"""
소방서 CSV 데이터를 데이터베이스에 import하는 스크립트
"""
import asyncio
import csv
import sys
from pathlib import Path

# Backend 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import text
from src.database.connection import engine


async def import_fire_stations():
    csv_path = Path(__file__).parent / "fire_stations_utf8.csv"

    if not csv_path.exists():
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    print(f"📂 CSV 파일 읽는 중: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📊 총 {len(rows)}개의 소방서 데이터 발견")

    async with engine.begin() as conn:
        # 기존 데이터 확인
        result = await conn.execute(text("SELECT COUNT(*) FROM fire_stations"))
        existing_count = result.scalar()
        print(f"📌 현재 데이터베이스에 {existing_count}개의 소방서 존재")

        if existing_count > 0:
            response = input("⚠️  기존 데이터를 삭제하고 새로 import 하시겠습니까? (y/N): ")
            if response.lower() == 'y':
                await conn.execute(text("DELETE FROM fire_stations"))
                print("🗑️  기존 데이터 삭제 완료")
            else:
                print("✅ Import 취소")
                return

        # 데이터 insert
        imported = 0
        for row in rows:
            try:
                # CSV 컬럼: 순번, 소방본부, 소방서, 주소, 전화번호, 팩스번호
                name = row['소방서'].strip()
                region = row['소방본부'].strip()
                address = row['주소'].strip()
                phone = row.get('전화번호', '').strip()

                # fire_stations 테이블 구조에 맞게 insert
                await conn.execute(text("""
                    INSERT INTO fire_stations
                    (name, region, address, phone, created_at, updated_at)
                    VALUES (:name, :region, :address, :phone, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """), {
                    "name": name,
                    "region": region,
                    "address": address,
                    "phone": phone
                })
                imported += 1

                if imported % 10 == 0:
                    print(f"✅ {imported}개 import 완료...")

            except Exception as e:
                print(f"❌ 에러 발생 (행 {row}): {e}")
                continue

        print(f"\n🎉 총 {imported}개의 소방서 데이터 import 완료!")


if __name__ == "__main__":
    asyncio.run(import_fire_stations())
