"""Tests for the session start hook (hooks/session/launcher.sh, templates/seat.md)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = ROOT / "hooks" / "session" / "launcher.sh"
SEAT = ROOT / "templates" / "seat.md"
SH = shutil.which("sh")

pytestmark = pytest.mark.skipif(SH is None, reason="sh not found")


def run(cwd: Path, project_dir: Path | None, plugin_root: Path | None = ROOT):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_ROOT")}
    if project_dir is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if plugin_root is not None:
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    return subprocess.run([SH, str(LAUNCHER)], cwd=cwd, env=env, capture_output=True,
                          text=True, encoding="utf-8", stdin=subprocess.DEVNULL, timeout=20)


def opted_in(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    (proj / ".sdlc").mkdir(parents=True)
    (proj / ".sdlc" / "project.md").write_text("# Project\n", encoding="utf-8")
    return proj


def test_silent_without_opt_in(tmp_path):
    proj = tmp_path / "plain"
    proj.mkdir()
    r = run(proj, proj)
    assert r.returncode == 0 and r.stdout == "" and r.stderr == ""


def test_prints_seat_when_opted_in(tmp_path):
    proj = opted_in(tmp_path)
    r = run(tmp_path, proj)
    assert r.returncode == 0
    assert r.stdout.strip() == SEAT.read_text(encoding="utf-8").strip()
    assert "Technical Lead" in r.stdout


def test_falls_back_to_start_folder(tmp_path):
    proj = opted_in(tmp_path)
    r = run(proj, None)
    assert r.returncode == 0 and "Technical Lead" in r.stdout
    other = tmp_path / "other"
    other.mkdir()
    r = run(other, None)
    assert r.returncode == 0 and r.stdout == ""


def test_missing_seat_file_is_silent_exit_0(tmp_path):
    proj = opted_in(tmp_path)
    empty = tmp_path / "emptyplugin"
    empty.mkdir()
    r = run(tmp_path, proj, plugin_root=empty)
    assert r.returncode == 0 and r.stdout == ""
    r = run(tmp_path, proj, plugin_root=None)
    assert r.returncode == 0 and r.stdout == ""


def test_hooks_json_registers_session_start():
    data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    cmds = [h["command"] for e in data["hooks"]["SessionStart"] for h in e["hooks"]]
    assert any("hooks/session/launcher.sh" in c for c in cmds)
    assert "PreToolUse" in data["hooks"]


def test_seat_text_shape():
    text = SEAT.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 18
    assert "go-ahead for a task is already given" in text
    assert "/sdlc-lead:contract" in text and "`developer` sub-agent" in text
    assert "Size each task E, M or H" in text and "no record entry of its own" in text
    assert "you write no code at any size" in text and "DEC-058" in text
    assert "--check-contract" in text and "fix it until it parses" in text
    assert "!" not in text
    assert "Sources:" in text
    for word in ("leverage", "seamless", "robust", "crucial", "comprehensive", "ensure that"):
        assert word not in text.lower()
