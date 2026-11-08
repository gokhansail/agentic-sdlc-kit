"""Tests for tools/events.py (T-41): reading the event file and the totals."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import events, scope_guard  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "server" / "events.jsonl"
SCRIPT = ROOT / "tools" / "events.py"


def project_with(tmp_path: Path, data: bytes | None) -> Path:
    if data is not None:
        (tmp_path / ".sdlc").mkdir(exist_ok=True)
        (tmp_path / ".sdlc" / "metrics.jsonl").write_bytes(data)
    return tmp_path


def line(**fields: object) -> str:
    base = {"agent": None, "date": "2026-11-08", "decision": "allow", "event": "scope",
            "state": "active", "task": "T-1", "tool": "Write"}
    base.update(fields)
    return json.dumps(base, sort_keys=True)


# --- reading -----------------------------------------------------------------------

def test_missing_file_gives_no_events(tmp_path: Path) -> None:
    assert events.read_events(tmp_path) == []
    got = events.totals(events.read_events(tmp_path))
    assert (got["allow"], got["deny"], got["tasks"], got["malformed"], got["other"]) == (0, 0, {}, 0, 0)


def test_blank_lines_are_skipped_and_unusable_lines_are_none(tmp_path: Path) -> None:
    text = "\n".join([line(), "", "   ", "not json", "[1]", "42", '"text"', "null", "{", line(task="T-2")]) + "\n"
    found = events.read_events(project_with(tmp_path, text.encode("utf-8")))
    assert [e is None for e in found] == [False, True, True, True, True, True, True, False]
    assert found[0] is not None and found[0]["task"] == "T-1"


def test_bom_and_crlf_are_accepted(tmp_path: Path) -> None:
    data = b"\xef\xbb\xbf" + (line() + "\r\n" + line(decision="deny") + "\r\n").encode("utf-8")
    got = events.totals(events.read_events(project_with(tmp_path, data)))
    assert (got["allow"], got["deny"], got["malformed"]) == (1, 1, 0)


def test_invalid_utf8_and_deep_nesting_count_as_malformed(tmp_path: Path) -> None:
    data = b"\xff\xfe broken\n" + b"[" * 200000 + b"\n" + line().encode("utf-8") + b"\n"
    found = events.read_events(project_with(tmp_path, data))
    assert [e is None for e in found] == [True, True, False]


def test_an_unreadable_event_file_raises_oserror(tmp_path: Path) -> None:
    (tmp_path / ".sdlc" / "metrics.jsonl").mkdir(parents=True)
    with pytest.raises(OSError):
        events.read_events(tmp_path)


# --- totals ------------------------------------------------------------------------

def fixture_events(tmp_path: Path) -> list:
    return events.read_events(project_with(tmp_path, FIXTURE.read_bytes()))


def test_totals_of_the_fixture(tmp_path: Path) -> None:
    got = events.totals(fixture_events(tmp_path))
    assert got["task"] is None
    assert (got["allow"], got["deny"], got["malformed"], got["other"]) == (4, 2, 3, 1)
    assert list(got["tasks"]) == ["T-77", "none"]
    t77 = got["tasks"]["T-77"]
    assert (t77["allow"], t77["deny"]) == (3, 1)
    assert t77["by_tool"] == {"Edit": {"allow": 1, "deny": 0}, "Write": {"allow": 2, "deny": 1}}
    assert t77["by_agent"] == {"developer": {"allow": 2, "deny": 1}, "main": {"allow": 1, "deny": 0}}
    none = got["tasks"]["none"]
    assert (none["allow"], none["deny"]) == (1, 1)
    assert none["by_agent"] == {"main": {"allow": 0, "deny": 1}, "scribe": {"allow": 1, "deny": 0}}
    assert none["by_tool"] == {"Edit": {"allow": 1, "deny": 1}}


def test_totals_for_one_task(tmp_path: Path) -> None:
    found = fixture_events(tmp_path)
    got = events.totals(found, "T-77")
    assert got["task"] == "T-77" and list(got["tasks"]) == ["T-77"]
    assert (got["allow"], got["deny"]) == (3, 1)
    assert got["tasks"]["T-77"] == events.totals(found)["tasks"]["T-77"]
    assert got["malformed"] == 3  # malformed lines belong to no task
    only_none = events.totals(found, "none")
    assert list(only_none["tasks"]) == ["none"] and (only_none["allow"], only_none["deny"]) == (1, 1)
    unknown = events.totals(found, "T-999")
    assert unknown["tasks"] == {} and (unknown["allow"], unknown["deny"]) == (0, 0)


def test_totals_name_a_missing_agent_main_and_a_missing_tool_unknown() -> None:
    got = events.totals([json.loads(line(tool=None, agent=None))])
    row = got["tasks"]["T-1"]
    assert row["by_agent"] == {"main": {"allow": 1, "deny": 0}}
    assert row["by_tool"] == {"unknown": {"allow": 1, "deny": 0}}


@pytest.mark.parametrize("bad", [
    {"decision": "maybe"}, {"decision": None}, {"decision": 1}, {"task": 5}, {"task": ["T-1"]},
    {"tool": 3}, {"agent": {"x": 1}},
])
def test_a_scope_event_with_an_unusable_field_is_malformed(bad: dict) -> None:
    got = events.totals([json.loads(line(**bad))])
    assert (got["malformed"], got["allow"], got["deny"], got["tasks"]) == (1, 0, 0, {})


def test_another_event_kind_is_counted_as_other() -> None:
    got = events.totals([{"event": "note"}, {"decision": "allow"}, json.loads(line())])
    assert (got["other"], got["malformed"], got["allow"]) == (2, 0, 1)


def test_totals_do_not_change_the_input() -> None:
    items = [json.loads(line()), None]
    before = json.dumps(items)
    events.totals(items, "T-1")
    assert json.dumps(items) == before


def test_totals_match_lines_written_by_the_guard(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir()
    for allow, task, agent in ((True, "T-5", None), (False, "T-5", "developer"), (True, None, "scribe")):
        decision = scope_guard.Decision(allow, "active" if task else "no-contract", "r", "", task, "a.py")
        scope_guard.log_event(tmp_path, decision, "Write", agent, "2026-11-08")
    got = events.totals(events.read_events(tmp_path))
    assert (got["allow"], got["deny"], got["malformed"], got["other"]) == (2, 1, 0, 0)
    assert got["tasks"]["T-5"]["by_agent"] == {"developer": {"allow": 0, "deny": 1}, "main": {"allow": 1, "deny": 0}}
    assert got["tasks"]["none"]["by_agent"] == {"scribe": {"allow": 1, "deny": 0}}


# --- command line --------------------------------------------------------------------

def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL)


def test_cli_prints_the_totals_as_json(tmp_path: Path) -> None:
    root = project_with(tmp_path, FIXTURE.read_bytes())
    res = run_cli("--root", str(root))
    assert res.returncode == 0 and res.stderr == ""
    assert json.loads(res.stdout) == events.totals(events.read_events(root))
    one = run_cli("--root", str(root), "--task", "T-77")
    assert json.loads(one.stdout) == events.totals(events.read_events(root), "T-77")


def test_cli_prints_no_path(tmp_path: Path) -> None:
    root = project_with(tmp_path, FIXTURE.read_bytes())
    out = run_cli("--root", str(root)).stdout
    assert str(root) not in out and root.name not in out and ".jsonl" not in out


def test_cli_on_a_folder_without_events_prints_zero_totals(tmp_path: Path) -> None:
    res = run_cli("--root", str(tmp_path))
    assert res.returncode == 0
    assert json.loads(res.stdout)["tasks"] == {}


def test_cli_reports_an_unreadable_file_without_a_path(tmp_path: Path) -> None:
    (tmp_path / ".sdlc" / "metrics.jsonl").mkdir(parents=True)
    res = run_cli("--root", str(tmp_path))
    assert res.returncode == 1 and res.stdout == ""
    assert res.stderr.strip() == "events: cannot read the event file"


def test_the_module_is_standard_library_only() -> None:
    import ast

    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert names <= set(sys.stdlib_module_names) | {"tools"}
