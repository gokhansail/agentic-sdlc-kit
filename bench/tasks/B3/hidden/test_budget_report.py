import datetime as dt
import re

import pytest

from budgetbook.ledger import Ledger

LINE = re.compile(
    r"^(?P<category>.+) (?P<spent>-?\d+\.\d\d) (?P<limit>\d+\.\d\d) (?P<percent>\d+\.\d)% (?P<status>OK|WARN|OVER)$"
)


def setup_ledger(data_file, budgets, transactions):
    ledger = Ledger()
    ledger.budgets.update(budgets)
    for day, cents, category in transactions:
        ledger.add(dt.date.fromisoformat(day), cents, category)
    ledger.save(data_file)


def budget_lines(out):
    lines = out.splitlines()
    start = lines.index("Budgets:")
    parsed = []
    for line in lines[start + 1:]:
        match = LINE.match(line)
        assert match, f"budget line not in the expected form: {line!r}"
        parsed.append((match["category"], match["spent"], match["limit"], match["percent"], match["status"]))
    return parsed


def test_lines_follow_the_report_sorted_by_category(run, data_file):
    setup_ledger(
        data_file,
        {"housing": 100000, "food": 40000, "eating out": 10000},
        [
            ("2024-03-05", -30000, "food/groceries"),
            ("2024-03-31", -11250, "food"),
            ("2024-03-10", -2500, "eating out"),
            ("2024-03-01", -90000, "housing"),
        ],
    )
    code, out, _ = run("report", "2024-03", "--budgets")
    assert code == 0
    assert budget_lines(out) == [
        ("eating out", "25.00", "100.00", "25.0", "OK"),
        ("food", "412.50", "400.00", "103.1", "OVER"),
        ("housing", "900.00", "1000.00", "90.0", "WARN"),
    ]


def test_the_existing_report_is_unchanged_and_the_section_follows_it(run, data_file):
    setup_ledger(data_file, {"food": 40000}, [("2024-03-05", -1000, "food"), ("2024-03-06", 5000, "salary")])
    _, plain, _ = run("report", "2024-03")
    _, full, _ = run("report", "2024-03", "--budgets")
    assert full.startswith(plain)
    assert full[len(plain):].splitlines()[0] == "Budgets:"


def test_without_the_flag_there_is_no_budget_section(run, data_file):
    setup_ledger(data_file, {"food": 40000}, [("2024-03-05", -1000, "food")])
    _, out, _ = run("report", "2024-03")
    assert "Budgets:" not in out


def test_no_budgets_set(run, data_file):
    setup_ledger(data_file, {}, [("2024-03-05", -1000, "food")])
    _, out, _ = run("report", "2024-03", "--budgets")
    assert out.splitlines()[-1] == "No budgets set."
    assert "Budgets:" not in out


def test_subcategories_roll_up_into_the_parent(run, data_file):
    setup_ledger(
        data_file,
        {"food": 40000, "food/groceries": 20000},
        [
            ("2024-03-05", -5000, "food"),
            ("2024-03-06", -8000, "food/groceries"),
            ("2024-03-07", -2000, "food/groceries/organic"),
            ("2024-03-08", -99900, "foodcourt"),
        ],
    )
    _, out, _ = run("report", "2024-03", "--budgets")
    assert budget_lines(out) == [
        ("food", "150.00", "400.00", "37.5", "OK"),
        ("food/groceries", "100.00", "200.00", "50.0", "OK"),
    ]


def test_refunds_reduce_what_was_spent(run, data_file):
    setup_ledger(data_file, {"food": 40000}, [("2024-03-05", -10000, "food"), ("2024-03-09", 3000, "food")])
    _, out, _ = run("report", "2024-03", "--budgets")
    assert budget_lines(out) == [("food", "70.00", "400.00", "17.5", "OK")]


def test_spent_is_never_shown_below_zero(run, data_file):
    setup_ledger(data_file, {"food": 40000}, [("2024-03-09", 2500, "food")])
    _, out, _ = run("report", "2024-03", "--budgets")
    assert budget_lines(out) == [("food", "0.00", "400.00", "0.0", "OK")]


def test_a_budget_without_any_spending_is_listed(run, data_file):
    setup_ledger(data_file, {"travel": 50000}, [("2024-03-09", -100, "food")])
    _, out, _ = run("report", "2024-03", "--budgets")
    assert budget_lines(out) == [("travel", "0.00", "500.00", "0.0", "OK")]


def test_only_the_month_asked_for_counts(run, data_file):
    setup_ledger(
        data_file,
        {"food": 40000},
        [
            ("2024-02-29", -1000, "food"),
            ("2024-03-01", -1000, "food"),
            ("2024-03-31", -1000, "food"),
            ("2024-04-01", -1000, "food"),
        ],
    )
    _, out, _ = run("report", "2024-03", "--budgets")
    assert budget_lines(out) == [("food", "20.00", "400.00", "5.0", "OK")]


def test_amounts_have_no_thousands_separator(run, data_file):
    setup_ledger(data_file, {"housing": 250000}, [("2024-03-01", -123456, "housing")])
    _, out, _ = run("report", "2024-03", "--budgets")
    assert budget_lines(out) == [("housing", "1234.56", "2500.00", "49.4", "OK")]


@pytest.mark.parametrize(
    "limit, spent, percent, status",
    [
        (40000, 4900, "12.3", "OK"),  # 12.25 rounds up
        (20000, 10, "0.1", "OK"),  # 0.05 rounds up
        (30000, 1, "0.0", "OK"),
        (30000, 10000, "33.3", "OK"),
        (30000, 20000, "66.7", "OK"),
        (40000, 31900, "79.8", "OK"),  # 79.75 rounds up, still below 80.0
        (40000, 31960, "79.9", "OK"),
        (40000, 31980, "80.0", "WARN"),  # 79.95 rounds up to 80.0
        (40000, 31996, "80.0", "WARN"),  # 79.99 shows as 80.0, so WARN
        (40000, 39980, "100.0", "WARN"),  # 99.95 rounds to 100.0, not over the limit
        (40000, 40000, "100.0", "WARN"),
        (40000, 40001, "100.0", "OVER"),  # over the limit by one cent
        (40000, 40400, "101.0", "OVER"),
    ],
)
def test_rounding_and_status_boundaries(run, data_file, limit, spent, percent, status):
    setup_ledger(data_file, {"food": limit}, [("2024-03-05", -spent, "food")])
    _, out, _ = run("report", "2024-03", "--budgets")
    assert budget_lines(out) == [("food", f"{spent // 100}.{spent % 100:02d}", f"{limit // 100}.{limit % 100:02d}", percent, status)]
