"""Utilities for hashing and verifying user passwords."""

from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plain-text password."""
    # bcrypt has a 72-byte limit, so truncate if necessary
    if len(password.encode("utf-8")) > 72:
        password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify that the password matches the stored hash."""
    # bcrypt has a 72-byte limit, so truncate if necessary
    if len(password.encode("utf-8")) > 72:
        password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return _pwd_context.verify(password, password_hash)


__all__ = ["hash_password", "verify_password"]
