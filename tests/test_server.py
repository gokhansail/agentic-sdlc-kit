"""Tests for the MCP server skeleton (T-40): status, root lock, start check, no network, stdio.

Projects live in pytest temp dirs and are built from tests/fixtures/server/. Tests that need
the `mcp` package skip when it is missing, so a clone without it still runs green.
"""
from __future__ import annotations

import ast
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import main as server_main  # noqa: E402
from server import inputs as server_inputs  # noqa: E402
from server import scope as server_scope  # noqa: E402
from server import status as server_status  # noqa: E402
from server.events import guard_events  # noqa: E402
from server.rootlock import RootLock, RootLockError  # noqa: E402
from server.scope import changed_outside, contract, scope_check  # noqa: E402
from server.status import status  # noqa: E402
from tools import events as event_totals  # noqa: E402
from tools import lookup  # noqa: E402
from tools import scope_guard  # noqa: E402
from tools.records import read_records  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "server"
RECORDS = FIXTURES / "lookup"
SERVER_DIR = ROOT / "server"
ENTRY = SERVER_DIR / "main.py"
TOOL_NAMES = ["status", "scope_check", "contract", "changed_outside", "guard_events",
              "decisions", "lessons", "findings", "tasks", "log"]
TOOL_ARGS: dict[str, dict[str, Any]] = {  # a tool with arguments adds its entry here
    "status": {},
    "scope_check": {"paths": ["src/a.py", "src/secret.py", "../outside.txt", "STATUS.md"], "actor": "sub-agent"},
    "contract": {},
    "changed_outside": {},
    "guard_events": {},
    "decisions": {"id": "DEC-002"},
    "lessons": {"query": "cache"},
    "findings": {"status": "closed"},
    "tasks": {"id": "T-2"},
    "log": {"count": 3},
}


def lookup_answers(root: Path, casefold: bool | None = None) -> dict[str, dict[str, Any]]:
    """What `tools/lookup.py` answers for the arguments in TOOL_ARGS."""
    return {
        "decisions": lookup.decisions(root, TOOL_ARGS["decisions"]["id"], None, casefold),
        "lessons": lookup.lessons(root, TOOL_ARGS["lessons"]["query"], casefold),
        "findings": lookup.findings(root, TOOL_ARGS["findings"]["status"], None, casefold),
        "tasks": lookup.tasks(root, TOOL_ARGS["tasks"]["id"], casefold),
        "log": lookup.log(root, TOOL_ARGS["log"]["count"], casefold),
    }


def add_records(root: Path) -> Path:
    """Copy the record fixtures (DECISIONS.md, LESSONS.md, TASKS.md, LOG.md, audits/) into a project."""
    shutil.copytree(RECORDS, root, dirs_exist_ok=True)
    return root


def make_project(base: Path, project: str | None, contract_fixture: str | None, events: str | None = None) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    if project is not None:
        (base / ".sdlc").mkdir(exist_ok=True)
        (base / ".sdlc" / "project.md").write_bytes((FIXTURES / project).read_bytes())
    if contract_fixture is not None:
        (base / ".sdlc").mkdir(exist_ok=True)
        (base / ".sdlc" / "active-contract.md").write_bytes((FIXTURES / contract_fixture).read_bytes())
    if events is not None:
        (base / ".sdlc").mkdir(exist_ok=True)
        (base / ".sdlc" / "metrics.jsonl").write_bytes((FIXTURES / events).read_bytes())
    return base


# --- status on fixture repositories --------------------------------------------------

def test_status_not_opted_in(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, None, None))
    assert got["opted_in"] is False
    assert got["guard_state"] == "not-opted-in"
    assert got["task_id"] is None and got["files_in"] == [] and got["files_out"] == []
    assert got["records"] == read_records(tmp_path)  # template defaults
    assert got["records"]["status"] == "STATUS.md"


def test_status_opted_in_without_contract(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, "project.md", None))
    assert got["opted_in"] is True
    assert got["guard_state"] == scope_guard.NO_CONTRACT
    assert got["task_id"] is None and got["files_in"] == [] and got["files_out"] == []
    assert got["broken_reason"] == ""


def test_status_with_an_active_contract(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, "project-custom.md", "contract.md"), "CLAUDE_PROJECT_DIR")
    assert got["opted_in"] is True
    assert got["guard_state"] == scope_guard.ACTIVE
    assert got["task_id"] == "T-77"
    assert got["files_in"] == ["src/a.py", "src/pkg/", "tests/a.py", "tests/b.py"]  # braces expanded as the guard does
    assert got["files_out"] == ["src/secret.py"]
    assert got["records"]["status"] == "docs/state.md"
    assert got["records"]["developer_rules"] == "rules/DEV.md"
    assert got["root_source"] == "CLAUDE_PROJECT_DIR"


def test_status_with_a_broken_contract(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, "project.md", "contract-broken.md"))
    assert got["guard_state"] == scope_guard.BROKEN
    assert got["task_id"] is None and got["files_in"] == []
    assert "active-contract.md" in got["broken_reason"]


def test_status_equals_the_guard_state_and_the_record_map(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project-custom.md", "contract.md")
    state, contract, _always, _reason = scope_guard.load_state(root)
    got = status(root)
    assert contract is not None
    assert (got["guard_state"], got["task_id"]) == (state, contract.task_id)
    assert got["files_in"] == list(contract.files_in) and got["files_out"] == list(contract.files_out)
    assert got["records"] == read_records(root)


def test_status_is_json_serialisable_and_names_no_path(tmp_path: Path) -> None:
    text = json.dumps(status(make_project(tmp_path, "project.md", "contract.md")))
    assert str(tmp_path) not in text and tmp_path.name not in text


# --- scope_check ---------------------------------------------------------------------

SCOPE_PATHS = ["src/a.py", "src/pkg/deep/x.py", "tests/b.py", "src/secret.py", "docs/other.md", "STATUS.md",
               "LOG.md", "DEV_RULES.md", ".sdlc/active-contract.md", "./src/../src/a.py", "src\\pkg\\y.py"]
OUTSIDE_PATHS = ["..", "../outside.txt", "src/../../outside.txt", "src\\..\\..\\outside.txt", "..\\outside.txt",
                 "/etc/passwd", "C:\\Windows\\win.ini", "C:/Windows/win.ini", "//server/share/x"]


@pytest.mark.parametrize("actor", ["sub-agent", "main"])
@pytest.mark.parametrize("fixture", [("project.md", "contract.md"), ("project.md", None),
                                     ("project.md", "contract-broken.md")])
def test_scope_check_equals_the_guard(tmp_path: Path, fixture: tuple[str, str | None], actor: str) -> None:
    root = make_project(tmp_path, *fixture)
    fold = os.name == "nt"
    got = scope_check(root, SCOPE_PATHS, actor, fold)
    assert [row["path"] for row in got["results"]][:3] == ["src/a.py", "src/pkg/deep/x.py", "tests/b.py"]
    for raw, row in zip(SCOPE_PATHS, got["results"]):
        want = scope_guard.check(root, raw, actor == "sub-agent", fold)
        assert want is not None
        assert (row["allow"], row["reason"], row["next_step"], row["state"], row["task"], row["path"]) == (
            want.allow, want.reason, want.next_step, want.state, want.task_id, want.rel), raw
    state, contract_obj, _always, _reason = scope_guard.load_state(root)
    assert (got["guard_state"], got["task_id"]) == (state, contract_obj.task_id if contract_obj else None)
    assert got["opted_in"] is True and got["note"] == "" and got["actor"] == actor


def test_scope_check_known_answers(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    rows = {r["path"]: r for r in scope_check(root, SCOPE_PATHS, "sub-agent", False)["results"]}
    assert rows["src/a.py"]["allow"] is True and rows["src/a.py"]["reason"] == "in scope of T-77"
    assert rows["src/pkg/y.py"]["allow"] is True  # backslashes unify
    assert rows["src/secret.py"]["allow"] is False and "Files out" in rows["src/secret.py"]["reason"]
    assert rows["docs/other.md"]["allow"] is False and "not in Files in" in rows["docs/other.md"]["reason"]
    assert rows["STATUS.md"]["allow"] is True and rows["LOG.md"]["allow"] is True  # always allowed
    assert rows["DEV_RULES.md"]["allow"] is False and "developer rules" in rows["DEV_RULES.md"]["reason"]
    assert rows[".sdlc/active-contract.md"]["allow"] is False
    main_rows = {r["path"]: r for r in scope_check(root, [".sdlc/active-contract.md", "docs/other.md"], "main", False)["results"]}
    assert main_rows[".sdlc/active-contract.md"]["allow"] is True
    assert main_rows["docs/other.md"]["allow"] is False  # the main session is held to Files in too


def test_scope_check_without_a_contract_and_with_a_broken_one(tmp_path: Path) -> None:
    none = scope_check(make_project(tmp_path / "a", "project.md", None), ["src/a.py", "STATUS.md"], "sub-agent")
    assert none["guard_state"] == scope_guard.NO_CONTRACT and none["task_id"] is None
    assert [r["allow"] for r in none["results"]] == [False, True]
    assert "no active contract" in none["results"][0]["reason"]
    broken = scope_check(make_project(tmp_path / "b", "project.md", "contract-broken.md"), ["STATUS.md"], "main")
    assert broken["guard_state"] == scope_guard.BROKEN
    assert broken["results"][0]["allow"] is False and "cannot be used" in broken["results"][0]["reason"]


def test_scope_check_when_not_opted_in_gives_one_clear_answer(tmp_path: Path) -> None:
    got = scope_check(make_project(tmp_path, None, None), ["src/a.py", "../outside.txt", str(tmp_path / "x.py")], "sub-agent")
    assert got["opted_in"] is False and got["guard_state"] == "not-opted-in" and got["task_id"] is None
    assert "the guard is off" in got["note"] and "every write is allowed" in got["note"]
    assert [r["allow"] for r in got["results"]] == [True, True, True]
    assert {r["state"] for r in got["results"]} == {"not-opted-in"}
    assert all("the guard is off" in r["reason"] for r in got["results"])
    assert got["results"][2]["path"] == "x.py"  # an absolute path inside the root comes back relative


@pytest.mark.parametrize("actor", ["sub-agent", "main"])
@pytest.mark.parametrize("raw", OUTSIDE_PATHS)
def test_scope_check_denies_a_path_outside_the_root(tmp_path: Path, raw: str, actor: str) -> None:
    root = make_project(tmp_path / "project", "project.md", "contract.md")
    row = scope_check(root, [raw], actor, False)["results"][0]
    assert row["allow"] is False and row["reason"] == "the path is outside the project root"
    assert row["state"] == scope_guard.ACTIVE and row["task"] == "T-77"


def test_scope_check_denies_an_absolute_path_outside_and_allows_one_inside(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project", "project.md", "contract.md")
    outside = str(tmp_path / "outside" / "secret.txt")
    sibling = str(tmp_path / "project2" / "a.py")
    got = scope_check(root, [outside, sibling, str(root / "src" / "a.py")], "sub-agent")
    assert [r["allow"] for r in got["results"]] == [False, False, True]
    assert got["results"][2]["path"] == "src/a.py"
    assert "project2" not in got["results"][2]["reason"]


def test_scope_check_case_follows_the_flag(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project", "project.md", "contract.md").resolve()
    upper = str(root).upper() + "\\SRC\\A.PY"
    assert scope_check(root, [upper], "sub-agent", True)["results"][0]["allow"] is True
    assert scope_check(root, [upper], "sub-agent", False)["results"][0]["allow"] is False


def test_scope_check_has_no_memory_folder_exception(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project", "project.md", "contract.md")
    memory = tmp_path / "home" / "projects" / "slug" / "memory" / "note.md"
    row = scope_check(root, [str(memory)], "main", False)["results"][0]
    assert row["allow"] is False and row["reason"] == "the path is outside the project root"


def test_scope_check_limit_is_50_paths(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    assert len(scope_check(root, ["src/a.py"] * 50, "main")["results"]) == 50
    assert scope_check(root, [], "main")["results"] == []
    with pytest.raises(ValueError, match="at most 50"):
        scope_check(root, ["src/a.py"] * 51, "main")


@pytest.mark.parametrize("actor", ["root", "Main", "sub_agent", "", None, "developer"])
def test_scope_check_refuses_an_unknown_actor(tmp_path: Path, actor: object) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    with pytest.raises(ValueError, match="actor"):
        scope_check(root, ["src/a.py"], actor)  # type: ignore[arg-type]


@pytest.mark.parametrize("project", [True, False])
def test_scope_check_unusable_entries_are_denied(tmp_path: Path, project: bool) -> None:
    root = make_project(tmp_path, "project.md" if project else None, None)
    got = scope_check(root, ["", "   ", "a\0b", None, 5], "main")["results"]  # type: ignore[list-item]
    assert [r["allow"] for r in got] == [False] * 5
    assert {r["reason"] for r in got} == {"not a usable path"}


def test_scope_check_answers_name_no_absolute_path(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project", "project-custom.md", "contract.md")
    text = json.dumps(scope_check(root, SCOPE_PATHS + [str(root / "src" / "a.py")], "sub-agent"))
    assert str(root) not in text and str(tmp_path) not in text and tmp_path.name not in text


# --- contract ------------------------------------------------------------------------

def test_contract_of_a_valid_contract(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    got = contract(root)
    code, message = scope_guard.check_contract(root)
    assert code == 0 and got["valid"] is True and got["message"] == message
    assert got["task_id"] == "T-77" and got["guard_state"] == scope_guard.ACTIVE and got["opted_in"] is True
    assert got["files_in"] == ["src/a.py", "src/pkg/", "tests/a.py", "tests/b.py"]
    assert got["files_out"] == ["src/secret.py"]
    assert got["always_allowed"] == ["STATUS.md", "LOG.md"]
    assert got["developer_rules"] == "DEV_RULES.md"


def test_contract_equals_the_guard_functions(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project-custom.md", "contract.md")
    got = contract(root)
    _state, parsed, always, _reason = scope_guard.load_state(root)
    assert parsed is not None
    assert (got["task_id"], got["files_in"], got["files_out"]) == (parsed.task_id, list(parsed.files_in), list(parsed.files_out))
    assert got["always_allowed"] == always == ["docs/state.md"]
    assert got["developer_rules"] == scope_guard.load_developer_rules(root) == "rules/DEV.md"


def test_contract_without_a_contract_and_with_a_broken_one(tmp_path: Path) -> None:
    none = contract(make_project(tmp_path / "a", "project.md", None))
    assert none["valid"] is False and none["task_id"] is None and none["files_in"] == []
    assert none["message"] == scope_guard.check_contract(tmp_path / "a")[1] and "no active contract" in none["message"]
    assert "Format: one '## <ID> <title>' heading" in none["message"] and "T-12a" in none["message"]
    assert none["guard_state"] == scope_guard.NO_CONTRACT and none["always_allowed"] == ["STATUS.md", "LOG.md"]
    broken = contract(make_project(tmp_path / "b", "project.md", "contract-broken.md"))
    assert broken["valid"] is False and broken["task_id"] is None and broken["files_in"] == []
    assert broken["message"] == scope_guard.check_contract(tmp_path / "b")[1] and "active-contract.md" in broken["message"]
    assert "Format: one '## <ID> <title>' heading" in broken["message"] and "T-12a" in broken["message"]
    assert broken["guard_state"] == scope_guard.BROKEN


def test_contract_when_not_opted_in(tmp_path: Path) -> None:
    got = contract(make_project(tmp_path, None, "contract.md"))
    assert got["opted_in"] is False and got["guard_state"] == "not-opted-in"
    assert got["valid"] is True and got["task_id"] == "T-77"  # the file parses even though the guard is off
    assert got["always_allowed"] == [] and got["developer_rules"] is None
    bare = contract(make_project(tmp_path / "bare", None, None))
    assert bare["valid"] is False and bare["opted_in"] is False and "no active contract" in bare["message"]


def test_contract_never_raises_and_names_no_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")

    def fail(path: Path) -> tuple[int, str]:
        raise PermissionError(f"denied: {path}")

    monkeypatch.setattr(scope_guard, "check_contract", fail)
    got = contract(root)
    assert got["valid"] is False and "PermissionError" in got["message"]
    assert str(root) not in got["message"] and "<root>" in got["message"]
    assert got["task_id"] is None


# --- changed_outside -----------------------------------------------------------------

def _git_available() -> bool:
    return shutil.which("git") is not None


def git_project(base: Path) -> Path:
    root = make_project(base, "project.md", "contract.md")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True, timeout=60)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (root / "src" / "secret.py").write_text("y = 1\n", encoding="utf-8")
    (root / "tests" / "b.py").write_text("z = 1\n", encoding="utf-8")
    (root / "notes.txt").write_text("n\n", encoding="utf-8")
    (root / "STATUS.md").write_text("s\n", encoding="utf-8")
    return root


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_changed_outside_equals_check_worktree(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    got = changed_outside(root, False)
    code, outside, message = scope_guard.check_worktree(root, False)
    assert code == 1 and sorted(outside) == ["notes.txt", "src/secret.py"]
    assert got["ok"] is False and got["outside"] == outside and got["message"] == message
    assert "before the task started" in got["limit"]


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_changed_outside_is_ok_when_all_changes_are_inside(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    (root / "notes.txt").unlink()
    (root / "src" / "secret.py").unlink()
    got = changed_outside(root, False)
    assert got["ok"] is True and got["outside"] == [] and "all inside T-77" in got["message"]


def test_changed_outside_without_a_contract_does_not_raise(tmp_path: Path) -> None:
    got = changed_outside(make_project(tmp_path, "project.md", None))
    assert got["ok"] is False and got["outside"] == [] and "no active contract" in got["message"]


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_changed_outside_in_a_folder_that_is_not_a_repository(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    if subprocess.run(["git", "-C", str(root), "rev-parse"], capture_output=True, timeout=60).returncode == 0:
        pytest.skip("the temp folder is inside a repository")
    got = changed_outside(root)
    assert got["ok"] is False and got["outside"] == [] and "git status failed" in got["message"]
    assert str(root) not in got["message"]


def test_changed_outside_when_git_is_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")

    def no_git(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError(f"git not found near {root}")

    monkeypatch.setattr(scope_guard.subprocess, "run", no_git)
    got = changed_outside(root)
    assert got["ok"] is False and got["outside"] == [] and "git status failed" in got["message"]
    assert str(root) not in got["message"]


def test_changed_outside_never_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def crash(root: Path, casefold: bool) -> tuple[int, list[str], str]:
        raise RuntimeError(f"boom in {root}")

    monkeypatch.setattr(scope_guard, "check_worktree", crash)
    got = changed_outside(tmp_path)
    assert got["ok"] is False and "RuntimeError" in got["message"] and str(tmp_path) not in got["message"]


# --- guard_events --------------------------------------------------------------------

def test_guard_events_equals_the_totals(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md", "events.jsonl")
    got = guard_events(root)
    want = event_totals.totals(event_totals.read_events(root))
    assert got == {**want, "error": ""}
    assert (got["allow"], got["deny"], got["malformed"], got["other"]) == (4, 2, 3, 1)
    one = guard_events(root, "T-77")
    assert one == {**event_totals.totals(event_totals.read_events(root), "T-77"), "error": ""}
    assert list(one["tasks"]) == ["T-77"]


def test_guard_events_empty_task_means_all_and_the_text_is_trimmed(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md", "events.jsonl")
    assert guard_events(root, "") == guard_events(root, None) == guard_events(root, "  ")
    assert guard_events(root, " T-77 ") == guard_events(root, "T-77")


def test_guard_events_without_a_file_or_with_an_unreadable_one(tmp_path: Path) -> None:
    got = guard_events(make_project(tmp_path / "a", "project.md", None))
    assert (got["allow"], got["deny"], got["tasks"], got["malformed"], got["error"]) == (0, 0, {}, 0, "")
    (tmp_path / "b" / ".sdlc" / "metrics.jsonl").mkdir(parents=True)
    bad = guard_events(tmp_path / "b")
    assert bad["error"] == "the event file is not a regular file" and bad["tasks"] == {}
    assert str(tmp_path) not in json.dumps(bad)


def test_guard_events_refuses_a_bad_task_argument(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="task"):
        guard_events(tmp_path, "T-" + "1" * 60)
    with pytest.raises(ValueError, match="task"):
        guard_events(tmp_path, 5)  # type: ignore[arg-type]


def test_guard_events_names_no_path(tmp_path: Path) -> None:
    root = make_project(tmp_path / "project", "project.md", "contract.md", "events.jsonl")
    text = json.dumps(guard_events(root))
    assert str(root) not in text and ".jsonl" not in text and "project" not in text


# --- the tools through the SDK: refused arguments are tool errors with the reason ------------

def test_tool_errors_carry_the_reason(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    from mcp.server.mcpserver.exceptions import ToolError

    root = make_project(tmp_path, "project.md", "contract.md", "events.jsonl")
    server = server_main.build_server(RootLock(root), "x")

    async def run() -> list[str]:
        out: list[str] = []
        for tool, args in (("scope_check", {"paths": ["a.py"] * 51, "actor": "main"}),
                           ("scope_check", {"paths": ["a.py"], "actor": "root"}),
                           ("scope_check", {"paths": ["a.py"]}),
                           ("guard_events", {"task": "T-" + "1" * 60}),
                           ("decisions", {"id": "D" * 41}),
                           ("decisions", {"query": "q" * 101}),
                           ("lessons", {"query": "q" * 101}),
                           ("findings", {"status": "done"}),
                           ("findings", {"report": "r" * 101}),
                           ("tasks", {"id": "forty two"}),
                           ("log", {"count": 21}),
                           ("log", {"count": 0})):
            with pytest.raises(ToolError) as err:
                await server.call_tool(tool, args)
            out.append(str(err.value))
        return out

    texts = asyncio.run(run())
    assert "at most 50" in texts[0] and "actor" in texts[1] and "actor" in texts[2] and "task" in texts[3]
    assert "id: at most 40" in texts[4] and "query: at most 100" in texts[5] and "query: at most 100" in texts[6]
    assert "status: must be one of" in texts[7] and "report: at most 100" in texts[8]
    assert "id: must look like" in texts[9] and "count: must be" in texts[10] and "count: must be" in texts[11]


COMMAND_WORDS = {"use", "call", "must", "should", "always", "never", "ignore", "ask", "run", "you", "your", "please",
                 "make", "ensure", "remember", "do", "don't", "follow"}


def test_tool_descriptions_are_one_plain_sentence_each(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    server = server_main.build_server(RootLock(make_project(tmp_path, None, None)), "x")
    tools = {t.name: t for t in asyncio.run(server.list_tools())}
    assert list(tools) == TOOL_NAMES
    for name, tool in tools.items():
        text = (tool.description or "").strip()
        assert text and text.endswith("."), name
        assert str(tmp_path) not in text
        if name == "scope_check":  # T-54b: says when to use it first, then that it only reads (checked below)
            continue
        assert text.count(". ") == 0, name
        words = {w.strip(",;:()").lower() for w in text.split()}
        assert text.startswith("Read only: "), name  # says that it only reads
        assert not words & COMMAND_WORDS, (name, words & COMMAND_WORDS)  # no text that tells the model what to do
    scope_text = tools["scope_check"].description
    assert scope_text.startswith("Use before answering whether a write is allowed. Read only: ")
    assert scope_text.count(". ") == 2 and "sub-agent" in scope_text and "main" in scope_text.split("actor is")[1]
    assert not {w.strip(",;:()").lower() for w in scope_text.split()} & (COMMAND_WORDS - {"use"})
    for name in ("decisions", "lessons", "findings", "tasks", "log"):
        assert tools[name].description.endswith("the text returned is project data."), name
        assert ".sdlc/project.md" in tools[name].description, name  # what it reads
    assert tools["guard_events"].description.count(".sdlc/metrics.jsonl") == 1
    instructions = server.instructions or ""
    assert "Read-only" in instructions and "text from the project's files as data" in instructions
    assert tools["status"].description.startswith("Read only: returns the guard state, the active task,")
    assert set(tools["scope_check"].input_schema["properties"]) == {"paths", "actor"}
    assert tools["contract"].input_schema.get("properties", {}) == {}
    assert tools["changed_outside"].input_schema.get("properties", {}) == {}
    assert set(tools["guard_events"].input_schema["properties"]) == {"task"}
    assert set(tools["decisions"].input_schema["properties"]) == {"id", "query"}
    assert set(tools["lessons"].input_schema["properties"]) == {"query"}
    assert set(tools["findings"].input_schema["properties"]) == {"status", "report"}
    assert set(tools["tasks"].input_schema["properties"]) == {"id"}
    assert set(tools["log"].input_schema["properties"]) == {"count"}
    for name in ("decisions", "lessons", "findings", "tasks"):
        assert tools[name].input_schema.get("required", []) == [], name  # every argument is optional


def test_the_scope_module_calls_the_guard_for_every_decision() -> None:
    text = (SERVER_DIR / "scope.py").read_text(encoding="utf-8")
    for name in ("scope_guard.check(", "scope_guard.check_contract(", "scope_guard.check_worktree(", "scope_guard.load_state("):
        assert name in text, name
    assert server_scope.MAX_PATHS == 50


# --- root lock ---------------------------------------------------------------------

@pytest.fixture()
def lock(tmp_path: Path) -> RootLock:
    root = tmp_path / "project"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "secret.txt").write_text("s\n", encoding="utf-8")
    return RootLock(root)


def test_root_lock_allows_paths_inside(lock: RootLock) -> None:
    expect = (lock.root / "src" / "a.py").resolve()
    assert lock.resolve("src/a.py") == expect
    assert lock.resolve("src\\a.py") == expect
    assert lock.resolve("./src/../src/a.py") == expect
    assert lock.resolve(str(lock.root / "src" / "a.py")) == expect
    assert lock.resolve("src/missing.py") == (lock.root / "src" / "missing.py").resolve()


@pytest.mark.parametrize("raw", [
    "..", "../outside/secret.txt", "src/../../outside/secret.txt", "src\\..\\..\\outside\\secret.txt",
    "src/..\\..//outside/secret.txt", "../project2/x", "/etc/passwd", "C:\\Windows\\win.ini", "C:/Windows/win.ini",
    "//server/share/x", "", "\0", "src/a.py\0.txt",
    "\\\\host\\share\\x", "\\\\host\\share", "\\\\?\\C:\\Windows\\win.ini", "//?/C:/Windows/win.ini",  # UNC and device forms
    "C:x", "C:..\\x", "c:x/../y", "Z:", "D:\\",  # drive-relative and bare drives
])
def test_root_lock_denies(lock: RootLock, raw: str) -> None:
    with pytest.raises(RootLockError):
        lock.resolve(raw)


def test_root_lock_denies_an_absolute_path_outside(lock: RootLock, tmp_path: Path) -> None:
    for outside in (tmp_path / "outside" / "secret.txt", lock.root.parent / "project2" / "a.py", lock.root.parent):
        with pytest.raises(RootLockError):
            lock.resolve(str(outside))


def test_root_lock_denies_the_root_itself_and_non_strings(lock: RootLock) -> None:
    for raw in (".", str(lock.root), None, 5, b"src/a.py"):
        with pytest.raises(RootLockError):
            lock.resolve(raw)


def test_root_lock_error_does_not_repeat_the_path(lock: RootLock) -> None:
    with pytest.raises(RootLockError) as err:
        lock.resolve("../outside/secret.txt")
    assert "secret" not in str(err.value) and "outside/" not in str(err.value)


def test_root_lock_case_follows_the_flag(lock: RootLock) -> None:
    upper = str(lock.root).upper() + "/src/a.py"
    assert RootLock(lock.root, casefold=True).resolve(upper).name == "a.py"
    with pytest.raises(RootLockError):
        RootLock(lock.root, casefold=False).resolve(upper)
    assert lock.casefold is (os.name == "nt")


def _make_link(link: Path, target: Path) -> bool:
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":  # a junction needs no privilege
        res = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        return res.returncode == 0 and link.exists()
    return False


def test_root_lock_denies_a_link_pointing_outside(lock: RootLock, tmp_path: Path) -> None:
    link = lock.root / "link"
    if not _make_link(link, tmp_path / "outside"):
        pytest.skip("cannot create a symlink or junction here")
    for raw in ("link", "link/secret.txt", "link/new.txt"):
        with pytest.raises(RootLockError):
            lock.resolve(raw)


def test_root_lock_allows_a_link_pointing_inside(lock: RootLock) -> None:
    link = lock.root / "inner"
    if not _make_link(link, lock.root / "src"):
        pytest.skip("cannot create a symlink or junction here")
    assert lock.resolve("inner/a.py") == (lock.root / "src" / "a.py").resolve()


# --- start check -------------------------------------------------------------------

@pytest.mark.parametrize("version,ok", [
    ("2.3.0", True), ("2.3", True), ("2.9.12", True), ("2.3.0rc1", True), ("2.10.0", True),
    ("2.2.9", False), ("1.30.0", False), ("3.0.0", False), ("3.0.0a1", False), ("", False), ("dev", False),
])
def test_sdk_range(monkeypatch: pytest.MonkeyPatch, version: str, ok: bool) -> None:
    monkeypatch.setattr(server_main.metadata, "version", lambda name: version)
    assert (server_main.sdk_problem() is None) is ok
    if not ok:
        assert server_main.sdk_problem() == server_main.INSTALL_HINT


def test_sdk_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def gone(name: str) -> str:
        raise server_main.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(server_main.metadata, "version", gone)
    assert server_main.sdk_problem() == server_main.INSTALL_HINT
    assert 'pip install "mcp>=2.3,<3"' in server_main.INSTALL_HINT and "\n" not in server_main.INSTALL_HINT


def _run_entry_with_version(version_code: str) -> subprocess.CompletedProcess:
    driver = (
        "import importlib.metadata as m, runpy\n"
        f"m.version = {version_code}\n"
        f"runpy.run_path({str(ENTRY)!r}, run_name='__main__')\n"
    )
    return subprocess.run([sys.executable, "-I", "-c", driver], capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL)


def test_entry_without_mcp_exits_1_with_one_line() -> None:
    res = _run_entry_with_version("lambda name: (_ for _ in ()).throw(m.PackageNotFoundError(name))")
    assert res.returncode == 1
    assert res.stdout == ""
    assert res.stderr.strip() == server_main.INSTALL_HINT and len(res.stderr.strip().splitlines()) == 1


def test_entry_with_mcp_out_of_range_exits_1() -> None:
    for version in ("1.30.0", "3.0.0"):
        res = _run_entry_with_version(f"lambda name: {version!r}")
        assert res.returncode == 1 and res.stderr.strip() == server_main.INSTALL_HINT


def test_entry_with_a_bad_root_exits_1(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    res = subprocess.run([sys.executable, "-I", str(ENTRY)], capture_output=True, text=True, timeout=60,
                         env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path / "missing")},
                         stdin=subprocess.DEVNULL)
    assert res.returncode == 1 and "not a folder" in res.stderr


def test_resolve_root_prefers_the_variable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert server_main.resolve_root() == (tmp_path, "CLAUDE_PROJECT_DIR")
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    root, source = server_main.resolve_root()
    assert source == "start folder" and root == Path.cwd()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    assert server_main.resolve_root()[1] == "start folder"


# --- no network, read only, one rule in one place --------------------------------------

def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


NETWORK = {"socket", "ssl", "http", "urllib", "urllib3", "ftplib", "smtplib", "poplib", "imaplib", "telnetlib",
           "socketserver", "xmlrpc", "requests", "httpx", "httpx2", "aiohttp", "websockets", "uvicorn", "starlette",
           "sse_starlette", "selectors", "asyncio"}


LOOKUP = ROOT / "tools" / "lookup.py"


def tools_closure() -> list[Path]:
    """The `tools/` modules the server files import, and those they import in turn, as files."""
    found: dict[str, Path] = {}
    todo = list(SERVER_DIR.glob("*.py"))
    while todo:
        tree = ast.parse(todo.pop().read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if node.module == "tools":
                    names = [f"tools.{a.name}" for a in node.names]
                elif node.module.startswith("tools."):
                    names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names if a.name.startswith("tools.")]
            for name in names:
                target = ROOT.joinpath(*name.split(".")).with_suffix(".py")
                if name not in found and target.is_file():
                    found[name] = target
                    todo.append(target)
    return sorted(found.values())


def test_the_server_imports_exactly_these_tools_modules() -> None:
    # A new import here has to be read for network and write calls first: add it to this set on purpose.
    assert {p.name for p in tools_closure()} == {"events.py", "lookup.py", "records.py", "scope_guard.py"}


def test_server_modules_import_no_network_module() -> None:
    files = sorted(SERVER_DIR.glob("*.py"))
    assert len(files) >= 4
    for path in [*files, *tools_closure()]:
        assert not (_imports(path) & NETWORK), path.name


def test_server_runs_stdio_only() -> None:
    for path in SERVER_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for word in ("streamable", "run_sse", "sse_app", "http_app", "uvicorn", " port=", "host="):
            assert word not in text, (path.name, word)
    assert 'transport="stdio"' in ENTRY.read_text(encoding="utf-8")


WRITE_NAMES = {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "replace", "touch", "remove",
               "makedirs", "rmtree", "copy", "copyfile", "copytree", "move", "symlink_to", "chmod"}


def test_the_server_never_reaches_the_guard_event_writer() -> None:
    for path in SERVER_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "log_event" not in text and "scope_guard.main" not in text, path.name


def test_server_has_no_write_call() -> None:
    # tools/scope_guard.py is left out: its `log_event` appends the hook's event line, and the test above
    # shows that the server never calls it.
    for path in [*SERVER_DIR.glob("*.py"), *(p for p in tools_closure() if p.name != "scope_guard.py")]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Attribute):
                assert node.attr not in WRITE_NAMES, (path.name, node.attr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                mode = node.args[1] if len(node.args) > 1 else None
                assert mode is None or (isinstance(mode, ast.Constant) and set(str(mode.value)) <= set("rbt")), path.name


def test_server_defines_no_glob_or_path_matching_rule() -> None:
    banned_imports = {"fnmatch", "glob", "re"}
    banned_attrs = {"glob", "rglob", "match", "fullmatch", "fnmatch", "is_relative_to"}
    for path in SERVER_DIR.glob("*.py"):
        assert not (_imports(path) & banned_imports), path.name
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Attribute):
                assert node.attr not in banned_attrs, (path.name, node.attr)


def test_root_lock_uses_the_guard_function() -> None:
    assert "relative_to_root" in (SERVER_DIR / "rootlock.py").read_text(encoding="utf-8")
    assert "relative_to_root" in LOOKUP.read_text(encoding="utf-8")  # the record paths use the same text rule


def test_the_server_entry_only_wraps_the_lookup_functions() -> None:
    text = ENTRY.read_text(encoding="utf-8")
    for name in ("decisions", "lessons", "findings", "tasks", "log"):
        assert f"lookup_tools.{name}(lock.root" in text, name
    for word in ("read_bytes", "read_text", "iterdir", "open(", "splitlines", "json.loads"):
        assert word not in text, word  # no reading or parsing of its own


def test_tools_import_neither_server_nor_mcp() -> None:
    for path in sorted((ROOT / "tools").rglob("*.py")):
        assert not (_imports(path) & {"server", "mcp"}), path.relative_to(ROOT)


def test_the_entry_imports_mcp_only_inside_a_function() -> None:
    # A clone without the SDK must reach the install hint, so no top-level mcp import.
    tree = ast.parse(ENTRY.read_text(encoding="utf-8"))
    top = {a.name.split(".")[0] for n in tree.body if isinstance(n, ast.Import) for a in n.names}
    top |= {n.module.split(".")[0] for n in tree.body if isinstance(n, ast.ImportFrom) and n.module}
    assert "mcp" not in top
    assert "mcp" in _imports(ENTRY)


# --- plugin config -------------------------------------------------------------------

def test_plugin_manifest_registers_the_stdio_server() -> None:
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    ((name, entry),) = data["mcpServers"].items()
    assert name == "sdlc"
    assert entry["command"] == "python"
    assert entry["args"] == ["${CLAUDE_PLUGIN_ROOT}/server/main.py"]
    assert "url" not in entry and "type" not in entry
    assert ENTRY.is_file()
    assert not (ROOT / ".mcp.json").exists()  # this folder's own sessions would read it as project config


def test_json_files_use_lf() -> None:
    lines = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "*.json text eol=lf" in lines
    assert b"\r" not in (ROOT / ".claude-plugin" / "plugin.json").read_bytes()


# --- the SDK: registered tools and one stdio round trip ---------------------------------

def _block_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise OSError("network blocked in this test")

    monkeypatch.setattr(socket.socket, "__init__", blocked)
    for name in ("socketpair", "create_connection", "getaddrinfo", "gethostbyname", "create_server"):
        monkeypatch.setattr(socket, name, blocked)


def test_every_tool_runs_with_socket_creation_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    root = add_records(make_project(tmp_path, "project.md", "contract.md", "events.jsonl"))
    lock = RootLock(root)
    server = server_main.build_server(lock, "CLAUDE_PROJECT_DIR")

    async def run() -> dict[str, Any]:
        seen: dict[str, Any] = {}
        _block_sockets(monkeypatch)  # after the event loop exists; the loop's own sockets are already open
        try:
            with pytest.raises(OSError):
                socket.socket()  # the block works
            for tool in await server.list_tools():
                result = await server.call_tool(tool.name, TOOL_ARGS[tool.name])
                assert not result.is_error, tool.name
                seen[tool.name] = result.structured_content
        finally:
            monkeypatch.undo()
        return seen

    seen = asyncio.run(run())
    assert set(seen) == set(TOOL_ARGS) == set(TOOL_NAMES)
    for path in tools_closure():  # every tools/ module the server imports ran inside the socket-blocked calls
        assert f"tools.{path.stem}" in sys.modules, path.name
    assert seen["status"] == status(root, "CLAUDE_PROJECT_DIR")
    args = TOOL_ARGS["scope_check"]
    assert seen["scope_check"] == scope_check(lock.root, args["paths"], args["actor"], lock.casefold)
    assert seen["contract"] == contract(lock.root)
    assert seen["changed_outside"] == changed_outside(lock.root, lock.casefold)
    assert seen["guard_events"] == guard_events(lock.root)
    assert seen["guard_events"]["allow"] == 4 and seen["contract"]["task_id"] == "T-77"
    for name, want in lookup_answers(lock.root, lock.casefold).items():
        assert seen[name] == want, name
    assert seen["decisions"]["items"][0]["id"] == "DEC-002" and seen["log"]["items"][0]["n"] == 2
    assert seen["findings"]["total"] == 3 and seen["tasks"]["items"][0]["id"] == "T-2"


def test_guard_events_and_scope_check_pass_their_optional_arguments_through(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    root = add_records(make_project(tmp_path, "project.md", "contract.md", "events.jsonl"))
    lock = RootLock(root)
    server = server_main.build_server(lock, "x")
    guarded = [".sdlc/active-contract.md", "docs/other.md"]  # main may write the first, a sub-agent may not
    calls = [
        ("guard_events", {"task": "T-77"}),
        ("scope_check", {"paths": guarded, "actor": "main"}),
        ("scope_check", {"paths": guarded, "actor": "sub-agent"}),
    ]

    async def run() -> list[Any]:
        return [(await server.call_tool(tool, args)).structured_content for tool, args in calls]

    one, as_main, as_sub = asyncio.run(run())
    assert one == guard_events(lock.root, "T-77")
    assert one != guard_events(lock.root) and list(one["tasks"]) == ["T-77"]
    assert as_main == scope_check(lock.root, guarded, "main", lock.casefold)
    assert as_sub == scope_check(lock.root, guarded, "sub-agent", lock.casefold)
    assert as_main != as_sub and as_main["actor"] == "main"
    assert as_main["results"][0]["allow"] is True and as_sub["results"][0]["allow"] is False


def test_each_lookup_tool_equals_its_function(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    root = add_records(make_project(tmp_path, "project.md", None))
    lock = RootLock(root)
    server = server_main.build_server(lock, "x")
    calls = [
        ("decisions", {}, lambda: lookup.decisions(lock.root, None, None, lock.casefold)),
        ("decisions", {"query": "plain files"}, lambda: lookup.decisions(lock.root, None, "plain files", lock.casefold)),
        ("decisions", {"id": "dec-1", "query": None}, lambda: lookup.decisions(lock.root, "dec-1", None, lock.casefold)),
        ("lessons", {}, lambda: lookup.lessons(lock.root, None, lock.casefold)),
        ("findings", {}, lambda: lookup.findings(lock.root, None, None, lock.casefold)),
        ("findings", {"report": "gate1", "status": "OPEN"}, lambda: lookup.findings(lock.root, "OPEN", "gate1", lock.casefold)),
        ("tasks", {}, lambda: lookup.tasks(lock.root, None, lock.casefold)),
        ("tasks", {"id": "T-5a"}, lambda: lookup.tasks(lock.root, "T-5a", lock.casefold)),
        ("log", {}, lambda: lookup.log(lock.root, 5, lock.casefold)),
        ("log", {"count": 20}, lambda: lookup.log(lock.root, 20, lock.casefold)),
    ]

    async def run() -> list[Any]:
        return [(await server.call_tool(tool, args)).structured_content for tool, args, _want in calls]

    for got, (tool, args, want) in zip(asyncio.run(run()), calls):
        assert got == want(), (tool, args)


@pytest.mark.parametrize("entry", ["../outside.md", "..", "/etc/passwd", "C:\\Windows\\win.ini", "sub/../../outside.md",
                                   "\\\\host\\share\\outside.md", "//host/share/outside.md", "C:outside.md", "a\0b.md"])
def test_a_record_map_entry_outside_the_root_gives_an_error_answer_not_a_read(tmp_path: Path, entry: str) -> None:
    pytest.importorskip("mcp")
    (tmp_path / "outside.md").write_text("## DEC-001 Secret\n- Date: 2026-01-01\n", encoding="utf-8")
    root = add_records(tmp_path / "p")
    (root / ".sdlc").mkdir()
    lines = "".join(f"- {label}: `{entry}`\n" for label in ("Decisions", "Lessons", "Tasks", "Log", "Audits"))
    (root / ".sdlc" / "project.md").write_text("# Project file\n\n## Records\n" + lines, encoding="utf-8")
    server = server_main.build_server(RootLock(root), "x")

    async def run() -> dict[str, Any]:
        out = {}
        for tool in ("decisions", "lessons", "findings", "tasks", "log"):
            res = await server.call_tool(tool, {})
            assert not res.is_error, tool
            out[tool] = res.structured_content
        return out

    got = asyncio.run(run())
    for tool, answer in got.items():
        assert answer["error"] != "" and answer["total"] == 0, tool
        assert "Secret" not in json.dumps(answer) and str(tmp_path) not in json.dumps(answer), tool


async def _round_trip(env: dict[str, str] | None, cwd: Path | None) -> tuple[list[str], Any, dict[str, Any]]:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(command=sys.executable, args=["-I", str(ENTRY)], env=env, cwd=cwd)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = [t.name for t in (await session.list_tools()).tools]
            result = await session.call_tool("status", {})
            assert not result.is_error
            extra: dict[str, Any] = {}
            for name in TOOL_NAMES[1:]:
                res = await session.call_tool(name, TOOL_ARGS[name])
                assert not res.is_error, name
                extra[name] = res.structured_content
            for label, args in (("too_many", {"paths": ["a.py"] * 51, "actor": "main"}),
                                ("bad_actor", {"paths": ["a.py"], "actor": "root"})):
                res = await session.call_tool("scope_check", args)
                extra[label] = (res.is_error, res.content[0].text)
            return names, result.structured_content, extra


def test_stdio_round_trip_with_the_project_variable(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    project = add_records(make_project(tmp_path / "p", "project-custom.md", "contract.md", "events.jsonl"))
    (project / "plan").mkdir()  # the custom project file maps Tasks to plan/TASKS.md
    shutil.copyfile(project / "TASKS.md", project / "plan" / "TASKS.md")
    names, got, extra = asyncio.run(asyncio.wait_for(
        _round_trip({"CLAUDE_PROJECT_DIR": str(project)}, tmp_path), 90))
    assert sorted(names) == sorted(TOOL_NAMES) and len(names) == 10
    assert got == status(project, "CLAUDE_PROJECT_DIR")
    assert got["task_id"] == "T-77" and got["records"]["tasks"] == "plan/TASKS.md"
    args = TOOL_ARGS["scope_check"]
    assert extra["scope_check"] == scope_check(project, args["paths"], args["actor"])
    assert extra["contract"] == contract(project)
    assert extra["guard_events"] == guard_events(project)
    assert extra["changed_outside"] == changed_outside(project)
    for name, want in lookup_answers(project).items():
        assert extra[name] == want, name
    assert extra["decisions"]["items"][0]["id"] == "DEC-002" and extra["tasks"]["items"][0]["done"] is True
    assert extra["tasks"]["source"] == "plan/TASKS.md"
    assert extra["too_many"][0] is True and "at most 50" in extra["too_many"][1]
    assert extra["bad_actor"][0] is True and "actor" in extra["bad_actor"][1]
    assert str(tmp_path) not in json.dumps(extra)


def test_stdio_round_trip_from_the_start_folder(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    project = make_project(tmp_path / "p", None, None)
    names, got, extra = asyncio.run(asyncio.wait_for(_round_trip(None, project), 90))
    assert sorted(names) == sorted(TOOL_NAMES)
    assert got == status(project, "start folder")
    assert got["guard_state"] == "not-opted-in"
    assert extra["scope_check"]["guard_state"] == "not-opted-in"
    assert extra["guard_events"]["tasks"] == {}
    assert extra["decisions"]["error"] == "the decisions file does not exist" and extra["log"]["items"] == []


@pytest.mark.skipif(shutil.which("git") is None, reason="no git on PATH")
def test_server_files_are_not_ignored_by_git() -> None:
    paths = ["server/main.py", "server/status.py", "server/rootlock.py", "server/scope.py", "server/events.py",
             "server/inputs.py", "tools/events.py", "tools/lookup.py", "tools/records.py",
             "docs/security.md", "tests/fixtures/server/events.jsonl",
             "tests/fixtures/server/lookup/DECISIONS.md", "tests/fixtures/server/lookup/LESSONS.md",
             "tests/fixtures/server/lookup/TASKS.md", "tests/fixtures/server/lookup/LOG.md",
             "tests/fixtures/server/lookup/audits/2026-01-10_gate1.md"]
    res = subprocess.run(["git", "check-ignore", *paths], cwd=ROOT, capture_output=True, timeout=60)
    assert res.returncode == 1 and res.stdout == b""  # 1 = none of the paths is ignored


# =====================================================================================
# Security pass (T-44). Findings are in docs/security.md; the test names there point here.
# =====================================================================================

OUTSIDE_PROJECT = "# P\n\n## Records\n- Status: `OUTSIDE-MARKER.md`\n- Decisions: `OUTSIDE-MARKER.md`\n"
OUTSIDE_CONTRACT = "### T-5 outside\n- Files in: `OUTSIDE-MARKER/*`\n- Files out: `none`\n"
OUTSIDE_EVENT = '{"event": "scope", "decision": "allow", "task": "OUTSIDE-MARKER", "tool": "Write"}\n'


def _file_link(link: Path, target: Path) -> bool:
    try:
        os.symlink(target, link)
        return True
    except (OSError, NotImplementedError):
        return False


def test_the_sdlc_folder_as_a_link_pointing_outside_is_never_read(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "project.md").write_text(OUTSIDE_PROJECT, encoding="utf-8")
    (elsewhere / "active-contract.md").write_text(OUTSIDE_CONTRACT, encoding="utf-8")
    (elsewhere / "metrics.jsonl").write_text(OUTSIDE_EVENT, encoding="utf-8")
    root = tmp_path / "p"
    root.mkdir()
    if not _make_link(root / ".sdlc", elsewhere):
        pytest.skip("cannot create a symlink or junction here")
    answers = {"status": status(root), "contract": contract(root), "changed_outside": changed_outside(root),
               "guard_events": guard_events(root), "records": read_records(root)}
    with pytest.raises(ValueError, match="resolves outside the project root"):
        scope_check(root, ["a.py"], "main")
    for name, got in answers.items():
        assert "OUTSIDE-MARKER" not in json.dumps(got), name
        assert str(tmp_path) not in json.dumps(got), name
    assert answers["status"]["guard_state"] == "broken" and "resolves outside" in answers["status"]["broken_reason"]
    assert answers["records"] == read_records(tmp_path / "nothing-here")  # the template defaults
    assert answers["contract"]["valid"] is False and "resolves outside" in answers["contract"]["message"]
    assert answers["guard_events"]["error"] == "the event file resolves outside the project root"
    assert answers["changed_outside"]["ok"] is False and "git status was not run" in answers["changed_outside"]["message"]


@pytest.mark.parametrize("rel,fixture", [(".sdlc/project.md", "project.md"), (".sdlc/active-contract.md", "contract.md"),
                                         (".sdlc/metrics.jsonl", "events.jsonl")])
def test_a_control_file_that_is_a_link_pointing_outside_is_refused(tmp_path: Path, rel: str, fixture: str) -> None:
    root = make_project(tmp_path / "p", "project.md", "contract.md", "events.jsonl")
    secret = tmp_path / "secret.txt"
    secret.write_bytes((FIXTURES / fixture).read_bytes())  # a valid file: followed, it would be read as one
    (root / rel).unlink()
    if not _file_link(root / rel, secret):
        pytest.skip("cannot create a file symlink here")
    if rel.endswith(".jsonl"):
        assert guard_events(root)["error"] == "the event file resolves outside the project root"
        assert guard_events(root)["allow"] == 0
    else:
        assert status(root)["guard_state"] == "broken"
        assert "resolves outside the project root" in status(root)["broken_reason"]
        assert contract(root)["valid"] is False
        with pytest.raises(ValueError, match="cannot be used"):
            scope_check(root, ["a.py"], "main")
        if rel.endswith("project.md"):
            assert read_records(root)["status"] == "STATUS.md" and read_records(root) == read_records(tmp_path / "none")


def test_a_control_file_over_the_size_limit_is_refused_and_one_at_the_limit_is_read(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    path = root / ".sdlc" / "project.md"
    base = path.read_bytes()
    path.write_bytes(base + b"\n" + b"x" * (server_inputs.CONTROL_LIMIT - len(base) - 1))
    assert path.stat().st_size == server_inputs.CONTROL_LIMIT
    assert status(root)["guard_state"] == "active" and server_inputs.control_problem(root) == ""
    path.write_bytes(path.read_bytes() + b"x")
    got = status(root)
    assert got["guard_state"] == "broken" and "larger than 256000 bytes" in got["broken_reason"]
    assert contract(root)["valid"] is False and changed_outside(root)["ok"] is False
    with pytest.raises(ValueError, match="larger than"):
        scope_check(root, ["a.py"], "main")


@pytest.mark.parametrize("line", ["# a" + " " * 17 + "x", "## " + "\t" * 17 + "x", "### a" + "#" * 17 + "x",
                                  "   # a" + " \t" * 9 + "x", "# a" + " " * 3000 + "x", "#" + " " * 20000 + "x"])
@pytest.mark.parametrize("name", ["project.md", "active-contract.md"])
def test_a_heading_with_a_long_run_is_parsed_by_the_guard_without_a_refusal(tmp_path: Path, line: str, name: str) -> None:
    # The old guard pattern needed about 13 s for a 2,000-space run (S-6); the server used to refuse the line.
    # Now the guard parses it in one pass, so the server hands the file over: a heading in the project file
    # is read as usual, a second heading in the contract is the contract's own error.
    root = make_project(tmp_path, "project.md", "contract.md")
    path = root / ".sdlc" / name
    path.write_bytes(path.read_bytes() + ("\n" + line + "\n").encode("utf-8"))
    started = time.perf_counter()
    got = status(root)
    assert server_inputs.control_problem(root) == ""
    if name == "project.md":
        assert got["guard_state"] == "active" and contract(root)["valid"] is True
        assert scope_check(root, ["src/a.py"], "sub-agent")["guard_state"] == "active"
    else:
        assert got["guard_state"] == "broken" and "second heading" in got["broken_reason"]
        assert contract(root)["valid"] is False
        assert scope_check(root, ["src/a.py"], "sub-agent")["results"][0]["allow"] is False
    assert time.perf_counter() - started < 2


def test_a_heading_with_a_short_run_is_read_as_usual(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    path = root / ".sdlc" / "project.md"
    path.write_bytes(path.read_bytes() + ("\n## Notes" + " " * 16 + "x\n\n#" + "#" * 5 + " six\n").encode("utf-8"))
    assert status(root)["guard_state"] == "active" and server_inputs.control_problem(root) == ""


def test_the_missing_control_files_are_not_a_problem(tmp_path: Path) -> None:
    assert server_inputs.control_problem(tmp_path) == ""
    assert server_inputs.control_problem(make_project(tmp_path / "a", "project.md", None)) == ""
    (tmp_path / "b" / ".sdlc").mkdir(parents=True)
    (tmp_path / "b" / ".sdlc" / "project.md").mkdir()  # a folder in place of the file
    assert "not a regular file" in server_inputs.control_problem(tmp_path / "b")


# --- leaks ---------------------------------------------------------------------------

def test_scrub_removes_the_root_and_the_home_folder_in_every_form(tmp_path: Path) -> None:
    root = tmp_path / "project"
    home = Path.home()
    text = (f"a {root} b {root.as_posix()} c {repr(str(root))[1:-1]} d {home} e {home.as_posix()}/.gitconfig "
            f"f {repr(str(home))[1:-1]}")
    got = server_inputs.scrub(text, root)
    for form in (str(root), root.as_posix(), repr(str(root))[1:-1], str(home), home.as_posix(), repr(str(home))[1:-1]):
        assert form not in got, form
    assert got.count("<root>") == 3 and got.count("<home>") >= 3


def test_an_error_text_from_the_guard_carries_no_root_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = make_project(tmp_path / "p", "project.md", None)
    (root / ".sdlc" / "active-contract.md").mkdir()  # the guard's read fails with an OS message that names the file
    monkeypatch.setattr(server_status, "control_problem", lambda r: "")  # let the guard see it, to test the scrub
    monkeypatch.setattr(server_scope, "control_problem", lambda r: "")
    got = status(root)
    assert got["guard_state"] == "broken" and got["broken_reason"] != ""
    rows = scope_check(root, ["src/a.py", "../x"], "sub-agent")["results"]
    texts = [json.dumps(got), json.dumps(rows), json.dumps(contract(root))]
    for text in texts:
        for form in (str(root), root.as_posix(), repr(str(root))[1:-1], str(Path.home()), Path.home().as_posix()):
            assert form not in text, form


def test_a_contract_that_is_a_folder_is_refused_with_no_path(tmp_path: Path) -> None:
    root = make_project(tmp_path / "p", "project.md", None)
    (root / ".sdlc" / "active-contract.md").mkdir()
    got = status(root)
    assert got["guard_state"] == "broken" and "not a regular file" in got["broken_reason"]
    assert str(tmp_path) not in json.dumps([got, contract(root), changed_outside(root)])
    with pytest.raises(ValueError) as err:
        scope_check(root, ["a.py"], "main")
    assert str(tmp_path) not in str(err.value)


def test_no_tool_answer_holds_the_root_or_a_home_path(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    from mcp.server.mcpserver.exceptions import ToolError

    good = add_records(git_project(tmp_path / "good"))
    (good / ".sdlc" / "metrics.jsonl").write_bytes((FIXTURES / "events.jsonl").read_bytes())
    hostile = add_records(make_project(tmp_path / "hostile", None, None))
    (hostile / ".sdlc").mkdir(exist_ok=True)
    # `status` repeats the map as written, so an absolute entry would show up there; the file's own text is not a leak
    entries = "".join(f"- {label}: `../outside.md`\n" for label in ("Decisions", "Lessons", "Tasks", "Log", "Audits"))
    (hostile / ".sdlc" / "project.md").write_text("# P\n\n## Records\n" + entries, encoding="utf-8")
    (hostile / ".sdlc" / "active-contract.md").mkdir()
    (hostile / ".sdlc" / "metrics.jsonl").mkdir()
    args = dict(TOOL_ARGS)
    args["scope_check"] = {"paths": ["src/a.py", "../outside.txt", str(good / "src" / "a.py"), "x" * 600], "actor": "main"}

    async def run(root: Path) -> dict[str, str]:
        server = server_main.build_server(RootLock(root), "CLAUDE_PROJECT_DIR")
        out: dict[str, str] = {}
        for name in TOOL_NAMES:
            try:
                result = await server.call_tool(name, args[name])
                out[name] = json.dumps(result.structured_content)
            except ToolError as exc:
                out[name] = str(exc)
        return out

    home = Path.home()
    for root in (good, hostile):
        answers = asyncio.run(run(root))
        assert set(answers) == set(TOOL_NAMES)
        for name, text in answers.items():
            for form in (str(root), root.as_posix(), repr(str(root))[1:-1], str(tmp_path), tmp_path.as_posix(),
                         str(home), home.as_posix(), repr(str(home))[1:-1]):
                assert form not in text, (root.name, name, form)
    good_rows = json.loads(asyncio.run(run(good))["scope_check"])["results"]
    assert good_rows[2]["path"] == "src/a.py" and good_rows[0]["path"] == "src/a.py"


def test_status_and_contract_answers_are_bounded(tmp_path: Path) -> None:
    root = tmp_path / "p"
    (root / ".sdlc").mkdir(parents=True)
    extras = "".join(f"- Extra{i}: `{'v' * 500}`\n" for i in range(100))
    allowed = ", ".join(f"`p{i}`" for i in range(2000))
    (root / ".sdlc" / "project.md").write_text(f"# P\n\n## Records\n{extras}\n## Always allowed\n- {allowed}\n", encoding="utf-8")
    (root / ".sdlc" / "active-contract.md").write_text(
        f"### T-1 x\n- Files in: {allowed}\n- Files out: {allowed}\n", encoding="utf-8")
    got = status(root)
    assert len(got["records"]) == server_inputs.MAX_RECORD_NAMES == 40
    assert max(len(v) for v in got["records"].values()) == server_inputs.MAX_RECORD_VALUE == 200
    assert len(got["files_in"]) == len(got["files_out"]) == server_inputs.MAX_PATTERNS == 500 and got["cut"] is True
    sure = contract(root)
    assert sure["valid"] is True and sure["cut"] is True
    assert len(sure["always_allowed"]) == len(sure["files_in"]) == len(sure["files_out"]) == 500
    normal = make_project(tmp_path / "n", "project.md", "contract.md")
    assert "cut" not in status(normal) and "cut" not in contract(normal)  # an ordinary answer is not touched


# --- git -----------------------------------------------------------------------------

def git_commit(root: Path, *paths: str) -> None:
    identity = ["-c", "user.name=T", "-c", "user.email=t@users.noreply.github.com"]
    for args in (["add", *paths], [*identity, "commit", "-q", "-m", "i"]):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, timeout=60)


def _no_git_run(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("git was started")

    monkeypatch.setattr(scope_guard.subprocess, "run", refuse)


@pytest.mark.parametrize("config", [
    '[filter "x"]\n\tclean = sh -c evil\n', '[ filter "x" ]\n\tclean = evil\n', '[FILTER "x"]\n', '  [filter]\n',
    '[include]\n\tpath = ../evil\n', '[includeIf "gitdir:/"]\n\tpath = x\n',
    '[remote "origin"]\n\turl = x\n[filter "lfs"]\n\tclean = git-lfs clean\n',
])
def test_changed_outside_does_not_start_git_for_a_config_with_a_filter_or_include(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, config: str) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("[core]\n\tbare = false\n" + config, encoding="utf-8")
    _no_git_run(monkeypatch)
    got = changed_outside(root)
    assert got["ok"] is False and got["outside"] == [] and "git status was not run" in got["message"]
    assert "filter or an include" in got["message"] and str(tmp_path) not in got["message"]


def test_changed_outside_looks_at_the_config_of_a_repository_above_the_root(monkeypatch: pytest.MonkeyPatch,
                                                                            tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text('[filter "x"]\n\tclean = evil\n', encoding="utf-8")
    root = make_project(tmp_path / "app", "project.md", "contract.md")
    _no_git_run(monkeypatch)
    assert "filter or an include" in changed_outside(root)["message"]


def test_changed_outside_does_not_start_git_for_a_dot_git_file_or_link(monkeypatch: pytest.MonkeyPatch,
                                                                       tmp_path: Path) -> None:
    root = make_project(tmp_path / "a", "project.md", "contract.md")
    (root / ".git").write_text("gitdir: ../elsewhere\n", encoding="utf-8")
    other = make_project(tmp_path / "b", "project.md", "contract.md")
    gitdir = tmp_path / "gitdir"
    gitdir.mkdir()
    (gitdir / "config").write_text("[core]\n\tbare = false\n", encoding="utf-8")
    linked = _make_link(other / ".git", gitdir)  # before the patch: the junction helper starts a process
    _no_git_run(monkeypatch)
    assert "linked worktree or a submodule" in changed_outside(root)["message"]
    if not linked:
        pytest.skip("cannot create a symlink or junction here")
    message = changed_outside(other)["message"]
    assert "git status was not run" in message and ("link" in message or "outside" in message)


def test_a_plain_repository_config_is_not_a_git_problem(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    if any((p / ".git").exists() for p in (root.resolve(), *root.resolve().parents)):
        pytest.skip("the temp folder is inside a repository")
    assert server_inputs.git_problem(root) == ""  # no repository: git itself will say so
    (root / ".git").mkdir()
    assert server_inputs.git_problem(root) == ""  # a repository with no config file
    (root / ".git" / "config").write_text('[core]\n\tbare = false\n[remote "origin"]\n\turl = x\n'
                                          '[branch "main"]\n\tremote = origin\n# [filter "x"] in a comment\n', encoding="utf-8")
    assert server_inputs.git_problem(root) == ""


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_a_clean_filter_in_the_repository_config_is_not_run_by_changed_outside(tmp_path: Path) -> None:
    root = git_project(tmp_path / "r")
    git_commit(root, "src/a.py")
    marker = tmp_path / "filter-ran"
    script = tmp_path / "clean.sh"
    script.write_text(f'#!/bin/sh\n: > "{marker.as_posix()}"\ncat\n', encoding="utf-8", newline="\n")
    (root / ".gitattributes").write_text("* filter=probe\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "config", "filter.probe.clean", f"sh {script.as_posix()}"], cwd=root, check=True, timeout=60)
    later = time.time() + 30  # only the time changed: git compares the content through the filter
    os.utime(root / "src" / "a.py", (later, later))
    scope_guard.check_worktree(root, False)  # control run: the guard's own call does start the program
    if not marker.exists():
        pytest.skip("this git does not run a clean filter on status here")
    marker.unlink()
    got = changed_outside(root, False)
    assert not marker.exists()
    assert got["ok"] is False and "filter or an include" in got["message"]


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_changed_outside_runs_git_for_a_repository_without_a_filter(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    assert server_inputs.git_problem(root) == ""
    assert sorted(changed_outside(root, False)["outside"]) == ["notes.txt", "src/secret.py"]


def _filter_probe(tmp_path: Path) -> tuple[str, Path]:
    """A clean filter command that appends a line to a marker file, and that marker (outside the project)."""
    marker = tmp_path / "filter-ran"
    script = tmp_path / "clean.sh"
    script.write_text(f'#!/bin/sh\necho x >> "{marker.as_posix()}"\ncat\n', encoding="utf-8", newline="\n")
    return f"sh {script.as_posix()}", marker


def _marker_lines(marker: Path) -> int:
    return len(marker.read_text(encoding="utf-8").splitlines()) if marker.exists() else 0


def _nested_repository_in(root: Path, command: str | None) -> Path:
    """`vendor/lib` is a repository of its own, committed in `root` as a gitlink; its own config names the filter."""
    nested = root / "vendor" / "lib"
    nested.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=nested, check=True, capture_output=True, timeout=60)
    (nested / "a.txt").write_text("a\n", encoding="utf-8", newline="\n")
    (nested / ".gitattributes").write_text("* filter=probe\n", encoding="utf-8", newline="\n")
    git_commit(nested, "a.txt", ".gitattributes")
    git_commit(root, "src/a.py", "vendor/lib")
    if command is not None:
        subprocess.run(["git", "config", "filter.probe.clean", command], cwd=nested, check=True, timeout=60)
    later = time.time() + 30  # only the time changed: git compares the content through the filter
    os.utime(nested / "a.txt", (later, later))
    return nested


def _as_a_git_folder(root: Path, command: str | None) -> None:
    """The project root laid out as a git folder: HEAD, objects, refs, index, config at the root, `core.worktree = .`."""
    for entry in list((root / ".git").iterdir()):
        shutil.move(str(entry), str(root / entry.name))
    (root / ".git").rmdir()
    settings = [("core.worktree", ".")] + ([("filter.probe.clean", command)] if command is not None else [])
    for key, value in settings:
        subprocess.run(["git", "config", "--file", str(root / "config"), key, value], check=True, timeout=60)
    (root / ".gitattributes").write_text("* filter=probe\n", encoding="utf-8", newline="\n")
    later = time.time() + 30
    os.utime(root / "src" / "a.py", (later, later))


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_a_filter_in_a_nested_repository_is_not_run_by_changed_outside(tmp_path: Path) -> None:
    command, marker = _filter_probe(tmp_path)
    clean = git_project(tmp_path / "control")
    _nested_repository_in(clean, None)
    assert server_inputs.git_problem(clean) == ""
    assert changed_outside(clean, False)["ok"] is False and _marker_lines(marker) == 0  # no filter: nothing to run
    root = git_project(tmp_path / "r")
    _nested_repository_in(root, command)
    assert server_inputs.git_problem(root) == ""  # the config git would read is not the one S-3 looks at
    subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, timeout=60)
    if _marker_lines(marker) == 0:
        pytest.skip("this git does not run a clean filter of a nested repository on status here")
    marker.unlink()  # control run above: plain git did start the program
    got = changed_outside(root, False)
    assert _marker_lines(marker) == 0
    assert sorted(got["outside"]) == ["notes.txt", "src/secret.py"]  # the other changes are still found
    assert "nested" in got["limit"]


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_a_root_laid_out_as_a_git_folder_does_not_run_its_filter_through_changed_outside(tmp_path: Path) -> None:
    command, marker = _filter_probe(tmp_path)
    clean = git_project(tmp_path / "control")
    git_commit(clean, "src/a.py")
    _as_a_git_folder(clean, None)
    assert changed_outside(clean, False)["ok"] is False  # the control layout is refused as well
    assert _marker_lines(marker) == 0
    root = git_project(tmp_path / "r")
    git_commit(root, "src/a.py")
    _as_a_git_folder(root, command)
    subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, timeout=60)
    if _marker_lines(marker) == 0:
        pytest.skip("this git does not run a clean filter from a root laid out as a git folder here")
    marker.unlink()  # control run above: plain git did start the program
    got = changed_outside(root, False)
    assert _marker_lines(marker) == 0
    assert got["ok"] is False and got["outside"] == []
    assert "git status was not run" in got["message"] and "git folder" in got["message"]
    assert str(tmp_path) not in got["message"]


@pytest.mark.parametrize("parts", [("objects",), ("refs",), ("commondir",), ("objects", "refs")])
def test_changed_outside_does_not_start_git_for_a_folder_laid_out_as_a_git_folder(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, parts: tuple[str, ...]) -> None:
    root = make_project(tmp_path / "a", "project.md", "contract.md")
    (root / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    for name in parts:
        (root / name).mkdir()
    above = make_project(tmp_path / "b" / "app", "project.md", "contract.md")  # the git folder is above the root
    (above.parent / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (above.parent / parts[0]).mkdir()
    _no_git_run(monkeypatch)
    for where in (root, above):
        got = changed_outside(where)
        assert got["ok"] is False and got["outside"] == []
        assert "git status was not run" in got["message"] and "git folder" in got["message"]


def test_a_head_file_or_an_objects_folder_alone_is_not_a_git_folder(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    if any((p / ".git").exists() for p in (root.resolve(), *root.resolve().parents)):
        pytest.skip("the temp folder is inside a repository")
    (root / "HEAD").write_text("x\n", encoding="utf-8")
    assert server_inputs.git_problem(root) == ""
    (root / "HEAD").unlink()
    (root / "objects").mkdir()
    (root / "refs").mkdir()
    assert server_inputs.git_problem(root) == ""  # git needs HEAD as well
    (root / ".git").mkdir()
    (root / "HEAD").write_text("x\n", encoding="utf-8")
    assert server_inputs.git_problem(root) == ""  # a `.git` entry is looked at first, as git does


def test_changed_outside_asks_git_not_to_take_optional_locks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    seen: list[str | None] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        seen.append(os.environ.get("GIT_OPTIONAL_LOCKS"))
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(scope_guard.subprocess, "run", fake_run)
    monkeypatch.delenv("GIT_OPTIONAL_LOCKS", raising=False)
    assert changed_outside(root)["ok"] is True
    assert seen == ["0", "0"] and "GIT_OPTIONAL_LOCKS" not in os.environ  # rev-parse and status; the variable is put back
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "1")
    changed_outside(root)
    assert os.environ["GIT_OPTIONAL_LOCKS"] == "1"


@pytest.mark.skipif(not _git_available(), reason="no git on PATH")
def test_changed_outside_leaves_the_git_index_alone(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    git_commit(root, "src/a.py")
    later = time.time() + 30
    os.utime(root / "src" / "a.py", (later, later))  # a stale stat entry: plain `git status` would refresh the index
    index = root / ".git" / "index"
    before = index.read_bytes()
    assert sorted(changed_outside(root, False)["outside"]) == ["notes.txt", "src/secret.py"]
    assert index.read_bytes() == before
    subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True, timeout=60)
    if index.read_bytes() == before:
        pytest.skip("this git did not rewrite the index in the control run, so the test could not tell")


# --- argument limits -----------------------------------------------------------------

# Every argument of every tool, with the call that must be refused. A new argument without a row fails the first test.
REFUSED_ARGUMENTS: dict[tuple[str, str], tuple[dict[str, Any], str]] = {
    ("scope_check", "paths"): ({"paths": ["a.py"] * 51, "actor": "main"}, "at most 50"),
    ("scope_check", "actor"): ({"paths": ["a.py"], "actor": "root"}, "actor"),
    ("guard_events", "task"): ({"task": "T-" + "1" * 60}, "at most 40"),
    ("decisions", "id"): ({"id": "D" * 41}, "id: at most 40"),
    ("decisions", "query"): ({"query": "q" * 101}, "query: at most 100"),
    ("lessons", "query"): ({"query": "q" * 101}, "query: at most 100"),
    ("findings", "status"): ({"status": "done"}, "status: must be one of"),
    ("findings", "report"): ({"report": "r" * 101}, "report: at most 100"),
    ("tasks", "id"): ({"id": "x" * 41}, "id: at most 40"),
    ("log", "count"): ({"count": 21}, "count: must be"),
}


def test_every_argument_of_every_tool_has_a_limit_that_refuses(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    from mcp.server.mcpserver.exceptions import ToolError

    root = add_records(make_project(tmp_path, "project.md", "contract.md", "events.jsonl"))
    server = server_main.build_server(RootLock(root), "x")
    tools = {t.name: t for t in asyncio.run(server.list_tools())}
    declared = {(name, arg) for name, tool in tools.items() for arg in tool.input_schema.get("properties", {})}
    assert declared == set(REFUSED_ARGUMENTS)

    async def run() -> dict[tuple[str, str], str]:
        out: dict[tuple[str, str], str] = {}
        for (tool, arg), (args, _word) in REFUSED_ARGUMENTS.items():
            with pytest.raises(ToolError) as err:
                await server.call_tool(tool, args)
            out[(tool, arg)] = str(err.value)
        return out

    for key, text in asyncio.run(run()).items():
        assert REFUSED_ARGUMENTS[key][1] in text, key
        assert str(tmp_path) not in text and "q" * 20 not in text and "D" * 20 not in text  # the value is not echoed


def test_each_argument_accepts_its_limit(tmp_path: Path) -> None:
    root = add_records(make_project(tmp_path, "project.md", "contract.md", "events.jsonl"))
    assert len(scope_check(root, ["a.py"] * 50, "main")["results"]) == 50
    assert guard_events(root, "T-" + "1" * 38)["error"] == ""
    assert lookup.decisions(root, "D" * 38 + "-1", "q" * 100)["error"] == ""
    assert lookup.lessons(root, "q" * 100)["error"] == "" and lookup.findings(root, "closed", "r" * 100)["error"] == ""
    assert lookup.tasks(root, "T" * 38 + "-1")["error"] == "" and lookup.log(root, 20)["error"] == ""


@pytest.mark.parametrize("opted_in", [True, False])
def test_scope_check_limits_one_path_to_500_characters(tmp_path: Path, opted_in: bool) -> None:
    root = make_project(tmp_path, "project.md" if opted_in else None, "contract.md" if opted_in else None)
    ok, long = "src/" + "a" * 496, "src/" + "a" * 497
    assert len(ok) == server_scope.PATH_LIMIT and len(long) == server_scope.PATH_LIMIT + 1
    first, second = scope_check(root, [ok, long], "main")["results"]
    assert "longer than" not in first["reason"]
    assert second["allow"] is False and second["reason"] == "the path is longer than 500 characters"
    assert long not in json.dumps(second)


# --- sizes of the control files and the event file --------------------------------------

def test_an_event_file_over_the_limit_is_an_error_answer_and_one_at_the_limit_is_read(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project.md", "contract.md")
    path = root / ".sdlc" / "metrics.jsonl"
    path.write_bytes(b"\n" * event_totals.MAX_BYTES)
    assert guard_events(root)["error"] == "" and guard_events(root)["tasks"] == {}
    path.write_bytes(b"\n" * (event_totals.MAX_BYTES + 1))
    got = guard_events(root)
    assert got["error"] == f"the event file is larger than {event_totals.MAX_BYTES} bytes" and got["tasks"] == {}


def test_a_project_file_over_2_mb_gives_the_template_defaults(tmp_path: Path) -> None:
    root = tmp_path / "p"
    (root / ".sdlc").mkdir(parents=True)
    head = b"# P\n\n## Records\n- Status: `CUSTOM.md`\n"
    (root / ".sdlc" / "project.md").write_bytes(head + b"x" * (2_000_000 - len(head)))
    assert read_records(root)["status"] == "CUSTOM.md"
    (root / ".sdlc" / "project.md").write_bytes(head + b"x" * (2_000_001 - len(head)))
    assert read_records(root)["status"] == "STATUS.md"


def test_the_event_file_and_the_project_file_may_be_folders_without_a_hang(tmp_path: Path) -> None:
    root = tmp_path / "p"
    (root / ".sdlc").mkdir(parents=True)
    (root / ".sdlc" / "metrics.jsonl").mkdir()
    (root / ".sdlc" / "project.md").mkdir()
    started = time.perf_counter()
    assert guard_events(root)["error"] == "the event file is not a regular file"
    assert read_records(root)["status"] == "STATUS.md"
    assert time.perf_counter() - started < 5
