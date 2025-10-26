"""Service for managing refresh tokens."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken


class RefreshTokenExpiredError(Exception):
    """Raised when a refresh token has expired."""


class RefreshTokenRevokedError(Exception):
    """Raised when a refresh token has been revoked."""


class RefreshTokenNotFoundError(Exception):
    """Raised when a refresh token cannot be found."""


class RefreshTokenService:
    """Service for managing refresh tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_token(
        self, user_id: uuid.UUID, ttl_minutes: int = 10080
    ) -> RefreshToken:
        """
        Create a new refresh token for a user.

        Args:
            user_id: UUID of the user
            ttl_minutes: Time-to-live in minutes (default: 7 days = 10080 minutes)

        Returns:
            RefreshToken: The created refresh token
        """
        token_string = secrets.token_urlsafe(64)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

        refresh_token = RefreshToken(
            user_id=user_id,
            token=token_string,
            expires_at=expires_at,
            revoked=False,
        )

        self._session.add(refresh_token)
        await self._session.flush()

        return refresh_token

    async def get_token(self, token_string: str) -> RefreshToken:
        """
        Get a refresh token by its string value.

        Args:
            token_string: The token string

        Returns:
            RefreshToken: The refresh token

        Raises:
            RefreshTokenNotFoundError: If token doesn't exist
        """
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token == token_string)
        )
        token = result.scalar_one_or_none()

        if token is None:
            raise RefreshTokenNotFoundError("Token not found")

        return token

    async def validate_token(self, token_string: str) -> RefreshToken:
        """
        Validate a refresh token and return it if valid.

        Args:
            token_string: The token string

        Returns:
            RefreshToken: The valid refresh token

        Raises:
            RefreshTokenNotFoundError: If token doesn't exist
            RefreshTokenExpiredError: If token has expired
            RefreshTokenRevokedError: If token has been revoked
        """
        token = await self.get_token(token_string)

        if token.revoked:
            raise RefreshTokenRevokedError("Token has been revoked")

        if token.expires_at < datetime.now(timezone.utc):
            raise RefreshTokenExpiredError("Token has expired")

        return token

    async def revoke_token(self, token_string: str) -> RefreshToken:
        """
        Revoke a refresh token.

        Args:
            token_string: The token string

        Returns:
            RefreshToken: The revoked token

        Raises:
            RefreshTokenNotFoundError: If token doesn't exist
        """
        token = await self.get_token(token_string)
        token.revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        await self._session.flush()

        return token

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        """
        Revoke all refresh tokens for a user.

        Args:
            user_id: UUID of the user

        Returns:
            int: Number of tokens revoked
        """
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()

        now = datetime.now(timezone.utc)
        count = 0
        for token in tokens:
            token.revoked = True
            token.revoked_at = now
            count += 1

        await self._session.flush()
        return count

    async def cleanup_expired_tokens(self) -> int:
        """
        Delete all expired refresh tokens from the database.

        Returns:
            int: Number of tokens deleted
        """
        from sqlalchemy import delete

        result = await self._session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await self._session.flush()
        return result.rowcount or 0


__all__ = [
    "RefreshTokenService",
    "RefreshTokenExpiredError",
    "RefreshTokenRevokedError",
    "RefreshTokenNotFoundError",
]
