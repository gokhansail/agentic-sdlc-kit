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
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import main as server_main  # noqa: E402
from server import scope as server_scope  # noqa: E402
from server.events import guard_events  # noqa: E402
from server.rootlock import RootLock, RootLockError  # noqa: E402
from server.scope import changed_outside, contract, scope_check  # noqa: E402
from server.status import status  # noqa: E402
from tools import events as event_totals  # noqa: E402
from tools import scope_guard  # noqa: E402
from tools.records import read_records  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "server"
SERVER_DIR = ROOT / "server"
ENTRY = SERVER_DIR / "main.py"
TOOL_NAMES = ["status", "scope_check", "contract", "changed_outside", "guard_events"]
TOOL_ARGS: dict[str, dict[str, Any]] = {  # a tool with arguments adds its entry here
    "status": {},
    "scope_check": {"paths": ["src/a.py", "src/secret.py", "../outside.txt", "STATUS.md"], "actor": "sub-agent"},
    "contract": {},
    "changed_outside": {},
    "guard_events": {},
}


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
    assert none["guard_state"] == scope_guard.NO_CONTRACT and none["always_allowed"] == ["STATUS.md", "LOG.md"]
    broken = contract(make_project(tmp_path / "b", "project.md", "contract-broken.md"))
    assert broken["valid"] is False and broken["task_id"] is None and broken["files_in"] == []
    assert broken["message"] == scope_guard.check_contract(tmp_path / "b")[1] and "active-contract.md" in broken["message"]
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
    assert bad["error"] == "the event file could not be read" and bad["tasks"] == {}
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
                           ("guard_events", {"task": "T-" + "1" * 60})):
            with pytest.raises(ToolError) as err:
                await server.call_tool(tool, args)
            out.append(str(err.value))
        return out

    texts = asyncio.run(run())
    assert "at most 50" in texts[0] and "actor" in texts[1] and "actor" in texts[2] and "task" in texts[3]


def test_tool_descriptions_are_one_plain_sentence_each(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    server = server_main.build_server(RootLock(make_project(tmp_path, None, None)), "x")
    tools = {t.name: t for t in asyncio.run(server.list_tools())}
    assert list(tools) == TOOL_NAMES
    for name, tool in tools.items():
        text = (tool.description or "").strip()
        assert text and text.endswith(".") and text.count(". ") == 0, name
        assert str(tmp_path) not in text
    assert tools["status"].description == "Guard state, active task, Files in and Files out, and the record file names of this project."
    assert set(tools["scope_check"].input_schema["properties"]) == {"paths", "actor"}
    assert tools["contract"].input_schema.get("properties", {}) == {}
    assert tools["changed_outside"].input_schema.get("properties", {}) == {}
    assert set(tools["guard_events"].input_schema["properties"]) == {"task"}


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


def test_server_modules_import_no_network_module() -> None:
    files = sorted(SERVER_DIR.glob("*.py"))
    assert len(files) >= 4
    for path in files:
        assert not (_imports(path) & NETWORK), path.name


def test_server_runs_stdio_only() -> None:
    for path in SERVER_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for word in ("streamable", "run_sse", "sse_app", "http_app", "uvicorn", " port=", "host="):
            assert word not in text, (path.name, word)
    assert 'transport="stdio"' in ENTRY.read_text(encoding="utf-8")


WRITE_NAMES = {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "replace", "touch", "remove",
               "makedirs", "rmtree", "copy", "copyfile", "copytree", "move", "symlink_to", "chmod"}


def test_server_has_no_write_call() -> None:
    for path in SERVER_DIR.glob("*.py"):
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
    root = make_project(tmp_path, "project.md", "contract.md", "events.jsonl")
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
    assert seen["status"] == status(root, "CLAUDE_PROJECT_DIR")
    args = TOOL_ARGS["scope_check"]
    assert seen["scope_check"] == scope_check(lock.root, args["paths"], args["actor"], lock.casefold)
    assert seen["contract"] == contract(lock.root)
    assert seen["changed_outside"] == changed_outside(lock.root, lock.casefold)
    assert seen["guard_events"] == guard_events(lock.root)
    assert seen["guard_events"]["allow"] == 4 and seen["contract"]["task_id"] == "T-77"


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
    project = make_project(tmp_path / "p", "project-custom.md", "contract.md", "events.jsonl")
    names, got, extra = asyncio.run(asyncio.wait_for(
        _round_trip({"CLAUDE_PROJECT_DIR": str(project)}, tmp_path), 90))
    assert sorted(names) == sorted(TOOL_NAMES) and len(names) == 5
    assert got == status(project, "CLAUDE_PROJECT_DIR")
    assert got["task_id"] == "T-77" and got["records"]["tasks"] == "plan/TASKS.md"
    args = TOOL_ARGS["scope_check"]
    assert extra["scope_check"] == scope_check(project, args["paths"], args["actor"])
    assert extra["contract"] == contract(project)
    assert extra["guard_events"] == guard_events(project)
    assert extra["changed_outside"] == changed_outside(project)
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


@pytest.mark.skipif(shutil.which("git") is None, reason="no git on PATH")
def test_server_files_are_not_ignored_by_git() -> None:
    paths = ["server/main.py", "server/status.py", "server/rootlock.py", "server/scope.py", "server/events.py",
             "tools/events.py", "tests/fixtures/server/events.jsonl"]
    res = subprocess.run(["git", "check-ignore", *paths], cwd=ROOT, capture_output=True, timeout=60)
    assert res.returncode == 1 and res.stdout == b""  # 1 = none of the paths is ignored
