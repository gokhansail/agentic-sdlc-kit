"""Tests for tools/eval_table.py (T-46f): fixture totals file, no model call, no network."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import eval_table as et  # noqa: E402

DOC = f"# T\n\ntext before\n{et.START}\nold\n{et.END}\ntext after\n"


def group(model: str, condition: str, correct: int, calls: dict[str, int]) -> dict:
    return {
        "model": model, "condition": condition, "runs": 6, "correct": correct,
        "accuracy_mean": 0.8333333, "accuracy_min": 0.75, "accuracy_max": 1.0,
        "by_category": {"tasks": {"correct": 3, "total": 4}, "guard": {"correct": 2, "total": 2}},
        "cost_usd": 1.23456, "cost_usd_per_run": 0.20576, "output_tokens": 1000,
        "duration_ms_per_run": 12345.6, "turns_per_run": 3.2666, "tool_calls_total": sum(calls.values()),
        "tool_calls": calls, "errors": 1, "unparsed": 0,
    }


def totals() -> dict:
    return {
        "schema": 2, "label": "fx", "date": "2026-01-01", "cli_version": "9.9.9 (Claude Code)",
        "git_commit": "0123456789abcdef0123", "git_dirty": False, "repeats": 3,
        "settings": {"max_turns": 12, "restricted": True}, "complete": True,
        "groups": [
            group("sonnet", "server", 5, {"Read": 2, "mcp__sdlc__status": 3, "mcp__sdlc__tasks": 4}),
            group("haiku", "no-server", 4, {"Read": 7}),
        ],
    }


def setup(tmp_path: Path, data: dict, doc: str = DOC) -> tuple[Path, Path]:
    totals_path = tmp_path / "t.json"
    doc_path = tmp_path / "d.md"
    totals_path.write_text(json.dumps(data), encoding="utf-8")
    doc_path.write_bytes(doc.encode("utf-8"))
    return totals_path, doc_path


def run(totals_path: Path, doc_path: Path) -> int:
    return et.main(["--doc", str(doc_path), str(totals_path)])


def test_render_and_second_render_no_diff(tmp_path):
    t, d = setup(tmp_path, totals())
    assert run(t, d) == 0
    first = d.read_bytes()
    text = first.decode()
    assert text.startswith("# T\n\ntext before\n" + et.START) and text.endswith(et.END + "\ntext after\n")
    assert "old" not in text
    assert run(t, d) == 0
    assert d.read_bytes() == first


def test_values_and_server_tool_sum(tmp_path):
    t, d = setup(tmp_path, totals())
    run(t, d)
    rows = [[c.strip() for c in l.strip("|").split("|")] for l in d.read_text().splitlines() if l.startswith("| ")]
    wide = {(r[0], r[1]): r for r in rows if len(r) == 17}
    haiku, sonnet = wide[("haiku", "no-server")], wide[("sonnet", "server")]
    # Sorted by model: haiku first. Columns: correct 3, cost 9, duration 12, turns 13, total 14, server 15, Read 16.
    assert haiku[3] == "4" and haiku[9] == "1.235" and haiku[10] == "0.2058"
    assert haiku[12] == "12.3" and haiku[13] == "3.27" and haiku[15] == "0" and haiku[16] == "7"
    assert sonnet[3] == "5" and sonnet[14] == "9" and sonnet[15] == "7" and sonnet[16] == "2"
    assert sonnet[4] == "0.833"
    assert "| sonnet | server | 3 of 4 | 2 of 2 |" not in d.read_text()  # category columns are sorted: guard first
    assert "| sonnet | server | 2 of 2 | 3 of 4 |" in d.read_text()
    assert "Label fx; date 2026-01-01; CLI 9.9.9 (Claude Code); runner commit 0123456789ab; git_dirty false; repeats 3; settings: max_turns 12, restricted true." in d.read_text()


def refuse(tmp_path, data, doc=DOC):
    t, d = setup(tmp_path, data, doc)
    before = d.read_bytes()
    assert run(t, d) == 2
    assert d.read_bytes() == before


def test_refuse_incomplete(tmp_path):
    data = totals()
    data["complete"] = False
    refuse(tmp_path, data)


def test_refuse_schema(tmp_path):
    data = totals()
    data["schema"] = 1
    refuse(tmp_path, data)


def test_refuse_missing_top_key(tmp_path):
    data = totals()
    del data["label"]
    refuse(tmp_path, data)


def test_refuse_missing_group_key(tmp_path):
    data = copy.deepcopy(totals())
    del data["groups"][0]["tool_calls"]
    refuse(tmp_path, data)


@pytest.mark.parametrize("doc", [
    "no markers\n",
    f"{et.START}\nonly start\n",
    f"{et.START}\n{et.END}\n{et.START}\n{et.END}\n",
    f"{et.END}\n{et.START}\n",
])
def test_refuse_bad_markers(tmp_path, doc):
    refuse(tmp_path, totals(), doc)


def test_refuse_unreadable_json(tmp_path):
    t, d = setup(tmp_path, totals())
    t.write_text("{not json", encoding="utf-8")
    before = d.read_bytes()
    assert run(t, d) == 2
    assert d.read_bytes() == before


def test_crlf_document_kept(tmp_path):
    t, d = setup(tmp_path, totals(), DOC.replace("\n", "\r\n"))
    assert run(t, d) == 0
    raw = d.read_bytes()
    assert b"\n" not in raw.replace(b"\r\n", b"")
    assert run(t, d) == 0 and d.read_bytes() == raw


def test_full_2_rendered_values(tmp_path):
    source = ROOT / "eval" / "results" / "full-2.json"
    if not source.exists():
        pytest.skip("full-2.json not present")
    d = tmp_path / "d.md"
    d.write_text(DOC, encoding="utf-8")
    assert et.main(["--doc", str(d), str(source)]) == 0
    rows = {}
    for line in d.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if line.startswith("| ") and len(cells) == 17 and cells[0] in ("sonnet", "haiku"):
            rows[(cells[0], cells[1])] = cells
    assert rows[("sonnet", "server")][3] == "90" and rows[("sonnet", "server")][9] == "0.785"
    assert rows[("haiku", "server")][3] == "83" and rows[("haiku", "server")][15] == "40"
