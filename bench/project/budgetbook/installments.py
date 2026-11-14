"""Instalment plans: pay one amount in several monthly parts."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .dates import add_months
from .ledger import Ledger
from .models import Transaction
from .money import split_evenly


@dataclass(frozen=True)
class Installment:
    date: dt.date
    amount: int  # cents, negative: an expense


def plan(total: int, parts: int, first: dt.date) -> list[Installment]:
    """Split a positive ``total`` into ``parts`` monthly expenses starting on ``first``.

    The shares add up to the total exactly; the first shares carry the extra cents. The day
    of the month follows ``first`` and is clamped in short months.
    """
    if total <= 0:
        raise ValueError("total must be positive")
    shares = split_evenly(total, parts)
    return [Installment(add_months(first, index), -share) for index, share in enumerate(shares)]


def book(
    ledger: Ledger,
    total: int,
    parts: int,
    first: dt.date,
    category: str,
    description: str = "",
    account: str = "main",
) -> list[Transaction]:
    """Book every instalment of a plan in the ledger and return the new transactions."""
    booked = []
    for number, item in enumerate(plan(total, parts, first), start=1):
        label = f"{description} ({number}/{parts})".strip()
        booked.append(ledger.add(item.date, item.amount, category, label, account))
    return booked
