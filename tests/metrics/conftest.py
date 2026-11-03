"""Shared helpers for the metrics tests.

Fixtures are ASCII. The em dash of the source record format is written as {EM}
in the fixture files and replaced here with a code point built at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "tests" / "fixtures" / "metrics"
EM_DASH = chr(0x2014)


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="ascii").replace("{EM}", EM_DASH)


@pytest.fixture
def test_profile():
    from tools.metrics.profile import load_profile

    return load_profile(FIXTURES / "profile-test.json")


# --- temporary git repositories with fixed dates ---------------------------

def git_run(cwd: Path, *args: str, env: dict | None = None) -> str:
    import os
    import subprocess

    res = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, **(env or {})},
    )
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def git_init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git_run(path, "init", "-q", "-b", "main")
    git_run(path, "config", "user.name", "Test")
    git_run(path, "config", "user.email", "test@users.noreply.github.com")
    git_run(path, "config", "core.autocrlf", "false")
    return path


def git_commit(repo: Path, files: dict[str, str], author: str, committer: str | None = None) -> str:
    """Commit `files` with fixed author and committer dates (ISO 8601 with offset)."""
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    env = {"GIT_AUTHOR_DATE": author, "GIT_COMMITTER_DATE": committer or author}
    git_run(repo, "add", "-A", env=env)
    git_run(repo, "commit", "-q", "-m", "Change", env=env)
    return git_run(repo, "rev-parse", "HEAD")
