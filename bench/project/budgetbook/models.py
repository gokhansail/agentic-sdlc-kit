"""Plain data types: a booked transaction and a recurring item."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .errors import AmountError

FREQUENCIES = ("weekly", "monthly", "yearly")


@dataclass(frozen=True)
class Transaction:
    """One booked movement of money. Negative amounts are expenses."""

    id: int
    date: dt.date
    amount: int
    category: str
    description: str = ""
    account: str = "main"

    def __post_init__(self) -> None:
        if self.amount == 0:
            raise AmountError("amount must not be zero")
        if not self.account.strip():
            raise ValueError("account must not be empty")

    @property
    def is_expense(self) -> bool:
        return self.amount < 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "account": self.account,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            id=int(data["id"]),
            date=dt.date.fromisoformat(data["date"]),
            amount=int(data["amount"]),
            category=str(data["category"]),
            description=str(data.get("description", "")),
            account=str(data.get("account", "main")),
        )


@dataclass(frozen=True)
class RecurringItem:
    """A payment or income that repeats: rent, a salary, a yearly insurance."""

    name: str
    amount: int
    category: str
    frequency: str
    start: dt.date
    end: dt.date | None = None
    account: str = "main"

    def __post_init__(self) -> None:
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {', '.join(FREQUENCIES)}")
        if self.amount == 0:
            raise AmountError("amount must not be zero")
        if self.end is not None and self.end < self.start:
            raise ValueError("end must not be before start")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "amount": self.amount,
            "category": self.category,
            "frequency": self.frequency,
            "start": self.start.isoformat(),
            "end": self.end.isoformat() if self.end else None,
            "account": self.account,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecurringItem":
        end = data.get("end")
        return cls(
            name=str(data["name"]),
            amount=int(data["amount"]),
            category=str(data["category"]),
            frequency=str(data["frequency"]),
            start=dt.date.fromisoformat(data["start"]),
            end=dt.date.fromisoformat(end) if end else None,
            account=str(data.get("account", "main")),
        )
