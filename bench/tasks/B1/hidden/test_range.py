import datetime as dt
import re

import pytest

from budgetbook.ledger import Ledger

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


@pytest.fixture
def march(data_file):
    ledger = Ledger()
    ledger.add(dt.date(2024, 2, 29), -100, "food", "leap day")
    ledger.add(dt.date(2024, 3, 1), -200, "food", "first")
    ledger.add(dt.date(2024, 3, 15), -300, "food", "middle")
    ledger.add(dt.date(2024, 3, 31), -400, "food", "last")
    ledger.add(dt.date(2024, 4, 1), -800, "food", "next month")
    ledger.save(data_file)


def listed_dates(out):
    return [DATE.search(line).group(0) for line in out.splitlines()[1:] if DATE.search(line)]


def test_last_day_of_the_range_is_listed(run, march):
    code, out, _ = run("list", "--from", "2024-03-01", "--to", "2024-03-31")
    assert code == 0
    assert listed_dates(out) == ["2024-03-01", "2024-03-15", "2024-03-31"]


def test_total_line_counts_the_last_day(run, march):
    _, out, _ = run("list", "--from", "2024-03-01", "--to", "2024-03-31")
    assert out.splitlines()[-1] == "Total: -9.00 (3 transactions)"


def test_range_of_a_single_day(run, march):
    _, out, _ = run("list", "--from", "2024-03-31", "--to", "2024-03-31")
    assert listed_dates(out) == ["2024-03-31"]
    assert out.splitlines()[-1] == "Total: -4.00 (1 transaction)"


def test_to_alone_includes_that_day(run, march):
    _, out, _ = run("list", "--to", "2024-03-15")
    assert listed_dates(out) == ["2024-02-29", "2024-03-01", "2024-03-15"]


def test_from_alone_includes_that_day(run, march):
    _, out, _ = run("list", "--from", "2024-03-31")
    assert listed_dates(out) == ["2024-03-31", "2024-04-01"]


def test_range_ending_on_a_leap_day(run, march):
    _, out, _ = run("list", "--to", "2024-02-29")
    assert listed_dates(out) == ["2024-02-29"]


def test_days_after_the_range_stay_out(run, march):
    _, out, _ = run("list", "--from", "2024-03-01", "--to", "2024-03-31")
    assert "2024-04-01" not in out and "2024-02-29" not in out
