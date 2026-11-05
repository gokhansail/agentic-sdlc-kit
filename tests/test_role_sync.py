"""Role files: `agents/` is the source, `.claude/agents/` a tested copy (DEC-035)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "agents"
COPY = ROOT / ".claude" / "agents"

MODELS = {"opus", "sonnet", "haiku", "fable"}
EFFORTS = {"low", "medium", "high", "xhigh"}
EXPECTED = {"auditor-mini", "auditor", "cto", "developer", "scout", "scribe", "tech-writer"}


def _text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _names(folder: Path) -> set[str]:
    return {p.stem for p in folder.glob("*.md")}


def differences(a: Path, b: Path) -> list[str]:
    """Names that are missing on one side or whose normalized text differs."""
    na, nb = _names(a), _names(b)
    out = sorted(na ^ nb)
    out += [n for n in sorted(na & nb) if _text(a / f"{n}.md") != _text(b / f"{n}.md")]
    return out


def frontmatter(path: Path) -> dict[str, str] | None:
    """The frontmatter fields, or None when the file has no frontmatter block."""
    m = re.match(r"---\n(.*?)\n---\n", _text(path), re.S)
    if not m:
        return None
    fields = {}
    for line in m.group(1).split("\n"):
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def value_errors(path: Path) -> list[str]:
    """Problems with `model` and `effort` in one role file; empty when valid."""
    fm = frontmatter(path)
    if fm is None:
        return ["frontmatter: missing"]
    errors = []
    if fm.get("model") not in MODELS:
        errors.append(f"model: {fm.get('model')!r}")
    if fm.get("effort") not in EFFORTS:
        errors.append(f"effort: {fm.get('effort')!r}")
    return errors


def test_folders_hold_the_seven_roles():
    assert _names(SOURCE) == EXPECTED
    assert _names(COPY) == EXPECTED


def test_folders_have_the_same_text():
    assert differences(SOURCE, COPY) == []


def test_line_endings_are_normalized(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "x.md").write_bytes(b"one\ntwo\n")
    (b / "x.md").write_bytes(b"one\r\ntwo\r\n")
    assert differences(a, b) == []


def test_planted_text_difference_is_found(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "x.md").write_text("one\ntwo\n", encoding="utf-8")
    (b / "x.md").write_text("one\nthree\n", encoding="utf-8")
    (a / "only_a.md").write_text("z\n", encoding="utf-8")
    assert differences(a, b) == ["only_a", "x"]


def _role(tmp_path: Path, model: str, effort: str) -> Path:
    p = tmp_path / "role.md"
    p.write_text(f"---\nname: r\nmodel: {model}\neffort: {effort}\n---\n\nBody\n", encoding="utf-8")
    return p


def test_model_and_effort_values_are_valid():
    for folder in (SOURCE, COPY):
        for path in sorted(folder.glob("*.md")):
            assert value_errors(path) == [], path.name


def test_valid_role_has_no_errors(tmp_path):
    assert value_errors(_role(tmp_path, "sonnet", "medium")) == []


def test_bad_model_is_reported(tmp_path):
    errors = value_errors(_role(tmp_path, "gpt", "medium"))
    assert len(errors) == 1 and errors[0].startswith("model")


def test_bad_effort_is_reported(tmp_path):
    errors = value_errors(_role(tmp_path, "sonnet", "max"))
    assert len(errors) == 1 and errors[0].startswith("effort")


def test_missing_frontmatter_is_reported(tmp_path):
    p = tmp_path / "plain.md"
    p.write_text("No frontmatter here\n", encoding="utf-8")
    assert value_errors(p) == ["frontmatter: missing"]
