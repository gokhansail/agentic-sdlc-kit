import datetime as dt

import pytest

from budgetbook.ledger import Ledger


@pytest.fixture
def ledger_file(data_file):
    """Six transactions, added out of date order. Ids by date: 4, 2, 1, 3 (same day), 5, 6."""
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 10), -1000, "food", "id one")
    ledger.add(dt.date(2024, 3, 5), -200, "food", "id two")
    ledger.add(dt.date(2024, 3, 10), -3000, "rent", "id three")
    ledger.add(dt.date(2024, 3, 1), -400, "food", "id four")
    ledger.add(dt.date(2024, 3, 20), -5000, "food", "id five")
    ledger.add(dt.date(2024, 3, 25), -6000, "rent", "id six")
    ledger.save(data_file)


def shown_ids(out):
    ids = []
    for line in out.splitlines()[1:]:
        first = line.split()[0] if line.split() else ""
        if first.isdigit():
            ids.append(int(first))
    return ids


def test_keeps_the_latest_rows_and_prints_them_oldest_first(run, ledger_file):
    code, out, _ = run("list", "--limit", "3")
    assert code == 0
    assert shown_ids(out) == [3, 5, 6]


def test_same_day_rows_are_cut_by_id(run, ledger_file):
    _, out, _ = run("list", "--limit", "4")
    assert shown_ids(out) == [1, 3, 5, 6]
    _, out, _ = run("list", "--limit", "5")
    assert shown_ids(out) == [2, 1, 3, 5, 6]


def test_total_line_covers_only_the_shown_rows(run, ledger_file):
    _, out, _ = run("list", "--limit", "2")
    assert out.splitlines()[-2] == "Total: -110.00 (2 transactions)"


def test_showing_line_is_last_when_rows_were_left_out(run, ledger_file):
    _, out, _ = run("list", "--limit", "2")
    assert out.splitlines()[-1] == "Showing 2 of 6"


def test_no_showing_line_when_everything_fits(run, ledger_file):
    for limit in ("6", "7", "100"):
        _, out, _ = run("list", "--limit", limit)
        assert "Showing" not in out
        assert out.splitlines()[-1].startswith("Total: ")
        assert len(shown_ids(out)) == 6


def test_filters_apply_before_the_limit(run, ledger_file):
    _, out, _ = run("list", "--category", "food", "--limit", "2")
    assert shown_ids(out) == [1, 5]
    assert out.splitlines()[-2] == "Total: -60.00 (2 transactions)"
    assert out.splitlines()[-1] == "Showing 2 of 4"


def test_limit_together_with_a_date_range(run, ledger_file):
    _, out, _ = run("list", "--from", "2024-03-05", "--to", "2024-03-21", "--limit", "1")
    assert shown_ids(out) == [5]
    assert out.splitlines()[-1] == "Showing 1 of 4"


@pytest.mark.parametrize("value", ["0", "-1", "-20"])
def test_limit_below_one_is_a_usage_error(run, ledger_file, value):
    code, out, err = run("list", "--limit", value)
    assert code == 2
    assert "--limit" in err
    assert out == ""


def test_limit_with_no_matching_rows_prints_no_showing_line(run, ledger_file):
    _, out, _ = run("list", "--category", "travel", "--limit", "3")
    assert out == "No transactions.\n"


def test_list_without_limit_is_unchanged(run, ledger_file):
    _, out, _ = run("list")
    assert shown_ids(out) == [4, 2, 1, 3, 5, 6]
    assert "Showing" not in out
