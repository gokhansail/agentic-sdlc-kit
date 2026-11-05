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
writes under .sdlc/; the main session always may.

Grammar (only backticked tokens count; `{a,b}` expands; a trailing `/` is a
folder; `*` stays inside one folder, `**` crosses folders; patterns are anchored
at the project root):
    .sdlc/project.md          backticked globs in a "## Always allowed" section
    .sdlc/active-contract.md  one heading holding the task ID, one "Files in:" line
                              and one "Files out:" line (see templates/task-contract.md)

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
import sys
from dataclasses import dataclass
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
_HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.*?)\s*#*\s*$")
_TASK_ID = re.compile(r"(?<![\w-])[A-Z][A-Z0-9]{0,9}-\d+[a-z]?(?![\w-])")
_FIELD = re.compile(r"^\s*(?:[-*+]\s+)?(Files in|Files out)\s*:(.*)$", re.IGNORECASE)


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
        heading = _HEADING.match(line)
        if heading:
            inside = heading.group(1).strip().lower() == "always allowed"
            continue
        if inside:
            out.extend(patterns_from_line(line))
    return out


def parse_contract(text: str) -> Contract:
    """Parse one contract. Raises ConfigError, with the line number, when it is broken."""
    headings: list[tuple[int, str]] = []
    fields: dict[str, list[tuple[int, str]]] = {"files in": [], "files out": []}
    for number, line in enumerate(text.splitlines(), start=1):
        heading = _HEADING.match(line)
        if heading:
            headings.append((number, heading.group(1)))
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
    return Contract(task.group(0), found["files in"], found["files out"])


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


def matches(rel: str, patterns: Sequence[str], casefold: bool) -> bool:
    flags = re.IGNORECASE if casefold else 0
    return any(re.fullmatch(glob_to_regex(p), rel, flags) for p in patterns)


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


def _under_sdlc(rel: str, casefold: bool) -> bool:
    return (rel.casefold() if casefold else rel).startswith(SDLC_PREFIX)


# --- decision ------------------------------------------------------------------

def decide(
    rel: str,
    state: str,
    contract: Contract | None,
    always_allowed: Sequence[str],
    is_agent: bool,
    casefold: bool,
    broken_reason: str = "",
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
                      "Ask the technical lead to fix .sdlc/active-contract.md.")
    if state == NO_CONTRACT:
        if matches(rel, always_allowed, casefold):
            return result(True, "in the always-allowed list")
        return result(False, "there is no active contract",
                      "Ask the technical lead to place .sdlc/active-contract.md for this task.")
    if contract is None:
        raise ValueError("state active needs a contract")
    if matches(rel, contract.files_out, casefold):
        return result(False, f"the path is in Files out of {contract.task_id}",
                      "Return an OPEN QUESTION; do not work around the contract.")
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


def check(
    root: Path,
    raw_path: str | None,
    is_agent: bool,
    casefold: bool,
    input_error: str = "",
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
    if rel is None:
        return Decision(False, state, "the path is outside the project root",
                        "Write only inside the project folder.", task, raw_path.replace("\\", "/"))
    return decide(rel, state, contract, always, is_agent, casefold, broken)


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


def main(
    argv: Sequence[str] | None = None,
    stdin_bytes: bytes | None = None,
    stderr: TextIO | None = None,
    today: str | None = None,
    casefold: bool | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="scope_guard", add_help=False)
    parser.add_argument("--root", default=None)
    args, _ = parser.parse_known_args(argv)
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

    decision = check(root, raw_path, is_agent, fold, input_error)
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
