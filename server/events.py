"""The `guard_events` tool as a plain function: totals from `tools.events` on the project root."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools import events as event_totals

TASK_LIMIT = 40


def guard_events(root: Path, task: str | None = None) -> dict[str, Any]:
    """Allow and deny counts per task, tool and agent. An empty `task` means all tasks. Reads only."""
    if task is not None and not isinstance(task, str):
        raise ValueError("task: must be a task ID such as T-1, or 'none'")
    task = task.strip() if task else None
    if task is not None and len(task) > TASK_LIMIT:
        raise ValueError(f"task: at most {TASK_LIMIT} characters")
    try:
        found = event_totals.read_events(root)
    except OSError:
        out = event_totals.totals([], task or None)
        out["error"] = "the event file could not be read"
        return out
    out = event_totals.totals(found, task or None)
    out["error"] = ""
    return out
