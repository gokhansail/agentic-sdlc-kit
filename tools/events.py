"""Totals of the scope guard's event lines in `.sdlc/metrics.jsonl`.

Standard library only. `read_events(root)` gives one entry per non-blank line: the parsed JSON
object, or None when the line is not valid JSON or not an object. `totals(events, task=None)`
counts the scope events per task: allow and deny, then by tool and by agent (no agent is
"main", no task is "none"). A scope event whose fields are unusable counts as malformed; an
object of another event kind counts as "other". Malformed lines belong to no task, so the
malformed count is the same with or without a task filter. Event lines hold no path.

CLI: `python tools/events.py --root <folder> [--task T-1]` prints the totals as JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

if __package__ in (None, ""):  # started as a script: make `tools` importable
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.records import read_inside  # noqa: E402
from tools.scope_guard import EVENT_FILE  # noqa: E402

MAX_BYTES = 8_000_000  # about 50,000 event lines
NO_TASK = "none"
NO_AGENT = "main"
NO_TOOL = "unknown"
DECISIONS = ("allow", "deny")


def read_events(root: Path) -> list[dict[str, Any] | None]:
    """Parsed lines of the event file; None marks an unusable line. A missing file gives [].

    An OSError (UnsafeFile for a link out of the root, a device or a file over MAX_BYTES) means the file
    was not read.
    """
    try:
        data = read_inside(Path(root), EVENT_FILE, MAX_BYTES)
    except FileNotFoundError:
        return []
    events: list[dict[str, Any] | None] = []
    for line in data.decode("utf-8-sig", errors="replace").split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except (ValueError, RecursionError):
            events.append(None)
            continue
        events.append(value if isinstance(value, dict) else None)
    return events


def _name(value: object, empty: str) -> str | None:
    """The key for a task, tool or agent field; None when the field has the wrong type."""
    if value is None:
        return empty
    return value if isinstance(value, str) else None


def _bump(table: dict[str, dict[str, int]], key: str, decision: str) -> None:
    row = table.setdefault(key, {"allow": 0, "deny": 0})
    row[decision] += 1


def totals(events: Iterable[dict[str, Any] | None], task: str | None = None) -> dict[str, Any]:
    """Counts per task, tool and agent for the scope events; `task` keeps one task (or "none")."""
    per_task: dict[str, dict[str, Any]] = {}
    allow = deny = malformed = other = 0
    for event in events:
        if event is None:
            malformed += 1
            continue
        if event.get("event") != "scope":
            other += 1
            continue
        decision = event.get("decision")
        key = _name(event.get("task"), NO_TASK)
        tool = _name(event.get("tool"), NO_TOOL)
        agent = _name(event.get("agent"), NO_AGENT)
        if decision not in DECISIONS or key is None or tool is None or agent is None:
            malformed += 1
            continue
        if task is not None and key != task:
            continue
        row = per_task.setdefault(key, {"allow": 0, "deny": 0, "by_tool": {}, "by_agent": {}})
        row[decision] += 1
        _bump(row["by_tool"], tool, decision)
        _bump(row["by_agent"], agent, decision)
        if decision == "allow":
            allow += 1
        else:
            deny += 1
    ordered = {
        name: {
            "allow": row["allow"],
            "deny": row["deny"],
            "by_tool": dict(sorted(row["by_tool"].items())),
            "by_agent": dict(sorted(row["by_agent"].items())),
        }
        for name, row in sorted(per_task.items())
    }
    return {"task": task, "allow": allow, "deny": deny, "tasks": ordered, "malformed": malformed, "other": other}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="events", description="Totals of the scope guard event lines.")
    parser.add_argument("--root", default=".", help="project folder (default: the current folder)")
    parser.add_argument("--task", default=None, help="keep one task, for example T-1; 'none' keeps events with no task")
    args = parser.parse_args(argv)
    try:
        events = read_events(Path(args.root))
    except OSError:
        sys.stderr.write("events: cannot read the event file\n")
        return 1
    sys.stdout.write(json.dumps(totals(events, args.task), indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
