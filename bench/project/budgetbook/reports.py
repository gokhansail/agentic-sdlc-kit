"""Monthly reports: income, expenses and totals per category."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .categories import normalize_category
from .ledger import Ledger
from .models import Transaction


@dataclass(frozen=True)
class MonthlyReport:
    """Numbers of one calendar month, in cents.

    ``income`` and ``expenses`` are both non-negative; ``by_category`` holds signed totals.
    """

    year: int
    month: int
    income: int
    expenses: int
    by_category: dict[str, int]
    count: int

    @property
    def net(self) -> int:
        return self.income - self.expenses


def totals_by_category(transactions: Iterable[Transaction]) -> dict[str, int]:
    """Sum of amounts per category, ordered by category name.

    Names are normalized while grouping, so transactions loaded from an older file that
    kept the names as typed are still grouped with the rest.
    """
    totals: dict[str, int] = {}
    for tx in transactions:
        key = normalize_category(tx.category)
        totals[key] = totals.get(key, 0) + tx.amount
    return dict(sorted(totals.items()))


def monthly_report(ledger: Ledger, year: int, month: int) -> MonthlyReport:
    """Report for one calendar month. ``expenses`` is a positive number."""
    transactions = ledger.in_month(year, month)
    income = sum(tx.amount for tx in transactions if tx.amount > 0)
    expenses = -sum(tx.amount for tx in transactions if tx.amount < 0)
    return MonthlyReport(
        year=year,
        month=month,
        income=income,
        expenses=expenses,
        by_category=totals_by_category(transactions),
        count=len(transactions),
    )
