"""Deterministic JSON writer that refuses free text.

Published metric files may hold only fixed keys, numbers, booleans, null and a
few kinds of string: a status word, an ISO date, a label, a hex hash. Keys under
"metrics" are metric IDs, keys under "warnings" are names from a fixed list, keys
under "files" are role names. Anything else is refused before a byte is written,
so record text cannot reach a committed file. Refusal messages name the place,
never the value.

Output is sorted, ASCII, with a final newline and no timestamp, so a rerun on the
same input is byte-identical.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SCHEMA = 1
STATUS_WORDS = frozenset({"ok", "no data"})
WARNING_NAMES = frozenset(
    {
        "source_not_git",
        "record_file_missing",
        "m1_undated_heading",
        "m2_undated_heading",
        "m5_undated_line",
        "m5_session_line",
        "m5_line_without_number",
        "m6_undated_line",
        "m6_session_line",
        "m6_line_without_number",
        "m6_missing_questions_back",
        "m6_missing_out_of_scope",
        "record_folder_missing",
        "folder_file_skipped",
        "m8_file_without_date",
        "m8_duplicate_finding",
        "m8_unrated_finding",
        "m8_unknown_status",
        "m8_unlinked_row",
        "m9_entry_without_outcome",
        "m9_undated_entry",
        "m12_author_date_outside_span",
        "m12_undated_version",
        "m13_untagged_heading",
        "m13_unknown_tag",
    }
)
RESULT_KEYS = frozenset(
    {"schema", "label", "cutoff", "kit_commit", "input", "metrics", "warnings"}
)
INPUT_KEYS = frozenset({"head", "dirty", "files", "folders", "profile_sha256"})
MANIFEST_KEYS = frozenset(
    {"schema", "label", "kit_commit", "head", "dirty", "profile_sha256", "files", "folders", "warnings"}
)
METRIC_KEYS = frozenset({"status", "v1", "v2", "undated"})
CELL_KEYS = frozenset(
    {
        "n", "count", "items", "no_change", "distribution", "versions", "weeks", "done",
        "severity", "latest", "days_to_closed",
    }
)
FIELD_KEYS = frozenset({"questions_back", "out_of_scope"})
# Keys of the small count tables inside a cell. The distribution keys depend on the metric.
DISTRIBUTION_KEYS = {
    "M5": frozenset({"0", "1", "2", "3+"}),
    "M13": frozenset({"E", "M", "H"}),
}
SEVERITY_KEYS = frozenset({"critical", "high", "medium", "low", "unrated"})
LATEST_KEYS = frozenset({"closed", "partial", "open", "deferred", "none"})
DAY_KEYS = frozenset({"0", "1-3", "4-7", "8+"})

LABEL_RE = re.compile(r"[a-z0-9-]+")
ROLE_RE = re.compile(r"[a-z][a-z0-9_]{0,31}")
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")
WEEK_RE = re.compile(r"[0-9]{4}-W[0-9]{2}")
METRIC_ID_RE = re.compile(r"M[0-9]{1,2}")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
GIT_HASH_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class OutputError(ValueError):
    pass


def _refuse(where: str, why: str) -> OutputError:
    return OutputError(f"output refused at {where}: {why}")


def _int(value: Any, where: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _refuse(where, "expected a non-negative integer")


def _string(value: Any, where: str, rx: "re.Pattern[str]", allow_null: bool = False) -> None:
    if value is None and allow_null:
        return
    if not isinstance(value, str) or not rx.fullmatch(value):
        raise _refuse(where, "string is not an allowed fixed form")


def _object(value: Any, where: str) -> dict:
    if not isinstance(value, dict):
        raise _refuse(where, "expected an object")
    return value


def _check_keys(obj: dict, allowed: frozenset, where: str) -> None:
    for key in obj:
        if key not in allowed:
            raise _refuse(where, "key is not in the fixed schema")


def _count_table(value: Any, allowed: frozenset, where: str) -> None:
    table = _object(value, where)
    _check_keys(table, allowed, where)
    for key, number in table.items():
        _int(number, f"{where}.{key}")


def _check_cell(cell: Any, where: str, mid: str) -> None:
    cell = _object(cell, where)
    _check_keys(cell, CELL_KEYS | FIELD_KEYS, where)
    for key, value in cell.items():
        here = f"{where}.{key}"
        if key == "distribution":
            _count_table(value, DISTRIBUTION_KEYS.get(mid, frozenset()), here)
        elif key == "severity":
            _count_table(value, SEVERITY_KEYS, here)
        elif key == "latest":
            _count_table(value, LATEST_KEYS, here)
        elif key == "days_to_closed":
            _count_table(value, DAY_KEYS, here)
        elif key == "weeks" and isinstance(value, dict):
            weeks = _object(value, here)
            for week, number in weeks.items():
                if not WEEK_RE.fullmatch(week):
                    raise _refuse(here, "key is not an ISO week")
                _int(number, f"{here}.{week}")
        elif key in FIELD_KEYS:
            _check_cell(value, here, mid)
        else:
            _int(value, here)


def _check_metrics(metrics: Any) -> None:
    for mid, entry in _object(metrics, "metrics").items():
        if not METRIC_ID_RE.fullmatch(mid):
            raise _refuse("metrics", "key is not a metric ID")
        where = f"metrics.{mid}"
        entry = _object(entry, where)
        _check_keys(entry, METRIC_KEYS, where)
        if entry.get("status") not in STATUS_WORDS:
            raise _refuse(f"{where}.status", "not a fixed status word")
        for period in ("v1", "v2", "undated"):
            if period in entry:
                _check_cell(entry[period], f"{where}.{period}", mid)


def _check_warnings(warnings: Any) -> None:
    for name, count in _object(warnings, "warnings").items():
        if name not in WARNING_NAMES:
            raise _refuse("warnings", "name is not in the fixed list")
        _int(count, f"warnings.{name}")


def _check_files(files: Any, where: str) -> None:
    for role, digest in _object(files, where).items():
        if not ROLE_RE.fullmatch(role):
            raise _refuse(where, "key is not a role name")
        _string(digest, f"{where}.{role}", SHA256_RE, allow_null=True)


def _check_folders(folders: Any, where: str, listing: bool) -> None:
    """listing: manifest form {role: {name: {sha256, tracked}}}; else the summary form."""
    for role, entry in _object(folders, where).items():
        if not ROLE_RE.fullmatch(role):
            raise _refuse(where, "key is not a role name")
        here = f"{where}.{role}"
        entry = _object(entry, here)
        if listing:
            for name, info in entry.items():
                if not NAME_RE.fullmatch(name):
                    raise _refuse(here, "key is not a safe file name")
                info = _object(info, f"{here}.{name}")
                _check_keys(info, frozenset({"sha256", "tracked"}), f"{here}.{name}")
                _string(info.get("sha256"), f"{here}.{name}.sha256", SHA256_RE)
                if not isinstance(info.get("tracked"), bool):
                    raise _refuse(f"{here}.{name}.tracked", "expected a boolean")
        else:
            _check_keys(entry, frozenset({"files", "untracked", "sha256"}), here)
            _int(entry.get("files"), f"{here}.files")
            _int(entry.get("untracked"), f"{here}.untracked")
            _string(entry.get("sha256"), f"{here}.sha256", SHA256_RE)


def _check_common(obj: dict) -> None:
    if obj.get("schema") != SCHEMA:
        raise _refuse("schema", f"expected {SCHEMA}")
    _string(obj.get("label"), "label", LABEL_RE)
    _string(obj.get("kit_commit"), "kit_commit", GIT_HASH_RE, allow_null=True)
    _check_warnings(obj.get("warnings"))


def _check_state(state: dict, where: str) -> None:
    _string(state.get("head"), f"{where}head", GIT_HASH_RE, allow_null=True)
    if state.get("dirty") is not None and not isinstance(state.get("dirty"), bool):
        raise _refuse(f"{where}dirty", "expected a boolean or null")
    _string(state.get("profile_sha256"), f"{where}profile_sha256", SHA256_RE)
    _check_files(state.get("files"), f"{where}files")
    if "folders" in state:
        _check_folders(state["folders"], f"{where}folders", listing=where == "")


def validate_result(obj: Any) -> None:
    obj = _object(obj, "result")
    _check_keys(obj, RESULT_KEYS, "result")
    _check_common(obj)
    _string(obj.get("cutoff"), "cutoff", DATE_RE)
    state = _object(obj.get("input"), "input")
    _check_keys(state, INPUT_KEYS, "input")
    _check_state(state, "input.")
    _check_metrics(obj.get("metrics"))


def validate_manifest(obj: Any) -> None:
    obj = _object(obj, "manifest")
    _check_keys(obj, MANIFEST_KEYS, "manifest")
    _check_common(obj)
    _check_state(obj, "")


def dumps(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def write_json(path: Path, obj: Any, kind: str) -> None:
    """Validate, then write. kind is "result" or "manifest"."""
    if kind == "result":
        validate_result(obj)
    elif kind == "manifest":
        validate_manifest(obj)
    else:
        raise ValueError("kind must be 'result' or 'manifest'")
    data = dumps(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
