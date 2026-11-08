"""Tests for the plugin skills (skills/<name>/SKILL.md) and templates/project.md.

The skills are thin text; these tests keep their form: the five folders, the flag
that keeps `init` and `install-hooks` away from the model, the plugin paths, and
the opt-in template read by the scope guard's own parser.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import scope_guard as sg  # noqa: E402

SKILLS = ROOT / "skills"
NAMES = ["contract", "init", "install-hooks", "review", "status"]
FLAGGED = {"init", "install-hooks"}
LINE_LIMIT = 40


def text_of(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def frontmatter(name: str) -> dict[str, str]:
    lines = text_of(name).split("\n")
    assert lines[0] == "---"
    end = lines.index("---", 1)
    out: dict[str, str] = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def test_exactly_the_five_skill_folders() -> None:
    assert sorted(p.name for p in SKILLS.iterdir()) == NAMES
    for name in NAMES:
        assert sorted(p.name for p in (SKILLS / name).iterdir()) == ["SKILL.md"]


@pytest.mark.parametrize("name", NAMES)
def test_the_flag_is_on_init_and_install_hooks_only(name: str) -> None:
    flag = frontmatter(name).get("disable-model-invocation")
    if name in FLAGGED:
        assert flag == "true"
    else:
        assert flag is None


@pytest.mark.parametrize("name", NAMES)
def test_description_is_one_short_line(name: str) -> None:
    text = text_of(name)
    description = frontmatter(name).get("description", "")
    assert description and len(description) <= 160
    assert text.count("\ndescription:") == 1
    assert re.search(r"^description:.*\n(?![a-z-]+:|---)", text, re.MULTILINE) is None


@pytest.mark.parametrize("name", NAMES)
def test_line_limit_ascii_and_lf(name: str) -> None:
    raw = (SKILLS / name / "SKILL.md").read_bytes()
    raw.decode("ascii")
    assert b"\r" not in raw
    assert len(raw.decode("ascii").splitlines()) <= LINE_LIMIT


@pytest.mark.parametrize("name", NAMES)
def test_only_the_brace_form_of_the_plugin_root(name: str) -> None:
    text = text_of(name)
    assert re.search(r"\$CLAUDE_PLUGIN_ROOT", text) is None
    assert text.count("CLAUDE_PLUGIN_ROOT") == text.count("${CLAUDE_PLUGIN_ROOT}")


@pytest.mark.parametrize("name", NAMES)
def test_every_plugin_path_named_in_a_skill_exists(name: str) -> None:
    paths = re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)", text_of(name))
    for rel in paths:
        assert (ROOT / rel).is_file(), rel


def test_the_skills_name_the_scripts_and_the_template_they_need() -> None:
    assert "${CLAUDE_PLUGIN_ROOT}/templates/project.md" in text_of("init")
    assert "${CLAUDE_PLUGIN_ROOT}/templates/task-contract.md" in text_of("contract")
    assert "${CLAUDE_PLUGIN_ROOT}/tools/scope_guard.py\" --check-contract" in text_of("contract")
    assert "${CLAUDE_PLUGIN_ROOT}/tools/scope_guard.py\" --check-worktree" in text_of("review")
    assert "${CLAUDE_PLUGIN_ROOT}/tools/install_git_hooks.py\" --target ." in text_of("install-hooks")


@pytest.mark.parametrize("name", ["contract", "install-hooks", "review"])
def test_python_is_tried_in_the_launcher_order(name: str) -> None:
    text = text_of(name)
    assert text.index("`python`") < text.index("`python3`") < text.index("`py -3`")


def test_read_only_skills_name_no_write_tool() -> None:
    for name in ("status", "review"):
        tools = frontmatter(name).get("allowed-tools", "")
        assert not re.search(r"\b(Write|Edit|NotebookEdit)\b", tools)


def test_init_and_contract_name_the_file_tools_they_write_with() -> None:
    assert re.search(r"\bWrite\b", frontmatter("init").get("allowed-tools", ""))
    contract_tools = frontmatter("contract").get("allowed-tools", "")
    assert re.search(r"\bWrite\b", contract_tools) and re.search(r"\bEdit\b", contract_tools)


def test_init_keeps_the_developer_rules_file_out_of_the_always_allowed_list() -> None:
    text = " ".join(text_of("init").split())
    assert "The developer rules file never goes in the always-allowed list, even when the arguments name it" in text
    assert "Tell the customer so." in text
    assert "exact path, with no glob" in text


@pytest.mark.parametrize("name", ["init", "contract"])
def test_init_and_contract_have_no_heredoc_or_redirect(name: str) -> None:
    text = text_of(name)
    assert "<<" not in text
    assert re.search(r"(^|\s)\d?>{1,2}", text, re.MULTILINE) is None


# --- templates/project.md ---------------------------------------------------------

def filled_project() -> str:
    text = (ROOT / "templates" / "project.md").read_text(encoding="utf-8")
    text = text.replace("<test folder>", "tests")
    text = re.sub(r"<language[^>]*>", "English", text)
    return text


def test_a_filled_project_template_gives_the_expected_always_allowed_list() -> None:
    assert sg.parse_always_allowed(filled_project()) == [
        "STATUS.md", "TASKS.md", "LOG.md", "DECISIONS.md", "CHANGELOG.md", "audits/", "cto/", "tests/",
    ]


def test_a_filled_template_lets_the_guard_allow_a_record_and_a_test_and_deny_the_rest() -> None:
    always = sg.parse_always_allowed(filled_project())
    allow = sg.decide("tests/test_a.py", sg.NO_CONTRACT, None, always, False, False)
    deny = sg.decide("src/a.py", sg.NO_CONTRACT, None, always, False, False)
    assert allow.allow and not deny.allow


def test_the_unfilled_template_has_one_placeholder_for_the_tests_and_none_in_other_lists() -> None:
    text = (ROOT / "templates" / "project.md").read_text(encoding="utf-8")
    assert sg.parse_always_allowed(text)[-1] == "<test folder>/"
    assert "<" not in "".join(sg.parse_always_allowed(text)[:-1])


def test_the_template_has_the_record_map_and_the_section_name() -> None:
    text = (ROOT / "templates" / "project.md").read_text(encoding="utf-8")
    for label in ("Status", "Tasks", "Log", "Decisions", "Lessons", "Audits", "Changelog", "Developer rules",
                  "Report language"):
        assert f"- {label}:" in text
    assert "\n## Always allowed\n" in text
    assert text.startswith("# Project file\n\nWhat is this file?")
