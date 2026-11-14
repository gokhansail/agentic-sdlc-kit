import datetime as dt

from budgetbook.filters import largest, only_expenses, only_income, select


def test_category_filter_includes_subcategories(march_ledger):
    found = select(march_ledger.all(), category="Food")
    assert sorted(tx.category for tx in found) == ["food/eating out", "food/groceries", "food/groceries"]


def test_category_filter_does_not_match_a_longer_name(march_ledger):
    march_ledger.add(dt.date(2024, 3, 20), -500, "foodcourt")
    assert all(tx.category != "foodcourt" for tx in select(march_ledger.all(), category="food"))


def test_account_and_text_filters(march_ledger):
    march_ledger.add(dt.date(2024, 3, 21), -700, "gifts", "Birthday card", "joint")
    assert [tx.description for tx in select(march_ledger.all(), account="joint")] == ["Birthday card"]
    assert [tx.description for tx in select(march_ledger.all(), text="SHOP")] == ["weekly shop"]


def test_expense_and_income_split_and_largest(march_ledger):
    everything = march_ledger.all()
    assert len(only_expenses(everything)) == 4
    assert [tx.category for tx in only_income(everything)] == ["salary"]
    assert [tx.category for tx in largest(everything, 2)] == ["salary", "housing"]
