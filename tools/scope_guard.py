#!/usr/bin/env python3
"""Scope guard: allow or deny one Write, Edit or NotebookEdit call by the active contract.

Called by `hooks/scope/launcher.sh` as a PreToolUse hook: the hook input is JSON
on stdin, exit 0 allows, exit 2 denies and the reason goes to stderr. It catches
a developer leaving its contract by mistake. It is not a security boundary: a
write through Bash is not seen.

States, in the order they are decided:
    not opted in   no .sdlc/project.md                -> allow, silent
    no contract    no .sdlc/active-contract.md        -> allow only the always-allowed list
    active         the contract parses                -> allow Files in and the always-allowed
                                                         list; Files out wins over both
    broken         the contract does not parse        -> deny everything

Beyond the table: a path outside the project root is denied; a sub-agent never
writes under .sdlc/; the main session always may. The developer rules file (the
backticked path on the `Developer rules:` line of .sdlc/project.md) is never covered by
the always-allowed list: a sub-agent may write it only when Files in names its exact
path as one token (checked before brace expansion, no `*`, `?` or `{`; a glob does not count).
One exception to the root rule: the main session may write in the CLI's memory folder, the
`memory` folder next to the hook input's `transcript_path` file, when that file sits in a
folder whose parent is named `projects`. A sub-agent, or any other layout, stays denied.

Grammar (only backticked tokens count; `{a,b}` expands; a trailing `/` is a
folder; `*` stays inside one folder, `**` crosses folders; patterns are anchored
at the project root):
    .sdlc/project.md          backticked globs in a "## Always allowed" section
    .sdlc/active-contract.md  one heading holding the task ID, one "Files in:" line
                              and one "Files out:" line (see templates/task-contract.md)

Two script modes serve the plugin commands. They run before stdin is read, write
no event line and reuse the parser and the matcher above:
    --check-contract   exit 0 when .sdlc/active-contract.md parses, else 1 with the reason
    --check-worktree   compare `git status --porcelain -z` with the contract; print the paths
                       outside it; exit 0 when none, else 1 (no contract is exit 1 too)

The parser and the decision are plain functions so that the phase 4 server can
import them. Standard library only; Python 3.10 or newer.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import posixpath
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence, TextIO

PROJECT_FILE = ".sdlc/project.md"
CONTRACT_FILE = ".sdlc/active-contract.md"
EVENT_FILE = ".sdlc/metrics.jsonl"
SDLC_PREFIX = ".sdlc/"
PATH_FIELDS = ("file_path", "notebook_path")
BRACE_LIMIT = 1000

NO_CONTRACT = "no-contract"
ACTIVE = "active"
BROKEN = "broken"


class ConfigError(Exception):
    """A record the guard reads cannot be used. The message names the line."""


@dataclass(frozen=True)
class Contract:
    task_id: str
    files_in: tuple[str, ...]
    files_out: tuple[str, ...]
    files_in_raw: tuple[str, ...] = ()  # Files in tokens before brace expansion


@dataclass(frozen=True)
class Decision:
    allow: bool
    state: str
    reason: str
    next_step: str = ""
    task_id: str | None = None
    rel: str | None = None


# --- parsing -------------------------------------------------------------------

_TICKED = re.compile(r"`([^`\r\n]+)`")
_TASK_ID = re.compile(r"(?<![\w-])[A-Z][A-Z0-9]{0,9}-\d+[a-z]?(?![\w-])")
_FIELD = re.compile(r"^\s*(?:[-*+]\s+)?(Files in|Files out)\s*:(.*)$", re.IGNORECASE)


_RULES_FIELD = re.compile(r"^\s*(?:[-*+]\s+)?Developer rules\s*:(.*)$", re.IGNORECASE)


def heading_text(line: str) -> str | None:
    """The text of a Markdown heading line, or None when the line is not a heading.

    A heading has at most 3 spaces, 1 to 6 `#`, then whitespace; closing `#` characters and the
    blanks around them are not part of the text. Same result as the pattern
    `^ {0,3}#{1,6}\\s+(.*?)\\s*#*\\s*$` that this replaced, which backtracks without a bound on a long
    run of blanks (S-7). Here every step is a single pass over the line.
    """
    body = line.lstrip(" ")
    if len(line) - len(body) > 3:
        return None
    rest = body.lstrip("#")
    hashes = len(body) - len(rest)
    if not 1 <= hashes <= 6 or not rest[:1].isspace():
        return None
    return rest.strip().rstrip("#").rstrip()


def backticked(line: str) -> list[str]:
    """The non-empty backticked tokens of one line."""
    return [t.strip() for t in _TICKED.findall(line) if t.strip()]


def expand_braces(token: str, limit: int = BRACE_LIMIT) -> list[str]:
    """Expand `{a,b}` groups, nested ones included. An unbalanced brace stays literal."""
    start = token.find("{")
    if start < 0:
        return [token]
    depth = 0
    end = -1
    parts: list[str] = []
    piece_from = start + 1
    for i in range(start, len(token)):
        ch = token[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                parts.append(token[piece_from:i])
                end = i
                break
        elif ch == "," and depth == 1:
            parts.append(token[piece_from:i])
            piece_from = i + 1
    if end < 0:
        return [token]
    prefix, suffix = token[:start], token[end + 1:]
    out: list[str] = []
    for part in parts:
        out.extend(expand_braces(prefix + part + suffix, limit))
        if len(out) > limit:
            raise ConfigError(f"brace expansion of `{token[:40]}` gives more than {limit} patterns")
    return out


def normalize_pattern(token: str) -> str:
    pattern = token.replace("\\", "/")
    while pattern.startswith("./"):
        pattern = pattern[2:]
    return pattern


def patterns_from_line(line: str) -> list[str]:
    out: list[str] = []
    for token in backticked(line):
        out.extend(normalize_pattern(p) for p in expand_braces(token))
    return out


def parse_always_allowed(text: str) -> list[str]:
    """Backticked globs under a heading named "Always allowed". No section: empty list."""
    out: list[str] = []
    inside = False
    for line in text.splitlines():
        title = heading_text(line)
        if title is not None:
            inside = title.strip().lower() == "always allowed"
            continue
        if inside:
            out.extend(patterns_from_line(line))
    return out


def parse_developer_rules(text: str) -> str | None:
    """The first backticked path on the `Developer rules:` line of the project file, or None."""
    for line in text.splitlines():
        field = _RULES_FIELD.match(line)
        if field:
            tokens = backticked(field.group(1))
            return normalize_pattern(tokens[0]) if tokens else None
    return None


def parse_contract(text: str) -> Contract:
    """Parse one contract. Raises ConfigError, with the line number, when it is broken."""
    headings: list[tuple[int, str]] = []
    fields: dict[str, list[tuple[int, str]]] = {"files in": [], "files out": []}
    for number, line in enumerate(text.splitlines(), start=1):
        title = heading_text(line)
        if title is not None:
            headings.append((number, title))
            continue
        field = _FIELD.match(line)
        if field:
            fields[field.group(1).lower()].append((number, field.group(2)))
    if not headings:
        raise ConfigError("no heading with a task ID")
    if len(headings) > 1:
        raise ConfigError(f"line {headings[1][0]}: second heading; one contract has one heading")
    number, title = headings[0]
    task = _TASK_ID.search(title)
    if not task:
        raise ConfigError(f"line {number}: the heading has no task ID")
    found: dict[str, tuple[str, ...]] = {}
    for name in ("files in", "files out"):
        rows = fields[name]
        label = "Files in" if name == "files in" else "Files out"
        if not rows:
            raise ConfigError(f"no `{label}` line")
        if len(rows) > 1:
            raise ConfigError(f"line {rows[1][0]}: `{label}` is repeated (first at line {rows[0][0]})")
        found[name] = tuple(patterns_from_line(rows[0][1]))
        if name == "files in" and not found[name]:
            raise ConfigError(f"line {rows[0][0]}: `Files in` has no backticked path")
    raw_in = tuple(normalize_pattern(t) for t in backticked(fields["files in"][0][1]))
    return Contract(task.group(0), found["files in"], found["files out"], raw_in)


# --- paths ---------------------------------------------------------------------

def glob_to_regex(pattern: str) -> str:
    if pattern.endswith("/"):
        pattern += "**"
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return "".join(out)


_LIT, _ANY_DIR, _ANY_LINE, _ANY_NAME, _ONE_NAME = range(5)


@lru_cache(maxsize=1024)
def _glob_tokens(pattern: str) -> tuple[tuple[int, str], ...]:
    """The pattern as tokens, cut the same way `glob_to_regex` cuts it.

    _ANY_DIR is `**/` (`(?:.*/)?`), _ANY_LINE is `**` (`.*`, which stops at a newline),
    _ANY_NAME is `*` (`[^/]*`), _ONE_NAME is `?` (`[^/]`), _LIT is one literal character.
    """
    if pattern.endswith("/"):
        pattern += "**"
    out: list[tuple[int, str]] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append((_ANY_DIR, ""))
            i += 3
        elif pattern.startswith("**", i):
            out.append((_ANY_LINE, ""))
            i += 2
        elif pattern[i] == "*":
            out.append((_ANY_NAME, ""))
            i += 1
        elif pattern[i] == "?":
            out.append((_ONE_NAME, ""))
            i += 1
        else:
            out.append((_LIT, pattern[i]))
            i += 1
    return tuple(out)


@lru_cache(maxsize=65536)
def _same_char(want: str, have: str, casefold: bool) -> bool:
    """Whether the literal `want` matches the character `have`, as the regex engine decides it."""
    if want == have:
        return True
    return casefold and re.fullmatch(re.escape(want), have, re.IGNORECASE) is not None


def _spread(reached: int, allowed: int) -> int:
    """Add every position reachable by consuming zero or more characters of `allowed`.

    Bit i of a mask is position i of the path. One addition carries through each run of allowed
    characters, so the whole spread is a few big-integer operations.
    """
    return (((reached & allowed) + allowed) ^ allowed) | reached


class _Subject:
    """One path, with the bit masks that the matcher needs. Built lazily, once per path."""

    def __init__(self, rel: str, casefold: bool) -> None:
        self.rel = rel
        self.size = len(rel)
        self.casefold = casefold
        self._chars: set[str] | None = None
        self._literal: dict[str, int] = {}
        self.slash = self._mask(lambda ch: ch == "/")
        full = (1 << self.size) - 1
        self.name = full & ~self.slash
        self.line = full & ~self._mask(lambda ch: ch == "\n")

    def _mask(self, wanted) -> int:
        bits = "".join("1" if wanted(ch) else "0" for ch in reversed(self.rel))
        return int(bits, 2) if bits else 0

    def literal(self, want: str) -> int:
        mask = self._literal.get(want)
        if mask is None:
            if not self.casefold:
                mask = self._mask(lambda ch: ch == want)
            else:
                if self._chars is None:
                    self._chars = set(self.rel)
                same = {ch for ch in self._chars if _same_char(want, ch, True)}
                mask = self._mask(lambda ch: ch in same)
            self._literal[want] = mask
        return mask

    def fullmatch(self, pattern: str) -> bool:
        """Same answer as `re.fullmatch(glob_to_regex(pattern), rel, flags)`, without backtracking.

        The set of path positions that the pattern's tokens can reach is kept as one integer and
        moved token by token: O(pattern length x path length / word size), never exponential.
        """
        reached = 1
        for kind, char in _glob_tokens(pattern):
            if kind == _LIT:
                reached = (reached & self.literal(char)) << 1
            elif kind == _ONE_NAME:
                reached = (reached & self.name) << 1
            elif kind == _ANY_NAME:
                reached = _spread(reached, self.name)
            elif kind == _ANY_LINE:
                reached = _spread(reached, self.line)
            else:
                reached |= (_spread(reached, self.line) & self.slash) << 1
            if not reached:
                return False
        return bool((reached >> self.size) & 1)


def matches(rel: str, patterns: Sequence[str], casefold: bool) -> bool:
    subject = _Subject(rel, casefold)
    return any(subject.fullmatch(p) for p in patterns)


def _is_absolute(path: str) -> bool:
    return path.startswith("/") or re.match(r"^[A-Za-z]:", path) is not None


def _normalize(path: str) -> str:
    """Forward slashes, `.` and `..` resolved, no filesystem access."""
    path = path.replace("\\", "/")
    drive = ""
    if re.match(r"^[A-Za-z]:", path):
        drive, path = path[:2], path[2:]
    return drive + (posixpath.normpath(path) if path else ".")


def relative_to_root(root: str, raw: str, casefold: bool) -> str | None:
    """Path of `raw` relative to `root`, `/`-separated; None when it is outside the root."""
    root_n = _normalize(root)
    unified = raw.replace("\\", "/")
    path_n = _normalize(unified if _is_absolute(unified) else root_n + "/" + unified)
    prefix = root_n if root_n.endswith("/") else root_n + "/"
    head = path_n[: len(prefix)]
    if casefold:
        same = head.casefold() == prefix.casefold()
    else:
        same = head == prefix
    if not same or len(path_n) <= len(prefix):
        return None
    return path_n[len(prefix):]


def memory_folder(transcript_path: object, casefold: bool) -> str | None:
    """The CLI's memory folder for a hook input, or None when the layout is not the known one.

    The transcript is `<config>/projects/<project-slug>/<session>.jsonl`; the memory folder is
    `memory` next to it. Only an absolute path with a parent folder named `projects` counts.
    """
    if not isinstance(transcript_path, str) or not transcript_path.strip():
        return None
    text = transcript_path.replace("\\", "/")
    if not _is_absolute(text):
        return None
    folder = posixpath.dirname(_normalize(text))
    grand = posixpath.dirname(folder)
    name = posixpath.basename(grand)
    if not posixpath.basename(folder) or not name or posixpath.dirname(grand) == grand:
        return None
    if (name.casefold() if casefold else name) != "projects":
        return None
    return folder + "/memory"


def _names_exactly(tokens: Sequence[str], path: str, casefold: bool) -> bool:
    """True when one raw Files in token is the plain path, with no glob character."""
    want = posixpath.normpath(path)
    want = want.casefold() if casefold else want
    for token in tokens:
        if any(c in token for c in "*?{") or token.endswith("/"):
            continue
        have = posixpath.normpath(token)
        if (have.casefold() if casefold else have) == want:
            return True
    return False


def _under_sdlc(rel: str, casefold: bool) -> bool:
    return (rel.casefold() if casefold else rel).startswith(SDLC_PREFIX)


# --- decision ------------------------------------------------------------------

# Next-step texts for the main session (the technical lead). The format named here is what
# `parse_contract` accepts: one heading with a task ID, one `Files in:` line, one `Files out:` line.
_CONTRACT_FORMAT = ("one '## <ID> <title>' heading (the ID is capital letters, one dash, digits and an optional "
                    "lower-case letter, for example T-12 or T-12a; with no tasks record, number from T-1), "
                    "one '- Files in:' line and one '- Files out:' line, every path in backticks")
MAIN_NO_CONTRACT_NEXT = (f"You are the technical lead. Place the contract with /sdlc:contract <task>, or write "
                         f".sdlc/active-contract.md yourself: {_CONTRACT_FORMAT}. "
                         "Then hand the code work to the developer sub-agent.")
MAIN_BROKEN_NEXT = (f"You are the technical lead. Fix .sdlc/active-contract.md or place a new one with "
                    f"/sdlc:contract <task>: {_CONTRACT_FORMAT}. Then hand the code work to the developer sub-agent.")

def decide(
    rel: str,
    state: str,
    contract: Contract | None,
    always_allowed: Sequence[str],
    is_agent: bool,
    casefold: bool,
    broken_reason: str = "",
    developer_rules: str | None = None,
) -> Decision:
    """Decide for a path already known to be inside the root."""
    task = contract.task_id if contract else None

    def result(allow: bool, reason: str, next_step: str = "") -> Decision:
        return Decision(allow, state, reason, next_step, task, rel)

    if _under_sdlc(rel, casefold):
        if is_agent:
            return result(False, "a sub-agent never writes under .sdlc/",
                          "Return to the technical lead; the contract and the project file are theirs to change.")
        return result(True, "the main session may write under .sdlc/")
    if state == BROKEN:
        return result(False, f"the contract cannot be used: {broken_reason}",
                      "Ask the technical lead to fix .sdlc/active-contract.md." if is_agent else MAIN_BROKEN_NEXT)
    rules_file = bool(is_agent and developer_rules and matches(rel, [developer_rules], casefold))
    if rules_file and state == NO_CONTRACT:
        return result(False, f"the path is the developer rules file ({developer_rules}); "
                      "the always-allowed list does not cover it and there is no active contract",
                      "Return an OPEN QUESTION; only a contract whose Files in names this file lets a sub-agent change it.")
    if state == NO_CONTRACT:
        if matches(rel, always_allowed, casefold):
            return result(True, "in the always-allowed list")
        return result(False, "there is no active contract",
                      "Ask the technical lead to place .sdlc/active-contract.md for this task." if is_agent
                      else MAIN_NO_CONTRACT_NEXT)
    if contract is None:
        raise ValueError("state active needs a contract")
    if matches(rel, contract.files_out, casefold):
        return result(False, f"the path is in Files out of {contract.task_id}",
                      "Return an OPEN QUESTION; do not work around the contract.")
    if rules_file:
        if developer_rules and _names_exactly(contract.files_in_raw, developer_rules, casefold):
            return result(True, f"in scope of {contract.task_id} (Files in names the developer rules file)")
        return result(False, f"the path is the developer rules file ({developer_rules}) and Files in of "
                      f"{contract.task_id} does not name its exact path (no glob); the always-allowed list does not cover it",
                      "Return an OPEN QUESTION naming the developer rules file, or ask the technical lead to widen the contract.")
    if matches(rel, contract.files_in, casefold) or matches(rel, always_allowed, casefold):
        return result(True, f"in scope of {contract.task_id}")
    return result(False, f"the path is not in Files in of {contract.task_id}",
                  "Return an OPEN QUESTION naming the file, or ask the technical lead to widen the contract.")


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig", errors="replace")


def load_state(root: Path) -> tuple[str, Contract | None, list[str], str]:
    """State, contract, always-allowed list and, for a broken state, the reason.

    Call only for an opted-in project (.sdlc/project.md exists).
    """
    always: list[str] = []
    broken = ""
    try:
        always = parse_always_allowed(_read(root / PROJECT_FILE))
    except (ConfigError, OSError) as exc:
        broken = f"{PROJECT_FILE}: {exc}"
    contract_path = root / CONTRACT_FILE
    contract: Contract | None = None
    if not broken:
        if not contract_path.exists():
            return NO_CONTRACT, None, always, ""
        try:
            contract = parse_contract(_read(contract_path))
        except (ConfigError, OSError) as exc:
            broken = f"{CONTRACT_FILE}: {exc}"
    if broken:
        return BROKEN, None, always, broken
    return ACTIVE, contract, always, ""


def load_developer_rules(root: Path) -> str | None:
    """The developer rules path named in .sdlc/project.md; None when absent or unreadable."""
    try:
        return parse_developer_rules(_read(root / PROJECT_FILE))
    except OSError:
        return None


def check(
    root: Path,
    raw_path: str | None,
    is_agent: bool,
    casefold: bool,
    input_error: str = "",
    memory_dir: str | None = None,
) -> Decision | None:
    """Decide one call. None means the project has not opted in: allow, say nothing."""
    if not (root / PROJECT_FILE).is_file():
        return None
    state, contract, always, broken = load_state(root)
    task = contract.task_id if contract else None
    if raw_path is None:
        return Decision(False, state, input_error or "the hook input has no path",
                        "Report this to the technical lead; the call was not checked.", task)
    rel = relative_to_root(str(root), raw_path, casefold)
    if rel is None and memory_dir and not is_agent:
        absolute = raw_path.replace("\\", "/")
        if not _is_absolute(absolute):
            absolute = _normalize(str(root)) + "/" + absolute
        inside = relative_to_root(memory_dir, absolute, casefold)
        if inside is not None:
            return Decision(True, state, "the main session may write in the CLI memory folder",
                            "", task, f"<memory>/{inside}")
    if rel is None:
        return Decision(False, state, "the path is outside the project root",
                        "Write only inside the project folder.", task, raw_path.replace("\\", "/"))
    return decide(rel, state, contract, always, is_agent, casefold, broken, load_developer_rules(root))


# --- script modes -----------------------------------------------------------------

def check_contract(root: Path) -> tuple[int, str]:
    """Exit code and message for `--check-contract`."""
    contract_path = root / CONTRACT_FILE
    if not contract_path.is_file():
        return 1, f"no active contract: {CONTRACT_FILE} does not exist"
    try:
        contract = parse_contract(_read(contract_path))
    except (ConfigError, OSError) as exc:
        return 1, f"{CONTRACT_FILE}: {exc}"
    project = root / PROJECT_FILE
    if project.is_file():
        try:
            parse_always_allowed(_read(project))
        except (ConfigError, OSError) as exc:
            return 1, f"{PROJECT_FILE}: {exc}"
    return 0, f"contract {contract.task_id}: {len(contract.files_in)} Files in, {len(contract.files_out)} Files out"


def _git(root: Path, *args: str) -> bytes:
    done = subprocess.run(["git", "-C", str(root), "-c", "core.fsmonitor=false", *args], capture_output=True, timeout=60)
    if done.returncode != 0:
        raise OSError(done.stderr.decode("utf-8", errors="replace").strip() or "git failed")
    return done.stdout


def porcelain_paths(raw: bytes) -> list[str]:
    """Paths of `git status --porcelain -z`. A rename or copy gives both its paths."""
    fields = raw.decode("utf-8", errors="replace").split("\0")
    out: list[str] = []
    i = 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4:
            continue
        out.append(entry[3:])
        if entry[0] in "RC" or entry[1] in "RC":
            if i < len(fields) and fields[i]:
                out.append(fields[i])
            i += 1
    return out


def check_worktree(root: Path, casefold: bool) -> tuple[int, list[str], str]:
    """Exit code, paths outside the contract, and a message for `--check-worktree`."""
    if not (root / CONTRACT_FILE).is_file():
        return 1, [], f"no active contract: {CONTRACT_FILE} does not exist"
    state, contract, always, broken = load_state(root)
    if contract is None:
        return 1, [], f"the contract cannot be used: {broken}"
    try:
        prefix = _git(root, "rev-parse", "--show-prefix").decode("utf-8", errors="replace").strip()
        # a nested repository keeps its own config, which git would read (and run a filter from) when it enters it
        raw = _git(root, "status", "--porcelain", "-z", "--untracked-files=all", "--ignore-submodules=all", "--", ".")
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, [], f"git status failed: {exc}"
    outside: list[str] = []
    checked = 0
    for path in porcelain_paths(raw):
        rel = path[len(prefix):] if prefix and path.startswith(prefix) else path
        if _under_sdlc(rel, casefold):
            continue
        checked += 1
        if not decide(rel, state, contract, always, False, casefold).allow and rel not in outside:
            outside.append(rel)
    if outside:
        return 1, outside, f"{len(outside)} of {checked} changed paths are outside {contract.task_id}"
    return 0, [], f"{checked} changed paths, all inside {contract.task_id}"


# --- event line and entry point -------------------------------------------------

def log_event(root: Path, decision: Decision, tool: str | None, agent: str | None, today: str) -> None:
    """One line per decision. No path. A failed write changes nothing."""
    event = {
        "event": "scope",
        "date": today,
        "task": decision.task_id,
        "state": decision.state,
        "decision": "allow" if decision.allow else "deny",
        "tool": tool,
        "agent": agent,
    }
    try:
        with open(root / EVENT_FILE, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
    except Exception:
        pass


def _field_path(tool_input: object) -> tuple[str | None, str]:
    if not isinstance(tool_input, dict):
        return None, "the hook input has no tool_input object"
    for name in PATH_FIELDS:
        value = tool_input.get(name)
        if isinstance(value, str) and value.strip():
            return value, ""
    return None, "the hook input has neither file_path nor notebook_path"


def _denial_text(decision: Decision) -> str:
    where = decision.rel if decision.rel else "(no path)"
    lines = [f"scope guard: denied [{decision.state}] {where}", decision.reason]
    if decision.next_step:
        lines.append(f"Next: {decision.next_step}")
    return "\n".join(lines) + "\n"


def _script_mode(args: argparse.Namespace, stdout: TextIO | None, stderr: TextIO | None,
                 casefold: bool | None) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    for stream in (out, err):
        reconfigure = getattr(stream, "reconfigure", None)
        if stream in (sys.stdout, sys.stderr) and callable(reconfigure):
            reconfigure(errors="backslashreplace")
    fold = (os.name == "nt") if casefold is None else casefold
    root = Path(os.path.abspath(args.root or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()))
    if args.check_contract and args.check_worktree:
        err.write("scope guard: use one of --check-contract and --check-worktree\n")
        return 1
    if args.check_contract:
        code, message = check_contract(root)
        (out if code == 0 else err).write(message + "\n")
        return code
    code, outside, message = check_worktree(root, fold)
    for path in outside:
        out.write(path + "\n")
    (out if code == 0 else err).write(message + "\n")
    return code


USAGE = (
    "usage: scope_guard [--root DIR] [--check-contract | --check-worktree]\n"
    "  no option: hook mode, reads the hook input as JSON on stdin\n"
    "  --check-contract   exit 0 when .sdlc/active-contract.md parses\n"
    "  --check-worktree   print the changed paths outside the contract\n"
)


def main(
    argv: Sequence[str] | None = None,
    stdin_bytes: bytes | None = None,
    stderr: TextIO | None = None,
    today: str | None = None,
    casefold: bool | None = None,
    stdout: TextIO | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="scope_guard", add_help=False, allow_abbrev=False)
    parser.add_argument("--root", default=None)
    parser.add_argument("--check-contract", action="store_true")
    parser.add_argument("--check-worktree", action="store_true")
    args, unknown = parser.parse_known_args(argv)
    if any(item.startswith("-") for item in unknown):
        # An option that is not one of these would fall through to hook mode: it would wait on
        # stdin and log a decision no write caused (finding C-2 of gate G4).
        (stderr if stderr is not None else sys.stderr).write(USAGE)
        return 2
    if args.check_contract or args.check_worktree:
        return _script_mode(args, stdout, stderr, casefold)
    if stdin_bytes is None:
        stdin_bytes = sys.stdin.buffer.read()
    out = stderr if stderr is not None else sys.stderr
    fold = (os.name == "nt") if casefold is None else casefold

    data: object = None
    input_error = ""
    try:
        data = json.loads(stdin_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        input_error = "the hook input is not valid JSON"
    if input_error == "" and not isinstance(data, dict):
        input_error = "the hook input is not a JSON object"
        data = None
    event_in: dict = data if isinstance(data, dict) else {}

    root_text = args.root or os.environ.get("CLAUDE_PROJECT_DIR") or event_in.get("cwd")
    root = Path(os.path.abspath(root_text if isinstance(root_text, str) and root_text else os.getcwd()))

    raw_path: str | None = None
    if not input_error:
        raw_path, input_error = _field_path(event_in.get("tool_input"))
    is_agent = "agent_id" in event_in or "agent_type" in event_in
    agent: str | None = None
    if is_agent:
        agent_type = event_in.get("agent_type")
        agent = agent_type[:80] if isinstance(agent_type, str) and agent_type else "unknown"
    tool = event_in.get("tool_name")
    tool = tool[:40] if isinstance(tool, str) else None

    memory = memory_folder(event_in.get("transcript_path"), fold)
    decision = check(root, raw_path, is_agent, fold, input_error, memory)
    if decision is None:
        return 0
    stamp = today or datetime.date.today().isoformat()
    log_event(root, decision, tool, agent, stamp)
    if decision.allow:
        return 0
    out.write(_denial_text(decision))
    return 2


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:  # fail closed: the launcher would turn any other code into 2 as well
        sys.stderr.write(f"scope guard: internal error ({type(exc).__name__}); the call is denied\n")
        code = 2
    sys.exit(code)
