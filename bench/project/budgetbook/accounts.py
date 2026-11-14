"""Balances per account."""
from __future__ import annotations

import datetime as dt

from .ledger import Ledger


def balances(ledger: Ledger, as_of: dt.date | None = None) -> dict[str, int]:
    """Sum of all amounts per account up to and including ``as_of`` (all dates when None).

    Accounts are ordered by name. An account whose transactions all fall after ``as_of`` is
    not listed.
    """
    totals: dict[str, int] = {}
    for tx in ledger.all():
        if as_of is not None and tx.date > as_of:
            continue
        totals[tx.account] = totals.get(tx.account, 0) + tx.amount
    return dict(sorted(totals.items()))


def net_worth(ledger: Ledger, as_of: dt.date | None = None) -> int:
    """Sum of all account balances up to ``as_of``."""
    return sum(balances(ledger, as_of).values())
