#!/usr/bin/env python3
"""Pre-push guard: reject pushes that carry secrets or private content.

Hook mode (git calls it with the ref list on stdin):
    pre_push_guard.py <remote-name> <remote-url>

Manual mode (scan whole files, e.g. the working tree):
    pre_push_guard.py --files PATH [PATH ...]

Only what is new in the push is scanned: the added lines and the messages of
the commits that the remote does not have yet. Standard library only.

Pattern files: `<name> <regex>` lines. The public file may also hold
`forbid-path <glob>` lines. A glob with no `/` matches the file name in any
folder, otherwise the full path. When the public file has any such line, those
lines replace the built-in list; when it has none, the built-in list stays.
"""
from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ZERO_SHA = "0" * 40
PUBLIC_PATTERNS = ".sdlc/guard-patterns.txt"
PRIVATE_PATTERNS = ".sdlc/local/private-patterns.txt"
# Files that may legitimately contain the patterns themselves.
CONTENT_EXEMPT = {PUBLIC_PATTERNS, "templates/guard-patterns.txt"}
FORBID_KEYWORD = "forbid-path"

# (glob, any_directory). Globs match the full path, or the file name when any_directory.
FORBIDDEN_PATHS: list[tuple[str, bool]] = [
    (".env", True),
    (".env.*", True),
    ("CLAUDE.local.md", True),
    ("PLAN.md", False),
    ("PRIVATE.md", False),
    ("evidence/raw/*", False),
    (".sdlc/local/*", False),
]
ENV_TEMPLATE_SUFFIXES = (".example", ".sample", ".template")

Pattern = tuple[str, "re.Pattern[str]", bool]  # name, regex, is_private
PathRule = tuple[str, bool]  # glob, any_directory
Hit = tuple[str, str, str, str]  # short sha or label, file, location, pattern name


class PatternError(Exception):
    pass


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "core.quotepath=off", *args],
        cwd=root,
        capture_output=True,
    )


def text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if out.returncode != 0:
        raise SystemExit("pre-push guard: not inside a git repository")
    return Path(out.stdout.strip())


def load_pattern_file(
    path: Path, private: bool, forbids: list[PathRule] | None = None
) -> list[Pattern]:
    """Parse a pattern file. `forbids` collects forbid-path rules; None means they are not allowed."""
    patterns: list[Pattern] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise PatternError(f"{path.name}:{number}: expected '<name> <regex>'")
        name, regex = parts
        if name == FORBID_KEYWORD:
            if forbids is None:
                # Do not echo the glob: in a private file it may be a private name.
                raise PatternError(f"{path.name}:{number}: {FORBID_KEYWORD} is not allowed in this file")
            glob = regex.strip()
            forbids.append((glob, "/" not in glob))
            continue
        try:
            patterns.append((name, re.compile(regex), private))
        except re.error:
            # Do not echo the regex: in a private file it may be a private word.
            raise PatternError(f"{path.name}:{number}: pattern '{name}' is not a valid regex")
    return patterns


def load_rules(root: Path) -> tuple[list[Pattern], list[PathRule]]:
    """Return the content patterns and the forbidden-path rules for a repository."""
    public = root / PUBLIC_PATTERNS
    if not public.is_file():
        raise PatternError(f"{PUBLIC_PATTERNS} not found")
    forbids: list[PathRule] = []
    patterns = load_pattern_file(public, private=False, forbids=forbids)
    private = root / PRIVATE_PATTERNS
    if private.is_file():
        patterns += load_pattern_file(private, private=True)
    return patterns, forbids or FORBIDDEN_PATHS


def load_patterns(root: Path) -> list[Pattern]:
    return load_rules(root)[0]


def forbidden_path(path: str, rules: list[PathRule] = FORBIDDEN_PATHS) -> str | None:
    norm = path.replace("\\", "/")
    name = PurePosixPath(norm).name
    for glob, any_dir in rules:
        if any_dir:
            if fnmatch.fnmatchcase(name, glob):
                if name.startswith(".env") and name.endswith(ENV_TEMPLATE_SUFFIXES):
                    continue
                return f"forbidden-path:{glob}"
        elif fnmatch.fnmatchcase(norm, glob):
            return f"forbidden-path:{glob}"
    return None


def scan_line(line: str, patterns: list[Pattern]) -> list[str]:
    return [name for name, rx, _ in patterns if rx.search(line)]


def scan_message(message: str, patterns: list[Pattern]) -> list[str]:
    names: list[str] = []
    for line in message.splitlines():
        for name in scan_line(line, patterns):
            if name not in names:
                names.append(name)
    return names


def parse_added_lines(diff: str):
    """Yield (file, line number in the new file, text) for each added line."""
    current: str | None = None
    new_line = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            target = raw[4:].split("\t")[0]
            current = None if target == "/dev/null" else target[2:] if target.startswith("b/") else target
            continue
        if raw.startswith("--- ") or raw.startswith("diff --git"):
            continue
        if raw.startswith("@@"):
            m = re.match(r"@@ -\S+ \+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
            continue
        if raw.startswith("+") and current is not None:
            yield current, new_line, raw[1:]
            new_line += 1


def commits_to_scan(root: Path, local: str, remote: str) -> list[str]:
    if remote != ZERO_SHA:
        res = git(root, "rev-list", "--reverse", f"{remote}..{local}")
        if res.returncode == 0:
            return text(res.stdout).split()
    # New branch, or the remote sha is unknown locally: everything the remotes lack.
    res = git(root, "rev-list", "--reverse", local, "--not", "--remotes")
    if res.returncode != 0:
        raise SystemExit(f"pre-push guard: cannot list commits for {local}")
    return text(res.stdout).split()


def scan_commit(
    root: Path, sha: str, patterns: list[Pattern], rules: list[PathRule] = FORBIDDEN_PATHS
) -> list[Hit]:
    short = sha[:7]
    hits: list[Hit] = []
    msg = git(root, "log", "-1", "--format=%B", sha)
    for name in scan_message(text(msg.stdout), patterns):
        hits.append((short, "commit message", "", name))

    paths = git(
        root, "diff-tree", "--root", "-r", "-m", "--no-commit-id", "--no-renames",
        "--name-only", "--diff-filter=ACMR", "-z", sha,
    )
    for path in sorted(set(text(paths.stdout).split("\0"))):
        if path and (reason := forbidden_path(path, rules)):
            hits.append((short, path, "", reason))

    diff = git(
        root, "diff-tree", "-p", "--root", "-m", "--no-commit-id", "--no-renames",
        "--unified=0", "--no-color", "--no-ext-diff", sha,
    )
    seen: set[Hit] = set()
    for path, number, line in parse_added_lines(text(diff.stdout)):
        if path in CONTENT_EXEMPT:
            continue
        for name in scan_line(line, patterns):
            hit = (short, path, f":{number}", name)
            if hit not in seen:
                seen.add(hit)
                hits.append(hit)
    return hits


def scan_files(
    root: Path, files: list[str], patterns: list[Pattern], rules: list[PathRule] = FORBIDDEN_PATHS
) -> list[Hit]:
    hits: list[Hit] = []
    for item in files:
        path = Path(item)
        try:
            rel = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            rel = path.as_posix()
        if reason := forbidden_path(rel, rules):
            hits.append(("worktree", rel, "", reason))
        if rel in CONTENT_EXEMPT or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        for number, line in enumerate(text(data).splitlines(), 1):
            for name in scan_line(line, patterns):
                hits.append(("worktree", rel, f":{number}", name))
    return hits


def report(hits: list[Hit], patterns: list[Pattern]) -> None:
    private = {name for name, _, is_private in patterns if is_private}
    for short, path, loc, name in hits:
        tag = " (private pattern)" if name in private else ""
        place = path if path == "commit message" else f"{path}{loc}"
        print(f"  {short}  {place}  {name}{tag}", file=sys.stderr)
    print(
        "pre-push guard: push rejected. Remove the content (amend, or rebase to rewrite "
        "the commits) and push again.",
        file=sys.stderr,
    )


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="backslashreplace")
    root = repo_root()
    try:
        patterns, rules = load_rules(root)
    except PatternError as err:
        print(f"pre-push guard: {err}", file=sys.stderr)
        return 1

    hits: list[Hit] = []
    if argv and argv[0] == "--files":
        hits = scan_files(root, argv[1:], patterns, rules)
    else:
        for raw in sys.stdin.read().splitlines():
            fields = raw.split()
            if len(fields) != 4:
                continue
            _, local, _, remote = fields
            if local == ZERO_SHA:
                continue
            for sha in commits_to_scan(root, local, remote):
                hits += scan_commit(root, sha, patterns, rules)

    if hits:
        report(hits, patterns)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
