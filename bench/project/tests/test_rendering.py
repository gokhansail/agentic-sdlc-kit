import datetime as dt

from budgetbook.ledger import Ledger
from budgetbook.rendering import format_table, render_report, render_transactions
from budgetbook.reports import monthly_report


def test_format_table_aligns_columns():
    lines = format_table(["Name", "Amount"], [["rent", "-900.00"], ["gym", "-30.00"]], right=(1,))
    assert lines == ["Name   Amount", "rent  -900.00", "gym    -30.00"]


def test_render_transactions_has_a_total_line(march_ledger):
    text = render_transactions(march_ledger.in_month(2024, 3))
    lines = text.splitlines()
    assert lines[0].split() == ["ID", "Date", "Amount", "Account", "Category", "Description"]
    assert lines[-1] == "Total: 1541.70 (4 transactions)"


def test_render_transactions_singular_and_empty():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -100, "food", "x")
    assert render_transactions(ledger.all()).splitlines()[-1] == "Total: -1.00 (1 transaction)"
    assert render_transactions([]) == "No transactions."


def test_render_report(march_ledger):
    text = render_report(monthly_report(march_ledger, 2024, 3))
    assert text.splitlines() == [
        "Report 2024-03",
        "Income: 2500.00",
        "Expenses: 958.30",
        "Net: 1541.70",
        "By category:",
        "  food/eating out: -15.50",
        "  food/groceries: -42.80",
        "  housing: -900.00",
        "  salary: 2500.00",
    ]
