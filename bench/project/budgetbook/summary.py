"""Yearly summary: one line of numbers per month."""
from __future__ import annotations

from dataclasses import dataclass

from .ledger import Ledger
from .reports import monthly_report


@dataclass(frozen=True)
class MonthLine:
    """Income and expenses of one month (both non-negative cents); ``month`` 0 means a total."""

    month: int
    income: int
    expenses: int

    @property
    def net(self) -> int:
        return self.income - self.expenses


def yearly_summary(ledger: Ledger, year: int) -> list[MonthLine]:
    """Twelve lines, January first; months without transactions are all zero."""
    lines = []
    for month in range(1, 13):
        report = monthly_report(ledger, year, month)
        lines.append(MonthLine(month, report.income, report.expenses))
    return lines


def year_totals(lines: list[MonthLine]) -> MonthLine:
    """The sum of the month lines, as a line with month 0."""
    return MonthLine(0, sum(line.income for line in lines), sum(line.expenses for line in lines))
