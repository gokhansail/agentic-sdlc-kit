"""Tests for tools/records.py: the record map of .sdlc/project.md."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import records  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "server"


def _project(tmp_path: Path, fixture: str | None) -> Path:
    if fixture is not None:
        (tmp_path / ".sdlc").mkdir()
        (tmp_path / ".sdlc" / "project.md").write_bytes((FIXTURES / fixture).read_bytes())
    return tmp_path


def test_no_project_file_gives_the_template_defaults(tmp_path: Path) -> None:
    assert records.read_records(tmp_path) == records.DEFAULTS


def test_defaults_match_the_template() -> None:
    text = (ROOT / "templates" / "project.md").read_text(encoding="utf-8")
    parsed = records.parse_records(text)
    for key, value in records.DEFAULTS.items():
        if key != "report_language":  # the template holds a placeholder there
            assert parsed[key] == value


def test_template_placeholder_falls_back_to_the_default() -> None:
    text = (ROOT / "templates" / "project.md").read_text(encoding="utf-8")
    assert records.parse_records(text)["report_language"] == records.DEFAULTS["report_language"]


def test_file_without_a_records_section_gives_defaults(tmp_path: Path) -> None:
    root = _project(tmp_path, None)
    (root / ".sdlc").mkdir()
    (root / ".sdlc" / "project.md").write_text("# Project file\n\n## Always allowed\n- `docs/`\n", encoding="utf-8")
    assert records.read_records(root) == records.DEFAULTS


def test_lines_outside_the_records_section_are_ignored() -> None:
    text = "## Other\n- Status: `NOPE.md`\n\n## Records\n- Tasks: `T.md`\n\n## Later\n- Log: `NOPE.md`\n"
    got = records.parse_records(text)
    assert got["status"] == "STATUS.md" and got["log"] == "LOG.md" and got["tasks"] == "T.md"


def test_custom_file_overrides_extras_and_placeholders(tmp_path: Path) -> None:
    got = records.read_records(_project(tmp_path, "project-custom.md"))
    assert got["status"] == "docs/state.md"
    assert got["tasks"] == "plan/TASKS.md"
    assert got["developer_rules"] == "rules/DEV.md"
    assert got["report_language"] == "German"
    assert got["lessons"] == "LESSONS.md"  # an extra line keeps its own key
    assert got["log"] == "LOG.md"  # placeholder in angle brackets: default
    assert got["decisions"] == "DECISIONS.md"  # no line: default


def test_first_line_wins_and_bom_is_read(tmp_path: Path) -> None:
    (tmp_path / ".sdlc").mkdir()
    (tmp_path / ".sdlc" / "project.md").write_bytes(
        b"\xef\xbb\xbf## Records\n- Status: `A.md`\n- Status: `B.md`\n")
    assert records.read_records(tmp_path)["status"] == "A.md"


def test_cli_prints_json(tmp_path: Path) -> None:
    root = _project(tmp_path, "project-custom.md")
    for argv in ([sys.executable, str(ROOT / "tools" / "records.py")], [sys.executable, "-m", "tools.records"]):
        res = subprocess.run([*argv, "--root", str(root)], cwd=ROOT, capture_output=True, timeout=60)
        assert res.returncode == 0, res.stderr
        assert json.loads(res.stdout.decode("utf-8")) == records.read_records(root)


def test_records_module_uses_the_standard_library_and_tools_only() -> None:
    tree = ast.parse((ROOT / "tools" / "records.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    assert names <= set(sys.stdlib_module_names) | {"tools"}
