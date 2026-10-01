"""Time helpers. Tests patch `now` to move through days."""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def now() -> datetime:
    return datetime.now(timezone.utc)


def valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def local_today(tz_name: str) -> date:
    tz = ZoneInfo(tz_name) if valid_timezone(tz_name) else timezone.utc
    return now().astimezone(tz).date()
