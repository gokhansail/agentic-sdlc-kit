"""Date helpers: parsing, month arithmetic and month boundaries."""
from __future__ import annotations

import calendar
import datetime as dt
import re

from .errors import DateError

_MONTH = re.compile(r"^(\d{4})-(\d{2})$")


def parse_date(text: str) -> dt.date:
    """Parse an ISO date (``YYYY-MM-DD``)."""
    try:
        return dt.date.fromisoformat(text.strip())
    except ValueError:
        raise DateError(f"not a date (use YYYY-MM-DD): {text!r}") from None


def parse_month(text: str) -> tuple[int, int]:
    """Parse ``YYYY-MM`` into ``(year, month)``."""
    match = _MONTH.match(text.strip())
    if match is None:
        raise DateError(f"not a month (use YYYY-MM): {text!r}")
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12 or year < 1:
        raise DateError(f"not a month (use YYYY-MM): {text!r}")
    return year, month


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def month_bounds(year: int, month: int) -> tuple[dt.date, dt.date]:
    """First and last day of a month, both inclusive."""
    return dt.date(year, month, 1), dt.date(year, month, days_in_month(year, month))


def add_months(day: dt.date, months: int) -> dt.date:
    """Move a date by whole months; a day that does not exist in the target month is clamped.

    ``add_months(date(2024, 1, 31), 1)`` is 2024-02-29.
    """
    index = day.year * 12 + (day.month - 1) + months
    year, month_zero = divmod(index, 12)
    month = month_zero + 1
    return dt.date(year, month, min(day.day, days_in_month(year, month)))


def month_label(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"
