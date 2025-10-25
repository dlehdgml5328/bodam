#!/usr/bin/env python3
"""
관리자 계정 생성 스크립트

사용법:
    python scripts/create_admin.py --email admin@bodam.local --name "관리자"
"""
import argparse
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from src.database.connection import get_db_session
from src.models.user import User, UserRole
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin_user(email: str, name: str, password: str = "admin1234"):
    """관리자 계정 생성"""
    print(f"🔐 관리자 계정 생성 중...")
    print(f"  Email: {email}")
    print(f"  Name: {name}")
    print(f"  Password: {password}")
    print()

    async with get_db_session() as session:
        # 기존 사용자 확인
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"⚠️  이미 존재하는 사용자입니다: {email}")
            response = input("기존 사용자를 관리자로 업데이트하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("취소되었습니다.")
                return

            # 기존 사용자 업데이트
            existing_user.role = UserRole.ADMIN
            existing_user.name = name
            existing_user.hashed_password = pwd_context.hash(password)
            await session.commit()
            print(f"✅ 기존 사용자를 관리자로 업데이트했습니다!")
        else:
            # 새 관리자 생성
            admin_user = User(
                email=email,
                name=name,
                hashed_password=pwd_context.hash(password),
                role=UserRole.ADMIN,
                is_active=True,
                email_verified=True,
            )
            session.add(admin_user)
            await session.commit()
            print(f"✅ 새로운 관리자 계정이 생성되었습니다!")

    print()
    print("=" * 50)
    print("📋 로그인 정보:")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    print("=" * 50)
    print()
    print("⚠️  보안을 위해 첫 로그인 후 비밀번호를 변경하세요!")


def main():
    parser = argparse.ArgumentParser(description="BoDam 관리자 계정 생성")
    parser.add_argument("--email", required=True, help="관리자 이메일")
    parser.add_argument("--name", required=True, help="관리자 이름")
    parser.add_argument("--password", default="admin1234", help="관리자 비밀번호 (기본값: admin1234)")

    args = parser.parse_args()

    asyncio.run(create_admin_user(args.email, args.name, args.password))


if __name__ == "__main__":
    main()
