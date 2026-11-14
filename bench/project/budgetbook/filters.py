"""Filters applied to lists of transactions after they have been selected by date."""
from __future__ import annotations

from typing import Iterable

from .categories import is_within, normalize_category
from .models import Transaction


def select(
    transactions: Iterable[Transaction],
    *,
    category: str | None = None,
    account: str | None = None,
    text: str | None = None,
) -> list[Transaction]:
    """Keep the transactions that match every given criterion.

    ``category`` matches the category itself and everything below it. ``account`` is an
    exact match. ``text`` is a case-insensitive search in description and category.
    """
    wanted = normalize_category(category) if category is not None else None
    needle = text.lower() if text else None
    result = []
    for tx in transactions:
        if wanted is not None and not is_within(normalize_category(tx.category), wanted):
            continue
        if account is not None and tx.account != account:
            continue
        if needle is not None and needle not in f"{tx.description} {tx.category}".lower():
            continue
        result.append(tx)
    return result


def only_expenses(transactions: Iterable[Transaction]) -> list[Transaction]:
    """Transactions with a negative amount."""
    return [tx for tx in transactions if tx.is_expense]


def only_income(transactions: Iterable[Transaction]) -> list[Transaction]:
    """Transactions with a positive amount (income and refunds)."""
    return [tx for tx in transactions if not tx.is_expense]


def largest(transactions: Iterable[Transaction], count: int) -> list[Transaction]:
    """The ``count`` transactions with the largest absolute amount; ties keep id order."""
    ranked = sorted(transactions, key=lambda tx: (-abs(tx.amount), tx.id))
    return ranked[:count]
