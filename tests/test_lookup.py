"""Tests for tools/lookup.py: the decision, lesson, finding, task and log readers (T-42).

Fixtures are in tests/fixtures/server/lookup/ (one file per record, in the template format).
Projects are copied into pytest temp dirs. The last group parses this repository's own records.
"""
from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import lookup  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "server" / "lookup"


def project(base: Path, records: str | None = None) -> Path:
    """A copy of the record fixtures; `records` is the body of `## Records` in `.sdlc/project.md`."""
    root = base / "p"
    shutil.copytree(FIXTURES, root)
    if records is not None:
        (root / ".sdlc").mkdir()
        (root / ".sdlc" / "project.md").write_text("# Project file\n\n## Records\n" + records, encoding="utf-8")
    return root


def bare(base: Path, **files: str) -> Path:
    """A project with only the given record files (name -> text), at the default names."""
    root = base / "b"
    root.mkdir(parents=True)
    for name, text in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    return root


# --- decisions -------------------------------------------------------------------------

def test_decisions_list(tmp_path: Path) -> None:
    got = lookup.decisions(project(tmp_path))
    assert got["source"] == "DECISIONS.md" and got["error"] == ""
    assert (got["total"], got["matched"], got["unreadable"], got["truncated"]) == (4, 4, 0, False)
    rows = got["items"]
    assert [r["id"] for r in rows] == ["DEC-001", "DEC-002", "DEC-003", "DEC-010"]  # both heading levels
    assert [r["title"] for r in rows][:2] == ["Pick the storage format", "Cache the parsed records"]
    assert [r["date"] for r in rows] == ["2026-01-05", "2026-01-07", "2026-01-09", "2026-01-15"]
    assert [r["outcome_filled"] for r in rows] == [True, False, False, True]  # empty and placeholder are not filled
    assert all("fields" not in r for r in rows)


def test_decisions_name_the_later_decisions_that_mention_them(tmp_path: Path) -> None:
    rows = {r["id"]: r for r in lookup.decisions(project(tmp_path))["items"]}
    assert rows["DEC-001"]["named_by"] == ["DEC-002", "DEC-010"]  # "DEC-1" counts; DEC-100 does not
    assert rows["DEC-002"]["named_by"] == ["DEC-010"]  # DEC-001 names DEC-002 but is earlier
    assert rows["DEC-003"]["named_by"] == [] and rows["DEC-010"]["named_by"] == []


def test_decisions_by_id_gives_all_fields(tmp_path: Path) -> None:
    root = project(tmp_path)
    got = lookup.decisions(root, "dec-2")  # case and zero padding do not matter
    assert got["matched"] == 1 and got["id"] == "dec-2"
    (item,) = got["items"]
    assert item["id"] == "DEC-002" and item["cut"] is False
    assert list(item["fields"]) == ["Date", "Options", "Decision", "Reason", "Consequences", "Outcome"]
    assert item["fields"]["Date"].startswith("2026-01-07") and "Question: D-2" in item["fields"]["Date"]
    assert item["fields"]["Consequences"] == "- no cache to invalidate\n- the reader parses on every call"
    assert item["fields"]["Outcome"] == ""
    ten = lookup.decisions(root, "DEC-010")["items"][0]
    assert ten["fields"]["Outcome"] == "reviewed 2026-01-20,\nthe cache is still not needed."
    assert lookup.decisions(root, "DEC-3")["items"][0]["title"] == "Answer limit"


def test_decisions_unknown_id_is_an_empty_answer(tmp_path: Path) -> None:
    got = lookup.decisions(project(tmp_path), "DEC-999")
    assert got["items"] == [] and got["matched"] == 0 and got["error"] == "" and got["total"] == 4


def test_decisions_query_needs_every_word(tmp_path: Path) -> None:
    root = project(tmp_path)
    ids = lambda q: [r["id"] for r in lookup.decisions(root, None, q)["items"]]  # noqa: E731
    assert ids("cache") == ["DEC-001", "DEC-002", "DEC-010"]
    assert ids("PLAIN files") == ["DEC-001"]
    assert ids("plain cache") == ["DEC-001"]
    assert ids("zebra") == []
    assert ids("   ") == ["DEC-001", "DEC-002", "DEC-003", "DEC-010"]
    assert lookup.decisions(root, "DEC-002", "plain")["items"] == []  # id and query both apply


def test_decisions_count_an_unreadable_entry(tmp_path: Path) -> None:
    text = ("## DEC-001 Good\n- Date: 2026-01-01\n\n## No id here\n- Date: 2026-01-02\n- Decision: a\n\n"
            "## DEC-003 No date\n- Decision: a\n\n## Plain section\nsome words\n\n## DEC-005 Bad date\n- Date: 2026-13-45\n")
    got = lookup.decisions(bare(tmp_path, **{"DECISIONS.md": text}))
    assert [r["id"] for r in got["items"]] == ["DEC-001"] and got["total"] == 1
    assert got["unreadable"] == 3
    assert got["unreadable_headings"] == ["No id here", "DEC-003 No date", "DEC-005 Bad date"]  # a plain section is not an entry


def test_decisions_ignore_a_heading_inside_a_code_fence(tmp_path: Path) -> None:
    text = "## DEC-001 One\n- Date: 2026-01-01\n```\n## DEC-002 Not a heading\n```\n"
    got = lookup.decisions(bare(tmp_path, **{"DECISIONS.md": text}))
    assert [r["id"] for r in got["items"]] == ["DEC-001"] and got["unreadable"] == 0


def test_decisions_limit_100_items_and_the_truncated_flag(tmp_path: Path) -> None:
    text = "".join(f"## DEC-{i:03d} Title {i}\n- Date: 2026-01-01\n- Outcome:\n\n" for i in range(1, 106))
    got = lookup.decisions(bare(tmp_path, **{"DECISIONS.md": text}))
    assert len(got["items"]) == 100 and got["matched"] == 105 and got["total"] == 105 and got["truncated"] is True
    assert got["items"][-1]["id"] == "DEC-100"
    exact = "".join(f"## DEC-{i:03d} Title\n- Date: 2026-01-01\n\n" for i in range(1, 101))
    assert lookup.decisions(bare(tmp_path / "x", **{"DECISIONS.md": exact}))["truncated"] is False


def test_decisions_cut_a_very_long_field(tmp_path: Path) -> None:
    text = "## DEC-001 Long\n- Date: 2026-01-01\n- Reason: " + "word " * 2000 + "\n"
    item = lookup.decisions(bare(tmp_path, **{"DECISIONS.md": text}), "DEC-1")["items"][0]
    assert item["cut"] is True and len(item["fields"]["Reason"]) <= lookup.TEXT_LIMIT
    assert item["fields"]["Reason"].endswith("...")


@pytest.mark.parametrize("args,word", [
    (("D" * 41, None), "at most 40"), (("DEC", None), "look like"), ((5, None), "id"), (("../x", None), "look like"),
    ((None, "q" * 101), "at most 100"), ((None, 5), "query"),
])
def test_decisions_refuse_a_bad_argument(tmp_path: Path, args: tuple[Any, Any], word: str) -> None:
    with pytest.raises(ValueError, match=word):
        lookup.decisions(project(tmp_path), *args)


def test_decisions_accept_the_limits(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert lookup.decisions(root, "D" * 38 + "-1")["items"] == []  # 40 characters
    assert lookup.decisions(root, None, "q" * 100)["items"] == []


# --- lessons ---------------------------------------------------------------------------

def test_lessons_read_both_heading_forms_and_skip_the_format_example(tmp_path: Path) -> None:
    got = lookup.lessons(project(tmp_path))
    assert got["source"] == "LESSONS.md" and got["error"] == ""
    assert (got["total"], got["unreadable"], got["template_entries"], got["truncated"]) == (2, 0, 1, False)
    first, second = got["items"]
    assert (first["title"], first["date"]) == ("A stale cache hid a changed record", "2026-01-12")
    assert list(first["fields"]) == ["Problem", "Cause", "Fix", "Lesson"]
    assert first["fields"]["Lesson"] == "a read tool holds no state between calls."
    assert (second["title"], second["date"]) == ("A limit copied without its reason", "2026-01-20")
    assert second["fields"]["Project"] == "Project A" and second["fields"]["Date"] == "2026-01-20"


def test_lessons_query(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert [i["date"] for i in lookup.lessons(root, "cache")["items"]] == ["2026-01-12"]
    assert [i["date"] for i in lookup.lessons(root, "CAP")["items"]] == ["2026-01-20"]
    assert [i["date"] for i in lookup.lessons(root, "state between")["items"]] == ["2026-01-12"]
    assert lookup.lessons(root, "zebra")["items"] == [] and lookup.lessons(root, "zebra")["total"] == 2


def test_lessons_count_an_entry_without_a_valid_date(tmp_path: Path) -> None:
    text = ("## One\n- Date: 2026-02-01\n- Problem: p\n\n## Two\n- Problem: no date\n\n### 2026-99-99 - Three\n- Problem: p\n\n"
            "### Heading only\n\nsome words\n")
    got = lookup.lessons(bare(tmp_path, **{"LESSONS.md": text}))
    assert [i["title"] for i in got["items"]] == ["One"] and got["unreadable"] == 2
    assert got["unreadable_headings"] == ["Two", "2026-99-99 - Three"]


def test_lessons_refuse_a_long_query(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="query"):
        lookup.lessons(project(tmp_path), "q" * 101)


# --- tasks -----------------------------------------------------------------------------

def test_tasks_list(tmp_path: Path) -> None:
    got = lookup.tasks(project(tmp_path))
    assert got["source"] == "TASKS.md" and got["error"] == "" and got["unreadable"] == 0 and got["total"] == 5
    assert [(t["id"], t["size"], t["done"]) for t in got["items"]] == [
        ("T-1", "E", True), ("T-2", "M", True), ("T-3", "H", False), ("T-4", "", True), ("T-5a", "E", True)]
    by_id = {t["id"]: t for t in got["items"]}
    assert by_id["T-1"]["result"] == "" and by_id["T-1"]["title"] == "first task, a list line only."
    assert by_id["T-2"]["title"] == "Second task (`developer`, Sonnet)"  # the block wins over its list line
    assert by_id["T-2"]["result"] == "12 tests green; review rounds 1."
    assert by_id["T-3"]["result"] == "" and by_id["T-3"]["title"] == "Third task"
    assert by_id["T-4"]["title"] == "Gate G1" and by_id["T-4"]["result"] == "ACCEPT."
    assert got["now_next"] == "T-3 is next: add the tools. T-1 and T-2 are done." and got["now_next_cut"] is False


def test_tasks_by_id(tmp_path: Path) -> None:
    root = project(tmp_path)
    got = lookup.tasks(root, "t-5A")
    assert [t["id"] for t in got["items"]] == ["T-5a"] and got["matched"] == 1 and got["total"] == 5
    assert got["now_next"].startswith("T-3 is next")  # NOW NEXT comes with every answer
    assert lookup.tasks(root, "T-03")["items"][0]["done"] is False
    assert lookup.tasks(root, "T-77")["items"] == []


def test_tasks_without_a_now_next_section(tmp_path: Path) -> None:
    got = lookup.tasks(bare(tmp_path, **{"TASKS.md": "### [ ] T-1 [E] Only\n- Goal: g\n"}))
    assert got["now_next"] == "" and [t["id"] for t in got["items"]] == ["T-1"]


def test_tasks_count_a_task_without_an_id(tmp_path: Path) -> None:
    text = "### [x] no id here\n\n- [ ] also no id\n\n### [ ] T-1 [E] Fine\n\n- Plain bullet [x] T-9\n"
    got = lookup.tasks(bare(tmp_path, **{"TASKS.md": text}))
    assert [t["id"] for t in got["items"]] == ["T-1"] and got["unreadable"] == 2
    assert got["unreadable_headings"] == ["[x] no id here", "[ ] also no id"]


def test_tasks_shorten_a_result_in_the_list_but_not_for_one_task(tmp_path: Path) -> None:
    text = "### [x] T-1 [E] Long\n- Result: " + "word " * 100 + "\n"
    root = bare(tmp_path, **{"TASKS.md": text})
    short = lookup.tasks(root)["items"][0]
    assert short["cut"] is True and len(short["result"]) <= lookup.SHORT_LIMIT
    full = lookup.tasks(root, "T-1")["items"][0]
    assert full["cut"] is False and len(full["result"]) > 400


def test_tasks_refuse_a_bad_id(tmp_path: Path) -> None:
    root = project(tmp_path)
    with pytest.raises(ValueError, match="id"):
        lookup.tasks(root, "forty two")
    with pytest.raises(ValueError, match="at most 40"):
        lookup.tasks(root, "T-" + "1" * 60)


# --- log -------------------------------------------------------------------------------

def test_log_gives_the_newest_entries_first(tmp_path: Path) -> None:
    got = lookup.log(project(tmp_path), 3)
    assert got["source"] == "LOG.md" and got["error"] == "" and got["count"] == 3
    assert [(e["date"], e["n"]) for e in got["items"]] == [("2026-01-20", 2), ("2026-01-20", 1), ("2026-01-12", 1)]
    assert got["items"][0]["title"] == "Second entry of the day"
    assert got["items"][0]["text"] == "- Built the tools.\n- Tests green."
    assert (got["total"], got["unreadable"], got["truncated"]) == (4, 0, True)
    assert lookup.log(project(tmp_path / "x"), 20)["truncated"] is False
    assert len(lookup.log(project(tmp_path / "y"), 20)["items"]) == 4


def test_log_default_count_is_5(tmp_path: Path) -> None:
    assert lookup.log(project(tmp_path))["count"] == 5


def test_log_sorts_by_date_not_by_position(tmp_path: Path) -> None:
    text = "# Log\n\n## 2026-01-01 (1) - old\n\n## 2026-03-01 (1) - new\n\n## 2026-03-01 (2) - newest\n\n## 2026-02-01 (1) - mid\n"
    got = lookup.log(bare(tmp_path, **{"LOG.md": text}), 4)
    assert [e["title"] for e in got["items"]] == ["newest", "new", "mid", "old"]


def test_log_counts_a_heading_it_cannot_read(tmp_path: Path) -> None:
    text = "## 2026-01-01 (1) - fine\n\n## Notes without a date\n\n## 2026-13-01 (1) - bad month\n"
    got = lookup.log(bare(tmp_path, **{"LOG.md": text}), 5)
    assert [e["title"] for e in got["items"]] == ["fine"] and got["unreadable"] == 2
    assert got["unreadable_headings"] == ["Notes without a date", "2026-13-01 (1) - bad month"]


def test_log_cuts_a_long_entry(tmp_path: Path) -> None:
    text = "## 2026-01-01 (1) - long\n" + "line of text\n" * 600
    item = lookup.log(bare(tmp_path, **{"LOG.md": text}), 1)["items"][0]
    assert item["cut"] is True and len(item["text"]) <= lookup.TEXT_LIMIT


@pytest.mark.parametrize("count", [0, 21, -1, True, "5", 2.5, None])
def test_log_refuses_a_count_outside_1_to_20(tmp_path: Path, count: object) -> None:
    with pytest.raises(ValueError, match="count"):
        lookup.log(project(tmp_path), count)


# --- findings --------------------------------------------------------------------------

def _report(got: dict[str, Any], name: str) -> dict[str, Any]:
    return next(r for r in got["reports"] if r["report"] == name)


def test_findings_per_report(tmp_path: Path) -> None:
    got = lookup.findings(project(tmp_path))
    assert got["source"] == "audits" and got["error"] == "" and got["total"] == 3
    assert [r["report"] for r in got["reports"]] == ["2026-01-10_gate1.md", "2026-01-15_reverify.md", "2026-01-20_reverify.md"]
    gate = _report(got, "2026-01-10_gate1.md")
    assert gate["date"] == "2026-01-10"
    assert gate["verdict"] == "conditional: P-1 must be fixed before the gate closes."
    assert [(f["id"], f["severity"], f["status"]) for f in gate["findings"]] == [
        ("P-1", "high", "CLOSED"), ("D-1", "medium", "CLOSED"), ("D-2", "low", "PARTIAL"),
        ("C-1", "low", "none"), ("R-1", "unrated", "OPEN")]
    assert gate["findings"][0]["title"] == "The cache is stale" and gate["rows"] == []


def test_findings_rows_link_to_the_finding_and_the_latest_row_wins(tmp_path: Path) -> None:
    got = lookup.findings(project(tmp_path))
    first = _report(got, "2026-01-15_reverify.md")
    assert first["verdict"] == "Gate verdict: conditional" and first["findings"] == []
    assert [(r["id"], r["status"], r["finding_report"]) for r in first["rows"]] == [
        ("P-1", "PARTIAL", "2026-01-10_gate1.md"), ("D-1", "CLOSED", "2026-01-10_gate1.md"),
        ("D-2", "PARTIAL", "2026-01-10_gate1.md"), ("X-9", "CLOSED", "")]  # the PASS check row is not read
    second = _report(got, "2026-01-20_reverify.md")
    assert second["verdict"] == "accept: one finding open, not a gate item."
    assert [(r["id"], r["status"]) for r in second["rows"]] == [("P-1", "CLOSED"), ("R-1", "OPEN")]
    assert second["rows"][1]["claim"] == 'The role file says "a \\| b"'  # an escaped bar stays in the cell
    assert got["unlinked_rows"] == 1 and got["unreadable"] == 0


@pytest.mark.parametrize("status,ids", [
    ("closed", ["P-1", "D-1"]), ("CLOSED", ["P-1", "D-1"]), ("open", ["R-1"]), ("partial", ["D-2"]), ("none", ["C-1"])])
def test_findings_filter_by_the_latest_status(tmp_path: Path, status: str, ids: list[str]) -> None:
    got = lookup.findings(project(tmp_path), status)
    assert [f["id"] for f in _report(got, "2026-01-10_gate1.md")["findings"]] == ids
    assert got["status"] == status.lower()


def test_findings_status_filter_also_filters_rows(tmp_path: Path) -> None:
    got = lookup.findings(project(tmp_path), "partial")
    assert [(r["report"], [x["id"] for x in r["rows"]]) for r in got["reports"][1:]] == [("2026-01-15_reverify.md", ["P-1", "D-2"])]
    assert got["matched"] == 3  # D-2, and two PARTIAL rows


def test_findings_filter_by_report_name(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert [r["report"] for r in lookup.findings(root, None, "gate1")["reports"]] == ["2026-01-10_gate1.md"]
    assert [r["report"] for r in lookup.findings(root, None, "2026-01-20")["reports"]] == ["2026-01-20_reverify.md"]
    assert [r["report"] for r in lookup.findings(root, None, "REVERIFY")["reports"]] == [
        "2026-01-15_reverify.md", "2026-01-20_reverify.md"]
    none = lookup.findings(root, None, "zebra")
    assert none["reports"] == [] and none["total"] == 3 and none["matched"] == 0


def test_findings_refuse_a_bad_argument(tmp_path: Path) -> None:
    root = project(tmp_path)
    with pytest.raises(ValueError, match="status"):
        lookup.findings(root, "done")
    with pytest.raises(ValueError, match="status"):
        lookup.findings(root, 5)
    with pytest.raises(ValueError, match="report"):
        lookup.findings(root, None, "r" * 101)


def test_findings_count_what_they_cannot_read(tmp_path: Path) -> None:
    root = project(tmp_path)
    (root / "audits" / "notes.md").write_text("# Notes without a date in the name\n", encoding="utf-8")
    (root / "audits" / "readme.txt").write_text("not a report\n", encoding="utf-8")  # other suffix: ignored
    (root / "audits" / "2026-02-01_odd.md").write_text("### Severity but no id\n- Severity: High\n", encoding="utf-8")
    got = lookup.findings(root)
    assert got["total"] == 4 and got["unreadable"] == 2
    assert got["unreadable_headings"] == ["Severity but no id", "notes.md"]  # files in name order, a file's headings first


def test_findings_limit_100_items_and_the_truncated_flag(tmp_path: Path) -> None:
    body = "".join(f"### P-{i} Finding {i}\n- Severity: Low\n\n" for i in range(1, 121))
    got = lookup.findings(bare(tmp_path, **{"audits/2026-01-01_big.md": body}))
    (rep,) = got["reports"]
    assert len(rep["findings"]) == 100 and got["matched"] == 120 and got["truncated"] is True


def test_findings_row_in_a_report_before_the_finding_is_unlinked(tmp_path: Path) -> None:
    early = "| Finding | Claim | Evidence | Status |\n|---|---|---|---|\n| P-1 | c | e | CLOSED |\n"
    late = "### P-1 Title\n- Severity: High\n"
    root = bare(tmp_path, **{"audits/2026-01-01_early.md": early, "audits/2026-02-01_late.md": late})
    got = lookup.findings(root)
    assert got["unlinked_rows"] == 1 and _report(got, "2026-02-01_late.md")["findings"][0]["status"] == "none"


# --- the record map and the root --------------------------------------------------------

KEYS = ("decisions", "lessons", "tasks", "log")


def _call(root: Path, kind: str) -> dict[str, Any]:
    return {"decisions": lookup.decisions, "lessons": lookup.lessons, "tasks": lookup.tasks,
            "log": lookup.log, "audits": lookup.findings}[kind](root)


def test_the_map_can_name_other_files_inside_the_root(tmp_path: Path) -> None:
    root = project(tmp_path, "- Decisions: `notes/DEC.md`\n- Audits: `reports`\n")
    (root / "notes").mkdir()
    shutil.copyfile(root / "DECISIONS.md", root / "notes" / "DEC.md")
    shutil.copytree(root / "audits", root / "reports")
    got = lookup.decisions(root)
    assert got["source"] == "notes/DEC.md" and got["total"] == 4 and got["error"] == ""
    assert lookup.findings(root)["source"] == "reports" and lookup.findings(root)["total"] == 3


@pytest.mark.parametrize("entry", [
    "..", "../outside.md", "../../outside.md", "sub/../../outside.md", "sub\\..\\..\\outside.md", "..\\outside.md",
    "/etc/passwd", "C:\\Windows\\win.ini", "C:/Windows/win.ini", "//server/share/x", ".",
])
@pytest.mark.parametrize("kind", ["decisions", "lessons", "tasks", "log", "audits"])
def test_a_map_entry_outside_the_root_gives_an_error_answer(tmp_path: Path, kind: str, entry: str) -> None:
    (tmp_path / "outside.md").write_text("## DEC-001 Secret\n- Date: 2026-01-01\n", encoding="utf-8")
    root = project(tmp_path / "x", f"- {kind.capitalize()}: `{entry}`\n")
    got = _call(root, kind)
    assert got["items" if kind != "audits" else "reports"] == [] and got["error"].startswith(f"{kind}: ")
    assert "outside the project root" in got["error"] or "not usable" in got["error"]
    assert "Secret" not in json.dumps(got) and str(tmp_path) not in json.dumps(got) and entry not in got["error"]


def test_a_map_entry_with_an_absolute_path_outside_is_refused_and_one_inside_is_read(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("## DEC-001 Secret\n- Date: 2026-01-01\n", encoding="utf-8")
    root = project(tmp_path / "x", f"- Decisions: `{outside}`\n")
    got = lookup.decisions(root)
    assert got["items"] == [] and "outside the project root" in got["error"] and str(tmp_path) not in json.dumps(got)
    inside = project(tmp_path / "y", f"- Decisions: `{(tmp_path / 'y' / 'p' / 'DECISIONS.md').resolve()}`\n")
    ok = lookup.decisions(inside)
    assert ok["error"] == "" and ok["total"] == 4 and ok["source"] == "DECISIONS.md"


def _make_link(link: Path, target: Path) -> bool:
    try:
        os.symlink(target, link, target_is_directory=target.is_dir())
        return True
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt" and target.is_dir():
        res = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        return res.returncode == 0 and link.exists()
    return False


def test_a_map_entry_through_a_link_pointing_outside_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    shutil.copyfile(FIXTURES / "DECISIONS.md", outside / "DECISIONS.md")
    shutil.copytree(FIXTURES / "audits", outside / "audits")
    root = project(tmp_path / "x", "- Decisions: `link/DECISIONS.md`\n- Audits: `link/audits`\n")
    if not _make_link(root / "link", outside):
        pytest.skip("cannot create a symlink or junction here")
    for got in (lookup.decisions(root), lookup.findings(root)):
        assert "resolves outside the project root" in got["error"] and got["total"] == 0
        assert str(tmp_path) not in json.dumps(got)


def test_a_report_file_that_is_a_link_pointing_outside_is_counted_unreadable(tmp_path: Path) -> None:
    outside = tmp_path / "secret.md"
    outside.write_text("### P-9 Secret\n- Severity: High\n", encoding="utf-8")
    root = project(tmp_path / "x")
    try:
        os.symlink(outside, root / "audits" / "2026-03-01_link.md")
    except (OSError, NotImplementedError):
        pytest.skip("cannot create a symlink here")
    got = lookup.findings(root)
    assert got["unreadable"] == 1 and "Secret" not in json.dumps(got)


def test_resolve_in_root_allows_inside_and_refuses_outside(tmp_path: Path) -> None:
    root = project(tmp_path)
    assert lookup.resolve_in_root(root, "audits/2026-01-10_gate1.md", False).name == "2026-01-10_gate1.md"
    assert lookup.resolve_in_root(root, "./audits/../LOG.md", False) == (root / "LOG.md").resolve()
    for raw in ("..", "../x", "/etc/passwd", "", "a\0b", None, 5):
        with pytest.raises(lookup.RecordPathError):
            lookup.resolve_in_root(root, raw, False)  # type: ignore[arg-type]


def test_a_missing_or_unreadable_record_gives_an_error_answer(tmp_path: Path) -> None:
    root = bare(tmp_path)
    for kind in KEYS:
        got = _call(root, kind)
        assert got["error"] == f"the {kind} file does not exist" and got["items"] == [] and got["total"] == 0
    missing = lookup.findings(root)
    assert missing["error"] == "the audits folder does not exist" and missing["reports"] == []
    (root / "DECISIONS.md").mkdir()
    assert lookup.decisions(root)["error"] == "the decisions file could not be read"
    (root / "LOG.md").write_bytes(b"x" * (lookup.MAX_BYTES + 1))
    assert "larger than" in lookup.log(root)["error"]
    (root / "audits").write_text("a file, not a folder\n", encoding="utf-8")
    assert lookup.findings(root)["error"] == "the audits folder could not be read"


def test_the_files_are_read_with_a_bom_and_crlf(tmp_path: Path) -> None:
    raw = b"\xef\xbb\xbf## DEC-001 One\r\n- Date: 2026-01-01\r\n- Outcome: done\r\n"
    root = bare(tmp_path)
    (root / "DECISIONS.md").write_bytes(raw)
    got = lookup.decisions(root, "DEC-1")
    assert got["items"][0]["fields"]["Outcome"] == "done" and got["unreadable"] == 0


# --- command line ----------------------------------------------------------------------

def _cli(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ROOT / "tools" / "lookup.py"), *argv], cwd=ROOT,
                          capture_output=True, text=True, timeout=60)


def test_cli_prints_the_same_answers(tmp_path: Path) -> None:
    root = project(tmp_path)
    cases = [
        (["decisions", "--id", "DEC-1"], lookup.decisions(root, "DEC-1")),
        (["decisions", "--query", "cache"], lookup.decisions(root, None, "cache")),
        (["lessons", "--query", "cache"], lookup.lessons(root, "cache")),
        (["findings", "--status", "closed", "--report", "gate1"], lookup.findings(root, "closed", "gate1")),
        (["tasks", "--id", "T-2"], lookup.tasks(root, "T-2")),
        (["log", "--count", "2"], lookup.log(root, 2)),
    ]
    for argv, want in cases:
        res = _cli("--root", str(root), *argv)
        assert res.returncode == 0, res.stderr
        assert json.loads(res.stdout) == want, argv
    res = subprocess.run([sys.executable, "-m", "tools.lookup", "--root", str(root), "log"], cwd=ROOT,
                         capture_output=True, text=True, timeout=60)
    assert res.returncode == 0 and json.loads(res.stdout) == lookup.log(root)


def test_cli_refuses_a_bad_argument_and_reports_an_error_answer(tmp_path: Path) -> None:
    root = project(tmp_path)
    bad = _cli("--root", str(root), "log", "--count", "99")
    assert bad.returncode == 2 and "count" in bad.stderr and bad.stdout == ""
    empty = _cli("--root", str(bare(tmp_path / "e")), "tasks")
    assert empty.returncode == 1 and json.loads(empty.stdout)["error"] == "the tasks file does not exist"


# --- module hygiene --------------------------------------------------------------------

def test_lookup_uses_the_standard_library_and_tools_only() -> None:
    tree = ast.parse((ROOT / "tools" / "lookup.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    assert names <= set(sys.stdlib_module_names) | {"tools"}
    assert not names & {"socket", "ssl", "http", "urllib", "asyncio", "subprocess", "server", "mcp"}


def test_lookup_has_no_write_call() -> None:
    writes = {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "replace", "touch", "remove",
              "makedirs", "rmtree", "copy", "copyfile", "copytree", "move", "symlink_to", "chmod"}
    tree = ast.parse((ROOT / "tools" / "lookup.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in writes, node.attr
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            raise AssertionError("open() is not used; files are read with read_bytes")


# --- this repository's own records ------------------------------------------------------

def _count(path: str, pattern: str) -> int:
    return len(re.findall(pattern, (ROOT / path).read_text(encoding="utf-8"), re.MULTILINE))


def test_the_repository_records_parse_with_no_unreadable_entry() -> None:
    answers = {
        "decisions": lookup.decisions(ROOT), "lessons": lookup.lessons(ROOT), "tasks": lookup.tasks(ROOT),
        "log": lookup.log(ROOT, 20), "findings": lookup.findings(ROOT),
    }
    for name, got in answers.items():
        assert got["error"] == "", name
        assert got["unreadable"] == 0 and got["unreadable_headings"] == [], (name, got["unreadable_headings"])
        assert got["total"] > 0, name
    assert answers["decisions"]["total"] == _count("DECISIONS.md", r"^## DEC-\d+ ")
    assert answers["log"]["total"] == _count("LOG.md", r"^## \d{4}-\d{2}-\d{2} \(\d+\) - ")
    assert answers["tasks"]["total"] >= _count("TASKS.md", r"^### \[[ x]\] ")
    assert answers["lessons"]["total"] >= 1 and answers["lessons"]["template_entries"] == 1
    assert answers["findings"]["total"] == len(list((ROOT / "audits").glob("*.md")))
    assert answers["tasks"]["now_next"] != "" and len(answers["decisions"]["items"]) <= lookup.ITEM_LIMIT
