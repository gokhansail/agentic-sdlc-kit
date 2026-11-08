"""The `status` tool as a plain function: no SDK import, testable on a folder."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from server.inputs import bounded, bounded_records, control_problem, scrub
from tools import scope_guard
from tools.records import read_records

NOT_OPTED_IN = "not-opted-in"


def status(root: Path, root_source: str = "") -> dict[str, Any]:
    """Guard state, active task and record names of the project at `root`. Reads only."""
    opted_in = (root / scope_guard.PROJECT_FILE).is_file()
    out: dict[str, Any] = {
        "opted_in": opted_in,
        "guard_state": NOT_OPTED_IN,
        "task_id": None,
        "files_in": [],
        "files_out": [],
        "broken_reason": "",
        "records": bounded_records(read_records(root)),
        "root_source": root_source,
    }
    if not opted_in:
        return out
    problem = control_problem(root)
    if problem:
        out["guard_state"] = scope_guard.BROKEN
        out["broken_reason"] = problem
        return out
    state, contract, _always, reason = scope_guard.load_state(root)
    out["guard_state"] = state
    out["broken_reason"] = scrub(reason, root)
    if contract is not None:
        out["task_id"] = contract.task_id
        out["files_in"], cut_in = bounded(list(contract.files_in))
        out["files_out"], cut_out = bounded(list(contract.files_out))
        if cut_in or cut_out:
            out["cut"] = True
    return out
