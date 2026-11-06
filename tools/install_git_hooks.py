#!/usr/bin/env python3
"""Install the pre-push guard, in this repository or in another one.

Kit mode points core.hooksPath at hooks/git. Safe to run twice. Refuses to
replace a hooksPath that points somewhere else unless --force is given.

    python tools/install_git_hooks.py [--repo PATH] [--force]

Target mode puts the guard into another repository and leaves core.hooksPath
alone: the guard is copied to .sdlc/guard/, and a wrapper in the repository's
own hooks folder runs the saved old pre-push hook first, then the guard.

    python tools/install_git_hooks.py --target PATH [--refresh | --uninstall]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = "hooks/git"

KIT_ROOT = Path(__file__).resolve().parent.parent
GUARD_SOURCE = KIT_ROOT / "tools" / "pre_push_guard.py"
TEMPLATE_SOURCE = KIT_ROOT / "templates" / "guard-patterns.txt"

MARKER = "# sdlc-guard-wrapper"
SAVED_HOOK = "pre-push.sdlc-old"
SDLC_DIR = ".sdlc"
EXCLUDE_LINE = ".sdlc/"
EXCLUDE_ALIASES = {".sdlc/", "/.sdlc/", ".sdlc", "/.sdlc"}

# The hook input is the ref list on stdin, which can be read only once. It goes to a
# temp file so the saved hook and the guard each get the same bytes. Fails closed.
WRAPPER = """#!/bin/sh
# sdlc-guard-wrapper
# Written by tools/install_git_hooks.py --target; remove it with --uninstall.
# Runs the saved old pre-push hook first, then the pre-push guard. Fails closed.
fail() {
    echo "pre-push guard: $1" >&2
    exit 1
}
root=$(git rev-parse --show-toplevel) || fail "not inside a working tree"
old=$(git rev-parse --git-path hooks/pre-push.sdlc-old) || fail "cannot locate the hooks folder"
guard="$root/.sdlc/guard/pre_push_guard.py"
patterns="$root/.sdlc/guard-patterns.txt"
input=$(mktemp) || fail "cannot create a temp file"
trap 'rm -f "$input"' EXIT
cat >"$input" || fail "cannot read the push input"
if [ -x "$old" ]; then
    "$old" "$@" <"$input"
    code=$?
    [ "$code" -eq 0 ] || exit "$code"
fi
[ -f "$guard" ] || fail "$guard not found (each working tree needs its own install); push stopped"
[ -f "$patterns" ] || fail "$patterns not found; push stopped"
probe() {
    "$@" -I -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' </dev/null >/dev/null 2>&1
}
if probe python; then
    set -- python
elif probe python3; then
    set -- python3
elif probe py -3; then
    set -- py -3
else
    fail "no working Python 3.10 or newer found (tried python, python3, py -3); push stopped"
fi
PYTHONUTF8=1 "$@" -I -X utf8 "$guard" <"$input"
exit $?
"""
WRAPPER_BYTES = WRAPPER.encode("ascii")


class Refused(Exception):
    """A precondition failed. Raised before anything is written."""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    # git prints paths as UTF-8 on every platform; the locale encoding would garble them.
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


# ---------------------------------------------------------------- kit mode

def kit_mode(repo: str, force: bool) -> int:
    top = git(Path(repo), "rev-parse", "--show-toplevel")
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
    if current and not force:
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


# ------------------------------------------------------------- target mode

class Target:
    """Paths of a target repository, all taken from git and checked to lie inside it."""

    def __init__(self, arg: str) -> None:
        start = Path(arg)
        if not start.is_dir():
            raise Refused("the target is not a folder")
        if git(start, "rev-parse", "--git-dir").returncode != 0:
            raise Refused("the target is not a git repository")
        if git(start, "rev-parse", "--is-bare-repository").stdout.strip() == "true":
            raise Refused("the target is a bare repository; it has no working tree to guard")
        top = git(start, "rev-parse", "--show-toplevel")
        if top.returncode != 0 or not top.stdout.strip():
            raise Refused("the target has no working tree")
        self.root = Path(top.stdout.strip())
        if not os.path.samefile(self.root, start):
            raise Refused("the target is not the top folder of its working tree; name that folder")

        hooks_path = git(self.root, "config", "--get", "core.hooksPath")
        if hooks_path.returncode == 0:
            raise Refused(
                f"core.hooksPath is set to '{hooks_path.stdout.strip()}'; target mode does not "
                "work with it, unset it or install by hand"
            )
        self.hooks = self._git_path("hooks")
        self.exclude = self._git_path("info/exclude")
        self.pre_push = self.hooks / "pre-push"
        self.saved = self.hooks / SAVED_HOOK
        self.sdlc = self.root / SDLC_DIR
        self.guard_dir = self.sdlc / "guard"
        self.guard_copy = self.guard_dir / "pre_push_guard.py"
        self.patterns = self.sdlc / "guard-patterns.txt"
        self.local_dir = self.sdlc / "local"
        self.private = self.local_dir / "private-patterns.txt"

    def _git_path(self, name: str) -> Path:
        res = git(self.root, "rev-parse", "--git-path", name)
        if res.returncode != 0 or not res.stdout.strip():
            raise Refused("git could not name its own folders")
        return self.root / res.stdout.strip()  # an absolute answer replaces the root

    def check_writable(self) -> None:
        """Refuse if something we would create is in the way. Writes nothing."""
        inside = self.root.resolve()
        for folder in (self.sdlc, self.guard_dir, self.local_dir):
            if folder.exists() or folder.is_symlink():
                if not folder.is_dir():
                    raise Refused(f"{folder.relative_to(self.root).as_posix()} exists and is not a folder")
                if inside not in folder.resolve().parents:
                    raise Refused(f"{folder.relative_to(self.root).as_posix()} leads outside the repository")
        for path in (self.patterns, self.private, self.guard_copy):
            if path.exists() and not path.is_file():
                raise Refused(f"{path.relative_to(self.root).as_posix()} exists and is not a file")
        for path in (self.pre_push, self.saved):
            if path.exists() and not path.is_file():
                raise Refused(f"{path.name} exists and is not a file")
        if self.hooks.exists() and not self.hooks.is_dir():
            raise Refused("the hooks path exists and is not a folder")


def is_wrapper(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_bytes().decode("latin-1")
    return any(line.strip() == MARKER for line in text.splitlines())


def write_wrapper(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(WRAPPER_BYTES)  # bytes: LF endings on every platform
    os.chmod(path, 0o755)


def copy_guard(target: Target) -> None:
    target.guard_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GUARD_SOURCE, target.guard_copy)


def ensure_pattern_files(target: Target) -> list[str]:
    """Create the pattern files that are absent. Existing ones are never touched."""
    made: list[str] = []
    if not target.patterns.exists():
        target.sdlc.mkdir(exist_ok=True)
        shutil.copyfile(TEMPLATE_SOURCE, target.patterns)
        made.append(".sdlc/guard-patterns.txt")
    if not target.private.exists():
        target.local_dir.mkdir(parents=True, exist_ok=True)
        target.private.write_bytes(b"")
        made.append(".sdlc/local/private-patterns.txt")
    return made


def ensure_exclude(target: Target) -> bool:
    target.exclude.parent.mkdir(parents=True, exist_ok=True)
    data = target.exclude.read_bytes() if target.exclude.is_file() else b""
    lines = [line.strip() for line in data.decode("utf-8", errors="replace").splitlines()]
    if any(line in EXCLUDE_ALIASES for line in lines):
        return False
    if data and not data.endswith(b"\n"):
        data += b"\n"
    target.exclude.write_bytes(data + EXCLUDE_LINE.encode("ascii") + b"\n")
    return True


def check_kit_files() -> None:
    for source in (GUARD_SOURCE, TEMPLATE_SOURCE):
        if not source.is_file():
            raise Refused(f"kit file {source.relative_to(KIT_ROOT).as_posix()} not found")


def target_install(target: Target, refresh: bool) -> int:
    check_kit_files()
    target.check_writable()
    wrapped = is_wrapper(target.pre_push)

    if wrapped:
        copy_ok = target.guard_copy.is_file() and target.guard_copy.read_bytes() == GUARD_SOURCE.read_bytes()
        wrapper_ok = target.pre_push.read_bytes() == WRAPPER_BYTES
        if copy_ok and wrapper_ok:
            print("no change: the guard copy and the wrapper are current")
            return 0
        stale = [name for name, ok in (("guard copy", copy_ok), ("wrapper", wrapper_ok)) if not ok]
        if not refresh:
            verb = "differs" if len(stale) == 1 else "differ"
            print(
                f"install_git_hooks: stale: {' and '.join(stale)} {verb} from the kit; "
                "run again with --refresh (nothing changed)",
                file=sys.stderr,
            )
            return 1
        copy_guard(target)
        write_wrapper(target.pre_push)
        made = ensure_pattern_files(target)
        ensure_exclude(target)
        print(f"refreshed: {' and '.join(stale)} replaced; the pattern files were not touched")
        if made:
            print("created, because they were missing: " + ", ".join(made))
        return 0

    if target.pre_push.exists() and target.saved.exists():
        raise Refused(
            f"{SAVED_HOOK} already exists beside a pre-push hook that is not the wrapper; "
            "resolve this by hand (nothing changed)"
        )

    copy_guard(target)
    made = ensure_pattern_files(target)
    added = ensure_exclude(target)
    target.hooks.mkdir(parents=True, exist_ok=True)
    saved_note = ""
    if target.pre_push.exists():
        os.replace(target.pre_push, target.saved)  # a rename keeps bytes and mode
        saved_note = f"; the old hook is kept as {SAVED_HOOK} and runs first"
    write_wrapper(target.pre_push)
    print(f"installed: pre-push guard in the target{saved_note}")
    print("created: .sdlc/guard/pre_push_guard.py" + "".join(", " + name for name in made))
    if added:
        print(f"added '{EXCLUDE_LINE}' to the repository's info/exclude")
    return 0


def target_uninstall(target: Target) -> int:
    target.check_writable()
    if not is_wrapper(target.pre_push):
        # A pre-push without the marker is refused when it sits beside traces of an
        # install (a saved hook or a guard copy): someone replaced the wrapper, and
        # removing anything would lose the saved hook. With no trace it is simply
        # not installed, which also makes a second --uninstall a no-op.
        if target.pre_push.exists() and (target.saved.exists() or target.guard_copy.exists()):
            raise Refused("pre-push is not the sdlc wrapper but install traces remain; nothing changed")
        print("not installed: no change")
        if target.saved.exists():
            print(f"note: {SAVED_HOOK} exists without a wrapper and was left in place")
        return 0

    if target.saved.exists():
        os.replace(target.saved, target.pre_push)  # one step, bytes and mode kept
        restored = "the old hook was put back as pre-push"
    else:
        target.pre_push.unlink()
        restored = "there was no old hook"
    if target.guard_dir.is_dir():
        shutil.rmtree(target.guard_dir)
    print(f"uninstalled: wrapper and .sdlc/guard/ removed; {restored}")
    print("left in place; remove by hand to finish the rollback:")
    print("  .sdlc/guard-patterns.txt")
    print("  .sdlc/local/")
    print(f"  the '{EXCLUDE_LINE}' line in the repository's info/exclude")
    return 0


def target_mode(path: str, refresh: bool, uninstall: bool) -> int:
    try:
        target = Target(path)
        if uninstall:
            return target_uninstall(target)
        return target_install(target, refresh)
    except Refused as err:
        print(f"install_git_hooks: {err}", file=sys.stderr)
        return 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=None, help="kit mode: repository to install into (default: current)")
    parser.add_argument("--force", action="store_true", help="kit mode: replace a different core.hooksPath")
    parser.add_argument("--target", default=None, help="target mode: another repository to guard")
    parser.add_argument("--refresh", action="store_true", help="target mode: replace a stale guard copy and wrapper")
    parser.add_argument("--uninstall", action="store_true", help="target mode: remove the guard, restore the old hook")
    args = parser.parse_args(argv)

    problem = None
    if args.target is None and (args.refresh or args.uninstall):
        problem = "--refresh and --uninstall need --target"
    elif args.target is not None and args.force:
        problem = "--force is a kit-mode flag and is refused with --target"
    elif args.target is not None and args.repo is not None:
        problem = "--repo is a kit-mode flag and is refused with --target"
    elif args.refresh and args.uninstall:
        problem = "--refresh and --uninstall cannot be used together"
    if problem:
        print(f"install_git_hooks: {problem}", file=sys.stderr)
        return 1

    if args.target is not None:
        return target_mode(args.target, args.refresh, args.uninstall)
    return kit_mode(args.repo or ".", args.force)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
