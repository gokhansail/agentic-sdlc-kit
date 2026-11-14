import datetime as dt

import pytest

from budgetbook.budgets import set_budget
from budgetbook.categories import normalize_category
from budgetbook.csvio import import_csv
from budgetbook.errors import CategoryError
from budgetbook.filters import select
from budgetbook.ledger import Ledger
from budgetbook.reports import monthly_report


@pytest.mark.parametrize(
    "name",
    ["food/groceries", "Food / Groceries", "food/ groceries", "FOOD /groceries", "  food   /   groceries  ", "food\t/\tgroceries"],
)
def test_spaces_around_the_separator_do_not_matter(name):
    assert normalize_category(name) == "food/groceries"


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Eating  Out", "eating out"),
        ("Eating Out / Cafe", "eating out/cafe"),
        ("  EATING   OUT/ Late   Night ", "eating out/late night"),
        ("home/ pets / vet bills", "home/pets/vet bills"),
    ],
)
def test_spaces_inside_a_name_are_kept_as_one_space(name, expected):
    assert normalize_category(name) == expected


@pytest.mark.parametrize("name", ["", "  ", "food//x", "food / / x", "/food", "food /", " / ", "a/ /b"])
def test_empty_names_and_empty_parts_are_rejected(name):
    with pytest.raises(CategoryError):
        normalize_category(name)


def test_the_report_has_one_line_for_a_category_typed_with_add(run, data_file):
    run("add", "2024-03-05", "-10.00", "food/groceries")
    run("add", "2024-03-06", "-5.50", "Food / Groceries")
    run("add", "2024-03-07", "-2.25", "food /groceries")
    code, out, _ = run("report", "2024-03")
    assert code == 0
    category_lines = [line for line in out.splitlines() if line.startswith("  ")]
    assert category_lines == ["  food/groceries: -17.75"]


def test_the_report_has_one_line_after_a_csv_import(data_file):
    ledger = Ledger()
    text = (
        "date,amount,category\n"
        "2024-03-05,-10.00,food/groceries\n"
        "2024-03-06,-5.50,Food / Groceries\n"
        "2024-03-07,-1.00,Eating  Out / Cafe\n"
        "2024-03-08,-2.00,eating out/cafe\n"
    )
    assert import_csv(ledger, text) == 4
    assert monthly_report(ledger, 2024, 3).by_category == {"eating out/cafe": -300, "food/groceries": -1550}


def test_names_stored_by_an_older_version_are_grouped_too():
    ledger = Ledger.from_dict(
        {
            "version": 1,
            "transactions": [
                {"id": 1, "date": "2024-03-05", "amount": -1000, "category": "Food / Groceries"},
                {"id": 2, "date": "2024-03-06", "amount": -550, "category": "food/groceries"},
                {"id": 3, "date": "2024-03-07", "amount": -100, "category": "FOOD/ groceries"},
            ],
        }
    )
    assert monthly_report(ledger, 2024, 3).by_category == {"food/groceries": -1650}


def test_a_budget_is_stored_under_the_same_name(data_file):
    ledger = Ledger()
    assert set_budget(ledger, "Eating Out / Cafe", 5000) == "eating out/cafe"
    assert set_budget(ledger, "food /groceries", 20000) == "food/groceries"
    assert ledger.budgets == {"eating out/cafe": 5000, "food/groceries": 20000}


def test_a_category_filter_finds_names_typed_with_spaces():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -100, "food/groceries")
    ledger.add(dt.date(2024, 3, 6), -200, "Food / Groceries / Organic")
    ledger.add(dt.date(2024, 3, 7), -300, "food/eating out")
    found = select(ledger.all(), category="Food / Groceries")
    assert [tx.amount for tx in found] == [-100, -200]


def test_a_name_with_spaces_inside_a_part_survives_the_command_line(run, data_file):
    run("add", "2024-03-05", "-4.00", "Eating  Out")
    _, out, _ = run("list")
    assert "eating out" in out
