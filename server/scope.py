"""The `scope_check`, `contract` and `changed_outside` tools as plain functions (no SDK import).

Each one calls the guard's own function on the project root; this module has no path or glob rule.
Answers name paths relative to the root. A path given outside the root comes back as given.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Sequence

from server.status import NOT_OPTED_IN
from tools import scope_guard

ACTORS = ("sub-agent", "main")
MAX_PATHS = 50
GUARD_OFF = "the guard is off in this project (no .sdlc/project.md): every write is allowed"
WORKTREE_LIMIT = (
    "git cannot tell when a file changed, so files changed before the task started are listed too; "
    "paths under .sdlc/ are not checked"
)


def _fold(casefold: bool | None) -> bool:
    return (os.name == "nt") if casefold is None else casefold


def _scrub(text: str, root: Path) -> str:
    """The text without the root's absolute path (an OS error message can carry it)."""
    for form in {str(root), root.as_posix()}:
        text = "<root>".join(text.split(form))
    return text


def _slashes(raw: str) -> str:
    return "/".join(raw.split("\\"))


def _decision_row(decision: scope_guard.Decision, raw: str) -> dict[str, Any]:
    return {
        "path": decision.rel if decision.rel is not None else _slashes(raw),
        "allow": decision.allow,
        "reason": decision.reason,
        "next_step": decision.next_step,
        "state": decision.state,
        "task": decision.task_id,
    }


def _one(root: Path, raw: object, is_agent: bool, fold: bool, opted_in: bool) -> dict[str, Any]:
    usable = isinstance(raw, str) and bool(raw.strip()) and "\0" not in raw
    if not usable:
        if not opted_in:
            return {"path": "", "allow": False, "reason": "not a usable path", "next_step": "",
                    "state": NOT_OPTED_IN, "task": None}
        denied = scope_guard.check(root, None, is_agent, fold, "not a usable path")
        assert denied is not None
        return _decision_row(denied, "")
    text = str(raw)
    if not opted_in:
        rel = scope_guard.relative_to_root(str(root), text, fold)
        return {"path": rel if rel is not None else _slashes(text), "allow": True, "reason": GUARD_OFF,
                "next_step": "", "state": NOT_OPTED_IN, "task": None}
    decision = scope_guard.check(root, text, is_agent, fold)
    assert decision is not None
    return _decision_row(decision, text)


def scope_check(root: Path, paths: Sequence[str], actor: str, casefold: bool | None = None) -> dict[str, Any]:
    """Allow or deny for each path, as the guard decides a write by `actor` ("sub-agent" or "main")."""
    if actor not in ACTORS:
        raise ValueError("actor: must be 'sub-agent' or 'main'")
    if not isinstance(paths, (list, tuple)):
        raise ValueError("paths: must be a list of paths")
    if len(paths) > MAX_PATHS:
        raise ValueError(f"paths: at most {MAX_PATHS} paths per call, got {len(paths)}")
    fold = _fold(casefold)
    opted_in = (root / scope_guard.PROJECT_FILE).is_file()
    state, task = NOT_OPTED_IN, None
    if opted_in:
        state, contract, _always, _reason = scope_guard.load_state(root)
        task = contract.task_id if contract else None
    return {
        "actor": actor,
        "opted_in": opted_in,
        "guard_state": state,
        "task_id": task,
        "note": "" if opted_in else GUARD_OFF,
        "results": [_one(root, raw, actor == "sub-agent", fold, opted_in) for raw in paths],
    }


def contract(root: Path) -> dict[str, Any]:
    """Whether `.sdlc/active-contract.md` parses, and what it holds. Never raises."""
    opted_in = (root / scope_guard.PROJECT_FILE).is_file()
    out: dict[str, Any] = {
        "opted_in": opted_in,
        "guard_state": NOT_OPTED_IN,
        "valid": False,
        "message": "",
        "task_id": None,
        "files_in": [],
        "files_out": [],
        "always_allowed": [],
        "developer_rules": None,
    }
    try:
        code, message = scope_guard.check_contract(root)
        out["valid"] = code == 0
        out["message"] = _scrub(message, root)
        out["developer_rules"] = scope_guard.load_developer_rules(root)
        if opted_in:
            state, _contract, always, _reason = scope_guard.load_state(root)
            out["guard_state"] = state
            out["always_allowed"] = list(always)
        if code == 0:
            raw = (root / scope_guard.CONTRACT_FILE).read_bytes().decode("utf-8-sig", errors="replace")
            parsed = scope_guard.parse_contract(raw)
            out["task_id"] = parsed.task_id
            out["files_in"] = list(parsed.files_in)
            out["files_out"] = list(parsed.files_out)
    except Exception as exc:
        out["valid"] = False
        out["message"] = _scrub(f"the contract could not be read ({type(exc).__name__}: {exc})", root)
    return out


def changed_outside(root: Path, casefold: bool | None = None) -> dict[str, Any]:
    """Changed paths git shows that the active contract does not cover. Never raises."""
    try:
        code, outside, message = scope_guard.check_worktree(root, _fold(casefold))
    except Exception as exc:
        code, outside, message = 1, [], f"the check could not run ({type(exc).__name__}: {exc})"
    return {"ok": code == 0, "outside": list(outside), "message": _scrub(message, root), "limit": WORKTREE_LIMIT}
