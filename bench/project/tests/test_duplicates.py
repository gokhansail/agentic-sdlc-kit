import datetime as dt

from budgetbook.csvio import import_csv
from budgetbook.duplicates import DuplicateFilter, signature
from budgetbook.ledger import Ledger


def test_signature_ignores_case_and_extra_spaces():
    day = dt.date(2024, 3, 5)
    assert signature(day, -100, "Coffee  Shop") == signature(day, -100, "coffee shop")


def test_each_existing_booking_absorbs_one_candidate():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -350, "food", "coffee")
    known = DuplicateFilter(ledger.all())
    assert known.is_duplicate(dt.date(2024, 3, 5), -350, "Coffee") is True
    assert known.is_duplicate(dt.date(2024, 3, 5), -350, "coffee") is False


def test_import_can_skip_rows_that_are_already_booked():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -350, "food", "coffee")
    text = "date,amount,category,description\n2024-03-05,-3.50,food,coffee\n2024-03-06,-3.50,food,coffee\n"
    assert import_csv(ledger, text, skip_duplicates=True) == 1
    assert len(ledger) == 2
    assert import_csv(ledger, text) == 2
