"""Tests for the pre-push guard and its installer.

Secret-looking strings are built at runtime so this file passes its own guard.
All repositories live in pytest temp dirs; the project's own .git is never used.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ZERO = "0" * 40

AWS_KEY = "AKIA" + "X" * 16
SLACK = "xox" + "b-" + "1" * 12
GH_TOKEN = "gh" + "p_" + "a" * 36
EMAIL = "someone" + "@" + "example.org"
TURKISH = "ca" + chr(0x11F) + "r"
WIN_PATH = "C" + ":" + chr(92) + "Us" + "ers" + chr(92) + "bob"
HOME_PATH = "/ho" + "me/bob/x"
GDOC = "https://docs." + "google" + ".com/document/d/abc"
DEBUG_ON = "debug" + "Enabled = " + "true"


def run(cwd: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, input=stdin, capture_output=True, text=True, encoding="utf-8")


def git(cwd: Path, *args: str) -> str:
    res = run(cwd, "git", *args)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "Test")
    git(path, "config", "user.email", "test@users.noreply.github.com")
    git(path, "config", "core.autocrlf", "false")
    (path / "tools").mkdir()
    (path / "hooks" / "git").mkdir(parents=True)
    (path / ".sdlc").mkdir()
    for rel in ("tools/pre_push_guard.py", "tools/install_git_hooks.py",
                "hooks/git/pre-push", ".sdlc/guard-patterns.txt"):
        shutil.copy(ROOT / rel, path / rel)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "Add guard")
    return path


def commit(repo: Path, files: dict[str, str], message: str = "Change") -> str:
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    git(repo, "add", "-A", "-f")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def guard(repo: Path, local: str, remote: str = ZERO) -> subprocess.CompletedProcess:
    line = f"refs/heads/main {local} refs/heads/main {remote}\n"
    return run(repo, sys.executable, str(repo / "tools" / "pre_push_guard.py"), "origin", "none", stdin=line)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "work")


def test_rejects_planted_secret(repo: Path) -> None:
    sha = commit(repo, {"app.txt": f"line one\nline two\nkey = {AWS_KEY}\n"})
    res = guard(repo, sha)
    assert res.returncode != 0
    assert sha[:7] in res.stderr
    assert "app.txt:3" in res.stderr
    assert "aws-key" in res.stderr
    assert AWS_KEY not in res.stderr


def test_passes_clean_commit(repo: Path) -> None:
    sha = commit(repo, {"app.txt": "nothing to see\n", "doc.md": "Plain English text.\n"},
                 "Add app and doc\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    res = guard(repo, sha)
    assert res.returncode == 0, res.stderr


def test_rejects_secret_in_commit_message(repo: Path) -> None:
    sha = commit(repo, {"a.txt": "ok\n"}, f"Fix thing {GH_TOKEN}")
    res = guard(repo, sha)
    assert res.returncode != 0
    assert "commit message" in res.stderr and "github-token" in res.stderr


@pytest.mark.parametrize("name,value", [
    ("slack-token", SLACK),
    ("email-address", EMAIL),
    ("non-english-char", TURKISH),
    ("abs-path-windows", WIN_PATH),
    ("abs-path-home", HOME_PATH),
    ("google-url", GDOC),
    ("debug-flag-on", DEBUG_ON),
])
def test_pattern_catalogue(repo: Path, name: str, value: str) -> None:
    sha = commit(repo, {"f.txt": f"x {value} y\n"})
    res = guard(repo, sha)
    assert res.returncode != 0
    assert name in res.stderr


def test_allowed_emails_pass(repo: Path) -> None:
    text = "a" + "@users.noreply.github.com\nnoreply" + "@anthropic.com\n"
    sha = commit(repo, {"f.txt": text})
    assert guard(repo, sha).returncode == 0


@pytest.mark.parametrize("text", [
    "bench" + "@" + "example.invalid",
    "a" + "@" + "b.c.invalid",
    "a" + "@" + "b.invalid.",
])
def test_reserved_invalid_domain_passes(repo: Path, text: str) -> None:
    sha = commit(repo, {"f.txt": f"{text}\n"})
    assert guard(repo, sha).returncode == 0


@pytest.mark.parametrize("text", [
    "someone" + "@" + "example.com",
    "x" + "@" + "invalid.com",
    "x" + "@" + "foo.invalidate.org",
    "x" + "@" + "foo.invalid" + ".com",
])
def test_email_lookalikes_still_flagged(repo: Path, text: str) -> None:
    sha = commit(repo, {"f.txt": f"{text}\n"})
    res = guard(repo, sha)
    assert res.returncode != 0
    assert "email-address" in res.stderr


def test_only_new_commits_are_scanned(repo: Path) -> None:
    old = commit(repo, {"f.txt": f"{AWS_KEY}\n"})
    new = commit(repo, {"g.txt": "clean\n"})
    assert guard(repo, new, remote=old).returncode == 0
    assert guard(repo, new, remote=git(repo, "rev-parse", "HEAD~2")).returncode != 0


def test_deleting_a_branch_passes(repo: Path) -> None:
    line = f"(delete) {ZERO} refs/heads/old {'1' * 40}\n"
    res = run(repo, sys.executable, str(repo / "tools" / "pre_push_guard.py"), "origin", "none", stdin=line)
    assert res.returncode == 0


def test_private_pattern_reports_name_only(repo: Path) -> None:
    local = repo / ".sdlc" / "local"
    local.mkdir()
    (local / "private-patterns.txt").write_text("# private\nproject-codename  zebrafoxtrot\n", encoding="utf-8")
    sha = commit(repo, {"notes.txt": "we call it zebrafoxtrot internally\n"})
    res = guard(repo, sha)
    assert res.returncode != 0
    assert "project-codename" in res.stderr
    assert "zebrafoxtrot" not in res.stderr + res.stdout


def test_invalid_private_regex_fails_closed_without_echo(repo: Path) -> None:
    local = repo / ".sdlc" / "local"
    local.mkdir()
    (local / "private-patterns.txt").write_text("broken  secretword(\n", encoding="utf-8")
    sha = commit(repo, {"a.txt": "ok\n"})
    res = guard(repo, sha)
    assert res.returncode != 0
    assert "broken" in res.stderr and "secretword" not in res.stderr


@pytest.mark.parametrize("path", [
    ".env", "sub/.env", "PLAN.md", "PRIVATE.md", "CLAUDE.local.md",
    "evidence/raw/data.csv", ".sdlc/local/private-patterns.txt",
])
def test_forbidden_paths_rejected(repo: Path, path: str) -> None:
    sha = commit(repo, {path: "harmless  content\n"})
    res = guard(repo, sha)
    assert res.returncode != 0
    assert "forbidden-path" in res.stderr and Path(path).name in res.stderr


@pytest.mark.parametrize("path", [".env.example", "docs/PLAN.md", "evidence/summary.md"])
def test_legal_paths_pass(repo: Path, path: str) -> None:
    sha = commit(repo, {path: "harmless\n"})
    assert guard(repo, sha).returncode == 0


def test_pattern_file_is_exempt(repo: Path) -> None:
    sha = commit(repo, {".sdlc/guard-patterns.txt": f"extra  {AWS_KEY}\n"})
    assert guard(repo, sha).returncode == 0


def test_repo_files_pass_their_own_guard() -> None:
    files = [
        "hooks/git/pre-push", "tools/install_git_hooks.py", "tools/pre_push_guard.py",
        ".sdlc/guard-patterns.txt", ".gitattributes", "tests/test_pre_push.py",
    ]
    res = run(ROOT, sys.executable, str(ROOT / "tools" / "pre_push_guard.py"), "--files", *files)
    assert res.returncode == 0, res.stderr


def test_hook_file_has_lf_endings() -> None:
    data = (ROOT / "hooks" / "git" / "pre-push").read_bytes()
    assert data.startswith(b"#!/bin/sh\n")
    assert b"\r" not in data


def test_installer_is_idempotent(repo: Path) -> None:
    installer = str(repo / "tools" / "install_git_hooks.py")
    first = run(repo, sys.executable, installer)
    second = run(repo, sys.executable, installer)
    assert first.returncode == 0 and second.returncode == 0
    assert "installed" in first.stdout
    assert "already installed" in second.stdout
    assert git(repo, "config", "--local", "core.hooksPath") == "hooks/git"
    assert run(repo, "git", "config", "--local", "--get-all", "core.hooksPath").stdout.count("\n") == 1


def test_installer_refuses_foreign_hooks_path(repo: Path) -> None:
    git(repo, "config", "--local", "core.hooksPath", "other")
    installer = str(repo / "tools" / "install_git_hooks.py")
    assert run(repo, sys.executable, installer).returncode != 0
    assert git(repo, "config", "--local", "core.hooksPath") == "other"
    assert run(repo, sys.executable, installer, "--force").returncode == 0


def test_end_to_end_push(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "work")
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    assert run(repo, sys.executable, str(repo / "tools" / "install_git_hooks.py")).returncode == 0

    commit(repo, {"ok.txt": "clean\n"})
    assert run(repo, "git", "push", "-q", "origin", "main").returncode == 0
    good_head = git(repo, "rev-parse", "HEAD")

    commit(repo, {"leak.txt": f"token {AWS_KEY}\n"})
    res = run(repo, "git", "push", "origin", "main")
    assert res.returncode != 0
    assert "leak.txt:1" in res.stderr and "aws-key" in res.stderr
    assert git(remote, "rev-parse", "main") == good_head

    git(repo, "reset", "-q", "--hard", "HEAD~1")
    commit(repo, {"fine.txt": "clean again\n"})
    assert run(repo, "git", "push", "-q", "origin", "main").returncode == 0
    assert git(remote, "rev-parse", "main") == git(repo, "rev-parse", "HEAD")
