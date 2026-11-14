import ast
import datetime as dt
import json
import os
from pathlib import Path

import pytest

from budgetbook.errors import LedgerFileError
from budgetbook.ledger import Ledger

ROOT = Path(__file__).resolve().parents[1]

# The file written by Ledger.save for the ledger built in golden_ledger(), as before the refactor.
GOLDEN = (
    "{\n"
    '  "budgets": {\n'
    '    "food": 40000\n'
    "  },\n"
    '  "next_id": 2,\n'
    '  "recurring": [],\n'
    '  "transactions": [\n'
    "    {\n"
    '      "account": "main",\n'
    '      "amount": -4280,\n'
    '      "category": "food",\n'
    '      "date": "2024-03-05",\n'
    '      "description": "café shop",\n'
    '      "id": 1\n'
    "    }\n"
    "  ],\n"
    '  "version": 1\n'
    "}\n"
)


def storage_module():
    import budgetbook.storage as storage

    return storage


def golden_ledger():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -4280, "food", "café shop")
    ledger.budgets["food"] = 40000
    return ledger


def test_storage_is_abstract():
    storage = storage_module()
    with pytest.raises(TypeError):
        storage.Storage()

    class OnlyLoad(storage.Storage):
        def load(self):
            return None

    with pytest.raises(TypeError):
        OnlyLoad()


def test_a_custom_storage_works_with_the_ledger():
    storage = storage_module()

    class ListStorage(storage.Storage):
        def __init__(self):
            self.saved = []

        def load(self):
            return self.saved[-1] if self.saved else None

        def save(self, data):
            self.saved.append(data)

    backend = ListStorage()
    assert len(Ledger.from_storage(backend)) == 0
    assert golden_ledger().save_to(backend) is None
    again = Ledger.from_storage(backend)
    assert again.to_dict() == golden_ledger().to_dict()


def test_memory_storage_starts_empty_and_keeps_copies():
    storage = storage_module()
    memory = storage.MemoryStorage()
    assert memory.load() is None
    data = {"version": 1, "transactions": [], "note": ["a"]}
    memory.save(data)
    data["note"].append("changed after save")
    first = memory.load()
    assert first == {"version": 1, "transactions": [], "note": ["a"]}
    first["note"].append("changed after load")
    assert memory.load()["note"] == ["a"]


def test_a_ledger_round_trips_through_memory_storage():
    storage = storage_module()
    memory = storage.MemoryStorage()
    ledger = golden_ledger()
    ledger.save_to(memory)
    assert memory.load() == ledger.to_dict()
    assert Ledger.from_storage(memory).to_dict() == ledger.to_dict()


def test_from_storage_checks_the_format_version():
    storage = storage_module()
    memory = storage.MemoryStorage()
    memory.save({"version": 2})
    with pytest.raises(LedgerFileError):
        Ledger.from_storage(memory)


def test_json_file_storage_missing_file_loads_none(tmp_path):
    storage = storage_module()
    assert storage.JsonFileStorage(tmp_path / "nothing.json").load() is None


def test_json_file_storage_writes_the_same_bytes_as_before(tmp_path):
    storage = storage_module()
    target = tmp_path / "ledger.json"
    golden_ledger().save_to(storage.JsonFileStorage(target))
    assert target.read_bytes() == GOLDEN.encode("utf-8")
    other = tmp_path / "other.json"
    golden_ledger().save(other)
    assert other.read_bytes() == GOLDEN.encode("utf-8")


def test_json_file_storage_round_trip_and_new_folders(tmp_path):
    storage = storage_module()
    target = tmp_path / "a" / "b" / "ledger.json"
    backend = storage.JsonFileStorage(target)
    backend.save({"version": 1, "x": [1, 2]})
    assert backend.load() == {"version": 1, "x": [1, 2]}
    assert json.loads(target.read_text(encoding="utf-8")) == {"version": 1, "x": [1, 2]}


@pytest.mark.parametrize("content", ["{not json", "", "[1, 2]", '"text"'])
def test_json_file_storage_rejects_bad_files(tmp_path, content):
    storage = storage_module()
    broken = tmp_path / "broken.json"
    broken.write_text(content, encoding="utf-8")
    with pytest.raises(LedgerFileError) as info:
        storage.JsonFileStorage(broken).load()
    assert "broken.json" in str(info.value)


def test_a_failed_write_keeps_the_old_file_and_leaves_no_temp_file(tmp_path, monkeypatch):
    storage = storage_module()
    target = tmp_path / "ledger.json"
    backend = storage.JsonFileStorage(target)
    backend.save({"version": 1, "old": True})
    before = target.read_bytes()

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        backend.save({"version": 1, "new": True})
    assert target.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["ledger.json"]


def test_ledger_load_and_save_still_work_as_before(tmp_path):
    target = tmp_path / "ledger.json"
    golden_ledger().save(target)
    loaded = Ledger.load(target)
    assert loaded.to_dict() == golden_ledger().to_dict()
    assert len(Ledger.load(tmp_path / "missing.json")) == 0
    broken = tmp_path / "broken.json"
    broken.write_text("{nope", encoding="utf-8")
    with pytest.raises(LedgerFileError):
        Ledger.load(broken)


def test_the_ledger_module_no_longer_touches_files():
    tree = ast.parse((ROOT / "budgetbook" / "ledger.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    assert not imported & {"json", "os", "tempfile", "shutil"}
    calls = [n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    assert "open" not in calls


def test_the_command_line_still_works_end_to_end(run, data_file):
    assert run("add", "2024-03-05", "-42.80", "food", "shop")[0] == 0
    code, out, _ = run("list")
    assert code == 0
    assert out.splitlines()[-1] == "Total: -42.80 (1 transaction)"
    assert Ledger.load(data_file).get(1).description == "shop"
