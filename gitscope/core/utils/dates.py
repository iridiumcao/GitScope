from __future__ import annotations

from datetime import date, datetime

from gitscope.core.utils.errors import InvalidDateRangeError


def parse_optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - exercised via CLI exit handling
        raise InvalidDateRangeError(f"Invalid date value '{value}'. Expected YYYY-MM-DD.") from exc


def format_datetime(value: datetime | None) -> str:
    return value.isoformat() if value else "N/A"


def short_date(value: datetime | None) -> str:
    if value is None:
        return "N/A"
    return value.date().isoformat()


def month_key(value: datetime) -> str:
    return value.strftime("%Y-%m")


def iso_week_key(value: datetime) -> str:
    year, week, _ = value.isocalendar()
    return f"{year}-W{week:02d}"


def safe_day_span(start: datetime | None, end: datetime | None) -> int:
    if not start or not end:
        return 1
    return max((end.date() - start.date()).days + 1, 1)
