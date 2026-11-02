"""Source profiles: which record files to read and which folded regexes to match.

A profile is one ASCII JSON file per source. Non-ASCII characters are written as
\\uXXXX escapes. Marker regexes are matched against folded lines (see fold.py),
so they are written in folded ASCII form. No marker lives in the code.

    {
      "schema": 1,
      "files": {"<role>": "<path relative to the source root>"},
      "metrics": {"M1": {...}, "M2": {...}, "M5": {...}, "M6": {...}}
    }

A metric entry that is empty or absent means the source has no such record; the
metric then shows "no data".
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = 1
ROLE_RE = re.compile(r"[a-z][a-z0-9_]{0,31}")

# metric id -> keys that hold one regex each
REQUIRED = {
    "M1": ("version_heading", "date", "revert_version"),
    "M2": ("version_heading", "date", "status", "to_be_tested"),
    "M5": ("entry_heading", "task_line"),
    "M6": ("entry_heading", "task_line"),
}
OPTIONAL = {
    "M1": ("revert_item",),
    "M2": ("no_change",),
    "M5": ("session_line",),
    "M6": ("session_line",),
}
# metric id -> field names allowed under "fields" (each regex needs a group "n")
FIELDS = {
    "M5": ("review_rounds",),
    "M6": ("questions_back", "out_of_scope"),
}
# keys whose regex must define a named group
GROUPS = {"date": "date", "status": "status", "entry_heading": "date"}


class ProfileError(ValueError):
    pass


@dataclass(frozen=True)
class Profile:
    files: dict[str, str]
    metrics: dict[str, dict[str, Any]]  # compiled; a metric with no entry is absent
    sha256: str


def profile_hash(raw: bytes) -> str:
    # Line ends are normalised so the hash does not depend on the checkout.
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _compile(where: str, source: Any, group: str | None) -> "re.Pattern[str]":
    if not isinstance(source, str) or not source:
        raise ProfileError(f"{where}: expected a non-empty regex string")
    try:
        rx = re.compile(source)
    except re.error:
        raise ProfileError(f"{where}: not a valid regex")
    if group is not None and group not in rx.groupindex:
        raise ProfileError(f"{where}: regex needs a named group '{group}'")
    return rx


def _compile_metric(mid: str, entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ProfileError(f"{mid}: expected an object")
    allowed = {"file", *REQUIRED[mid], *OPTIONAL[mid], *(("fields",) if mid in FIELDS else ())}
    unknown = sorted(set(entry) - allowed)
    if unknown:
        raise ProfileError(f"{mid}: unknown key '{unknown[0]}'")
    out: dict[str, Any] = {}
    role = entry.get("file")
    if not isinstance(role, str) or not ROLE_RE.fullmatch(role):
        raise ProfileError(f"{mid}: 'file' must name a role")
    out["file"] = role
    for key in (*REQUIRED[mid], *OPTIONAL[mid]):
        if key in entry:
            out[key] = _compile(f"{mid}.{key}", entry[key], GROUPS.get(key))
        elif key in REQUIRED[mid]:
            raise ProfileError(f"{mid}: missing '{key}'")
    if mid in FIELDS:
        fields = entry.get("fields")
        if not isinstance(fields, dict) or not fields:
            raise ProfileError(f"{mid}: missing 'fields'")
        bad = sorted(set(fields) - set(FIELDS[mid]))
        if bad:
            raise ProfileError(f"{mid}.fields: unknown field '{bad[0]}'")
        out["fields"] = {
            name: _compile(f"{mid}.fields.{name}", rx, "n") for name, rx in fields.items()
        }
    return out


def parse_profile(raw: bytes) -> Profile:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        raise ProfileError("profile must be ASCII; write other characters as \\u escapes")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise ProfileError(f"profile is not valid JSON (line {err.lineno})")
    if not isinstance(data, dict) or set(data) != {"schema", "files", "metrics"}:
        raise ProfileError("profile needs exactly the keys schema, files, metrics")
    if data["schema"] != SCHEMA:
        raise ProfileError(f"profile schema must be {SCHEMA}")
    files = data["files"]
    if not isinstance(files, dict) or not files:
        raise ProfileError("profile 'files' must map roles to paths")
    for role, rel in files.items():
        if not ROLE_RE.fullmatch(role):
            raise ProfileError("profile 'files' has an invalid role name")
        if not isinstance(rel, str) or not rel:
            raise ProfileError(f"profile file '{role}': expected a path string")
    metrics = data["metrics"]
    if not isinstance(metrics, dict):
        raise ProfileError("profile 'metrics' must be an object")
    compiled: dict[str, dict[str, Any]] = {}
    for mid, entry in metrics.items():
        if mid not in REQUIRED:
            raise ProfileError(f"unknown metric '{mid[:16]}'")
        if not entry:
            continue
        compiled[mid] = _compile_metric(mid, entry)
        if compiled[mid]["file"] not in files:
            raise ProfileError(f"{mid}: role '{compiled[mid]['file']}' is not in 'files'")
    return Profile(files=dict(files), metrics=compiled, sha256=profile_hash(raw))


def load_profile(path: Path) -> Profile:
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise ProfileError("cannot read the profile file")
    return parse_profile(raw)
