"""Find rows that are already in the ledger, so a bank export can be imported twice."""
from __future__ import annotations

import datetime as dt
from collections import Counter
from typing import Iterable

from .models import Transaction

Signature = tuple[dt.date, int, str]


def signature(day: dt.date, amount: int, description: str) -> Signature:
    """What makes two rows the same booking: day, amount and description (case-insensitive)."""
    return day, amount, " ".join(description.lower().split())


class DuplicateFilter:
    """Tells whether a candidate row is already booked.

    Each booked transaction absorbs one candidate: with one existing coffee on a day, the
    first candidate coffee is a duplicate and a second one is new.
    """

    def __init__(self, existing: Iterable[Transaction]) -> None:
        self._open = Counter(signature(tx.date, tx.amount, tx.description) for tx in existing)

    def is_duplicate(self, day: dt.date, amount: int, description: str) -> bool:
        key = signature(day, amount, description)
        if self._open[key] > 0:
            self._open[key] -= 1
            return True
        return False
