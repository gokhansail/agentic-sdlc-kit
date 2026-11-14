"""Category names. A category may have parts separated by ``/``: ``food/groceries``.

Everything that stores or compares a category goes through ``normalize_category`` first,
so ``Food``, ``food`` and `` FOOD `` are one category.
"""
from __future__ import annotations

from .errors import CategoryError

SEPARATOR = "/"


def normalize_category(name: str) -> str:
    """Return the canonical form of a category name.

    Lower case, runs of white space inside a name become one space, parts joined by ``/``.
    An empty name or an empty part (``food//x``, ``/food``) is rejected.
    """
    cleaned = " ".join(name.lower().split())
    if not cleaned:
        raise CategoryError("category must not be empty")
    parts = cleaned.split(SEPARATOR)
    if any(not part for part in parts):
        raise CategoryError(f"category has an empty part: {name!r}")
    return SEPARATOR.join(parts)


def parent_of(category: str) -> str | None:
    """Parent of a normalized category, or None for a top-level one."""
    head, sep, _ = category.rpartition(SEPARATOR)
    return head if sep else None


def top_level(category: str) -> str:
    return category.split(SEPARATOR, 1)[0]


def is_within(category: str, ancestor: str) -> bool:
    """True when ``category`` is ``ancestor`` or lies below it. Both must be normalized."""
    return category == ancestor or category.startswith(ancestor + SEPARATOR)
