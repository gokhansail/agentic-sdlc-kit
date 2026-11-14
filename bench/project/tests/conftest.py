import datetime as dt
import os

import pytest

from budgetbook.ledger import Ledger


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    """Run every test in an empty folder with no BUDGETBOOK_* variables set."""
    monkeypatch.chdir(tmp_path)
    for name in list(os.environ):
        if name.startswith("BUDGETBOOK_"):
            monkeypatch.delenv(name)


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "ledger.json"


@pytest.fixture
def march_ledger():
    """A small ledger with March 2024 data and one transaction in April."""
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 1), 250000, "salary", "March salary")
    ledger.add(dt.date(2024, 3, 5), -4280, "food/groceries", "weekly shop")
    ledger.add(dt.date(2024, 3, 12), -1550, "food/eating out", "lunch")
    ledger.add(dt.date(2024, 3, 15), -90000, "housing", "rent")
    ledger.add(dt.date(2024, 4, 2), -999, "food/groceries", "milk")
    return ledger
