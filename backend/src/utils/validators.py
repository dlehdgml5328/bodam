"""Validation utilities for common data types."""

from __future__ import annotations

import re

from email_validator import EmailNotValidError
from email_validator import validate_email as _validate_email


def validate_email(email: str) -> bool:
    """Validate email address using email-validator library."""
    try:
        _validate_email(email)
        return True
    except EmailNotValidError:
        return False


def validate_phone_number(phone: str) -> bool:
    """Validate Korean phone number format."""
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Korean mobile numbers: 010-XXXX-XXXX (11 digits)
    # Korean landline numbers: 0X-XXX-XXXX or 0XX-XXX-XXXX (10 digits)
    if len(digits) == 11 and digits.startswith("010"):
        return True
    elif len(digits) == 10 and digits.startswith("0"):
        return True
    else:
        return False


def validate_korean_name(name: str) -> bool:
    """Validate Korean name format (2-10 Korean characters)."""
    # Korean characters (Hangul) pattern
    korean_pattern = re.compile(r"^[가-힣]{2,10}$")
    return bool(korean_pattern.match(name.strip()))


def validate_donation_amount(amount: float) -> bool:
    """Validate donation amount (minimum 1000 KRW, maximum 10,000,000 KRW)."""
    return 1000 <= amount <= 10_000_000


def validate_password_strength(password: str) -> dict[str, bool]:
    """Validate password strength and return detailed results."""
    checks = {
        "min_length": len(password) >= 8,
        "has_upper": bool(re.search(r"[A-Z]", password)),
        "has_lower": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"\d", password)),
        "has_special": bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)),
        "no_common_patterns": not _has_common_patterns(password),
    }

    checks["is_strong"] = all([
        checks["min_length"],
        sum([checks["has_upper"], checks["has_lower"], checks["has_digit"], checks["has_special"]]) >= 3,
        checks["no_common_patterns"]
    ])

    return checks


def validate_business_number(business_number: str) -> bool:
    """Validate Korean business registration number format."""
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", business_number)

    if len(digits) != 10:
        return False

    # Check digit algorithm for Korean business numbers
    check_sum = 0
    multipliers = [1, 3, 7, 1, 3, 7, 1, 3, 5]

    for i in range(9):
        check_sum += int(digits[i]) * multipliers[i]

    check_sum += (int(digits[8]) * 5) // 10
    check_digit = (10 - (check_sum % 10)) % 10

    return int(digits[9]) == check_digit


def _has_common_patterns(password: str) -> bool:
    """Check for common password patterns."""
    common_patterns = [
        r"123",  # Sequential numbers
        r"abc",  # Sequential letters
        r"password",  # Common word
        r"admin",  # Common word
        r"qwer",  # Keyboard pattern
        r"(.)\1{2,}",  # Repeated characters
    ]

    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            return True

    return False