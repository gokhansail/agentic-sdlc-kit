"""Tests for tools/bench_table.py (T-57): fixture totals files, no model call, no network."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import bench_table as bt  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "bench_table"
FILE_A, FILE_B = FIX / "fx-a.json", FIX / "fx-b.json"
EXPECTED = (FIX / "expected.txt").read_text(encoding="utf-8").rstrip("\n")
DOC = f"# T\n\ntext before\n{bt.START}\nold\n{bt.END}\ntext after\n"


def make_doc(tmp_path: Path, text: str = DOC) -> Path:
    path = tmp_path / "doc.md"
    path.write_bytes(text.encode("utf-8"))
    return path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(tmp_path: Path, data: dict, name: str = "t.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def run(doc: Path, *files: Path) -> int:
    return bt.main(["--doc", str(doc), *[str(f) for f in files]])


def test_fixture_renders_to_expected_text(tmp_path: Path) -> None:
    doc = make_doc(tmp_path)
    assert run(doc, FILE_A, FILE_B) == 0
    new = doc.read_bytes().decode("utf-8")
    assert new == f"# T\n\ntext before\n{bt.START}\n{EXPECTED}\n{bt.END}\ntext after\n"


def test_second_run_is_byte_equal(tmp_path: Path) -> None:
    doc = make_doc(tmp_path)
    run(doc, FILE_A, FILE_B)
    first = doc.read_bytes()
    assert run(doc, FILE_A, FILE_B) == 0
    assert doc.read_bytes() == first


def test_text_outside_markers_is_untouched(tmp_path: Path) -> None:
    before, after = "# T\r\n\r\nbefore é\r\n", "\r\nafter  \r\nlast"
    doc = make_doc(tmp_path, f"{before}{bt.START}\r\nold\r\n{bt.END}{after}")
    assert run(doc, FILE_A) == 0
    new = doc.read_bytes().decode("utf-8")
    assert new.startswith(before + bt.START) and new.endswith(bt.END + after)
    assert "\r\n" in new and "\n" not in new.replace("\r\n", "")


def test_file_order_is_kept(tmp_path: Path) -> None:
    doc = make_doc(tmp_path)
    run(doc, FILE_B, FILE_A)
    text = doc.read_text(encoding="utf-8")
    assert text.index("Label fx-b") < text.index("Label fx-a")


def test_missing_test_change_key_shows_dash() -> None:
    block = bt.render_block([load(FILE_B)])
    assert "| fx-b | plain | 0 of 1 | 3 of 7 | 0 of 1 | 0 of 1 | - | 1 |" in block


def test_no_verdict_words() -> None:
    block = bt.render_block([load(FILE_A), load(FILE_B)]).lower()
    for word in ("better", "worse", "win", "ratio", "improve", "%", "faster"):
        assert word not in block


def test_unknown_arm_sorts_after_known_arms() -> None:
    data = load(FILE_A)
    data["arms"]["zeta"] = copy.deepcopy(data["arms"]["kit"])
    for task in data["task_ids"]:
        data["tasks"][task]["zeta"] = copy.deepcopy(data["tasks"][task]["kit"])
    rows = [ln for ln in bt.table_one([data]).splitlines() if ln.startswith("| fx-a")]
    assert [r.split(" | ")[1] for r in rows] == ["plain", "kit", "zeta"]


def _bad_schema(d: dict) -> None:
    d["schema"] = 2


def _incomplete(d: dict) -> None:
    d["complete"] = False


def _missing_top(d: dict) -> None:
    del d["spent_usd"]


def _missing_arm_key(d: dict) -> None:
    del d["arms"]["kit"]["guard_deny"]


def _missing_task_key(d: dict) -> None:
    del d["tasks"]["B2"]["plain"]["cost_usd_per_run"]


def _missing_task_cell(d: dict) -> None:
    del d["tasks"]["B1"]["kit"]


def _missing_task(d: dict) -> None:
    del d["tasks"]["B2"]


@pytest.mark.parametrize("mutate", [_bad_schema, _incomplete, _missing_top, _missing_arm_key,
                                    _missing_task_key, _missing_task_cell, _missing_task])
def test_bad_totals_exit_2_and_nothing_written(tmp_path: Path, mutate) -> None:
    data = load(FILE_A)
    mutate(data)
    bad = write_json(tmp_path, data)
    doc = make_doc(tmp_path)
    assert run(doc, FILE_B, bad) == 2
    assert doc.read_bytes() == DOC.encode("utf-8")


def test_unreadable_json_exit_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    doc = make_doc(tmp_path)
    assert run(doc, bad) == 2
    assert run(doc, tmp_path / "absent.json") == 2
    assert doc.read_bytes() == DOC.encode("utf-8")


@pytest.mark.parametrize("text", [
    "no markers\n",
    f"{bt.START}\nonly start\n",
    f"{bt.END}\nonly end\n",
    f"{bt.START}\na\n{bt.END}\n{bt.START}\nb\n{bt.END}\n",
    f"{bt.END}\nx\n{bt.START}\n",
])
def test_marker_errors_exit_2_and_nothing_written(tmp_path: Path, text: str) -> None:
    doc = make_doc(tmp_path, text)
    assert run(doc, FILE_A) == 2
    assert doc.read_bytes() == text.encode("utf-8")


def test_doc_not_readable_exit_2(tmp_path: Path) -> None:
    assert run(tmp_path / "absent.md", FILE_A) == 2


@pytest.mark.parametrize("name", ["check-2.json", "smoke-2.json"])
def test_real_sample_files_render(tmp_path: Path, name: str) -> None:
    sample = ROOT / "bench" / "results" / name
    if not sample.exists():
        pytest.skip("sample file not present")
    doc = make_doc(tmp_path)
    assert run(doc, sample) == 0
    text = doc.read_text(encoding="utf-8")
    assert f"Label {load(sample)['label']};" in text
    assert "| - |" in text  # the sample predates the test-change keys
