import datetime as dt
import os

import pytest

from budgetbook.ledger import Ledger
from budgetbook.models import RecurringItem


def day(text):
    return dt.date.fromisoformat(text)


def march_ledger():
    """The ledger of the visible suite: March 2024 and one booking in April."""
    ledger = Ledger()
    ledger.add(day("2024-03-01"), 250000, "salary", "March salary")
    ledger.add(day("2024-03-05"), -4280, "food/groceries", "weekly shop")
    ledger.add(day("2024-03-12"), -1550, "food/eating out", "lunch")
    ledger.add(day("2024-03-15"), -90000, "housing", "rent")
    ledger.add(day("2024-04-02"), -999, "food/groceries", "milk")
    return ledger


def rich_ledger():
    """March plus February bookings, two more accounts, a long description with a comma and
    quotes, an empty description, three budgets and four recurring items."""
    ledger = march_ledger()
    ledger.add(day("2024-02-10"), -80000, "housing", "rent")
    ledger.add(day("2024-02-14"), -5000, "food/groceries", "February shop", "cash")
    ledger.add(day("2024-03-20"), 30000, "gifts", "Birthday money, from grandma", "cash")
    ledger.add(day("2024-03-22"), -6425, "transport", 'Monthly pass "city zone" extended to next month', "cash")
    ledger.add(day("2024-03-28"), -2000, "savings", "", "savings")
    ledger.budgets.update({"food": 40000, "housing": 100000, "eating out": 10000})
    ledger.recurring.append(RecurringItem("rent", -90000, "housing", "monthly", day("2024-01-31")))
    ledger.recurring.append(RecurringItem("gym", -3000, "health", "weekly", day("2024-02-02"), None, "cash"))
    ledger.recurring.append(RecurringItem("salary", 250000, "salary", "monthly", day("2024-01-01"), None, "bank"))
    ledger.recurring.append(RecurringItem("insurance", -48000, "insurance", "yearly", day("2023-02-15")))
    return ledger


def description_lengths_ledger():
    """Descriptions of 30, 31 and 60 characters."""
    ledger = Ledger()
    ledger.add(day("2024-06-01"), -100, "food", "abcdefghijklmnopqrstuvwxyz0123")
    ledger.add(day("2024-06-02"), -200, "food", "abcdefghijklmnopqrstuvwxyz01234")
    ledger.add(day("2024-06-03"), -300, "food", "x" * 60)
    return ledger


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    """Empty working folder, no BUDGETBOOK_* variables."""
    monkeypatch.chdir(tmp_path)
    for name in list(os.environ):
        if name.startswith("BUDGETBOOK_"):
            monkeypatch.delenv(name)


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "ledger.json"


@pytest.fixture
def run(capsys, data_file):
    """Run the CLI against the data file; returns (exit code, stdout, stderr)."""
    from budgetbook.cli import main

    def _run(*args):
        try:
            code = main(["--data", str(data_file), *args])
        except SystemExit as exit_info:
            code = exit_info.code
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run


@pytest.fixture
def march(data_file):
    march_ledger().save(data_file)
    return data_file


@pytest.fixture
def rich(data_file):
    rich_ledger().save(data_file)
    return data_file


@pytest.fixture
def lengths(data_file):
    description_lengths_ledger().save(data_file)
    return data_file
