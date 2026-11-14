import datetime as dt

from budgetbook.ledger import Ledger
from budgetbook.reports import monthly_report, totals_by_category


def test_monthly_report_totals(march_ledger):
    report = monthly_report(march_ledger, 2024, 3)
    assert report.income == 250000
    assert report.expenses == 4280 + 1550 + 90000
    assert report.net == 250000 - 95830
    assert report.count == 4


def test_monthly_report_by_category_is_sorted(march_ledger):
    report = monthly_report(march_ledger, 2024, 3)
    assert list(report.by_category) == ["food/eating out", "food/groceries", "housing", "salary"]
    assert report.by_category["food/groceries"] == -4280


def test_report_of_an_empty_month(march_ledger):
    report = monthly_report(march_ledger, 2024, 5)
    assert (report.income, report.expenses, report.net, report.count) == (0, 0, 0, 0)
    assert report.by_category == {}


def test_report_includes_the_first_and_last_day_of_the_month():
    ledger = Ledger()
    ledger.add(dt.date(2024, 2, 29), -100, "a")
    ledger.add(dt.date(2024, 3, 1), -200, "a")
    ledger.add(dt.date(2024, 3, 31), -400, "a")
    ledger.add(dt.date(2024, 4, 1), -800, "a")
    assert monthly_report(ledger, 2024, 3).expenses == 600


def test_totals_group_names_that_were_stored_unnormalized():
    ledger = Ledger.from_dict(
        {
            "version": 1,
            "transactions": [
                {"id": 1, "date": "2024-03-05", "amount": -100, "category": "Food"},
                {"id": 2, "date": "2024-03-06", "amount": -250, "category": "food"},
            ],
        }
    )
    assert totals_by_category(ledger.all()) == {"food": -350}
