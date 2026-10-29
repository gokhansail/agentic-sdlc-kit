#!/usr/bin/env python3
"""Install the repository's git hooks by pointing core.hooksPath at hooks/git.

Safe to run twice. Refuses to replace a hooksPath that points somewhere else
unless --force is given.

    python tools/install_git_hooks.py [--repo PATH] [--force]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = "hooks/git"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository to install into (default: current)")
    parser.add_argument("--force", action="store_true", help="replace a different core.hooksPath")
    args = parser.parse_args(argv)

    top = git(Path(args.repo), "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        print("install_git_hooks: not a git repository", file=sys.stderr)
        return 1
    root = Path(top.stdout.strip())

    hooks = root / HOOKS_DIR
    hook_files = [p for p in hooks.iterdir() if p.is_file()] if hooks.is_dir() else []
    if not hook_files:
        print(f"install_git_hooks: no hooks found in {HOOKS_DIR}", file=sys.stderr)
        return 1

    for hook in hook_files:
        os.chmod(hook, hook.stat().st_mode | 0o111)

    current = git(root, "config", "--local", "--get", "core.hooksPath").stdout.strip()
    if current == HOOKS_DIR:
        print(f"already installed: core.hooksPath = {HOOKS_DIR} (no change)")
        return 0
    if current and not args.force:
        print(
            f"install_git_hooks: core.hooksPath is already set to '{current}'; "
            "use --force to replace it",
            file=sys.stderr,
        )
        return 1

    res = git(root, "config", "--local", "core.hooksPath", HOOKS_DIR)
    if res.returncode != 0:
        print(f"install_git_hooks: git config failed: {res.stderr.strip()}", file=sys.stderr)
        return 1
    names = ", ".join(sorted(p.name for p in hook_files))
    print(f"installed: core.hooksPath = {HOOKS_DIR} (hooks: {names})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
