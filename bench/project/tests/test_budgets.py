import pytest

from budgetbook.budgets import all_budgets, get_budget, remove_budget, set_budget
from budgetbook.errors import AmountError, NotFoundError
from budgetbook.ledger import Ledger


def test_set_budget_stores_the_normalized_name():
    ledger = Ledger()
    assert set_budget(ledger, "Eating Out", 20000) == "eating out"
    assert ledger.budgets == {"eating out": 20000}


def test_budget_lookup_uses_the_same_normalization():
    ledger = Ledger()
    set_budget(ledger, "Eating  Out", 20000)
    assert get_budget(ledger, "eating out") == 20000
    assert get_budget(ledger, "Eating OUT") == 20000
    assert get_budget(ledger, "food") is None


def test_budget_limit_must_be_positive():
    with pytest.raises(AmountError):
        set_budget(Ledger(), "food", 0)


def test_all_budgets_is_sorted_and_remove_needs_an_existing_budget():
    ledger = Ledger()
    set_budget(ledger, "housing", 100000)
    set_budget(ledger, "food", 40000)
    assert all_budgets(ledger) == [("food", 40000), ("housing", 100000)]
    remove_budget(ledger, "Food")
    with pytest.raises(NotFoundError):
        remove_budget(ledger, "food")
