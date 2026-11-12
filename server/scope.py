"""The `scope_check`, `contract` and `changed_outside` tools as plain functions (no SDK import).

Each one calls the guard's own function on the project root; this module has no path or glob rule.
Answers name paths relative to the root. A path given outside the root comes back as given.
Before a guard function reads `.sdlc/project.md` or the contract, `server.inputs` checks that the file
is a regular file inside the root and of a sane size (T-44).
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from server.inputs import bounded, control_problem, git_problem, scrub
from server.status import NOT_OPTED_IN
from tools import scope_guard

ACTORS = ("sub-agent", "main")
MAX_PATHS = 50
PATH_LIMIT = 500
GUARD_OFF = "the guard is off in this project (no .sdlc/project.md): every write is allowed"
WORKTREE_LIMIT = (
    "git cannot tell when a file changed, so files changed before the task started are listed too; "
    "paths under .sdlc/ are not checked; a change inside a nested repository is not reported"
)


def _fold(casefold: bool | None) -> bool:
    return (os.name == "nt") if casefold is None else casefold


def _slashes(raw: str) -> str:
    return "/".join(raw.split("\\"))


@contextmanager
def _no_optional_locks() -> Iterator[None]:
    """`git status` may rewrite .git/index to refresh its cache; this asks it not to take that lock."""
    name = "GIT_OPTIONAL_LOCKS"
    before = os.environ.get(name)
    os.environ[name] = "0"
    try:
        yield
    finally:
        if before is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = before


def _decision_row(decision: scope_guard.Decision, raw: str, root: Path) -> dict[str, Any]:
    return {
        "path": decision.rel if decision.rel is not None else _slashes(raw),
        "allow": decision.allow,
        "reason": scrub(decision.reason, root),
        "next_step": decision.next_step,
        "state": decision.state,
        "task": decision.task_id,
    }


def _unusable(raw: object) -> str:
    """Why `raw` is not a path the tool will look at; "" when it is usable."""
    if not isinstance(raw, str) or not raw.strip() or "\0" in raw:
        return "not a usable path"
    if len(raw) > PATH_LIMIT:
        return f"the path is longer than {PATH_LIMIT} characters"
    return ""


def _one(root: Path, raw: object, is_agent: bool, fold: bool, opted_in: bool) -> dict[str, Any]:
    why = _unusable(raw)
    if why:
        if not opted_in:
            return {"path": "", "allow": False, "reason": why, "next_step": "",
                    "state": NOT_OPTED_IN, "task": None}
        denied = scope_guard.check(root, None, is_agent, fold, why)
        assert denied is not None
        return _decision_row(denied, "", root)
    text = str(raw)
    if not opted_in:
        rel = scope_guard.relative_to_root(str(root), text, fold)
        return {"path": rel if rel is not None else _slashes(text), "allow": True, "reason": GUARD_OFF,
                "next_step": "", "state": NOT_OPTED_IN, "task": None}
    decision = scope_guard.check(root, text, is_agent, fold)
    assert decision is not None
    return _decision_row(decision, text, root)


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
        problem = control_problem(root)
        if problem:
            raise ValueError(f"the project files cannot be used: {problem}")
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
    cut = False
    try:
        problem = control_problem(root)
        if problem:
            out["message"] = problem
            if opted_in:
                out["guard_state"] = scope_guard.BROKEN
            return out
        code, message = scope_guard.check_contract(root)
        out["valid"] = code == 0
        out["message"] = scrub(message, root)
        out["developer_rules"] = scope_guard.load_developer_rules(root)
        if opted_in:
            state, _contract, always, _reason = scope_guard.load_state(root)
            out["guard_state"] = state
            out["always_allowed"], cut = bounded(list(always))
        if code == 0:
            raw = (root / scope_guard.CONTRACT_FILE).read_bytes().decode("utf-8-sig", errors="replace")
            parsed = scope_guard.parse_contract(raw)
            out["task_id"] = parsed.task_id
            out["files_in"], cut_in = bounded(list(parsed.files_in))
            out["files_out"], cut_out = bounded(list(parsed.files_out))
            cut = cut or cut_in or cut_out
        if cut:
            out["cut"] = True  # the key is absent when nothing was left out
    except Exception as exc:
        out["valid"] = False
        out["message"] = scrub(f"the contract could not be read ({type(exc).__name__}: {exc})", root)
    return out


def changed_outside(root: Path, casefold: bool | None = None) -> dict[str, Any]:
    """Changed paths git shows that the active contract does not cover. Never raises."""
    try:
        problem = control_problem(root) or (git_problem(root) if (root / scope_guard.CONTRACT_FILE).is_file() else "")
        if problem:
            code, outside, message = 1, [], f"git status was not run: {problem}"
        else:
            with _no_optional_locks():
                code, outside, message = scope_guard.check_worktree(root, _fold(casefold))
    except Exception as exc:
        code, outside, message = 1, [], f"the check could not run ({type(exc).__name__}: {exc})"
    return {"ok": code == 0, "outside": list(outside), "message": scrub(message, root), "limit": WORKTREE_LIMIT}
