"""Tests for the installer's target mode and the pattern-file rules it relies on.

Every repository lives in a pytest temp dir. The global and system git config are
replaced, so a hooksPath on the developer's machine cannot change a result. Secret-looking
strings and non-ASCII letters are built at runtime so this file passes its own guard.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "tools" / "install_git_hooks.py"
GUARD = ROOT / "tools" / "pre_push_guard.py"
TEMPLATE = ROOT / "templates" / "guard-patterns.txt"
KIT_PATTERNS = ROOT / ".sdlc" / "guard-patterns.txt"
ZERO = "0" * 40
AWS_KEY = "AKIA" + "X" * 16
MARKER = b"# sdlc-guard-wrapper"
OLD_HOOK = (
    b'#!/bin/sh\n# the project\'s own hook\ncat > "$OLD_HOOK_OUT"\n'
    b'echo "$@" > "$OLD_HOOK_OUT.args"\nexit "${OLD_HOOK_EXIT:-0}"\n'
)
SPACED_NAME = "my repo " + chr(0xE9)


def find_sh() -> str | None:
    found = shutil.which("sh")
    if found:
        return found
    git_exe = shutil.which("git")
    if git_exe:
        for rel in ("../bin/sh.exe", "../usr/bin/sh.exe", "../../usr/bin/sh.exe"):
            candidate = (Path(git_exe).parent / rel).resolve()
            if candidate.is_file():
                return str(candidate)
    return None


SH = find_sh()


def run(cwd: Path, *args: str, stdin: str | bytes | None = None) -> subprocess.CompletedProcess:
    if isinstance(stdin, bytes):
        return subprocess.run(args, cwd=cwd, input=stdin, capture_output=True)
    return subprocess.run(args, cwd=cwd, input=stdin, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def git(cwd: Path, *args: str) -> str:
    res = run(cwd, "git", *args)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def install(target: Path | str, *extra: str) -> subprocess.CompletedProcess:
    return run(ROOT, sys.executable, str(INSTALLER), "--target", str(target), *extra)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(folder: Path) -> dict[str, str]:
    return {
        p.relative_to(folder).as_posix(): sha(p) for p in sorted(folder.rglob("*")) if p.is_file()
    }


def tree_state(target: Path) -> dict[str, str]:
    """Hashes of everything an installer could touch: the work tree, hooks and info."""
    state = {}
    for rel, digest in hashes(target).items():
        if rel.startswith(".git/") and not rel.startswith((".git/hooks/", ".git/info/")):
            continue
        state[rel] = digest
    return state


@pytest.fixture(autouse=True)
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config = tmp_path / "cfg" / "global-gitconfig"
    config.parent.mkdir()
    config.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("OLD_HOOK_OUT", str(tmp_path / "cfg" / "old-hook-stdin"))
    monkeypatch.delenv("OLD_HOOK_EXIT", raising=False)
    return config


def make_target(base: Path, name: str = "target", old_hook: bytes | None = None) -> Path:
    path = base / name
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "Test")
    git(path, "config", "user.email", "test@users.noreply.github.com")
    git(path, "config", "core.autocrlf", "false")
    (path / "app.txt").write_text("hello\n", encoding="utf-8", newline="\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "Start")
    if old_hook is not None:
        hook = path / ".git" / "hooks" / "pre-push"
        hook.write_bytes(old_hook)
        os.chmod(hook, 0o755)
    return path


def add_remote(base: Path, target: Path) -> Path:
    remote = base / "remote.git"
    git(base, "init", "-q", "--bare", str(remote))
    git(target, "remote", "add", "origin", str(remote))
    return remote


def commit(repo: Path, files: dict[str, str], message: str = "Change") -> str:
    for rel, content in files.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    git(repo, "add", "--", *files)
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def remote_has_main(remote: Path) -> bool:
    return run(remote, "git", "rev-parse", "--verify", "-q", "refs/heads/main").returncode == 0


def hook_dir(target: Path) -> Path:
    return target / ".git" / "hooks"


def stdin_line(ref: str, local: str, remote: str = ZERO) -> str:
    return f"refs/heads/{ref} {local} refs/heads/{ref} {remote}\n"


# ------------------------------------------------------------------ install

def test_install_without_old_hook_guards_pushes(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    remote = add_remote(tmp_path, target)
    res = install(target)
    assert res.returncode == 0, res.stderr
    wrapper = hook_dir(target) / "pre-push"
    assert MARKER in wrapper.read_bytes()
    assert not (hook_dir(target) / "pre-push.sdlc-old").exists()
    assert (target / ".sdlc" / "guard" / "pre_push_guard.py").read_bytes() == GUARD.read_bytes()
    assert run(target, "git", "config", "--get", "core.hooksPath").returncode != 0

    commit(target, {"ok.txt": "clean\n"})
    assert run(target, "git", "push", "-q", "origin", "main").returncode == 0
    good = git(target, "rev-parse", "HEAD")
    assert git(remote, "rev-parse", "main") == good

    commit(target, {"leak.txt": f"key = {AWS_KEY}\n"})
    res = run(target, "git", "push", "origin", "main")
    assert res.returncode != 0
    assert "leak.txt:1" in res.stderr and "aws-key" in res.stderr
    assert git(remote, "rev-parse", "main") == good


def test_old_hook_runs_first_and_sees_the_same_stdin(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    head = commit(target, {"ok.txt": "clean\n"})

    res = run(target, "git", "push", "-q", "origin", "main")
    assert res.returncode == 0, res.stderr
    seen = Path(os.environ["OLD_HOOK_OUT"])
    assert seen.read_bytes() == stdin_line("main", head).encode("ascii")
    args = Path(os.environ["OLD_HOOK_OUT"] + ".args").read_text(encoding="utf-8").split()
    assert args[0] == "origin"
    assert git(remote, "rev-parse", "main") == head


def test_planted_secret_is_rejected_with_an_old_hook(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    commit(target, {"leak.txt": f"key = {AWS_KEY}\n"})
    res = run(target, "git", "push", "origin", "main")
    assert res.returncode != 0
    assert "aws-key" in res.stderr
    assert Path(os.environ["OLD_HOOK_OUT"]).exists()  # the old hook ran and passed
    assert not remote_has_main(remote)


def test_failing_old_hook_blocks_and_the_guard_is_not_reached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    commit(target, {"leak.txt": f"key = {AWS_KEY}\n"})
    monkeypatch.setenv("OLD_HOOK_EXIT", "3")
    res = run(target, "git", "push", "origin", "main")
    assert res.returncode != 0
    assert "aws-key" not in res.stderr  # the old hook stopped the push first
    assert not remote_has_main(remote)


@pytest.mark.skipif(SH is None, reason="no sh available")
def test_wrapper_returns_the_exit_code_of_the_old_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    assert install(target).returncode == 0
    wrapper = str(hook_dir(target) / "pre-push")
    line = stdin_line("main", git(target, "rev-parse", "HEAD")).encode("ascii")
    assert run(target, SH, wrapper, "origin", "none", stdin=line).returncode == 0
    monkeypatch.setenv("OLD_HOOK_EXIT", "7")
    assert run(target, SH, wrapper, "origin", "none", stdin=line).returncode == 7


@pytest.mark.skipif(SH is None, reason="no sh available")
def test_both_readers_get_the_same_bytes_even_without_a_final_newline(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    assert install(target).returncode == 0
    wrapper = str(hook_dir(target) / "pre-push")
    data = stdin_line("main", git(target, "rev-parse", "HEAD")).rstrip("\n").encode("ascii")
    res = run(target, SH, wrapper, "origin", "none", stdin=data)
    assert res.returncode == 0, res.stderr
    assert Path(os.environ["OLD_HOOK_OUT"]).read_bytes() == data


def test_two_refs_on_stdin_reach_both_readers(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    main_sha = commit(target, {"one.txt": "one\n"})
    git(target, "checkout", "-q", "-b", "feature")
    feature_sha = commit(target, {"two.txt": "two\n"})
    git(target, "checkout", "-q", "main")

    res = run(target, "git", "push", "-q", "origin", "main", "feature")
    assert res.returncode == 0, res.stderr
    seen = Path(os.environ["OLD_HOOK_OUT"]).read_text(encoding="ascii").splitlines()
    assert sorted(seen) == sorted(
        [stdin_line("main", main_sha).strip(), stdin_line("feature", feature_sha).strip()]
    )

    # The secret is in the second ref only: the guard must still read it.
    git(target, "checkout", "-q", "feature")
    commit(target, {"leak.txt": f"key = {AWS_KEY}\n"})
    git(target, "checkout", "-q", "main")
    res = run(target, "git", "push", "origin", "main", "feature")
    assert res.returncode != 0 and "aws-key" in res.stderr
    assert git(remote, "rev-parse", "feature") == feature_sha


def test_path_with_space_and_non_ascii_letter_round_trip(tmp_path: Path) -> None:
    target = make_target(tmp_path, SPACED_NAME, old_hook=OLD_HOOK)
    remote = add_remote(tmp_path, target)
    before = hashes(hook_dir(target))
    assert install(target).returncode == 0
    head = commit(target, {"ok.txt": "clean\n"})
    assert run(target, "git", "push", "-q", "origin", "main").returncode == 0
    assert git(remote, "rev-parse", "main") == head
    commit(target, {"leak.txt": f"key = {AWS_KEY}\n"})
    assert run(target, "git", "push", "origin", "main").returncode != 0
    assert install(target, "--uninstall").returncode == 0
    assert hashes(hook_dir(target)) == before


def test_missing_hooks_folder_is_created(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    shutil.rmtree(hook_dir(target))
    assert install(target).returncode == 0
    assert MARKER in (hook_dir(target) / "pre-push").read_bytes()


def test_wrapper_has_only_lf_endings(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    git(target, "config", "core.autocrlf", "true")
    assert install(target).returncode == 0
    data = (hook_dir(target) / "pre-push").read_bytes()
    assert data.startswith(b"#!/bin/sh\n")
    assert b"\r" not in data
    assert b"\r" not in (target / ".sdlc" / "guard" / "pre_push_guard.py").read_bytes()


# -------------------------------------------------------------- rerun, stale

def test_rerun_changes_nothing_and_never_chains_the_wrapper(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    assert install(target).returncode == 0
    state = tree_state(target)
    saved = hook_dir(target) / "pre-push.sdlc-old"
    assert saved.read_bytes() == OLD_HOOK

    for _ in range(2):
        res = install(target)
        assert res.returncode == 0 and "no change" in res.stdout
    assert tree_state(target) == state
    assert saved.read_bytes() == OLD_HOOK
    assert MARKER not in saved.read_bytes()


def test_stale_copy_is_reported_and_refresh_replaces_it(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    assert install(target).returncode == 0
    copy = target / ".sdlc" / "guard" / "pre_push_guard.py"
    patterns = target / ".sdlc" / "guard-patterns.txt"
    copy.write_bytes(copy.read_bytes() + b"# old\n")
    patterns.write_bytes(patterns.read_bytes() + b"my-own  mine\n")
    state = tree_state(target)

    res = install(target)
    assert res.returncode == 1 and "stale" in res.stderr
    assert tree_state(target) == state

    patterns_before = sha(patterns)
    res = install(target, "--refresh")
    assert res.returncode == 0, res.stderr
    assert copy.read_bytes() == GUARD.read_bytes()
    assert sha(patterns) == patterns_before
    assert "no change" in install(target).stdout


def test_stale_wrapper_is_refreshed_and_the_old_hook_stays(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    assert install(target).returncode == 0
    wrapper = hook_dir(target) / "pre-push"
    wrapper.write_bytes(wrapper.read_bytes() + b"# edited\n")
    res = install(target)
    assert res.returncode == 1 and "stale" in res.stderr
    assert install(target, "--refresh").returncode == 0
    assert b"# edited" not in wrapper.read_bytes()
    assert (hook_dir(target) / "pre-push.sdlc-old").read_bytes() == OLD_HOOK


# ----------------------------------------------------------------- uninstall

@pytest.mark.parametrize("with_old_hook", [True, False])
def test_uninstall_restores_the_hook_folder_byte_for_byte(tmp_path: Path, with_old_hook: bool) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK if with_old_hook else None)
    before = hashes(hook_dir(target))
    mode = (hook_dir(target) / "pre-push").stat().st_mode if with_old_hook else None
    assert install(target).returncode == 0
    assert hashes(hook_dir(target)) != before

    res = install(target, "--uninstall")
    assert res.returncode == 0, res.stderr
    assert hashes(hook_dir(target)) == before
    if with_old_hook:
        assert (hook_dir(target) / "pre-push").stat().st_mode == mode
    assert run(target, "git", "config", "--get", "core.hooksPath").returncode != 0
    assert not (target / ".sdlc" / "guard").exists()
    assert (target / ".sdlc" / "guard-patterns.txt").is_file()
    assert (target / ".sdlc" / "local").is_dir()
    for left in ("guard-patterns.txt", "local", "info/exclude"):
        assert left in res.stdout


def test_uninstall_when_not_installed_is_a_no_op(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    state = tree_state(target)
    res = install(target, "--uninstall")
    assert res.returncode == 0 and "no change" in res.stdout
    assert tree_state(target) == state
    # also after a real install and uninstall: the second call is a no-op
    assert install(target).returncode == 0
    assert install(target, "--uninstall").returncode == 0
    res = install(target, "--uninstall")
    assert res.returncode == 0 and "no change" in res.stdout


def test_uninstall_refuses_a_pre_push_that_is_not_the_wrapper(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    assert install(target).returncode == 0
    wrapper = hook_dir(target) / "pre-push"
    wrapper.write_bytes(OLD_HOOK)  # someone replaced the wrapper; our traces remain
    state = tree_state(target)
    res = install(target, "--uninstall")
    assert res.returncode == 1
    assert tree_state(target) == state


# ------------------------------------------------------------------ refusals

def test_not_a_git_repository_is_refused(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    res = install(plain)
    assert res.returncode == 1 and "not a git repository" in res.stderr
    assert list(plain.iterdir()) == []
    assert install(make_target(tmp_path)).returncode == 0


def test_bare_repository_is_refused(tmp_path: Path) -> None:
    bare = tmp_path / "bare.git"
    git(tmp_path, "init", "-q", "--bare", str(bare))
    state = hashes(bare)
    res = install(bare)
    assert res.returncode == 1 and "bare" in res.stderr
    assert hashes(bare) == state
    assert install(make_target(tmp_path)).returncode == 0


def test_local_hooks_path_is_refused(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    git(target, "config", "core.hooksPath", "elsewhere")
    state = tree_state(target)
    res = install(target)
    assert res.returncode == 1 and "core.hooksPath" in res.stderr
    assert tree_state(target) == state
    git(target, "config", "--unset", "core.hooksPath")
    assert install(target).returncode == 0


def test_global_hooks_path_is_refused(tmp_path: Path, isolated_git: Path) -> None:
    target = make_target(tmp_path)
    isolated_git.write_text("[core]\n\thooksPath = elsewhere\n", encoding="utf-8")
    state = tree_state(target)
    res = install(target)
    assert res.returncode == 1 and "core.hooksPath" in res.stderr
    assert tree_state(target) == state
    isolated_git.write_text("", encoding="utf-8")
    assert install(target).returncode == 0


@pytest.mark.parametrize("rel", [".sdlc", ".sdlc/guard", ".sdlc/local"])
def test_a_file_where_a_folder_is_needed_is_refused_cleanly(tmp_path: Path, rel: str) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    blocker = target / rel
    blocker.parent.mkdir(parents=True, exist_ok=True)
    blocker.write_text("not a folder\n", encoding="utf-8")
    state = tree_state(target)
    hooks_before = hashes(hook_dir(target))
    res = install(target)
    assert res.returncode == 1
    assert f"{rel} exists and is not a folder" in res.stderr
    assert "Traceback" not in res.stderr
    assert hashes(hook_dir(target)) == hooks_before
    assert blocker.read_text(encoding="utf-8") == "not a folder\n"
    assert tree_state(target) == state
    # legal case: a real folder with the user's own file installs and keeps it
    blocker.unlink()
    blocker.mkdir()
    (blocker / "notes.txt").write_text("mine\n", encoding="utf-8")
    assert install(target).returncode == 0
    assert (blocker / "notes.txt").read_text(encoding="utf-8") == "mine\n"


def test_saved_hook_beside_a_foreign_pre_push_is_refused(tmp_path: Path) -> None:
    target = make_target(tmp_path, old_hook=OLD_HOOK)
    saved = hook_dir(target) / "pre-push.sdlc-old"
    saved.write_bytes(b"#!/bin/sh\nexit 0\n")
    state = tree_state(target)
    res = install(target)
    assert res.returncode == 1 and "pre-push.sdlc-old" in res.stderr
    assert tree_state(target) == state
    saved.unlink()
    assert install(target).returncode == 0
    assert (hook_dir(target) / "pre-push.sdlc-old").read_bytes() == OLD_HOOK


def test_force_is_refused_with_target_but_kept_in_kit_mode(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    state = tree_state(target)
    res = install(target, "--force")
    assert res.returncode == 1 and "--force" in res.stderr
    assert tree_state(target) == state

    kit_like = make_target(tmp_path, "kit-like")
    (kit_like / "hooks" / "git").mkdir(parents=True)
    shutil.copy(ROOT / "hooks" / "git" / "pre-push", kit_like / "hooks" / "git" / "pre-push")
    git(kit_like, "config", "core.hooksPath", "other")
    assert run(ROOT, sys.executable, str(INSTALLER), "--repo", str(kit_like)).returncode == 1
    res = run(ROOT, sys.executable, str(INSTALLER), "--repo", str(kit_like), "--force")
    assert res.returncode == 0, res.stderr
    assert git(kit_like, "config", "--local", "core.hooksPath") == "hooks/git"


@pytest.mark.parametrize("flag", ["--refresh", "--uninstall"])
def test_refresh_and_uninstall_need_a_target(tmp_path: Path, flag: str) -> None:
    res = run(tmp_path, sys.executable, str(INSTALLER), flag)
    assert res.returncode == 1 and "--target" in res.stderr
    target = make_target(tmp_path)
    assert install(target, flag).returncode == 0


def test_refresh_and_uninstall_together_are_refused(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    res = install(target, "--refresh", "--uninstall")
    assert res.returncode == 1
    assert not (target / ".sdlc").exists()


def test_target_with_dot_dot_segments_resolves_inside_the_repository(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    (tmp_path / "side").mkdir()
    roundabout = tmp_path / "side" / ".." / "target"
    assert install(roundabout).returncode == 0
    assert (target / ".sdlc" / "guard" / "pre_push_guard.py").is_file()
    assert not (tmp_path / "side" / ".sdlc").exists()


def test_target_outside_a_repository_or_below_its_top_is_refused(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    (target / "sub").mkdir()
    state = tree_state(target)
    for bad in (target / "sub", target / "..", target / ".git"):
        res = install(bad)
        assert res.returncode == 1, str(bad)
    assert tree_state(target) == state
    assert not (tmp_path / ".sdlc").exists()
    outside = tmp_path / "outside"
    outside.mkdir()
    assert install(outside).returncode == 1
    assert list(outside.iterdir()) == []


# ----------------------------------------------------------- pattern files

def test_pattern_files_are_created_from_the_template_and_never_overwritten(tmp_path: Path) -> None:
    fresh = make_target(tmp_path, "fresh")
    assert install(fresh).returncode == 0
    assert (fresh / ".sdlc" / "guard-patterns.txt").read_bytes() == TEMPLATE.read_bytes()
    assert (fresh / ".sdlc" / "local" / "private-patterns.txt").read_bytes() == b""
    assert "non-english-char" not in TEMPLATE.read_text(encoding="utf-8")

    mine = make_target(tmp_path, "mine")
    (mine / ".sdlc" / "local").mkdir(parents=True)
    (mine / ".sdlc" / "guard-patterns.txt").write_text("own  ownpattern\n", encoding="utf-8")
    (mine / ".sdlc" / "local" / "private-patterns.txt").write_text("priv  privword\n", encoding="utf-8")
    before = hashes(mine / ".sdlc")
    assert install(mine).returncode == 0
    assert install(mine, "--refresh").returncode in (0, 1)
    assert install(mine, "--uninstall").returncode == 0
    after = hashes(mine / ".sdlc")
    assert after["guard-patterns.txt"] == before["guard-patterns.txt"]
    assert after["local/private-patterns.txt"] == before["local/private-patterns.txt"]


def test_created_private_file_holds_no_kit_term(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    assert install(target).returncode == 0
    created = (target / ".sdlc" / "local" / "private-patterns.txt").read_text(encoding="utf-8")
    assert created.strip() == ""
    kit_private = ROOT / ".sdlc" / "local" / "private-patterns.txt"
    if kit_private.is_file():
        terms = [
            line.split(None, 1)[1].strip()
            for line in kit_private.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#") and len(line.split(None, 1)) == 2
        ]
        everything = "".join(
            p.read_text(encoding="utf-8", errors="replace")
            for p in (target / ".sdlc").rglob("*")
            if p.is_file() and p.name != "pre_push_guard.py"
        )
        assert not any(term in everything for term in terms)


# ----------------------------------------------------------------- exclude

def exclude_lines(target: Path) -> list[str]:
    return (target / ".git" / "info" / "exclude").read_text(encoding="utf-8").splitlines()


def test_exclude_line_is_added_once(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    assert install(target).returncode == 0
    assert install(target, "--uninstall").returncode == 0
    assert install(target).returncode == 0
    assert install(target, "--refresh").returncode == 0
    assert exclude_lines(target).count(".sdlc/") == 1


def test_exclude_line_follows_a_file_without_a_final_newline(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    (target / ".git" / "info" / "exclude").write_bytes(b"build/")
    assert install(target).returncode == 0
    assert exclude_lines(target) == ["build/", ".sdlc/"]
    assert install(target, "--refresh").returncode == 0
    assert exclude_lines(target) == ["build/", ".sdlc/"]


def test_an_existing_equivalent_exclude_line_is_respected(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    (target / ".git" / "info" / "exclude").write_bytes(b"/.sdlc\n")
    assert install(target).returncode == 0
    assert exclude_lines(target) == ["/.sdlc"]


# ------------------------------------------- fail closed: no Python, no files

def fake_python_dir(base: Path) -> Path:
    fake = base / "fakebin"
    fake.mkdir()
    for name in ("python", "python3", "py"):
        script = fake / name
        script.write_bytes(b"#!/bin/sh\nexit 1\n")
        os.chmod(script, 0o755)
    return fake


def test_no_working_python_blocks_the_push(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = make_target(tmp_path)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    commit(target, {"ok.txt": "clean\n"})

    with monkeypatch.context() as m:
        m.setenv("PATH", str(fake_python_dir(tmp_path)) + os.pathsep + os.environ["PATH"])
        res = run(target, "git", "push", "origin", "main")
    assert res.returncode != 0
    assert "no working Python" in res.stderr
    assert not remote_has_main(remote)
    assert run(target, "git", "push", "-q", "origin", "main").returncode == 0  # legal case


def test_missing_guard_blocks_the_push(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    commit(target, {"ok.txt": "clean\n"})
    copy = target / ".sdlc" / "guard" / "pre_push_guard.py"
    copy.unlink()
    res = run(target, "git", "push", "origin", "main")
    assert res.returncode != 0 and "not found" in res.stderr
    assert not remote_has_main(remote)
    assert install(target, "--refresh").returncode == 0
    assert run(target, "git", "push", "-q", "origin", "main").returncode == 0


def test_missing_pattern_file_blocks_the_push(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    commit(target, {"ok.txt": "clean\n"})
    patterns = target / ".sdlc" / "guard-patterns.txt"
    saved = patterns.read_bytes()
    patterns.unlink()
    res = run(target, "git", "push", "origin", "main")
    assert res.returncode != 0 and "not found" in res.stderr
    assert not remote_has_main(remote)
    patterns.write_bytes(saved)
    assert run(target, "git", "push", "-q", "origin", "main").returncode == 0


def test_a_linked_worktree_fails_closed_because_the_guard_is_per_worktree(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    remote = add_remote(tmp_path, target)
    assert install(target).returncode == 0
    linked = tmp_path / "linked"
    git(target, "worktree", "add", "-q", "-b", "side", str(linked))
    git(linked, "config", "user.name", "Test")
    commit(linked, {"ok.txt": "clean\n"})
    res = run(linked, "git", "push", "origin", "side")
    assert res.returncode != 0 and "not found" in res.stderr
    assert run(remote, "git", "rev-parse", "--verify", "-q", "refs/heads/side").returncode != 0


# ------------------------------------------------- guard: forbid-path lines

def guard_repo(base: Path, patterns: str, private: str | None = None) -> Path:
    repo = make_target(base, "guarded")
    (repo / ".sdlc").mkdir()
    (repo / ".sdlc" / "guard-patterns.txt").write_text(patterns, encoding="utf-8", newline="\n")
    if private is not None:
        (repo / ".sdlc" / "local").mkdir()
        (repo / ".sdlc" / "local" / "private-patterns.txt").write_text(private, encoding="utf-8")
    return repo


def check(repo: Path, files: dict[str, str]) -> subprocess.CompletedProcess:
    """Commit the files, then run the guard over that one commit."""
    before = git(repo, "rev-parse", "HEAD")
    after = commit(repo, files)
    return run(repo, sys.executable, str(GUARD), "origin", "none", stdin=stdin_line("main", after, before))


def test_forbid_path_lines_replace_the_built_in_list(tmp_path: Path) -> None:
    repo = guard_repo(tmp_path, "forbid-path secret.txt\nforbid-path conf/*.key\n")
    # the built-in list no longer applies
    assert check(repo, {".env": "x\n"}).returncode == 0
    assert check(repo, {"PRIVATE.md": "x\n"}).returncode == 0
    # no slash: the file name in any folder
    res = check(repo, {"deep/er/secret.txt": "x\n"})
    assert res.returncode != 0 and "forbidden-path:secret.txt" in res.stderr
    # a slash: the full path only
    res = check(repo, {"conf/a.key": "x\n"})
    assert res.returncode != 0 and "forbidden-path:conf/*.key" in res.stderr
    assert check(repo, {"other/conf/a.key": "x\n"}).returncode == 0


def test_files_mode_uses_the_forbid_path_lines_of_the_pattern_file(tmp_path: Path) -> None:
    repo = guard_repo(tmp_path, "forbid-path secret.txt\n")
    (repo / "secret.txt").write_text("x\n", encoding="utf-8")
    (repo / ".env").write_text("x\n", encoding="utf-8")  # forbidden only by the built-in list
    res = run(repo, sys.executable, str(GUARD), "--files", "secret.txt")
    assert res.returncode != 0 and "forbidden-path:secret.txt" in res.stderr
    res = run(repo, sys.executable, str(GUARD), "--files", ".env")
    assert res.returncode == 0, res.stderr


def test_a_pattern_file_without_forbid_path_keeps_the_built_in_list(tmp_path: Path) -> None:
    repo = guard_repo(tmp_path, "aws-key  \\bAKIA[0-9A-Z]{16}\\b\n")
    res = check(repo, {"sub/.env": "x\n"})
    assert res.returncode != 0 and "forbidden-path" in res.stderr
    assert check(repo, {".env.example": "x\n"}).returncode == 0


def test_forbid_path_in_the_private_file_fails_closed_without_an_echo(tmp_path: Path) -> None:
    repo = guard_repo(tmp_path, "aws-key  \\bAKIA[0-9A-Z]{16}\\b\n", private="forbid-path hiddenword.txt\n")
    res = check(repo, {"a.txt": "ok\n"})
    assert res.returncode != 0
    assert "forbid-path" in res.stderr and "hiddenword" not in res.stderr + res.stdout


def test_forbid_path_without_a_glob_is_a_broken_pattern(tmp_path: Path) -> None:
    repo = guard_repo(tmp_path, "forbid-path\n")
    assert check(repo, {"a.txt": "ok\n"}).returncode != 0


def test_the_template_file_is_exempt_from_content_scanning(tmp_path: Path) -> None:
    repo = guard_repo(tmp_path, "aws-key  \\bAKIA[0-9A-Z]{16}\\b\n")
    body = f"example  {AWS_KEY}\n"
    assert check(repo, {"templates/guard-patterns.txt": body}).returncode == 0
    res = check(repo, {"docs/guard-patterns.txt": body})
    assert res.returncode != 0 and "aws-key" in res.stderr


# ------------------------------------------------------------------ template

def parse_patterns(path: Path) -> list[tuple[str, str]]:
    pairs = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            name, rest = line.split(None, 1)
            pairs.append((name, rest.strip()))
    return pairs


def load_guard_module():
    spec = importlib.util.spec_from_file_location("kit_pre_push_guard", GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_template_equals_the_kit_file_without_the_language_line() -> None:
    kit = [pair for pair in parse_patterns(KIT_PATTERNS) if pair[0] != "forbid-path"]
    template = [pair for pair in parse_patterns(TEMPLATE) if pair[0] != "forbid-path"]
    assert [pair for pair in kit if pair[0] != "non-english-char"] == template
    assert any(name == "non-english-char" for name, _ in kit)
    assert all(name != "non-english-char" for name, _ in template)
    assert "What is this file?" in TEMPLATE.read_text(encoding="utf-8").splitlines()[0]


def test_template_forbid_lines_are_the_built_in_list_without_the_kit_only_paths() -> None:
    built_in = {glob for glob, _ in load_guard_module().FORBIDDEN_PATHS}
    template = {rest for name, rest in parse_patterns(TEMPLATE) if name == "forbid-path"}
    assert template == built_in - {"PLAN.md", "evidence/raw/*"}


def test_template_is_ascii_and_lf_only() -> None:
    data = TEMPLATE.read_bytes()
    data.decode("ascii")
    assert b"\r" not in data
