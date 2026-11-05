"""Tests for the scope guard: the decision (tools/scope_guard.py) and its launcher.

Hook input comes from tests/fixtures/scope/*.json, copies of input captured from a
real session (P-30) with the project path replaced by {ROOT}. Every project here
lives in a pytest temp dir; this repository has no .sdlc/project.md and the guard
does not run on it.
"""
from __future__ import annotations

import ast
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import scope_guard as sg  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "scope"
LAUNCHER = ROOT / "hooks" / "scope" / "launcher.sh"
SH = shutil.which("sh")
TODAY = "2026-01-02"

CONTRACT = """\
### [ ] T-99 [M] Example task
- Size: medium.
- Goal: something.
- Files in: `src/a.py`, `src/pkg/`, `tools/metrics/{a,b}.py`, `tests/fixtures/x/*`, `docs/**/*.md`
- Files out: `src/secret.py`, `src/pkg/private/`
- Acceptance: it works. Mentions src/prose.py and docs/prose.txt without backticks.
"""
PROJECT = """\
# Project

## Always allowed
- records: `LOG.md`, `STATUS.md`, `reports/`

## Other
- `not-allowed.txt`
"""


# --- helpers -------------------------------------------------------------------

def make_project(tmp_path: Path, contract: str | None = CONTRACT, project: str | None = PROJECT) -> Path:
    root = tmp_path / "proj"
    (root / ".sdlc").mkdir(parents=True)
    if project is not None:
        (root / ".sdlc" / "project.md").write_text(project, encoding="utf-8", newline="\n")
    if contract is not None:
        (root / ".sdlc" / "active-contract.md").write_text(contract, encoding="utf-8", newline="\n")
    return root


def payload(name: str, root: Path, path: str | None = None) -> dict:
    """A fixture with {ROOT} filled in; `path` (relative or absolute) replaces the path field."""
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))

    def fill(value):
        if isinstance(value, str):
            return value.replace("{ROOT}", str(root))
        if isinstance(value, dict):
            return {k: fill(v) for k, v in value.items()}
        return value

    data = fill(data)
    if path is not None:
        field = "notebook_path" if "notebook_path" in data["tool_input"] else "file_path"
        data["tool_input"][field] = path
    return data


def run(root: Path, data: object, casefold: bool = False) -> tuple[int, str]:
    raw = data if isinstance(data, bytes) else json.dumps(data).encode("utf-8")
    err = io.StringIO()
    code = sg.main(["--root", str(root)], stdin_bytes=raw, stderr=err, today=TODAY, casefold=casefold)
    return code, err.getvalue()


def write_in(root: Path, rel: str, **kw) -> tuple[int, str]:
    return run(root, payload("write-main", root, str(root / rel)), **kw)


def events(root: Path) -> list[dict]:
    path = root / ".sdlc" / "metrics.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# --- state: not opted in --------------------------------------------------------

def test_not_opted_in_allows_silently_and_logs_nothing(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None, project=None)
    code, err = write_in(root, "anything/at/all.py")
    assert (code, err) == (0, "")
    assert events(root) == []


def test_not_opted_in_ignores_a_contract_that_exists(tmp_path: Path) -> None:
    root = make_project(tmp_path, project=None)
    assert write_in(root, "other.py")[0] == 0


# --- state: no contract ---------------------------------------------------------

def test_no_contract_denies_a_write_outside_the_always_allowed_list(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    code, err = write_in(root, "src/a.py")
    assert code == 2
    assert "[no-contract]" in err and "src/a.py" in err and "Next:" in err


def test_no_contract_allows_the_always_allowed_list(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    assert write_in(root, "LOG.md") == (0, "")
    assert write_in(root, "reports/audit/one.md")[0] == 0


def test_a_glob_in_another_section_is_not_always_allowed(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    assert write_in(root, "not-allowed.txt")[0] == 2


def test_project_file_without_the_section_means_an_empty_list(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None, project="# Project\n\nNothing here.\n")
    assert write_in(root, "LOG.md")[0] == 2


# --- state: active contract -----------------------------------------------------

@pytest.mark.parametrize("rel", [
    "src/a.py", "src/pkg/x.py", "src/pkg/deep/y.py", "tools/metrics/a.py", "tools/metrics/b.py",
    "tests/fixtures/x/one.json", "docs/one.md", "docs/a/b/two.md",
])
def test_active_contract_allows_files_in(tmp_path: Path, rel: str) -> None:
    root = make_project(tmp_path)
    assert write_in(root, rel) == (0, "")


@pytest.mark.parametrize("rel", [
    "src/b.py", "tools/metrics/c.py", "tests/fixtures/x/sub/deep.json", "docs/one.txt", "README.md",
    "src/prose.py", "docs/prose.txt",
])
def test_active_contract_denies_the_rest(tmp_path: Path, rel: str) -> None:
    root = make_project(tmp_path)
    code, err = write_in(root, rel)
    assert code == 2
    assert "[active]" in err and "T-99" in err and rel in err


def test_active_contract_still_allows_the_always_allowed_list(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert write_in(root, "STATUS.md")[0] == 0


def test_files_out_wins_over_files_in(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert write_in(root, "src/pkg/ok.py")[0] == 0
    code, err = write_in(root, "src/pkg/private/x.py")
    assert code == 2 and "Files out" in err


def test_files_out_wins_over_the_always_allowed_list(tmp_path: Path) -> None:
    contract = CONTRACT.replace("`src/secret.py`", "`LOG.md`")
    root = make_project(tmp_path, contract=contract)
    assert write_in(root, "LOG.md")[0] == 2


def test_files_out_with_no_token_is_fine(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=CONTRACT.replace("`src/secret.py`, `src/pkg/private/`", "none"))
    assert write_in(root, "src/a.py")[0] == 0


def test_only_backticked_tokens_count_and_braces_expand() -> None:
    contract = sg.parse_contract(CONTRACT)
    assert contract.task_id == "T-99"
    assert "src/prose.py" not in contract.files_in
    assert contract.files_in == ("src/a.py", "src/pkg/", "tools/metrics/a.py", "tools/metrics/b.py",
                                 "tests/fixtures/x/*", "docs/**/*.md")
    assert contract.files_out == ("src/secret.py", "src/pkg/private/")


def test_nested_and_unbalanced_braces() -> None:
    assert sg.expand_braces("a/{b,c{d,e}}/f") == ["a/b/f", "a/cd/f", "a/ce/f"]
    assert sg.expand_braces("a/{b,c") == ["a/{b,c"]


def test_runaway_brace_expansion_is_a_broken_contract(tmp_path: Path) -> None:
    token = "".join("{a,b}" for _ in range(30))
    root = make_project(tmp_path, contract=CONTRACT.replace("`src/a.py`", f"`{token}`"))
    code, err = write_in(root, "src/a.py")
    assert code == 2 and "[broken]" in err


# --- state: broken contract -----------------------------------------------------

BROKEN = {
    "no heading": CONTRACT.replace("### [ ] T-99 [M] Example task\n", ""),
    "second heading": CONTRACT + "\n## T-100 Another\n",
    "heading without task id": CONTRACT.replace("T-99 [M] ", ""),
    "no files in": CONTRACT.replace("- Files in:", "- Allowed:"),
    "files in repeated": CONTRACT + "- Files in: `src/c.py`\n",
    "files in without token": CONTRACT.replace(
        "`src/a.py`, `src/pkg/`, `tools/metrics/{a,b}.py`, `tests/fixtures/x/*`, `docs/**/*.md`", "src/a.py"),
    "no files out": CONTRACT.replace("- Files out:", "- Forbidden:"),
    "files out repeated": CONTRACT + "- Files out: `x`\n",
    "empty file": "",
}


@pytest.mark.parametrize("name", sorted(BROKEN))
def test_broken_contract_denies_and_names_the_problem(tmp_path: Path, name: str) -> None:
    root = make_project(tmp_path, contract=BROKEN[name])
    code, err = write_in(root, "src/a.py")
    assert code == 2
    assert "[broken]" in err and "active-contract.md" in err


def test_broken_contract_reason_names_the_line() -> None:
    with pytest.raises(sg.ConfigError, match=r"line 7: `Files in` is repeated \(first at line 4\)"):
        sg.parse_contract(BROKEN["files in repeated"])


def test_broken_contract_denies_even_the_always_allowed_list(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract="not a contract")
    assert write_in(root, "LOG.md")[0] == 2


def test_broken_contract_can_be_fixed_by_the_main_session(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract="not a contract")
    assert write_in(root, ".sdlc/active-contract.md") == (0, "")


def test_unreadable_contract_is_broken(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    (root / ".sdlc" / "active-contract.md").mkdir()
    assert write_in(root, "src/a.py")[0] == 2


# --- paths ----------------------------------------------------------------------

def test_dotdot_that_stays_inside_the_root_is_resolved(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert write_in(root, "src/pkg/../a.py")[0] == 0
    assert write_in(root, "src/pkg/../b.py")[0] == 2


def test_dotdot_out_of_the_root_is_denied(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    code, err = write_in(root, "src/../../elsewhere/a.py")
    assert code == 2 and "outside the project root" in err


def test_dotdot_cannot_climb_back_into_scope_from_outside(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    sibling = root.parent / "proj-other"
    assert run(root, payload("write-main", root, str(sibling / "src" / "a.py")))[0] == 2
    back_in = str(root / ".." / "proj" / "src" / "a.py")
    assert run(root, payload("write-main", root, back_in))[0] == 0


def test_absolute_path_outside_the_root_is_denied_in_every_state(tmp_path: Path) -> None:
    outside = str(tmp_path / "elsewhere" / "a.py")
    for contract, project in ((CONTRACT, PROJECT), (None, PROJECT), ("broken", PROJECT)):
        root = make_project(tmp_path / str(hash(contract)), contract=contract, project=project)
        code, err = run(root, payload("write-main", root, outside))
        assert code == 2 and "outside the project root" in err


def test_absolute_path_outside_the_root_is_denied_even_for_the_main_session_under_sdlc(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    other = root.parent / "proj2" / ".sdlc" / "x.md"
    assert run(root, payload("write-main", root, str(other)))[0] == 2


def test_a_root_prefix_that_is_not_a_folder_boundary_is_outside(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert run(root, payload("write-main", root, str(root) + "-twin/src/a.py"))[0] == 2


def test_the_root_itself_is_not_a_file(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert run(root, payload("write-main", root, str(root)))[0] == 2


def test_relative_path_is_read_against_the_root(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert run(root, payload("write-main", root, "src/a.py"))[0] == 0
    assert run(root, payload("write-main", root, "src/z.py"))[0] == 2


def test_both_separators_are_the_same(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert run(root, payload("write-main", root, "src\\a.py"))[0] == 0
    assert run(root, payload("write-main", root, str(root).replace("\\", "/") + "/src\\pkg\\x.py"))[0] == 0
    assert run(root, payload("write-main", root, "src\\b.py"))[0] == 2


def test_case_is_ignored_when_casefold_is_on(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert write_in(root, "SRC/A.PY", casefold=True)[0] == 0
    assert write_in(root, "SRC/PKG/Private/x.py", casefold=True)[0] == 2
    upper_root = str(root).upper() if os.name == "nt" else str(root)
    assert run(root, payload("write-main", root, upper_root + "/src/a.py"), casefold=True)[0] == 0


def test_case_matters_when_casefold_is_off(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert write_in(root, "SRC/A.PY", casefold=False)[0] == 2
    assert write_in(root, "src/a.py", casefold=False)[0] == 0


def test_casefold_applies_to_the_sdlc_folder(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    agent = payload("write-subagent", root, str(root / ".SDLC" / "active-contract.md"))
    assert run(root, agent, casefold=True)[0] == 2


def test_casefold_makes_the_sdlc_rule_cover_other_spellings(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=CONTRACT.replace("`src/a.py`", "`.sdlc/x.md`, `src/a.py`"))
    assert run(root, payload("write-subagent", root, str(root / ".SDLC" / "x.md")), casefold=True)[0] == 2
    broken = make_project(tmp_path / "b", contract="not a contract")
    assert run(broken, payload("write-main", broken, str(broken / ".SDLC" / "active-contract.md")), casefold=True)[0] == 0


def test_glob_rules() -> None:
    assert sg.matches("a/b.py", ["a/*.py"], False)
    assert not sg.matches("a/c/b.py", ["a/*.py"], False)
    assert sg.matches("a/c/b.py", ["a/**/*.py"], False)
    assert sg.matches("a/b.py", ["a/**/*.py"], False)
    assert sg.matches("a/c/d.py", ["a/"], False)
    assert not sg.matches("ab/c.py", ["a/"], False)
    assert sg.matches("a.b", ["a.b"], False) and not sg.matches("aXb", ["a.b"], False)


# --- the path field of each captured tool ---------------------------------------

@pytest.mark.parametrize("name,field", [
    ("write-main", "file_path"), ("edit-main", "file_path"), ("notebookedit-main", "notebook_path"),
])
def test_each_tool_path_field_is_read(tmp_path: Path, name: str, field: str) -> None:
    root = make_project(tmp_path, contract=CONTRACT.replace("`src/a.py`", "`src/a.py`, `n.ipynb`"))
    allowed = payload(name, root, str(root / "src" / "a.py"))
    denied = payload(name, root, str(root / "src" / "zzz.py"))
    assert field in allowed["tool_input"]
    assert run(root, allowed) == (0, "")
    assert run(root, denied)[0] == 2


def test_fixture_as_captured_is_decided_by_its_own_path(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=CONTRACT.replace("`src/a.py`", "`a.txt`"))
    assert run(root, payload("edit-main", root))[0] == 0
    assert run(root, payload("write-main", root))[0] == 2


@pytest.mark.parametrize("bad", [
    b"not json", b"", b"[1, 2]", b"\xff\xfe\x00",
    json.dumps({"tool_name": "Write"}).encode(),
    json.dumps({"tool_name": "Write", "tool_input": "x"}).encode(),
    json.dumps({"tool_name": "Write", "tool_input": {"content": "x"}}).encode(),
    json.dumps({"tool_name": "Write", "tool_input": {"file_path": ""}}).encode(),
    json.dumps({"tool_name": "Write", "tool_input": {"file_path": 7}}).encode(),
])
def test_missing_field_or_bad_json_is_a_deny(tmp_path: Path, bad: bytes) -> None:
    root = make_project(tmp_path)
    code, err = run(root, bad)
    assert code == 2 and "scope guard: denied" in err and "Next:" in err


def test_bad_input_in_a_project_that_has_not_opted_in_still_passes(tmp_path: Path) -> None:
    root = make_project(tmp_path, project=None)
    assert run(root, b"not json") == (0, "")


# --- sub-agent and main session under .sdlc/ ------------------------------------

@pytest.mark.parametrize("contract", [CONTRACT, None, "broken"])
@pytest.mark.parametrize("name", ["write-subagent"])
def test_sub_agent_never_writes_under_sdlc(tmp_path: Path, contract: str | None, name: str) -> None:
    root = make_project(tmp_path, contract=contract)
    code, err = run(root, payload(name, root, str(root / ".sdlc" / "active-contract.md")))
    assert code == 2 and "sub-agent" in err


@pytest.mark.parametrize("contract", [CONTRACT, None, "broken"])
def test_main_session_may_write_under_sdlc_in_every_state(tmp_path: Path, contract: str | None) -> None:
    root = make_project(tmp_path, contract=contract)
    assert run(root, payload("write-main", root, str(root / ".sdlc" / "active-contract.md"))) == (0, "")
    assert run(root, payload("edit-main", root, str(root / ".sdlc" / "project.md"))) == (0, "")


def test_sub_agent_is_denied_under_sdlc_even_if_the_contract_lists_it(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=CONTRACT.replace("`src/a.py`", "`.sdlc/x.md`, `src/a.py`"))
    assert run(root, payload("write-subagent", root, str(root / ".sdlc" / "x.md")))[0] == 2
    assert run(root, payload("write-main", root, str(root / ".sdlc" / "x.md")))[0] == 0


@pytest.mark.parametrize("field", ["agent_id", "agent_type"])
def test_either_agent_field_marks_a_sub_agent(tmp_path: Path, field: str) -> None:
    root = make_project(tmp_path)
    data = payload("write-main", root, str(root / ".sdlc" / "x.md"))
    data[field] = "something"
    assert run(root, data)[0] == 2


def test_sub_agent_is_bound_by_the_contract_outside_sdlc(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert run(root, payload("write-subagent", root, str(root / "src" / "a.py")))[0] == 0
    assert run(root, payload("write-subagent", root, str(root / "src" / "nope.py")))[0] == 2


# --- the event line -------------------------------------------------------------

def test_one_event_line_per_decision_without_a_path(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    write_in(root, "src/a.py")
    run(root, payload("write-subagent", root, str(root / "src" / "nope.py")))
    lines = events(root)
    assert lines == [
        {"event": "scope", "date": TODAY, "task": "T-99", "state": "active", "decision": "allow",
         "tool": "Write", "agent": None},
        {"event": "scope", "date": TODAY, "task": "T-99", "state": "active", "decision": "deny",
         "tool": "Write", "agent": "p30probe:writer-probe"},
    ]
    text = (root / ".sdlc" / "metrics.jsonl").read_text(encoding="utf-8")
    for forbidden in (str(root), "src", "nope", "a.py", "/", "\\"):
        assert forbidden not in text


def test_event_line_states_and_unknown_task(tmp_path: Path) -> None:
    for contract, state, task in ((None, "no-contract", None), ("broken", "broken", None), (CONTRACT, "active", "T-99")):
        root = make_project(tmp_path / state, contract=contract)
        write_in(root, "src/a.py")
        (line,) = events(root)
        assert (line["state"], line["task"]) == (state, task)


def test_event_line_for_a_notebook_edit_and_an_agent_with_only_an_id(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    data = payload("notebookedit-main", root, str(root / "src" / "a.py"))
    data["agent_id"] = "agentX"
    run(root, data)
    (line,) = events(root)
    assert (line["tool"], line["agent"]) == ("NotebookEdit", "unknown")


def test_event_line_for_a_deny_on_bad_input(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    run(root, b"not json")
    (line,) = events(root)
    assert (line["decision"], line["tool"]) == ("deny", None)


def test_a_failed_log_write_does_not_change_the_decision(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    (root / ".sdlc" / "metrics.jsonl").mkdir()
    assert write_in(root, "src/a.py")[0] == 0
    assert write_in(root, "src/nope.py")[0] == 2


# --- repository facts ------------------------------------------------------------

def test_this_repository_has_not_opted_in() -> None:
    assert not (ROOT / ".sdlc" / "project.md").exists()
    assert not (ROOT / ".sdlc" / "active-contract.md").exists()


def test_hook_registration() -> None:
    data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    (entry,) = data["hooks"]["PreToolUse"]
    assert entry["matcher"] == "Write|Edit|NotebookEdit"
    (hook,) = entry["hooks"]
    assert hook["type"] == "command" and hook["timeout"] == 30
    assert hook["command"] == 'sh "${CLAUDE_PLUGIN_ROOT}/hooks/scope/launcher.sh"'
    assert LAUNCHER.is_file()


def test_launcher_and_guard_files_use_lf() -> None:
    for path in (LAUNCHER, ROOT / "hooks" / "hooks.json", ROOT / "tools" / "scope_guard.py"):
        assert b"\r" not in path.read_bytes(), path.name


def test_gitignore_lists_the_local_scope_files() -> None:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".sdlc/metrics.jsonl" in lines and ".sdlc/active-contract.md" in lines


def test_guard_uses_the_standard_library_only() -> None:
    tree = ast.parse((ROOT / "tools" / "scope_guard.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    assert names <= set(sys.stdlib_module_names)


def test_fixtures_hold_no_absolute_path() -> None:
    for path in FIXTURES.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "Users" not in text and "{ROOT}" in text


# --- the launcher ---------------------------------------------------------------

needs_sh = pytest.mark.skipif(SH is None, reason="no sh on PATH")


def posix(path: Path) -> str:
    return path.as_posix()


def shim(directory: Path, name: str, body: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    target.write_text("#!/bin/sh\n" + body, encoding="utf-8", newline="\n")
    target.chmod(0o755)


def real_python_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "realpy"
    shim(directory, "python", f'exec "{posix(Path(sys.executable))}" "$@"\n')
    return directory


def launch(
    root: Path,
    stdin: bytes,
    path_dirs: list[Path],
    plugin_root: Path = ROOT,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(str(d) for d in path_dirs)
    env["CLAUDE_PROJECT_DIR"] = posix(root)
    env["CLAUDE_PLUGIN_ROOT"] = posix(plugin_root)
    env.pop("PYTHONUTF8", None)
    return subprocess.run([SH, posix(LAUNCHER)], input=stdin, env=env, capture_output=True, timeout=60)


def fake_plugin(tmp_path: Path, script: str | None) -> Path:
    plugin = tmp_path / "plugin"
    (plugin / "tools").mkdir(parents=True)
    if script is not None:
        (plugin / "tools" / "scope_guard.py").write_text(script, encoding="utf-8", newline="\n")
    return plugin


def input_for(root: Path, rel: str, name: str = "write-main") -> bytes:
    return json.dumps(payload(name, root, str(root / rel))).encode("utf-8")


@needs_sh
def test_launcher_passes_a_project_that_has_not_opted_in_with_no_python(tmp_path: Path) -> None:
    root = make_project(tmp_path, project=None)
    empty = tmp_path / "empty"
    empty.mkdir()
    res = launch(root, input_for(root, "src/a.py"), [empty])
    assert res.returncode == 0 and res.stderr == b""


@needs_sh
def test_launcher_end_to_end_allows_inside_the_contract(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    res = launch(root, input_for(root, "src/a.py"), [real_python_dir(tmp_path)])
    assert res.returncode == 0, res.stderr
    (line,) = events(root)
    assert (line["decision"], line["task"]) == ("allow", "T-99")


@needs_sh
def test_launcher_end_to_end_denies_outside_the_contract_and_stdin_arrives_unread(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    res = launch(root, input_for(root, "src/nope.py"), [real_python_dir(tmp_path)])
    assert res.returncode == 2
    assert b"[active]" in res.stderr and b"src/nope.py" in res.stderr


@needs_sh
def test_launcher_handles_a_non_ascii_path(tmp_path: Path) -> None:
    contract = CONTRACT.replace("`src/a.py`", "`src/café.py`")
    root = make_project(tmp_path, contract=contract)
    ok = launch(root, input_for(root, "src/café.py"), [real_python_dir(tmp_path)])
    assert ok.returncode == 0, ok.stderr
    bad = launch(root, input_for(root, "src/thé.py"), [real_python_dir(tmp_path)])
    assert bad.returncode == 2 and "thé.py".encode("utf-8") in bad.stderr


@needs_sh
def test_launcher_with_no_python_denies_in_an_opted_in_project(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    res = launch(root, input_for(root, "src/a.py"), [empty])
    assert res.returncode == 2 and b"no working Python" in res.stderr


@needs_sh
def test_launcher_with_a_too_old_python_denies(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    old = tmp_path / "old"
    # Behaves like Python 3.9: the probe fails only if it asks for 3.10; anything else runs and exits 0.
    body = 'case "$*" in *"version_info >= (3, 10)"*) exit 1;; esac\nexit 0\n'
    for name in ("python", "python3", "py"):
        shim(old, name, body)
    res = launch(root, input_for(root, "src/a.py"), [old])
    assert res.returncode == 2 and b"no working Python" in res.stderr


@needs_sh
def test_launcher_skips_a_store_stub_and_uses_the_next_candidate(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    stub = tmp_path / "stub"
    shim(stub, "python", "exit 49\n")
    real = tmp_path / "real"
    shim(real, "python3", f'exec "{posix(Path(sys.executable))}" "$@"\n')
    ok = launch(root, input_for(root, "src/a.py"), [stub, real])
    assert ok.returncode == 0, ok.stderr
    bad = launch(root, input_for(root, "src/nope.py"), [stub, real])
    assert bad.returncode == 2 and b"[active]" in bad.stderr


@needs_sh
def test_launcher_probe_does_not_consume_the_hook_input(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    directory = tmp_path / "greedy"
    # A candidate that reads stdin when probed would starve the guard if the probe shared stdin.
    body = 'case "$1 $2" in "-I -c") read ignored;; esac\n' + f'exec "{posix(Path(sys.executable))}" "$@"\n'
    shim(directory, "python", body)
    res = launch(root, input_for(root, "src/a.py"), [directory])
    assert res.returncode == 0, res.stderr


@needs_sh
def test_launcher_with_a_missing_script_denies(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    res = launch(root, input_for(root, "src/a.py"), [real_python_dir(tmp_path)],
                 plugin_root=fake_plugin(tmp_path, None))
    assert res.returncode == 2 and b"guard script not found" in res.stderr


@needs_sh
def test_launcher_with_no_plugin_root_denies(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    env = dict(os.environ, PATH=str(real_python_dir(tmp_path)), CLAUDE_PROJECT_DIR=posix(root))
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    res = subprocess.run([SH, posix(LAUNCHER)], input=b"{}", env=env, capture_output=True, timeout=60)
    assert res.returncode == 2 and b"guard script not found" in res.stderr


@needs_sh
@pytest.mark.parametrize("script", [
    "raise RuntimeError('boom')\n",
    "import sys\nsys.exit(1)\n",
    "import sys\nsys.exit(7)\n",
    "import os\nos._exit(139)\n",
    "def broken(:\n",
])
def test_launcher_turns_a_crashing_script_into_a_deny(tmp_path: Path, script: str) -> None:
    root = make_project(tmp_path)
    res = launch(root, input_for(root, "src/a.py"), [real_python_dir(tmp_path)],
                 plugin_root=fake_plugin(tmp_path, script))
    assert res.returncode == 2 and b"scope guard:" in res.stderr


@needs_sh
@pytest.mark.parametrize("script,expected", [("import sys\nsys.exit(0)\n", 0), ("import sys\nsys.exit(2)\n", 2)])
def test_launcher_passes_exit_0_and_2_through(tmp_path: Path, script: str, expected: int) -> None:
    root = make_project(tmp_path)
    res = launch(root, input_for(root, "src/a.py"), [real_python_dir(tmp_path)],
                 plugin_root=fake_plugin(tmp_path, script))
    assert res.returncode == expected


@needs_sh
def test_launcher_gives_the_script_its_stdin_and_project_root(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    script = (
        "import sys\n"
        "data = sys.stdin.buffer.read()\n"
        "sys.stderr.write('root=' + sys.argv[sys.argv.index('--root') + 1] + ' len=' + str(len(data)) + ' utf8=' + str(sys.flags.utf8_mode))\n"
        "sys.exit(2)\n"
    )
    stdin = input_for(root, "src/a.py")
    res = launch(root, stdin, [real_python_dir(tmp_path)], plugin_root=fake_plugin(tmp_path, script))
    assert res.returncode == 2
    assert f"len={len(stdin)} utf8=1".encode() in res.stderr
    assert posix(root).encode() in res.stderr
