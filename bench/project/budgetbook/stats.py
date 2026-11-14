"""Small statistics over the ledger: month against month, averages, largest categories."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable

from .categories import top_level
from .dates import add_months
from .ledger import Ledger
from .models import Transaction
from .money import round_half_up_div
from .reports import monthly_report


@dataclass(frozen=True)
class Comparison:
    """Expenses of a month against the month before it."""

    year: int
    month: int
    expenses: int
    previous_expenses: int
    change: int
    change_tenths: int | None  # change as a percentage of the previous month, in tenths of a percent


def previous_month(year: int, month: int) -> tuple[int, int]:
    earlier = add_months(dt.date(year, month, 1), -1)
    return earlier.year, earlier.month


def compare_with_previous_month(ledger: Ledger, year: int, month: int) -> Comparison:
    """Expenses of the month, of the month before, the change and the change in percent.

    The percentage is rounded to one decimal with halves going up, and is None when the
    previous month had no expenses.
    """
    expenses = monthly_report(ledger, year, month).expenses
    before_year, before_month = previous_month(year, month)
    previous = monthly_report(ledger, before_year, before_month).expenses
    change = expenses - previous
    tenths = round_half_up_div(change * 1000, previous) if previous else None
    return Comparison(year, month, expenses, previous, change, tenths)


def average_monthly_expenses(ledger: Ledger, year: int) -> int:
    """Average expenses of the months of ``year`` that have any transaction, in cents.

    Rounded to the nearest cent, halves up. Zero when the year has no transactions.
    """
    totals = []
    for month in range(1, 13):
        report = monthly_report(ledger, year, month)
        if report.count:
            totals.append(report.expenses)
    if not totals:
        return 0
    return round_half_up_div(sum(totals), len(totals))


def top_categories(transactions: Iterable[Transaction], count: int) -> list[tuple[str, int]]:
    """The ``count`` top-level categories with the highest expenses, as positive cents.

    Ordered by expenses, then by name. Income and refunds are not netted out.
    """
    totals: dict[str, int] = {}
    for tx in transactions:
        if tx.is_expense:
            key = top_level(tx.category)
            totals[key] = totals.get(key, 0) - tx.amount
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:count]
