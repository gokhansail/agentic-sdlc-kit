"""Source profiles: which record files to read and which folded regexes to match.

A profile is one ASCII JSON file per source. Non-ASCII characters are written as
\\uXXXX escapes. Marker regexes are matched against folded lines (see fold.py),
so they are written in folded ASCII form. No marker lives in the code.

    {
      "schema": 1,
      "files": {"<role>": "<path relative to the source root>"},
      "folders": {"<role>": {"dir": "<path>", "name": "<regex>", "skip": "<regex>"}},
      "metrics": {"M1": {...}, ..., "M13": {...}}
    }

`folders` is optional. A folder entry names a directory (not searched
recursively) and a file-name regex; files whose folded name matches `name` and
do not match `skip` are the folder's records. A metric entry that is empty or
absent means the source has no such record; the metric then shows "no data".

Metrics by kind:
  text      M1, M2, M5, M6   one record file, regexes per line
  git       M3               path glob and attribute pattern for `git grep`
  git+text  M12              commits from git, versions from a changelog file
  audit     M8               a folder of reports
  record    M9, M13          one record file, regexes per entry or heading

M5 and M6 give the per-task line either as `task_line` plus `fields`, or as
`task_lines`, an ordered list of {"line": <regex>, "fields": {...}} items. The two
forms are exclusive. With a list, each entry yields one task: the first item in
list order that matches a line of the entry decides; other matching lines of the
entry are ignored and counted as a warning.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = 1
ROLE_RE = re.compile(r"[a-z][a-z0-9_]{0,31}")
RESERVED_ROLES = frozenset({"git_log", "git_tests"})
TAG_LABELS = ("E", "M", "H")
GLOB_RE = re.compile(r"[A-Za-z0-9_./*?-]+")
PATTERN_RE = re.compile(r"[\x20-\x7e]+")

# metric id -> keys that hold one regex each
REQUIRED = {
    "M1": ("version_heading", "date", "revert_version"),
    "M2": ("version_heading", "date", "status", "to_be_tested"),
    "M5": ("entry_heading", "task_line"),
    "M6": ("entry_heading", "task_line"),
}
# metrics whose per-task line may be given as the ordered list `task_lines` instead
LISTED = {"M5": ("entry_heading",), "M6": ("entry_heading",)}
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

# New metrics: key -> named groups the regex must define.
RECORD_REQUIRED: dict[str, dict[str, tuple[str, ...]]] = {
    "M8": {"finding_heading": ("id",), "table_row": ("id", "status")},
    "M9": {"entry_heading": (), "outcome": ("value",), "empty": ()},
    "M13": {"heading": ("done",), "tag": ("tag",)},
}
RECORD_OPTIONAL: dict[str, dict[str, tuple[str, ...]]] = {
    "M8": {"severity_line": ("severity",)},
    "M9": {"date_line": ("date",)},
    "M13": {"done_date": ("date",), "done_date_body": ("date",)},
}
M12_VERSION_KEYS: dict[str, tuple[str, ...]] = {"version_heading": (), "date": ("date",)}
ALL_METRICS = frozenset(REQUIRED) | {"M3", "M8", "M9", "M12", "M13"}


class ProfileError(ValueError):
    pass


@dataclass(frozen=True)
class Profile:
    files: dict[str, str]
    metrics: dict[str, dict[str, Any]]  # compiled; a metric with no entry is absent
    sha256: str
    folders: dict[str, dict[str, Any]] = field(default_factory=dict)  # compiled


def profile_hash(raw: bytes) -> str:
    # Line ends are normalised so the hash does not depend on the checkout.
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _compile(where: str, source: Any, group: "str | tuple[str, ...] | None") -> "re.Pattern[str]":
    if not isinstance(source, str) or not source:
        raise ProfileError(f"{where}: expected a non-empty regex string")
    try:
        rx = re.compile(source)
    except re.error:
        raise ProfileError(f"{where}: not a valid regex")
    needed = (group,) if isinstance(group, str) else (group or ())
    for name in needed:
        if name not in rx.groupindex:
            raise ProfileError(f"{where}: regex needs a named group '{name}'")
    return rx


def _role(mid: str, key: str, entry: dict[str, Any], known: Any) -> str:
    role = entry.get(key)
    if not isinstance(role, str) or not ROLE_RE.fullmatch(role):
        raise ProfileError(f"{mid}: '{key}' must name a role")
    if role not in known:
        raise ProfileError(f"{mid}: role '{role}' is not in the profile")
    return role


def _compile_metric(mid: str, entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ProfileError(f"{mid}: expected an object")
    listed = mid in LISTED and "task_lines" in entry
    if listed and "task_line" in entry:
        raise ProfileError(f"{mid}: 'task_line' and 'task_lines' cannot both be given")
    allowed = {"file", *REQUIRED[mid], *OPTIONAL[mid], *(("fields",) if mid in FIELDS else ())}
    if mid in LISTED:
        allowed.add("task_lines")
    unknown = sorted(set(entry) - allowed)
    if unknown:
        raise ProfileError(f"{mid}: unknown key '{unknown[0]}'")
    if listed and "fields" in entry:
        raise ProfileError(f"{mid}: with 'task_lines' the fields belong to each item")
    out: dict[str, Any] = {}
    role = entry.get("file")
    if not isinstance(role, str) or not ROLE_RE.fullmatch(role):
        raise ProfileError(f"{mid}: 'file' must name a role")
    out["file"] = role
    for key in (*REQUIRED[mid], *OPTIONAL[mid]):
        if key in entry:
            out[key] = _compile(f"{mid}.{key}", entry[key], GROUPS.get(key))
        elif key in REQUIRED[mid] and not (listed and key == "task_line"):
            raise ProfileError(f"{mid}: missing '{key}'")
    if listed:
        out["task_lines"] = _compile_task_lines(mid, entry["task_lines"])
    elif mid in FIELDS:
        out["fields"] = _compile_fields(mid, f"{mid}.fields", entry.get("fields"))
    return out


def _compile_fields(mid: str, where: str, fields: Any) -> dict[str, "re.Pattern[str]"]:
    if not isinstance(fields, dict) or not fields:
        raise ProfileError(f"{where}: expected a non-empty object")
    bad = sorted(set(fields) - set(FIELDS[mid]))
    if bad:
        raise ProfileError(f"{where}: unknown field '{bad[0]}'")
    return {name: _compile(f"{where}.{name}", rx, "n") for name, rx in fields.items()}


def _compile_task_lines(mid: str, items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ProfileError(f"{mid}.task_lines: expected a non-empty list")
    out: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        where = f"{mid}.task_lines[{i}]"
        if not isinstance(item, dict):
            raise ProfileError(f"{where}: expected an object")
        _check_keys(where, item, {"line", "fields"})
        out.append({
            "line": _compile(f"{where}.line", item.get("line"), None),
            "fields": _compile_fields(mid, f"{where}.fields", item.get("fields")),
        })
    return out


def _as_object(mid: str, entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ProfileError(f"{mid}: expected an object")
    return entry


def _check_keys(mid: str, entry: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(entry) - allowed)
    if unknown:
        raise ProfileError(f"{mid}: unknown key '{unknown[0]}'")


def _compile_regexes(
    mid: str,
    entry: dict[str, Any],
    required: dict[str, tuple[str, ...]],
    optional: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, groups in {**required, **optional}.items():
        if key in entry:
            out[key] = _compile(f"{mid}.{key}", entry[key], groups)
        elif key in required:
            raise ProfileError(f"{mid}: missing '{key}'")
    return out


def _safe_rel(where: str, text: Any) -> str:
    if not isinstance(text, str) or not GLOB_RE.fullmatch(text):
        raise ProfileError(f"{where}: not an allowed path string")
    if text.startswith("/") or ".." in PurePosixPath(text).parts:
        raise ProfileError(f"{where}: must be relative and stay inside the source")
    return text


def _compile_m3(entry: Any) -> dict[str, Any]:
    entry = _as_object("M3", entry)
    _check_keys("M3", entry, {"path_glob", "attribute"})
    glob = _safe_rel("M3.path_glob", entry.get("path_glob"))
    pattern = entry.get("attribute")
    if not isinstance(pattern, str) or not PATTERN_RE.fullmatch(pattern) or pattern.startswith("-"):
        raise ProfileError("M3.attribute: expected a printable ASCII pattern")
    return {"path_glob": glob, "attribute": pattern}


def _compile_m8(entry: Any, files: dict, folders: dict) -> dict[str, Any]:
    entry = _as_object("M8", entry)
    _check_keys("M8", entry, {"folder", *RECORD_REQUIRED["M8"], *RECORD_OPTIONAL["M8"]})
    out: dict[str, Any] = {"folder": _role("M8", "folder", entry, folders)}
    out.update(_compile_regexes("M8", entry, RECORD_REQUIRED["M8"], RECORD_OPTIONAL["M8"]))
    return out


def _compile_m9(entry: Any, files: dict, folders: dict) -> dict[str, Any]:
    entry = _as_object("M9", entry)
    _check_keys("M9", entry, {"file", *RECORD_REQUIRED["M9"], *RECORD_OPTIONAL["M9"]})
    out: dict[str, Any] = {"file": _role("M9", "file", entry, files)}
    out.update(_compile_regexes("M9", entry, RECORD_REQUIRED["M9"], RECORD_OPTIONAL["M9"]))
    return out


def _compile_m12(entry: Any, files: dict, folders: dict) -> dict[str, Any]:
    entry = _as_object("M12", entry)
    _check_keys("M12", entry, {"commits", "file", *M12_VERSION_KEYS})
    out: dict[str, Any] = {"commits": False}
    if "commits" in entry:
        if not isinstance(entry["commits"], bool):
            raise ProfileError("M12.commits: expected true or false")
        out["commits"] = entry["commits"]
    if "file" in entry:
        out["file"] = _role("M12", "file", entry, files)
        out.update(_compile_regexes("M12", entry, M12_VERSION_KEYS, {}))
    elif any(key in entry for key in M12_VERSION_KEYS):
        raise ProfileError("M12: version regexes need a 'file'")
    if not out["commits"] and "file" not in out:
        raise ProfileError("M12: needs commits or a changelog file")
    return out


def _compile_m13(entry: Any, files: dict, folders: dict) -> dict[str, Any]:
    entry = _as_object("M13", entry)
    _check_keys("M13", entry, {"file", "tags", *RECORD_REQUIRED["M13"], *RECORD_OPTIONAL["M13"]})
    out: dict[str, Any] = {"file": _role("M13", "file", entry, files)}
    out.update(_compile_regexes("M13", entry, RECORD_REQUIRED["M13"], RECORD_OPTIONAL["M13"]))
    tags = entry.get("tags")
    if not isinstance(tags, dict) or not tags:
        raise ProfileError("M13: missing 'tags'")
    mapping: dict[str, str] = {}
    for label, letter in tags.items():
        if label not in TAG_LABELS:
            raise ProfileError("M13.tags: label must be E, M or H")
        if not isinstance(letter, str) or not letter:
            raise ProfileError("M13.tags: expected a non-empty tag string")
        mapping[label] = letter
    if len(set(mapping.values())) != len(mapping):
        raise ProfileError("M13.tags: two labels share one tag")
    out["tags"] = mapping
    return out


def _compile_folders(raw: Any, files: dict) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        raise ProfileError("profile 'folders' must be an object")
    out: dict[str, dict[str, Any]] = {}
    for role, entry in raw.items():
        if not ROLE_RE.fullmatch(role) or role in RESERVED_ROLES or role in files:
            raise ProfileError("profile 'folders' has an invalid or repeated role name")
        if not isinstance(entry, dict):
            raise ProfileError(f"folder '{role}': expected an object")
        _check_keys(f"folder '{role}'", entry, {"dir", "name", "skip"})
        out[role] = {
            "dir": _safe_rel(f"folder '{role}'.dir", entry.get("dir")),
            "name": _compile(f"folder '{role}'.name", entry.get("name"), "date"),
            "skip": _compile(f"folder '{role}'.skip", entry["skip"], None) if "skip" in entry else None,
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
    required = {"schema", "files", "metrics"}
    if not isinstance(data, dict) or not required <= set(data) or set(data) - required - {"folders"}:
        raise ProfileError("profile needs the keys schema, files, metrics (and may have folders)")
    if data["schema"] != SCHEMA:
        raise ProfileError(f"profile schema must be {SCHEMA}")
    files = data["files"]
    if not isinstance(files, dict) or not files:
        raise ProfileError("profile 'files' must map roles to paths")
    for role, rel in files.items():
        if not ROLE_RE.fullmatch(role) or role in RESERVED_ROLES:
            raise ProfileError("profile 'files' has an invalid role name")
        if not isinstance(rel, str) or not rel:
            raise ProfileError(f"profile file '{role}': expected a path string")
    folders = _compile_folders(data["folders"], files) if "folders" in data else {}
    metrics = data["metrics"]
    if not isinstance(metrics, dict):
        raise ProfileError("profile 'metrics' must be an object")
    compiled: dict[str, dict[str, Any]] = {}
    for mid, entry in metrics.items():
        if mid not in ALL_METRICS:
            raise ProfileError(f"unknown metric '{mid[:16]}'")
        if not entry:
            continue
        if mid in REQUIRED:
            compiled[mid] = _compile_metric(mid, entry)
            if compiled[mid]["file"] not in files:
                raise ProfileError(f"{mid}: role '{compiled[mid]['file']}' is not in 'files'")
        elif mid == "M3":
            compiled[mid] = _compile_m3(entry)
        elif mid == "M8":
            compiled[mid] = _compile_m8(entry, files, folders)
        elif mid == "M9":
            compiled[mid] = _compile_m9(entry, files, folders)
        elif mid == "M12":
            compiled[mid] = _compile_m12(entry, files, folders)
        else:
            compiled[mid] = _compile_m13(entry, files, folders)
    return Profile(files=dict(files), metrics=compiled, sha256=profile_hash(raw), folders=folders)


def load_profile(path: Path) -> Profile:
    try:
        raw = Path(path).read_bytes()
    except OSError:
        raise ProfileError("cannot read the profile file")
    return parse_profile(raw)
