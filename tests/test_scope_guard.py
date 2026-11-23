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
import random
import re
import shutil
import subprocess
import sys
import time
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


# --- deny texts for the main session and the sub-agent (T-58) --------------------

SUB_NO_CONTRACT = "Next: Ask the technical lead to place .sdlc/active-contract.md for this task."
SUB_BROKEN = "Next: Ask the technical lead to fix .sdlc/active-contract.md."


def test_main_session_no_contract_text_names_the_command_and_the_format(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    code, err = write_in(root, "src/a.py")
    assert code == 2 and "[no-contract]" in err
    assert sg.MAIN_NO_CONTRACT_NEXT in err
    for part in ("technical lead", "/sdlc-lead:contract <task>", "## <ID> <title>", "Files in:", "Files out:",
                 "backticks", "developer sub-agent"):
        assert part in sg.MAIN_NO_CONTRACT_NEXT
    assert "or write .sdlc/active-contract.md" in sg.MAIN_NO_CONTRACT_NEXT
    assert len(sg.MAIN_NO_CONTRACT_NEXT) <= 450
    assert SUB_NO_CONTRACT not in err


def test_main_session_broken_text_keeps_the_reason_and_adds_the_format(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=BROKEN["files in repeated"])
    code, err = write_in(root, "src/a.py")
    assert code == 2 and "[broken]" in err
    assert "line 7: `Files in` is repeated (first at line 4)" in err
    assert sg.MAIN_BROKEN_NEXT in err
    for part in ("/sdlc-lead:contract <task>", "## <ID> <title>", "Files in:", "Files out:", "backticks",
                 "developer sub-agent"):
        assert part in sg.MAIN_BROKEN_NEXT
    assert len(sg.MAIN_BROKEN_NEXT) <= 450
    assert SUB_BROKEN not in err


ID_SENTENCE_PARTS = ("capital letters", "one dash", "digits", "optional lower-case letter", "T-12 or T-12a",
                     "number from T-1")


def test_contract_format_text_states_the_id_format_and_its_examples_parse() -> None:
    for part in ID_SENTENCE_PARTS:
        assert part in sg._CONTRACT_FORMAT
    for example in ("T-12", "T-12a", "T-1"):
        assert sg._TASK_ID.search(f"{example} title")
    assert sg._TASK_ID.search("T-FIX-1 title") is None


def test_sub_agent_deny_texts_do_not_carry_the_id_format(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    code, err = run(root, payload("write-subagent", root, str(root / "src" / "a.py")))
    assert code == 2 and "capital letters" not in err


def test_sub_agent_deny_texts_are_unchanged(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    code, err = run(root, payload("write-subagent", root, str(root / "src" / "a.py")))
    assert code == 2 and SUB_NO_CONTRACT in err and "/sdlc-lead:contract" not in err
    root = make_project(tmp_path / "b", contract="not a contract")
    code, err = run(root, payload("write-subagent", root, str(root / "src" / "a.py")))
    assert code == 2 and SUB_BROKEN in err and "/sdlc-lead:contract" not in err


def test_sub_agent_next_steps_are_byte_equal_to_the_old_texts() -> None:
    no_contract = sg.decide("src/a.py", sg.NO_CONTRACT, None, [], True, False)
    assert no_contract.next_step == "Ask the technical lead to place .sdlc/active-contract.md for this task."
    broken = sg.decide("src/a.py", sg.BROKEN, None, [], True, False, broken_reason="x")
    assert broken.next_step == "Ask the technical lead to fix .sdlc/active-contract.md."


def test_check_contract_messages_carry_the_format_when_missing_or_broken(tmp_path: Path) -> None:
    ending = f"Format: {sg._CONTRACT_FORMAT}."
    missing = sg.check_contract(make_project(tmp_path / "a", contract=None))
    assert missing[0] == 1 and missing[1].startswith("no active contract") and missing[1].endswith(ending)
    broken = sg.check_contract(make_project(tmp_path / "b", contract="## no id\n- Files in: `a`\n- Files out: `b`\n"))
    assert broken[0] == 1 and "no task ID" in broken[1] and broken[1].endswith(ending)
    for message in (missing[1], broken[1]):
        for part in ID_SENTENCE_PARTS:
            assert part in message
        example = re.search(r"for example (T-\d+[a-z]?)", message)
        assert example and sg._TASK_ID.fullmatch(example.group(1))


def test_check_contract_message_for_a_valid_contract_is_unchanged(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    code, message = sg.check_contract(root)
    parsed = sg.parse_contract(CONTRACT)
    assert code == 0 and "Format" not in message
    assert message == f"contract T-99: {len(parsed.files_in)} Files in, {len(parsed.files_out)} Files out"


def test_the_format_in_the_main_session_text_parses_as_an_active_contract(tmp_path: Path) -> None:
    # Built only from what the deny text says: one `## <ID> <title>` heading, one `- Files in:`
    # line, one `- Files out:` line, every path in backticks.
    text = "## T-77 Sample task\n- Files in: `src/a.py`, `tests/test_a.py`\n- Files out: `docs/`\n"
    root = make_project(tmp_path, contract=text)
    out, err = io.StringIO(), io.StringIO()
    assert sg.main(["--root", str(root), "--check-contract"], stdout=out, stderr=err) == 0
    assert out.getvalue() == "contract T-77: 2 Files in, 1 Files out\n"
    contract = sg.parse_contract(text)
    assert contract.task_id == "T-77"
    assert write_in(root, "src/a.py") == (0, "")
    assert write_in(root, "docs/x.md")[0] == 2


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


# --- bounded time and the same answers as the regex (S-7, S-8) -----------------------

OLD_HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.*?)\s*#*\s*$")  # the pattern heading_text replaced
TIME_LIMIT = 0.5  # seconds for each worst case; the regex needed 13 s, 4.6 s and 1.6 s


def regex_answer(rel: str, pattern: str, casefold: bool) -> bool:
    return re.fullmatch(sg.glob_to_regex(pattern), rel, re.IGNORECASE if casefold else 0) is not None


def timed(call) -> float:
    started = time.perf_counter()
    call()
    return time.perf_counter() - started


def pattern_strings_in_tests() -> list[str]:
    """Every short string constant in tests/*.py. Any string may be a pattern, so all of them are used."""
    found: set[str] = set()
    for path in sorted((ROOT / "tests").glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if 0 < len(node.value) <= 120 and "\n" not in node.value and " " not in node.value:
                    found.add(node.value)
    return sorted(found)


def instance_of(pattern: str, rnd: random.Random) -> str:
    """A path that the pattern probably matches: wildcards are replaced by short random text."""
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append(rnd.choice(["", "a/", "a/b/", "x.y/"]))
            i += 3
        elif pattern.startswith("**", i):
            out.append(rnd.choice(["", "a", "a/b", "/"]))
            i += 2
        elif pattern[i] == "*":
            out.append(rnd.choice(["", "a", "bb", "x.y"]))
            i += 1
        elif pattern[i] == "?":
            out.append(rnd.choice("aB.x"))
            i += 1
        else:
            out.append(pattern[i])
            i += 1
    return "".join(out)


def test_the_linear_matcher_gives_the_regex_answer_on_generated_pairs() -> None:
    rnd = random.Random(20261108)
    pieces = ["a", "b", "A", "B", ".", "/", "*", "**", "**/", "?", "x", "ab", "\n", "ſ", "K", "k", "K", "s", "S"]
    path_pieces = ["a", "b", "A", "B", ".", "/", "x", "ab", "\n", "ſ", "K", "k", "K", "s", "S", "//"]
    pairs = 0
    matched = 0
    for _ in range(3000):
        pattern = "".join(rnd.choice(pieces) for _ in range(rnd.randint(0, 8)))
        if rnd.random() < 0.5:
            rel = instance_of(pattern, rnd)
        else:
            rel = "".join(rnd.choice(path_pieces) for _ in range(rnd.randint(0, 10)))
        for casefold in (False, True):
            want = regex_answer(rel, pattern, casefold)
            assert sg.matches(rel, [pattern], casefold) is want, (pattern, rel, casefold)
            pairs += 1
            matched += want
    assert pairs >= 2000 and 300 < matched < pairs - 300  # the corpus has both answers in quantity


def test_the_linear_matcher_gives_the_regex_answer_for_every_string_in_the_tests() -> None:
    patterns = pattern_strings_in_tests()
    paths = ["a/b.py", "src/a.py", "src/pkg/x/y.py", "docs/a/b.md", ".sdlc/active-contract.md", "TASKS.md", "a", "",
             "tests/fixtures/x/f.json", "tools/metrics/a.py", "audits/r.md", "a/", "SRC/A.PY", "x.y/z", "a\nb/c"]
    paths += [p for p in patterns if "/" in p][:40]
    assert len(patterns) > 500
    for casefold in (False, True):
        for pattern in patterns:
            for rel in paths:
                assert sg.matches(rel, [pattern], casefold) is regex_answer(rel, pattern, casefold), (pattern, rel, casefold)


def test_matches_answers_for_a_list_like_the_any_of_the_regex_answers() -> None:
    assert sg.matches("a/b.py", [], False) is False
    assert sg.matches("a/b.py", ["x/*", "a/*.py", "["], False) is True
    assert sg.matches("A/B.PY", ["a/*.py"], True) is True and sg.matches("A/B.PY", ["a/*.py"], False) is False
    assert sg.matches("", [""], False) is True and sg.matches("a", [""], False) is False


def test_glob_to_regex_is_still_the_reference() -> None:
    assert sg.glob_to_regex("a/**/*.py") == "a/(?:.*/)?[^/]*\\.py"
    assert sg.glob_to_regex("src/") == "src/.*"
    assert sg.glob_to_regex("a?b**") == "a[^/]b.*"


def test_nine_globstars_against_thirty_segments_are_matched_in_bounded_time() -> None:
    pattern = "**/" * 9 + "zz"
    path = "/".join(["a"] * 30)
    assert timed(lambda: sg.matches(path, [pattern], False)) < TIME_LIMIT
    assert sg.matches(path, [pattern], False) is False and sg.matches(path + "/zz", [pattern], False) is True
    assert sg.matches(path + "/ZZ", [pattern], True) is True and sg.matches(path + "/ZZ", [pattern], False) is False


def test_fifty_patterns_against_a_500_character_path_are_matched_in_bounded_time() -> None:
    path = "a" * 500
    patterns = ["*a*a*b", "*a" * 8 + "b", "**/*a*a*a*b", "a*a*a*a*a*a*a*a*c"] * 12 + ["*a*a*a"] * 2
    assert len(patterns) == 50
    for casefold in (False, True):
        assert timed(lambda: sg.matches(path, patterns, casefold)) < TIME_LIMIT
    assert sg.matches(path, patterns[:-2], False) is False and sg.matches(path, ["*a*a*a"], False) is True
    long_path = "a/" * 100_000 + "b"  # unbounded paths come from the hook input
    assert timed(lambda: sg.matches(long_path, ["**/" * 9 + "zz", "*a*a*b"], True)) < TIME_LIMIT * 4


def test_the_heading_parse_gives_the_regex_answer_on_generated_lines() -> None:
    rnd = random.Random(20261109)
    pieces = [" ", " ", "#", "#", "a", "\t", "b", " ", "\x1f", "　", "T-1", "``"]
    fixed = ["", "#", "# ", "# a", "#a", "## A b ##", "   ### x", "    # x", "####### x", "# x #  #", "# #", "\t# x",
             "#\tx", "###### six", "# Always allowed ", "## T-44a title #"]
    lines = fixed + ["".join(rnd.choice(pieces) for _ in range(rnd.randint(0, 14))) for _ in range(3000)]
    headings = 0
    for line in lines:
        found = OLD_HEADING.match(line)
        assert sg.heading_text(line) == (found.group(1) if found else None), repr(line)
        headings += found is not None
    assert headings > 300


def test_a_heading_with_a_2000_blank_run_is_parsed_in_bounded_time(tmp_path: Path) -> None:
    for blanks in (800, 2_000, 200_000):
        for line in ("# a" + " " * blanks + "x", "#" + " " * blanks, "#" + "\t " * blanks + "x ##", "   # a" + "#" * blanks):
            assert timed(lambda: sg.heading_text(line)) < TIME_LIMIT
    contract_text = CONTRACT.replace("### [ ] T-99 [M] Example task", "### [ ] T-99 [M] Example" + " " * 2_000 + "task")
    assert timed(lambda: sg.parse_contract(contract_text)) < TIME_LIMIT
    assert sg.parse_contract(contract_text).task_id == "T-99"
    project_text = PROJECT.replace("## Always allowed", "## Always allowed" + " " * 200_000 + "##")
    assert timed(lambda: sg.parse_always_allowed(project_text)) < TIME_LIMIT
    assert sg.parse_always_allowed(project_text) == ["LOG.md", "STATUS.md", "reports/"]
    root = make_project(tmp_path, contract=contract_text, project=project_text)
    assert timed(lambda: sg.check_contract(root)) < TIME_LIMIT
    assert sg.check_contract(root)[0] == 0
    assert sg.main(["--root", str(root), "--check-contract"], stdout=io.StringIO(), stderr=io.StringIO()) == 0


def test_a_contract_with_long_field_lines_is_parsed_in_bounded_time() -> None:
    contract_text = CONTRACT.replace("- Files in:", "-" + " " * 100_000 + "Files in:")
    assert timed(lambda: sg.parse_contract(contract_text)) < TIME_LIMIT
    assert sg.parse_contract(contract_text).files_in[0] == "src/a.py"
    assert timed(lambda: sg.parse_contract("#" + " " * 100_000 + "T-1\n- Files in: `a`\n- Files out: `b`\n")) < TIME_LIMIT


def test_a_decision_on_a_crafted_contract_is_made_in_bounded_time() -> None:
    contract = sg.Contract("T-1", ("**/" * 9 + "*a*a*a*b",), ("**/" * 9 + "zz",), ())
    path = "/".join(["a"] * 30)
    started = time.perf_counter()
    decision = sg.decide(path, sg.ACTIVE, contract, ["**/" * 9 + "q"], True, True)
    assert time.perf_counter() - started < TIME_LIMIT
    assert decision.allow is False and "not in Files in" in decision.reason
    assert sg.decide("/".join(["a"] * 29) + "/aaab", sg.ACTIVE, contract, [], True, False).allow is True


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

def test_this_repository_has_opted_in() -> None:
    text = (ROOT / ".sdlc" / "project.md").read_text(encoding="utf-8")
    assert sg.parse_developer_rules(text) == "DEV_RULES.md"
    allowed = sg.parse_always_allowed(text)
    assert allowed and "DEV_RULES.md" not in allowed
    for rel in ("DEV_RULES.md", "CLAUDE.md", "PLAYBOOK.md", "README.md", "tests/test_x.py"):
        assert not sg.matches(rel, allowed, False), rel
    for rel in ("STATUS.md", "TASKS.md", "LOG.md", "DECISIONS.md", "CHANGELOG.md", "LESSONS.md",
                "audits/x.md", "cto/x.md", "docs/toolchain.md"):
        assert sg.matches(rel, allowed, False), rel


@pytest.mark.skipif(shutil.which("git") is None, reason="no git on PATH")
def test_active_contract_is_not_tracked_in_this_repository() -> None:
    res = subprocess.run(["git", "ls-files", ".sdlc/active-contract.md", ".sdlc/metrics.jsonl"],
                         cwd=ROOT, capture_output=True, timeout=60)
    if res.returncode != 0:
        pytest.skip("not a git work tree")
    assert res.stdout.strip() == b""


def test_this_repository_decisions_with_no_contract() -> None:
    text = (ROOT / ".sdlc" / "project.md").read_text(encoding="utf-8")
    allowed = sg.parse_always_allowed(text)
    rules = sg.parse_developer_rules(text)

    def decide(rel: str, is_agent: bool = False) -> bool:
        return sg.decide(rel, sg.NO_CONTRACT, None, allowed, is_agent, False, developer_rules=rules).allow

    assert not decide("PLAYBOOK.md")
    for rel in ("LOG.md", "docs/toolchain.md", "cto/x.md"):
        assert decide(rel), rel
    assert not decide("DEV_RULES.md", is_agent=True)
    assert not decide("DEV_RULES.md")


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
def settings_command() -> str:
    data = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    (entry,) = data["hooks"]["PreToolUse"]
    assert entry["matcher"] == "Write|Edit|NotebookEdit"
    (hook,) = entry["hooks"]
    assert hook["type"] == "command" and hook["timeout"] == 30
    return hook["command"]


def run_settings_command(root: Path, rel: str, python_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(python_dir), env.get("PATH", "")])
    env["CLAUDE_PROJECT_DIR"] = posix(root)
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    env.pop("PYTHONUTF8", None)
    return subprocess.run([SH, "-c", settings_command()], input=input_for(root, rel), env=env,
                          capture_output=True, timeout=60)


def kit_project(tmp_path: Path) -> Path:
    """A folder shaped like the kit: this repository's project file, launcher and guard script."""
    root = tmp_path / "kit"
    (root / ".sdlc").mkdir(parents=True)
    (root / "hooks" / "scope").mkdir(parents=True)
    (root / "tools").mkdir()
    shutil.copyfile(ROOT / ".sdlc" / "project.md", root / ".sdlc" / "project.md")
    shutil.copyfile(LAUNCHER, root / "hooks" / "scope" / "launcher.sh")
    shutil.copyfile(ROOT / "tools" / "scope_guard.py", root / "tools" / "scope_guard.py")
    return root


@needs_sh
def test_settings_command_denies_playbook_with_no_contract(tmp_path: Path) -> None:
    root = kit_project(tmp_path)
    res = run_settings_command(root, "PLAYBOOK.md", real_python_dir(tmp_path))
    assert res.returncode == 2, res.stderr
    assert b"scope guard: denied" in res.stderr and b"[no-contract]" in res.stderr


@needs_sh
def test_settings_command_allows_the_log_with_no_contract(tmp_path: Path) -> None:
    root = kit_project(tmp_path)
    res = run_settings_command(root, "LOG.md", real_python_dir(tmp_path))
    assert res.returncode == 0, res.stderr
    (line,) = events(root)
    assert line["decision"] == "allow"


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


# --- script modes: --check-contract and --check-worktree (T-30a) ------------------

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="no git on PATH")


def mode(root: Path, flag: str, casefold: bool = False) -> tuple[int, str, str]:
    """Run one script mode. No stdin is given: reading it would fail under pytest."""
    out, err = io.StringIO(), io.StringIO()
    code = sg.main(["--root", str(root), flag], stdout=out, stderr=err, casefold=casefold)
    return code, out.getvalue(), err.getvalue()


def sh_git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0, res.stderr
    return res.stdout


def git_project(tmp_path: Path, contract: str | None = CONTRACT, project: str | None = PROJECT,
                files: tuple[str, ...] = ("src/a.py", "docs/old.md", "README.md")) -> Path:
    """A project that is also a git repository with one commit of `files`."""
    root = make_project(tmp_path, contract, project)
    for rel in files:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("x\n", encoding="utf-8", newline="\n")
    sh_git(root, "init", "-q")
    sh_git(root, "config", "user.name", "Test")
    sh_git(root, "config", "user.email", "test@users.noreply.github.com")
    sh_git(root, "config", "core.autocrlf", "false")
    sh_git(root, "add", "-A")
    sh_git(root, "commit", "-q", "-m", "init")
    return root


def touch(root: Path, rel: str, text: str = "y\n") -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text, encoding="utf-8", newline="\n")


def test_check_contract_passes_a_good_contract_and_names_the_task(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    code, out, err = mode(root, "--check-contract")
    assert code == 0 and "T-99" in out and err == ""


def test_script_modes_write_no_event_line_and_read_no_stdin(tmp_path: Path, monkeypatch) -> None:
    root = git_project(tmp_path) if shutil.which("git") else make_project(tmp_path)
    monkeypatch.setattr(sys, "stdin", None)
    assert mode(root, "--check-contract")[0] == 0
    assert mode(root, "--check-worktree")[0] in (0, 1)
    assert events(root) == []


@pytest.mark.parametrize("option", ["--help", "-h", "--check-worktre", "--check-wor", "--bogus=1", "-x"])
def test_an_unknown_option_prints_the_usage_exits_2_and_writes_no_event_line(
        tmp_path: Path, monkeypatch, option: str) -> None:
    root = make_project(tmp_path)
    monkeypatch.setattr(sys, "stdin", None)  # a read of stdin would raise
    before = events(root)
    err = io.StringIO()
    code = sg.main(["--root", str(root), option], stderr=err, today=TODAY)
    assert code == 2
    assert err.getvalue().startswith("usage: scope_guard") and "--check-worktree" in err.getvalue()
    assert events(root) == before == []
    assert not (root / ".sdlc" / "metrics.jsonl").exists()
    # an unknown option next to a valid script option is refused too
    assert sg.main(["--root", str(root), "--check-contract", option], stdout=io.StringIO(), stderr=io.StringIO()) == 2
    assert not (root / ".sdlc" / "metrics.jsonl").exists()


def test_hook_mode_without_an_option_and_the_script_modes_still_work(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    assert write_in(root, "src/a.py")[0] == 0
    assert write_in(root, "docs/other.txt")[0] == 2
    assert len(events(root)) == 2  # the legal case still logs one line per decision
    assert mode(root, "--check-contract")[0] == 0
    assert len(events(root)) == 2


def test_check_contract_refuses_when_there_is_no_active_contract(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None)
    code, out, err = mode(root, "--check-contract")
    assert code == 1 and out == "" and "no active contract" in err


def test_check_contract_refuses_the_unfilled_template(tmp_path: Path) -> None:
    template = (ROOT / "templates" / "task-contract.md").read_text(encoding="utf-8")
    root = make_project(tmp_path, contract=template)
    code, _, err = mode(root, "--check-contract")
    assert code == 1 and "active-contract.md" in err


@pytest.mark.parametrize("text, word", [
    ("### T-1 x\n- Files in: `a`\n", "Files out"),
    ("### T-1 x\n- Files in: none\n- Files out: `b`\n", "no backticked path"),
    ("### no id\n- Files in: `a`\n- Files out:\n", "task ID"),
])
def test_check_contract_refuses_a_broken_contract_with_the_reason(tmp_path: Path, text: str, word: str) -> None:
    root = make_project(tmp_path, contract=text)
    code, _, err = mode(root, "--check-contract")
    assert code == 1 and word in err


def test_check_contract_works_without_a_project_file(tmp_path: Path) -> None:
    root = make_project(tmp_path, project=None)
    assert mode(root, "--check-contract")[0] == 0


def test_two_script_modes_at_once_are_refused(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    err = io.StringIO()
    code = sg.main(["--root", str(root), "--check-contract", "--check-worktree"], stderr=err)
    assert code == 1 and "one of" in err.getvalue()


@needs_git
def test_check_worktree_passes_when_every_change_is_inside_the_contract(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    touch(root, "src/a.py")
    touch(root, "src/pkg/new.py")
    touch(root, "LOG.md")
    code, out, err = mode(root, "--check-worktree")
    assert code == 0 and "inside T-99" in out and err == ""


@needs_git
def test_check_worktree_prints_a_file_outside_the_contract(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    touch(root, "src/a.py")
    touch(root, "stray.txt")
    code, out, err = mode(root, "--check-worktree")
    assert code == 1 and out.splitlines() == ["stray.txt"] and "outside T-99" in err


@needs_git
def test_check_worktree_lists_each_untracked_file_of_a_new_folder(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    touch(root, "newdir/one.txt")
    touch(root, "newdir/two.txt")
    code, out, _ = mode(root, "--check-worktree")
    assert code == 1 and sorted(out.splitlines()) == ["newdir/one.txt", "newdir/two.txt"]


@needs_git
def test_check_worktree_files_out_wins_over_files_in(tmp_path: Path) -> None:
    root = git_project(tmp_path, files=("src/a.py", "src/pkg/private/k.py"))
    touch(root, "src/pkg/private/k.py")
    code, out, _ = mode(root, "--check-worktree")
    assert code == 1 and out.splitlines() == ["src/pkg/private/k.py"]


@needs_git
def test_check_worktree_files_out_wins_over_the_always_allowed_list(tmp_path: Path) -> None:
    contract = CONTRACT.replace("`src/secret.py`", "`LOG.md`")
    root = git_project(tmp_path, contract=contract, files=("src/a.py", "LOG.md"))
    touch(root, "LOG.md")
    touch(root, "STATUS.md")
    code, out, _ = mode(root, "--check-worktree")
    assert code == 1 and out.splitlines() == ["LOG.md"]


@needs_git
def test_check_worktree_checks_both_paths_of_a_rename(tmp_path: Path) -> None:
    root = git_project(tmp_path, files=("src/a.py", "lib/old.txt"))
    (root / "src" / "pkg").mkdir(parents=True)
    sh_git(root, "mv", "lib/old.txt", "src/pkg/moved.py")
    code, out, _ = mode(root, "--check-worktree")
    assert code == 1 and out.splitlines() == ["lib/old.txt"]


@needs_git
def test_check_worktree_a_rename_into_the_outside_is_found_too(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    (root / "lib").mkdir()
    sh_git(root, "mv", "src/a.py", "lib/elsewhere.txt")
    code, out, _ = mode(root, "--check-worktree")
    assert code == 1 and out.splitlines() == ["lib/elsewhere.txt"]


@needs_git
def test_check_worktree_skips_the_sdlc_folder(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    touch(root, ".sdlc/notes.md")
    touch(root, ".sdlc/guard/x.py")
    code, out, _ = mode(root, "--check-worktree")
    assert code == 0 and "0 changed paths" in out


@needs_git
def test_check_worktree_without_a_contract_is_exit_1(tmp_path: Path) -> None:
    root = git_project(tmp_path, contract=None)
    code, out, err = mode(root, "--check-worktree")
    assert code == 1 and out == "" and "no active contract" in err


@needs_git
def test_check_worktree_with_a_broken_contract_is_exit_1(tmp_path: Path) -> None:
    root = git_project(tmp_path, contract="### no id\n")
    code, _, err = mode(root, "--check-worktree")
    assert code == 1 and "cannot be used" in err


@needs_git
def test_check_worktree_in_a_project_below_the_repository_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    sh_git(repo, "init", "-q")
    root = repo / "app"
    (root / ".sdlc").mkdir(parents=True)
    (root / ".sdlc" / "project.md").write_text(PROJECT, encoding="utf-8", newline="\n")
    (root / ".sdlc" / "active-contract.md").write_text(CONTRACT, encoding="utf-8", newline="\n")
    touch(root, "src/a.py")
    touch(root, "other.txt")
    touch(repo, "outside-of-app.txt")
    code, out, _ = mode(root, "--check-worktree")
    assert code == 1 and out.splitlines() == ["other.txt"]


@needs_git
def test_check_worktree_path_with_a_space_and_a_non_ascii_letter(tmp_path: Path) -> None:
    name = "my dir/caf" + chr(0xE9) + ".txt"
    root = git_project(tmp_path)
    touch(root, name)
    code, out, _ = mode(root, "--check-worktree")
    assert code == 1 and out.splitlines() == [name]
    contract = CONTRACT.replace("`src/a.py`", f"`{name}`")
    (root / ".sdlc" / "active-contract.md").write_text(contract, encoding="utf-8", newline="\n")
    assert mode(root, "--check-worktree")[0] == 0


@needs_git
def test_check_worktree_respects_casefold(tmp_path: Path) -> None:
    root = git_project(tmp_path, files=("README.md",))
    touch(root, "SRC/a.py")
    assert mode(root, "--check-worktree", casefold=False)[0] == 1
    assert mode(root, "--check-worktree", casefold=True)[0] == 0


def test_the_hook_path_is_unchanged_by_the_new_modes(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    code, _ = write_in(root, "src/a.py")
    assert code == 0
    code, err = write_in(root, "docs/x.txt")
    assert code == 2 and "not in Files in" in err
    assert len(events(root)) == 2
    mode(root, "--check-contract")
    assert len(events(root)) == 2


def test_git_is_started_with_the_file_system_monitor_off(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        seen.append(list(args))
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(sg.subprocess, "run", fake_run)
    sg._git(tmp_path, "status", "--porcelain", "-z")
    assert seen == [["git", "-C", str(tmp_path), "-c", "core.fsmonitor=false", "status", "--porcelain", "-z"]]


@needs_git
def test_a_repository_config_cannot_start_a_program_through_core_fsmonitor(tmp_path: Path) -> None:
    root = git_project(tmp_path)
    marker = tmp_path / "fsmonitor-ran"
    script = tmp_path / "fsmonitor.sh"  # outside the repository, so it is not a change itself
    script.write_text(f'#!/bin/sh\n: > "{posix(marker)}"\nexit 1\n', encoding="utf-8", newline="\n")
    sh_git(root, "config", "core.fsmonitor", posix(script))
    touch(root, "src/a.py")
    sh_git(root, "status", "--porcelain")  # control run: plain git does start the program
    if not marker.exists():
        pytest.skip("this git does not start core.fsmonitor here")
    marker.unlink()
    assert sg.check_worktree(root, False)[0] in (0, 1)  # the real check ran git
    assert not marker.exists()


def test_check_worktree_asks_git_not_to_enter_nested_repositories(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        seen.append(list(args))
        return subprocess.CompletedProcess(args, 0, b"", b"")

    root = make_project(tmp_path)
    monkeypatch.setattr(sg.subprocess, "run", fake_run)
    assert sg.check_worktree(root, False)[0] == 0
    status = [args for args in seen if "status" in args]
    assert len(status) == 1 and "--ignore-submodules=all" in status[0]


@needs_git
def test_a_filter_in_a_nested_repository_cannot_start_a_program_through_check_worktree(tmp_path: Path) -> None:
    marker = tmp_path / "nested-filter-ran"
    script = tmp_path / "clean.sh"  # outside the repository, so it is not a change itself
    script.write_text(f'#!/bin/sh\necho x >> "{posix(marker)}"\ncat\n', encoding="utf-8", newline="\n")

    def lines() -> int:
        return len(marker.read_text(encoding="utf-8").splitlines()) if marker.exists() else 0

    def nested_project(base: Path, command: str | None) -> Path:
        root = git_project(base)
        nested = root / "vendor" / "lib"
        nested.mkdir(parents=True)
        sh_git(nested, "init", "-q")
        sh_git(nested, "config", "user.name", "Test")
        sh_git(nested, "config", "user.email", "test@users.noreply.github.com")
        touch(nested, "a.txt")
        (nested / ".gitattributes").write_text("* filter=probe\n", encoding="utf-8", newline="\n")
        sh_git(nested, "add", "-A")
        sh_git(nested, "commit", "-q", "-m", "n")
        sh_git(root, "add", "vendor/lib")  # a gitlink
        sh_git(root, "commit", "-q", "-m", "n")
        if command is not None:
            sh_git(nested, "config", "filter.probe.clean", command)
        later = time.time() + 30  # only the time changed: git compares the content through the filter
        os.utime(nested / "a.txt", (later, later))
        return root

    clean = nested_project(tmp_path / "control", None)  # control layout without the filter
    assert sg.check_worktree(clean, False)[0] == 0 and lines() == 0
    root = nested_project(tmp_path / "r", f"sh {posix(script)}")
    sh_git(root, "status", "--porcelain")  # control run: plain git does start the program
    if lines() == 0:
        pytest.skip("this git does not run a clean filter of a nested repository on status here")
    marker.unlink()
    touch(root, "stray.txt")
    code, outside, _ = sg.check_worktree(root, False)
    assert lines() == 0
    assert code == 1 and outside == ["stray.txt"]  # a change in the repository itself is still found


def test_check_worktree_outside_a_git_repository_is_exit_1(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    code, out, err = mode(root, "--check-worktree")
    assert code == 1 and out == "" and "git status failed" in err


def test_check_contract_names_the_project_file_when_it_cannot_be_read(tmp_path: Path) -> None:
    bad = "## Always allowed\n- `{" + ",".join(["a"] * 2000) + "}`\n"
    root = make_project(tmp_path, project=bad)
    code, _, err = mode(root, "--check-contract")
    assert code == 1 and ".sdlc/project.md" in err


@needs_git
def test_check_worktree_prints_a_non_ascii_name_escaped_on_an_ascii_stream(tmp_path: Path) -> None:
    name = "caf" + chr(0xE9) + ".txt"
    root = git_project(tmp_path)
    touch(root, name)
    env = {**os.environ, "PYTHONIOENCODING": "ascii"}
    res = subprocess.run([sys.executable, str(ROOT / "tools" / "scope_guard.py"), "--root", str(root),
                          "--check-worktree"], capture_output=True, env=env)
    assert res.returncode == 1
    assert b"Traceback" not in res.stderr and b"internal error" not in res.stderr
    assert b"caf\\xe9.txt" in res.stdout


# --- developer rules file (T-33b) -------------------------------------------------

RULES_PROJECT = PROJECT.replace(
    "## Always allowed", "## Records\n- Developer rules: `DEV_RULES.md`\n\n## Always allowed"
).replace("`reports/`", "`reports/`, `DEV_RULES.md`")
RULES_CONTRACT = CONTRACT.replace("`src/a.py`", "`DEV_RULES.md`, `src/a.py`")


def agent_write(root: Path, rel: str, **kw) -> tuple[int, str]:
    return run(root, payload("write-subagent", root, str(root / rel)), **kw)


def test_rules_file_is_denied_to_a_sub_agent_without_a_contract_even_if_always_allowed(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=None, project=RULES_PROJECT)
    code, err = agent_write(root, "DEV_RULES.md")
    assert code == 2 and "developer rules" in err and "Next:" in err
    assert agent_write(root, "LOG.md")[0] == 0


def test_rules_file_is_denied_to_a_sub_agent_when_files_in_does_not_name_it(tmp_path: Path) -> None:
    root = make_project(tmp_path, project=RULES_PROJECT)
    code, err = agent_write(root, "DEV_RULES.md")
    assert code == 2 and "developer rules" in err and "Next:" in err


def test_rules_file_is_allowed_to_a_sub_agent_when_files_in_names_it(tmp_path: Path) -> None:
    root = make_project(tmp_path, contract=RULES_CONTRACT, project=RULES_PROJECT)
    assert agent_write(root, "DEV_RULES.md")[0] == 0


def test_files_out_still_wins_over_files_in_for_the_rules_file(tmp_path: Path) -> None:
    contract = RULES_CONTRACT.replace("`src/secret.py`", "`DEV_RULES.md`, `src/secret.py`")
    root = make_project(tmp_path, contract=contract, project=RULES_PROJECT)
    assert agent_write(root, "DEV_RULES.md")[0] == 2


@pytest.mark.parametrize("contract", [None, CONTRACT])
def test_main_session_may_write_the_rules_file(tmp_path: Path, contract: str | None) -> None:
    root = make_project(tmp_path, contract=contract, project=RULES_PROJECT)
    assert write_in(root, "DEV_RULES.md") == (0, "")


def test_without_a_developer_rules_line_the_always_allowed_list_still_works(tmp_path: Path) -> None:
    project = PROJECT.replace("`reports/`", "`reports/`, `DEV_RULES.md`")
    root = make_project(tmp_path, contract=None, project=project)
    assert agent_write(root, "DEV_RULES.md")[0] == 0


def test_rules_path_is_parsed_from_its_line() -> None:
    assert sg.parse_developer_rules("- Developer rules: `docs\\RULES.md`\n") == "docs/RULES.md"
    assert sg.parse_developer_rules("- Status: `STATUS.md`\n") is None
    assert sg.parse_developer_rules("- Developer rules: none\n") is None


def test_rules_file_match_is_case_folded_when_casefold_is_on(tmp_path: Path) -> None:
    project = RULES_PROJECT.replace("`DEV_RULES.md`", "`docs/Rules.md`")
    root = make_project(tmp_path, contract=None, project=project)
    assert agent_write(root, "DOCS/RULES.MD", casefold=True)[0] == 2
    root_b = make_project(tmp_path / "b", contract=None, project=project.replace("`reports/`", "`reports/`, `DOCS/RULES.MD`"))
    assert agent_write(root_b, "DOCS/RULES.MD", casefold=False)[0] == 0


# --- exact rules path (T-39, DEC-048) -------------------------------------------------

@pytest.mark.parametrize("token", ["**", "*.md", "DEV_*.md", "DEV_RULES.m?", "{DEV_RULES,X}.md", "docs/**/*.md"])
def test_rules_file_is_denied_to_a_sub_agent_when_files_in_only_has_a_glob(tmp_path: Path, token: str) -> None:
    contract = CONTRACT.replace("`src/a.py`", f"`{token}`, `src/a.py`")
    root = make_project(tmp_path, contract=contract, project=RULES_PROJECT)
    code, err = agent_write(root, "DEV_RULES.md")
    assert code == 2 and "exact path" in err
    assert agent_write(root, "src/a.py")[0] == 0


def test_rules_file_exact_token_is_normalised_and_case_folded(tmp_path: Path) -> None:
    contract = CONTRACT.replace("`src/a.py`", "`./dev_rules.md`, `src/a.py`")
    root = make_project(tmp_path, contract=contract, project=RULES_PROJECT)
    assert agent_write(root, "DEV_RULES.md", casefold=True)[0] == 0
    assert agent_write(root, "DEV_RULES.md", casefold=False)[0] == 2


def test_contract_keeps_the_raw_files_in_tokens() -> None:
    parsed = sg.parse_contract(CONTRACT)
    assert "tools/metrics/{a,b}.py" in parsed.files_in_raw and "tools/metrics/a.py" in parsed.files_in
    assert sg.Contract("T-1", ("a",), ()).files_in_raw == ()


# --- memory folder (T-39, DEC-046) ----------------------------------------------------

def memory_input(root: Path, config: Path, rel: str, agent: bool = False, transcript: object = "default") -> dict:
    data = payload("write-subagent" if agent else "write-main", root, str(config / "projects" / "slug" / "memory" / rel))
    if transcript == "default":
        data["transcript_path"] = str(config / "projects" / "slug" / "s1.jsonl")
    elif transcript is None:
        data.pop("transcript_path", None)
    else:
        data["transcript_path"] = transcript
    return data


@pytest.mark.parametrize("contract", [None, CONTRACT])
def test_main_session_may_write_in_the_memory_folder(tmp_path: Path, contract: str | None) -> None:
    root, config = make_project(tmp_path, contract=contract), tmp_path / "cfg"
    assert run(root, memory_input(root, config, "note.md")) == (0, "")
    assert run(root, memory_input(root, config, "sub/deep.md")) == (0, "")


def test_sub_agent_is_denied_in_the_memory_folder(tmp_path: Path) -> None:
    root, config = make_project(tmp_path), tmp_path / "cfg"
    code, err = run(root, memory_input(root, config, "note.md", agent=True))
    assert code == 2 and "outside the project root" in err


def test_dotdot_out_of_the_memory_folder_is_denied(tmp_path: Path) -> None:
    root, config = make_project(tmp_path), tmp_path / "cfg"
    for rel in ("../other/x.md", "../../x.md", "../s1.jsonl"):
        assert run(root, memory_input(root, config, rel))[0] == 2
    assert run(root, memory_input(root, config, "a/../b.md"))[0] == 0


def test_memory_sibling_with_a_shared_prefix_is_denied(tmp_path: Path) -> None:
    root, config = make_project(tmp_path), tmp_path / "cfg"
    data = payload("write-main", root, str(config / "projects" / "slug" / "memory-x" / "n.md"))
    data["transcript_path"] = str(config / "projects" / "slug" / "s1.jsonl")
    assert run(root, data)[0] == 2


@pytest.mark.parametrize("transcript", [None, "", "transcript.jsonl", 5])
def test_missing_or_relative_transcript_path_keeps_the_deny(tmp_path: Path, transcript: object) -> None:
    root, config = make_project(tmp_path), tmp_path / "cfg"
    assert run(root, memory_input(root, config, "note.md", transcript=transcript))[0] == 2


def test_wrong_layout_transcript_path_keeps_the_deny(tmp_path: Path) -> None:
    root, config = make_project(tmp_path), tmp_path / "cfg"
    for layout in (config / "other" / "slug" / "s1.jsonl", config / "projects" / "s1.jsonl",
                   config / "projects" / ".." / "evil" / "s1.jsonl"):
        assert run(root, memory_input(root, config, "note.md", transcript=str(layout)))[0] == 2


def test_memory_write_does_not_apply_without_opt_in_or_inside_the_root(tmp_path: Path) -> None:
    root, config = make_project(tmp_path, project=None), tmp_path / "cfg"
    assert run(root, memory_input(root, config, "note.md")) == (0, "")
    assert events(root) == []
    root2 = make_project(tmp_path / "b")
    data = payload("write-main", root2, str(root2 / "src" / "other.py"))
    data["transcript_path"] = str(root2 / "projects" / "slug" / "s1.jsonl")
    assert run(root2, data)[0] == 2  # decided by the contract, not by the memory rule


def test_memory_decision_records_a_relative_marker_not_the_absolute_path(tmp_path: Path) -> None:
    root, config = make_project(tmp_path), tmp_path / "cfg"
    decision = sg.check(root, str(config / "projects" / "slug" / "memory" / "a" / "n.md"), False, False,
                        memory_dir=sg.memory_folder(str(config / "projects" / "slug" / "s1.jsonl"), False))
    assert decision is not None and decision.allow and decision.rel == "<memory>/a/n.md"
    run(root, memory_input(root, config, "a/n.md"))
    assert str(config) not in (root / ".sdlc" / "metrics.jsonl").read_text(encoding="utf-8")


def test_memory_folder_is_case_folded_only_when_casefold_is_on(tmp_path: Path) -> None:
    root = make_project(tmp_path)
    data = payload("write-main", root, "C:/cfg/Projects/slug/memory/n.md")
    data["transcript_path"] = "C:/cfg/PROJECTS/slug/s1.jsonl".replace("/", chr(92))
    assert run(root, data, casefold=True)[0] == 0
    assert run(root, data, casefold=False)[0] == 2
    assert sg.memory_folder("C:/cfg/projects/slug/s1.jsonl".replace("/", chr(92)), False) == "C:/cfg/projects/slug/memory"
