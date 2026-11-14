"""Money helpers. Amounts are integer cents; floats are never used for money."""
from __future__ import annotations

import re

from .errors import AmountError

_AMOUNT = re.compile(r"^([+-]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?$")


def parse_amount(text: str) -> int:
    """Parse ``"12"``, ``"-12.5"`` or ``"1,234.56"`` into cents.

    A thousands separator is a comma followed by exactly three digits. At most two
    decimals are accepted.
    """
    match = _AMOUNT.match(text.strip())
    if match is None:
        raise AmountError(f"not an amount: {text!r}")
    sign, whole, fraction = match.groups()
    cents = int(whole.replace(",", "")) * 100 + int((fraction or "").ljust(2, "0"))
    return -cents if sign == "-" else cents


def format_amount(cents: int) -> str:
    """Format cents with two decimals, a leading ``-`` for negatives, no thousands separator."""
    sign = "-" if cents < 0 else ""
    whole, fraction = divmod(abs(cents), 100)
    return f"{sign}{whole}.{fraction:02d}"


def round_half_up_div(numerator: int, denominator: int) -> int:
    """Divide and round to the nearest integer, halves going up (toward positive infinity).

    Integer arithmetic only, so exact halves are exact. The denominator must be positive.
    """
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (2 * numerator + denominator) // (2 * denominator)


def split_evenly(total: int, parts: int) -> list[int]:
    """Split ``total`` cents into ``parts`` shares that add up to ``total``.

    The first ``total % parts`` shares are one cent larger. Used for instalments.
    """
    if parts <= 0:
        raise ValueError("parts must be positive")
    base, extra = divmod(total, parts)
    return [base + 1 if index < extra else base for index in range(parts)]
