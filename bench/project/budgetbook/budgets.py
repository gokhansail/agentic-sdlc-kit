"""Monthly budgets per category. The limits live in ``Ledger.budgets`` (category to cents)."""
from __future__ import annotations

from .categories import normalize_category
from .errors import AmountError, NotFoundError
from .ledger import Ledger


def set_budget(ledger: Ledger, category: str, limit: int) -> str:
    """Set the monthly limit for a category and return the normalized category name."""
    if limit <= 0:
        raise AmountError("a budget limit must be more than zero")
    name = normalize_category(category)
    ledger.budgets[name] = limit
    return name


def get_budget(ledger: Ledger, category: str) -> int | None:
    return ledger.budgets.get(normalize_category(category))


def remove_budget(ledger: Ledger, category: str) -> None:
    name = normalize_category(category)
    if name not in ledger.budgets:
        raise NotFoundError(f"no budget for {name!r}")
    del ledger.budgets[name]


def all_budgets(ledger: Ledger) -> list[tuple[str, int]]:
    """Every budget as ``(category, limit)``, ordered by category name."""
    return sorted(ledger.budgets.items())
