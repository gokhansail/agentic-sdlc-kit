import datetime as dt

from budgetbook.installments import book, plan
from budgetbook.ledger import Ledger
from budgetbook.stats import average_monthly_expenses, compare_with_previous_month, previous_month, top_categories


def test_previous_month_crosses_the_year():
    assert previous_month(2024, 1) == (2023, 12)
    assert previous_month(2024, 3) == (2024, 2)


def test_compare_with_previous_month():
    ledger = Ledger()
    ledger.add(dt.date(2024, 2, 10), -30000, "food")
    ledger.add(dt.date(2024, 3, 10), -33700, "food")
    result = compare_with_previous_month(ledger, 2024, 3)
    assert (result.expenses, result.previous_expenses, result.change) == (33700, 30000, 3700)
    assert result.change_tenths == 123  # 12.333 percent, one decimal


def test_compare_without_a_previous_month_has_no_percentage():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 10), -100, "food")
    assert compare_with_previous_month(ledger, 2024, 3).change_tenths is None


def test_average_counts_only_months_with_transactions():
    ledger = Ledger()
    ledger.add(dt.date(2024, 1, 10), -1001, "a")
    ledger.add(dt.date(2024, 3, 10), -1000, "a")
    assert average_monthly_expenses(ledger, 2024) == 1001  # 1000.5 rounds up
    assert average_monthly_expenses(ledger, 2023) == 0


def test_top_categories_group_by_top_level_and_ignore_income(march_ledger):
    ranked = top_categories(march_ledger.in_month(2024, 3), 5)
    assert ranked == [("housing", 90000), ("food", 5830)]
    assert top_categories(march_ledger.in_month(2024, 3), 1) == [("housing", 90000)]


def test_installment_plan_adds_up_and_clamps_days():
    shares = plan(10000, 3, dt.date(2024, 1, 31))
    assert [s.amount for s in shares] == [-3334, -3333, -3333]
    assert [s.date for s in shares] == [dt.date(2024, 1, 31), dt.date(2024, 2, 29), dt.date(2024, 3, 31)]


def test_installments_are_booked_with_numbered_descriptions():
    ledger = Ledger()
    booked = book(ledger, 9000, 3, dt.date(2024, 5, 1), "Furniture", "sofa")
    assert [tx.description for tx in booked] == ["sofa (1/3)", "sofa (2/3)", "sofa (3/3)"]
    assert sum(tx.amount for tx in ledger.all()) == -9000
