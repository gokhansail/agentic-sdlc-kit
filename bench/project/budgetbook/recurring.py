"""Recurring items: expand them into dated occurrences and project them over a period."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable

from .dates import add_months
from .models import RecurringItem


@dataclass(frozen=True)
class Projected:
    """One expected future booking, not yet in the ledger."""

    date: dt.date
    name: str
    amount: int
    category: str
    account: str


def occurrences(item: RecurringItem, first: dt.date, last: dt.date) -> list[dt.date]:
    """Dates on which ``item`` falls between ``first`` and ``last``, both included.

    Monthly and yearly items keep the day of their start date and fall back to the last day
    of a shorter month: a monthly item that starts on January 31 falls on February 29 in a
    leap year and on March 31 again.
    """
    limit = last if item.end is None else min(last, item.end)
    dates: list[dt.date] = []
    step = 0
    while True:
        if item.frequency == "weekly":
            day = item.start + dt.timedelta(days=7 * step)
        elif item.frequency == "monthly":
            day = add_months(item.start, step)
        else:
            day = add_months(item.start, 12 * step)
        if day > limit:
            return dates
        if day >= first:
            dates.append(day)
        step += 1


def forecast(items: Iterable[RecurringItem], first: dt.date, last: dt.date) -> list[Projected]:
    """All occurrences of all items in the period, ordered by date, then name."""
    projected = [
        Projected(day, item.name, item.amount, item.category, item.account)
        for item in items
        for day in occurrences(item, first, last)
    ]
    projected.sort(key=lambda p: (p.date, p.name))
    return projected


def monthly_cost(items: Iterable[RecurringItem]) -> int:
    """Rough monthly total of all items in cents, for a quick overview (not for reports)."""
    total = 0
    for item in items:
        if item.frequency == "monthly":
            total += item.amount
        elif item.frequency == "weekly":
            total += item.amount * 52 // 12
        else:
            total += item.amount // 12
    return total
