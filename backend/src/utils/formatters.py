"""Formatting utilities for common data types."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal


def format_currency(amount: Decimal | float | int, currency: str = "KRW") -> str:
    """Format currency amount with Korean Won formatting."""
    if isinstance(amount, (float, int)):
        amount = Decimal(str(amount))

    # Format with thousands separator
    formatted = f"{amount:,.0f}"

    if currency == "KRW":
        return f"{formatted}원"
    else:
        return f"{formatted} {currency}"


def format_datetime(dt: datetime, format_type: str = "korean") -> str:
    """Format datetime for Korean locale."""
    if format_type == "korean":
        return dt.strftime("%Y년 %m월 %d일 %H시 %M분")
    elif format_type == "date_only":
        return dt.strftime("%Y년 %m월 %d일")
    elif format_type == "time_only":
        return dt.strftime("%H시 %M분")
    elif format_type == "iso":
        return dt.isoformat()
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_phone_number(phone: str) -> str:
    """Format Korean phone number with dashes."""
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif len(digits) == 10 and digits.startswith("0"):
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    else:
        return phone  # Return original if format is unexpected


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    size = size_bytes
    i = 0

    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1

    return f"{size:.1f} {size_names[i]}"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format percentage with specified decimal places."""
    return f"{value:.{decimal_places}f}%"