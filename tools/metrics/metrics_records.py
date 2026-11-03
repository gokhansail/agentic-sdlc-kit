"""Record metrics M8, M9, M13, counted from folded record files.

Each metric returns {"status": "no data"} or {"status": "ok", <period>: cell}.
A period cell with no items holds {"n": 0} only.

M8   audit findings. One report per file of the folder; the report date comes
     from the file name. A finding is a heading with an ID; its severity is in
     the heading or in the first severity line before the next heading. The key
     is report date + ID. A table row with an ID is a re-verify row: it links to
     the latest other report on or before its date that has that ID. Status is
     the first word of the status cell. Per period: severity counts, the status
     of each finding's latest row (`none` when never re-verified), and the days
     from the report to the first CLOSED row, in four buckets.
M9   decisions with an outcome filled / decisions with an outcome field.
M13  tasks by size tag (E, M, H) and how many are done; period by done date.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Mapping

from .fold import fold, folded_lines
from .profile import Profile
from .records import PERIODS, period_of, to_date

NO_DATA = {"status": "no data"}
SEVERITIES = ("critical", "high", "medium", "low")
STATUSES = ("closed", "partial", "open", "deferred")
DAY_BUCKETS = ("0", "1-3", "4-7", "8+")
TAGS = ("E", "M", "H")
# A heading of level 1 to 3 ends the current finding, entry or task body.
_HEADING = re.compile(r"#{1,3}\s")


def _cell_or_empty(cell: dict[str, Any]) -> dict[str, Any]:
    return cell if cell["n"] > 0 else {"n": 0}


def _finish(cells: dict[str, dict[str, Any]], periods: tuple[str, ...]) -> dict[str, Any]:
    if sum(cells[p]["n"] for p in periods) == 0:
        return dict(NO_DATA)
    return {"status": "ok", **{p: cells[p] for p in periods}}


# --- M8 -------------------------------------------------------------------

@dataclass
class Finding:
    day: date
    severity: str | None
    events: list[tuple[date, str, int, str]] = field(default_factory=list)  # day, file, seq, status


def _bucket_days(days: int) -> str:
    if days <= 0:
        return "0"
    return "1-3" if days <= 3 else "4-7" if days <= 7 else "8+"


def m8(reports: Mapping[str, str], folder: Mapping[str, Any], cfg: Mapping[str, Any]) -> tuple[dict[str, Any], Counter]:
    warnings: Counter = Counter()
    heading_rx, row_rx = cfg["finding_heading"], cfg["table_row"]
    severity_rx = cfg.get("severity_line")
    findings: dict[tuple[date, str], Finding] = {}
    index: dict[str, list[tuple[date, str]]] = {}
    rows: list[tuple[date, str, int, str, str]] = []  # day, file, seq, id, status
    seq = 0
    for name in sorted(reports):
        hit = folder["name"].search(fold(name))
        day = to_date(hit.group("date")) if hit else None
        if day is None:
            warnings["m8_file_without_date"] += 1
            continue
        lines = folded_lines(reports[name])
        for i, line in enumerate(lines):
            heading = heading_rx.search(line)
            if heading:
                fid = heading.group("id")
                if (day, fid) in findings:
                    warnings["m8_duplicate_finding"] += 1
                    continue
                severity = heading.group("severity") if "severity" in heading_rx.groupindex else None
                if not severity and severity_rx is not None:
                    for later in lines[i + 1:]:
                        if _HEADING.match(later):
                            break
                        found = severity_rx.search(later)
                        if found:
                            severity = found.group("severity")
                            break
                if severity not in SEVERITIES:
                    severity = None
                    warnings["m8_unrated_finding"] += 1
                findings[(day, fid)] = Finding(day, severity)
                index.setdefault(fid, []).append((day, name))
                continue
            row = row_rx.search(line)
            if row:
                seq += 1
                words = row.group("status").split()
                rows.append((day, name, seq, row.group("id"), words[0] if words else ""))
    for day, name, order, fid, status in rows:
        if status not in STATUSES:
            warnings["m8_unknown_status"] += 1
            continue
        candidates = [c for c in index.get(fid, []) if c[0] <= day and c[1] != name]
        if not candidates:
            warnings["m8_unlinked_row"] += 1
            continue
        report_day, _ = max(candidates)
        findings[(report_day, fid)].events.append((day, name, order, status))

    cells = {
        p: {
            "n": 0,
            "severity": {s: 0 for s in (*SEVERITIES, "unrated")},
            "latest": {s: 0 for s in (*STATUSES, "none")},
            "days_to_closed": {b: 0 for b in DAY_BUCKETS},
        }
        for p in PERIODS[:2]
    }
    for finding in findings.values():
        cell = cells[period_of(finding.day)]
        cell["n"] += 1
        cell["severity"][finding.severity or "unrated"] += 1
        events = sorted(finding.events)
        cell["latest"][events[-1][3] if events else "none"] += 1
        closed = next((e for e in events if e[3] == "closed"), None)
        if closed is not None:
            cell["days_to_closed"][_bucket_days((closed[0] - finding.day).days)] += 1
    cells = {p: _cell_or_empty(c) for p, c in cells.items()}
    return _finish(cells, PERIODS[:2]), warnings


# --- M9 -------------------------------------------------------------------

def m9(lines: list[str], cfg: Mapping[str, Any]) -> tuple[dict[str, Any], Counter]:
    warnings: Counter = Counter()
    entry_rx, outcome_rx, empty_rx = cfg["entry_heading"], cfg["outcome"], cfg["empty"]
    date_rx = cfg.get("date_line")
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines:
        start = entry_rx.search(line)
        if start:
            day = None
            if "date" in entry_rx.groupindex and start.group("date"):
                day = to_date(start.group("date"))
            current = {"day": day, "value": None}
            entries.append(current)
            continue
        if _HEADING.match(line):
            current = None
            continue
        if current is None:
            continue
        if current["day"] is None and date_rx is not None:
            found = date_rx.search(line)
            if found:
                current["day"] = to_date(found.group("date"))
        if current["value"] is None:
            found = outcome_rx.search(line)
            if found:
                current["value"] = found.group("value").strip()
    cells = {p: {"n": 0, "count": 0} for p in PERIODS}
    for entry in entries:
        if entry["value"] is None:
            warnings["m9_entry_without_outcome"] += 1
            continue
        if entry["day"] is None:
            warnings["m9_undated_entry"] += 1
            period = "undated"
        else:
            period = period_of(entry["day"])
        cell = cells[period]
        cell["n"] += 1
        cell["count"] += int(bool(entry["value"]) and not empty_rx.search(entry["value"]))
    cells = {p: _cell_or_empty(c) for p, c in cells.items()}
    return _finish(cells, PERIODS), warnings


# --- M13 ------------------------------------------------------------------

def m13(lines: list[str], cfg: Mapping[str, Any]) -> tuple[dict[str, Any], Counter]:
    warnings: Counter = Counter()
    by_letter = {letter: label for label, letter in cfg["tags"].items()}
    done_rx, body_rx = cfg.get("done_date"), cfg.get("done_date_body")
    tasks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines:
        head = cfg["heading"].search(line)
        if head:
            tag = cfg["tag"].search(line)
            label = by_letter.get(tag.group("tag")) if tag else None
            if tag is None:
                warnings["m13_untagged_heading"] += 1
            elif label is None:
                warnings["m13_unknown_tag"] += 1
            done = head.group("done") == "x"
            day = None
            if done and done_rx is not None:
                found = done_rx.search(line)
                day = to_date(found.group("date")) if found else None
            current = {"label": label, "done": done, "day": day}
            if label is not None:
                tasks.append(current)
            continue
        if _HEADING.match(line):
            current = None
            continue
        if current and current["done"] and current["day"] is None and body_rx is not None:
            found = body_rx.search(line)
            if found:
                current["day"] = to_date(found.group("date"))
    cells = {p: {"n": 0, "distribution": {t: 0 for t in TAGS}, "done": 0} for p in PERIODS}
    for task in tasks:
        cell = cells[period_of(task["day"]) if task["day"] else "undated"]
        cell["n"] += 1
        cell["distribution"][task["label"]] += 1
        cell["done"] += int(task["done"])
    cells = {p: _cell_or_empty(c) for p, c in cells.items()}
    return _finish(cells, PERIODS), warnings


LINE_METRICS: dict[str, Callable[[list[str], Mapping[str, Any]], tuple[dict[str, Any], Counter]]] = {
    "M9": m9,
    "M13": m13,
}


def compute(
    profile: Profile, texts: Mapping[str, str | None], folders: Mapping[str, Mapping[str, str]]
) -> tuple[dict[str, Any], Counter]:
    """Return ({"M8", "M9", "M13": result}, warnings). Missing input is "no data"."""
    results: dict[str, Any] = {}
    warnings: Counter = Counter()
    cfg = profile.metrics.get("M8")
    reports = folders.get(cfg["folder"]) if cfg else None
    if cfg is None or not reports:
        results["M8"] = dict(NO_DATA)
    else:
        results["M8"], found = m8(reports, profile.folders[cfg["folder"]], cfg)
        warnings.update(found)
    for mid, fn in LINE_METRICS.items():
        cfg = profile.metrics.get(mid)
        text = texts.get(cfg["file"]) if cfg else None
        if cfg is None or text is None:
            results[mid] = dict(NO_DATA)
            continue
        results[mid], found = fn(folded_lines(text), cfg)
        warnings.update(found)
    return results, warnings
