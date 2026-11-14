import datetime as dt
import json
import os

import pytest

from budgetbook.errors import LedgerFileError, NotFoundError
from budgetbook.ledger import Ledger


def test_add_assigns_increasing_ids_and_normalizes_the_category():
    ledger = Ledger()
    first = ledger.add(dt.date(2024, 3, 5), -100, "Eating Out", " lunch ")
    second = ledger.add(dt.date(2024, 3, 6), -200, "food")
    assert (first.id, second.id) == (1, 2)
    assert first.category == "eating out"
    assert first.description == "lunch"


def test_ids_are_not_reused_after_a_remove():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -100, "food")
    ledger.remove(1)
    assert ledger.add(dt.date(2024, 3, 6), -100, "food").id == 2


def test_get_and_remove_unknown_id():
    ledger = Ledger()
    with pytest.raises(NotFoundError):
        ledger.get(7)
    with pytest.raises(NotFoundError):
        ledger.remove(7)


def test_all_is_ordered_by_date_then_id():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 9), -1, "a")
    ledger.add(dt.date(2024, 3, 2), -1, "b")
    ledger.add(dt.date(2024, 3, 2), -1, "c")
    assert [tx.category for tx in ledger.all()] == ["b", "c", "a"]


def test_between_with_both_bounds(march_ledger):
    found = march_ledger.between(dt.date(2024, 3, 1), dt.date(2024, 3, 31))
    assert [tx.date.day for tx in found] == [1, 5, 12, 15]


def test_between_includes_the_start_day_and_leaves_open_sides_open(march_ledger):
    assert [tx.date.day for tx in march_ledger.between(dt.date(2024, 3, 5), None)] == [5, 12, 15, 2]
    assert [tx.date.day for tx in march_ledger.between(None, dt.date(2024, 3, 14))] == [1, 5, 12]


def test_in_month_covers_the_whole_month(march_ledger):
    assert len(march_ledger.in_month(2024, 3)) == 4
    assert len(march_ledger.in_month(2024, 4)) == 1
    assert march_ledger.in_month(2024, 5) == []


def test_save_and_load_round_trip(march_ledger, data_file):
    march_ledger.budgets["food"] = 40000
    march_ledger.save(data_file)
    loaded = Ledger.load(data_file)
    assert loaded.to_dict() == march_ledger.to_dict()
    assert loaded.add(dt.date(2024, 5, 1), -1, "x").id == 6


def test_saved_file_format(data_file):
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -4280, "food", "shop")
    ledger.save(data_file)
    data = json.loads(data_file.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["transactions"][0]["amount"] == -4280
    assert data_file.read_text(encoding="utf-8").endswith("}\n")


def test_load_missing_file_gives_an_empty_ledger(tmp_path):
    assert len(Ledger.load(tmp_path / "nope.json")) == 0


def test_load_rejects_bad_files(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(LedgerFileError):
        Ledger.load(broken)
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"version": 2}), encoding="utf-8")
    with pytest.raises(LedgerFileError):
        Ledger.load(wrong)
    listing = tmp_path / "list.json"
    listing.write_text("[]", encoding="utf-8")
    with pytest.raises(LedgerFileError):
        Ledger.load(listing)


def test_save_creates_missing_folders(tmp_path):
    target = tmp_path / "deep" / "er" / "ledger.json"
    Ledger().save(target)
    assert target.is_file()


def test_failed_save_keeps_the_old_file_and_leaves_no_temp_file(tmp_path, monkeypatch, march_ledger):
    target = tmp_path / "ledger.json"
    Ledger().save(target)
    before = target.read_bytes()

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        march_ledger.save(target)
    assert target.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["ledger.json"]
