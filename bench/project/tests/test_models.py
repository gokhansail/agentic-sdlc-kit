import datetime as dt

import pytest

from budgetbook.errors import AmountError
from budgetbook.models import RecurringItem, Transaction


def test_transaction_round_trips_through_a_dict():
    tx = Transaction(3, dt.date(2024, 3, 5), -4280, "food", "shop", "joint")
    assert Transaction.from_dict(tx.to_dict()) == tx


def test_transaction_rejects_zero_amount():
    with pytest.raises(AmountError):
        Transaction(1, dt.date(2024, 3, 5), 0, "food")


def test_transaction_is_expense_by_sign():
    assert Transaction(1, dt.date(2024, 3, 5), -1, "x").is_expense
    assert not Transaction(2, dt.date(2024, 3, 5), 1, "x").is_expense


def test_recurring_item_validates_frequency_and_dates():
    start = dt.date(2024, 1, 1)
    with pytest.raises(ValueError):
        RecurringItem("gym", -3000, "health", "daily", start)
    with pytest.raises(ValueError):
        RecurringItem("gym", -3000, "health", "monthly", start, end=dt.date(2023, 12, 31))


def test_recurring_item_round_trips_through_a_dict():
    item = RecurringItem("rent", -90000, "housing", "monthly", dt.date(2024, 1, 1), dt.date(2024, 12, 1))
    assert RecurringItem.from_dict(item.to_dict()) == item
