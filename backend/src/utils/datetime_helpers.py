"""DateTime utilities for Korean timezone handling."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Korean timezone (UTC+9)
KST = ZoneInfo("Asia/Seoul")
UTC_PLUS_9 = timezone(timedelta(hours=9))


def get_korean_timezone() -> ZoneInfo:
    """Get Korean timezone (Asia/Seoul)."""
    return KST


def to_korean_time(dt: datetime) -> datetime:
    """Convert datetime to Korean timezone."""
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(KST)


def from_korean_time(dt: datetime) -> datetime:
    """Convert Korean time to UTC."""
    if dt.tzinfo is None:
        # Assume KST if no timezone info
        dt = dt.replace(tzinfo=KST)

    return dt.astimezone(timezone.utc)


def now_in_korea() -> datetime:
    """Get current time in Korean timezone."""
    return datetime.now(KST)


def today_in_korea() -> datetime:
    """Get today's date at midnight in Korean timezone."""
    now = now_in_korea()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def korean_business_hours() -> tuple[datetime, datetime]:
    """Get today's Korean business hours (9 AM - 6 PM KST)."""
    today = today_in_korea()
    start = today.replace(hour=9)
    end = today.replace(hour=18)
    return start, end


def is_korean_business_hours(dt: datetime | None = None) -> bool:
    """Check if the given time (or now) is within Korean business hours."""
    if dt is None:
        dt = now_in_korea()
    else:
        dt = to_korean_time(dt)

    # Monday = 0, Sunday = 6
    if dt.weekday() >= 5:  # Saturday or Sunday
        return False

    start_time, end_time = korean_business_hours()
    return start_time.time() <= dt.time() <= end_time.time()


def format_korean_date(dt: datetime) -> str:
    """Format date in Korean style."""
    korean_dt = to_korean_time(dt)
    return korean_dt.strftime("%Y년 %m월 %d일")


def format_korean_datetime(dt: datetime) -> str:
    """Format datetime in Korean style."""
    korean_dt = to_korean_time(dt)
    return korean_dt.strftime("%Y년 %m월 %d일 %H시 %M분")


def parse_korean_date_input(date_str: str) -> datetime | None:
    """Parse various Korean date input formats."""
    formats = [
        "%Y년 %m월 %d일",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=KST)
        except ValueError:
            continue

    return None