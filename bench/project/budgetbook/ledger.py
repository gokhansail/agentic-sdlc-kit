"""The ledger: all transactions, budgets and recurring items, with load and save."""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from .categories import normalize_category
from .dates import month_bounds
from .errors import LedgerFileError, NotFoundError
from .models import RecurringItem, Transaction

FORMAT_VERSION = 1


class Ledger:
    """In-memory ledger. ``save`` and ``load`` use one JSON file."""

    def __init__(self) -> None:
        self._transactions: dict[int, Transaction] = {}
        self._next_id = 1
        self.budgets: dict[str, int] = {}
        self.recurring: list[RecurringItem] = []

    def __len__(self) -> int:
        return len(self._transactions)

    # -- transactions -----------------------------------------------------

    def add(
        self,
        date: dt.date,
        amount: int,
        category: str,
        description: str = "",
        account: str = "main",
    ) -> Transaction:
        """Book a transaction. The category is normalized; ids are never reused."""
        tx = Transaction(
            id=self._next_id,
            date=date,
            amount=amount,
            category=normalize_category(category),
            description=description.strip(),
            account=account.strip(),
        )
        self._transactions[tx.id] = tx
        self._next_id += 1
        return tx

    def get(self, tx_id: int) -> Transaction:
        try:
            return self._transactions[tx_id]
        except KeyError:
            raise NotFoundError(f"no transaction with id {tx_id}") from None

    def remove(self, tx_id: int) -> Transaction:
        tx = self.get(tx_id)
        del self._transactions[tx_id]
        return tx

    def update(
        self,
        tx_id: int,
        *,
        date: dt.date | None = None,
        amount: int | None = None,
        category: str | None = None,
        description: str | None = None,
        account: str | None = None,
    ) -> Transaction:
        """Change fields of a booked transaction; fields left as None keep their value."""
        old = self.get(tx_id)
        new = Transaction(
            id=old.id,
            date=old.date if date is None else date,
            amount=old.amount if amount is None else amount,
            category=old.category if category is None else normalize_category(category),
            description=old.description if description is None else description.strip(),
            account=old.account if account is None else account.strip(),
        )
        self._transactions[tx_id] = new
        return new

    def all(self) -> list[Transaction]:
        """Every transaction, oldest first; transactions on the same day are ordered by id."""
        return sorted(self._transactions.values(), key=lambda t: (t.date, t.id))

    def between(
        self, start: dt.date | None = None, end: dt.date | None = None
    ) -> list[Transaction]:
        """Transactions dated from ``start`` to ``end``, both days included.

        Either bound may be None, which leaves that side open.
        """
        return [
            tx
            for tx in self.all()
            if (start is None or tx.date >= start) and (end is None or tx.date < end)
        ]

    def in_month(self, year: int, month: int) -> list[Transaction]:
        first, last = month_bounds(year, month)
        return [tx for tx in self.all() if first <= tx.date <= last]

    def accounts(self) -> list[str]:
        return sorted({tx.account for tx in self._transactions.values()})

    # -- serialization ----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "version": FORMAT_VERSION,
            "next_id": self._next_id,
            "transactions": [tx.to_dict() for tx in self.all()],
            "budgets": dict(sorted(self.budgets.items())),
            "recurring": [item.to_dict() for item in self.recurring],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ledger":
        if data.get("version") != FORMAT_VERSION:
            raise LedgerFileError(f"unsupported ledger format version: {data.get('version')!r}")
        ledger = cls()
        try:
            for entry in data.get("transactions", []):
                tx = Transaction.from_dict(entry)
                ledger._transactions[tx.id] = tx
            ledger.budgets = {str(k): int(v) for k, v in data.get("budgets", {}).items()}
            ledger.recurring = [RecurringItem.from_dict(e) for e in data.get("recurring", [])]
            highest = max(ledger._transactions, default=0)
            ledger._next_id = max(int(data.get("next_id", 1)), highest + 1)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise LedgerFileError(f"ledger data is malformed: {exc}") from exc
        return ledger

    @classmethod
    def load(cls, path: str | os.PathLike) -> "Ledger":
        """Read a ledger file. A file that does not exist yet is an empty ledger."""
        path = Path(path)
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LedgerFileError(f"{path}: not valid JSON ({exc.msg})") from exc
        if not isinstance(data, dict):
            raise LedgerFileError(f"{path}: expected a JSON object")
        return cls.from_dict(data)

    def save(self, path: str | os.PathLike) -> None:
        """Write the ledger file. The old file stays intact if the write fails."""
        path = Path(path)
        payload = json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        try:
            tmp.write_text(payload, encoding="utf-8", newline="\n")
            os.replace(tmp, path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
