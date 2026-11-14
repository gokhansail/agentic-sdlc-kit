import datetime as dt

from budgetbook.accounts import balances, net_worth
from budgetbook.ledger import Ledger
from budgetbook.summary import yearly_summary, year_totals
from budgetbook.textfmt import truncate


def test_balances_per_account_up_to_a_date():
    ledger = Ledger()
    ledger.add(dt.date(2024, 1, 10), 100000, "salary", account="main")
    ledger.add(dt.date(2024, 2, 10), -2500, "food", account="joint")
    ledger.add(dt.date(2024, 3, 10), -1000, "food", account="main")
    assert balances(ledger) == {"joint": -2500, "main": 99000}
    assert balances(ledger, dt.date(2024, 2, 28)) == {"joint": -2500, "main": 100000}
    assert balances(ledger, dt.date(2024, 1, 31)) == {"main": 100000}
    assert net_worth(ledger) == 96500


def test_yearly_summary_has_twelve_months(march_ledger):
    lines = yearly_summary(march_ledger, 2024)
    assert len(lines) == 12
    assert lines[2].income == 250000 and lines[2].net == 154170
    assert lines[3].expenses == 999
    assert lines[0].income == lines[0].expenses == 0
    totals = year_totals(lines)
    assert (totals.income, totals.expenses) == (250000, 96829)


def test_truncate_leaves_short_text_alone():
    assert truncate("short", 30) == "short"
