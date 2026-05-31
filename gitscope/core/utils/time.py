"""Date and time helpers."""

from __future__ import annotations

from datetime import UTC, date, datetime, time


def to_naive_utc(value: datetime) -> datetime:
    """Convert any datetime to naive UTC for stable comparisons."""

    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def parse_datetime(value: str) -> datetime:
    """Parse an ISO date or datetime string."""

    if "T" not in value:
        parsed_date = date.fromisoformat(value)
        return datetime.combine(parsed_date, time.min)
    return to_naive_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def parse_since(value: str | None) -> datetime | None:
    """Parse the lower time bound."""

    if value is None:
        return None
    return parse_datetime(value)


def parse_until(value: str | None) -> datetime | None:
    """Parse the upper time bound."""

    if value is None:
        return None
    if "T" not in value:
        parsed_date = date.fromisoformat(value)
        return datetime.combine(parsed_date, time.max)
    return parse_datetime(value)


def format_iso(value: datetime | None) -> str | None:
    """Format a datetime for JSON output."""

    if value is None:
        return None
    return to_naive_utc(value).isoformat(timespec="seconds")


def days_between(start: datetime | None, end: datetime | None) -> int:
    """Return whole days between two datetimes."""

    if start is None or end is None:
        return 0
    delta = to_naive_utc(end) - to_naive_utc(start)
    return max(delta.days, 0)
