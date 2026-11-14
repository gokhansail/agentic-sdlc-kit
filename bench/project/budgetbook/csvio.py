"""CSV export and import.

The export has the columns ``id,date,amount,category,description,account``. An import needs
at least ``date``, ``amount`` and ``category``; ``description`` and ``account`` are optional
and an ``id`` column is ignored, because the ledger hands out its own ids.
"""
from __future__ import annotations

import csv
import io
from typing import Iterable

from .categories import normalize_category
from .dates import parse_date
from .duplicates import DuplicateFilter
from .errors import AmountError, CategoryError, CsvImportError, DateError
from .ledger import Ledger
from .models import Transaction
from .money import format_amount, parse_amount

COLUMNS = ("id", "date", "amount", "category", "description", "account")
REQUIRED = ("date", "amount", "category")


def export_csv(transactions: Iterable[Transaction]) -> str:
    """Render transactions as CSV text with a header line and LF line ends."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for tx in transactions:
        writer.writerow(
            [tx.id, tx.date.isoformat(), format_amount(tx.amount), tx.category, tx.description, tx.account]
        )
    return buffer.getvalue()


def import_csv(ledger: Ledger, text: str, skip_duplicates: bool = False) -> int:
    """Add the rows of a CSV text to the ledger and return how many were added.

    All rows are checked first: when one row is wrong nothing is added and the error names
    the line. With ``skip_duplicates`` a row that matches a booking already in the ledger
    (same day, amount and description) is left out and not counted.
    """
    reader = csv.DictReader(io.StringIO(text, newline=""))
    names = [name.strip().lower() for name in (reader.fieldnames or [])]
    reader.fieldnames = names
    missing = [name for name in REQUIRED if name not in names]
    if missing:
        raise CsvImportError(1, f"missing column: {', '.join(missing)}")

    rows = []
    for row in reader:
        line = reader.line_num
        try:
            rows.append(
                (
                    parse_date(row["date"] or ""),
                    parse_amount(row["amount"] or ""),
                    normalize_category(row["category"] or ""),
                    (row.get("description") or "").strip(),
                    (row.get("account") or "").strip() or "main",
                )
            )
        except (DateError, AmountError, CategoryError) as exc:
            raise CsvImportError(line, str(exc)) from None

    known = DuplicateFilter(ledger.all()) if skip_duplicates else None
    added = 0
    for day, amount, category, description, account in rows:
        if known is not None and known.is_duplicate(day, amount, description):
            continue
        ledger.add(day, amount, category, description, account)
        added += 1
    return added
