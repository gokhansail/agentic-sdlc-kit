"""Turn results into text for the terminal. Nothing here prints; callers print the strings."""
from __future__ import annotations

import calendar
from typing import Sequence

from .dates import month_label
from .models import Transaction
from .money import format_amount
from .recurring import Projected
from .reports import MonthlyReport
from .stats import Comparison
from .summary import MonthLine
from .textfmt import pad_left, pad_right, truncate

DESCRIPTION_WIDTH = 30


def format_table(
    headers: Sequence[str], rows: Sequence[Sequence[str]], right: Sequence[int] = ()
) -> list[str]:
    """Lay out a table with two spaces between columns; columns in ``right`` are right-aligned."""
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def line(cells: Sequence[str]) -> str:
        padded = [
            pad_left(cell, widths[i]) if i in right else pad_right(cell, widths[i])
            for i, cell in enumerate(cells)
        ]
        return "  ".join(padded).rstrip()

    return [line(headers)] + [line(row) for row in rows]


def render_transactions(transactions: Sequence[Transaction]) -> str:
    """The ``list`` output: a table and a ``Total:`` line, or ``No transactions.``"""
    if not transactions:
        return "No transactions."
    rows = [
        [
            str(tx.id),
            tx.date.isoformat(),
            format_amount(tx.amount),
            tx.account,
            tx.category,
            truncate(tx.description, DESCRIPTION_WIDTH),
        ]
        for tx in transactions
    ]
    lines = format_table(["ID", "Date", "Amount", "Account", "Category", "Description"], rows, right=(0, 2))
    total = sum(tx.amount for tx in transactions)
    noun = "transaction" if len(transactions) == 1 else "transactions"
    lines.append(f"Total: {format_amount(total)} ({len(transactions)} {noun})")
    return "\n".join(lines)


def render_report(report: MonthlyReport) -> str:
    lines = [
        f"Report {month_label(report.year, report.month)}",
        f"Income: {format_amount(report.income)}",
        f"Expenses: {format_amount(report.expenses)}",
        f"Net: {format_amount(report.net)}",
    ]
    if report.by_category:
        lines.append("By category:")
        for category, total in report.by_category.items():
            lines.append(f"  {category}: {format_amount(total)}")
    return "\n".join(lines)


def render_forecast(year: int, month: int, entries: Sequence[Projected]) -> str:
    label = month_label(year, month)
    if not entries:
        return f"Nothing expected in {label}."
    rows = [
        [e.date.isoformat(), e.name, format_amount(e.amount), e.category, e.account] for e in entries
    ]
    lines = [f"Forecast {label}"]
    lines += format_table(["Date", "Name", "Amount", "Category", "Account"], rows, right=(2,))
    lines.append(f"Net: {format_amount(sum(e.amount for e in entries))}")
    return "\n".join(lines)


def render_balances(balances: dict[str, int]) -> str:
    if not balances:
        return "No accounts."
    rows = [[name, format_amount(total)] for name, total in balances.items()]
    lines = format_table(["Account", "Balance"], rows, right=(1,))
    lines.append(f"Total: {format_amount(sum(balances.values()))}")
    return "\n".join(lines)


def render_budget_list(budgets: Sequence[tuple[str, int]]) -> str:
    if not budgets:
        return "No budgets set."
    rows = [[name, format_amount(limit)] for name, limit in budgets]
    return "\n".join(format_table(["Category", "Monthly limit"], rows, right=(1,)))


def render_top(ranked: Sequence[tuple[str, int]]) -> str:
    if not ranked:
        return "No expenses."
    rows = [[category, format_amount(total)] for category, total in ranked]
    return "\n".join(format_table(["Category", "Expenses"], rows, right=(1,)))


def render_comparison(comparison: Comparison) -> str:
    label = month_label(comparison.year, comparison.month)
    lines = [
        f"Expenses {label}: {format_amount(comparison.expenses)}",
        f"Expenses before: {format_amount(comparison.previous_expenses)}",
        f"Change: {format_amount(comparison.change)}",
    ]
    if comparison.change_tenths is None:
        lines.append("Change in percent: not available")
    else:
        sign = "-" if comparison.change_tenths < 0 else ""
        whole, tenth = divmod(abs(comparison.change_tenths), 10)
        lines.append(f"Change in percent: {sign}{whole}.{tenth}%")
    return "\n".join(lines)


def render_summary(year: int, lines: Sequence[MonthLine], totals: MonthLine) -> str:
    rows = [
        [calendar.month_abbr[line.month], format_amount(line.income), format_amount(line.expenses), format_amount(line.net)]
        for line in lines
    ]
    rows.append(["Year", format_amount(totals.income), format_amount(totals.expenses), format_amount(totals.net)])
    table = format_table(["Month", "Income", "Expenses", "Net"], rows, right=(1, 2, 3))
    return "\n".join([f"Summary {year}"] + table)
