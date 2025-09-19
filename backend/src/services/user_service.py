"""Service layer utilities for managing users."""

from __future__ import annotations

import logging
import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User, UserRole

logger = logging.getLogger(__name__)


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user with a duplicate email."""


class UserNotFoundError(Exception):
    """Raised when a user cannot be located for an operation."""


class UserService:
    """Encapsulates user persistence and domain logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        name: str,
        phone: str | None = None,
        role: UserRole = UserRole.DONOR,
    ) -> User:
        existing = await self._session.scalar(select(User).where(User.email == email))
        if existing:
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            phone=phone,
            role=role,
        )
        self._session.add(user)

        try:
            await self._session.flush()
        except IntegrityError as exc:  # pragma: no cover - defensive guard
            logger.exception("Failed to create user due to integrity error")
            raise UserAlreadyExistsError from exc

        return user

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self._session.get(User, user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))
        return user

    async def get_user_by_email(self, email: str) -> User:
        user = await self._session.scalar(select(User).where(User.email == email))
        if user is None:
            raise UserNotFoundError(email)
        return user

    async def list_users(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        result = await self._session.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars())

    async def update_user(self, user_id: uuid.UUID, **fields: object) -> User:
        user = await self.get_user(user_id)
        mutable_fields: Iterable[str] = {
            "name",
            "phone",
            "role",
            "tier",
            "is_active",
            "total_donated",
        }
        for key, value in fields.items():
            if key in mutable_fields and value is not None:
                setattr(user, key, value)
        await self._session.flush()
        return user

    async def deactivate_user(self, user_id: uuid.UUID) -> User:
        user = await self.get_user(user_id)
        user.is_active = False
        await self._session.flush()
        return user


__all__ = [
    "UserService",
    "UserAlreadyExistsError",
    "UserNotFoundError",
]
