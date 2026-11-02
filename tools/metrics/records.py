"""Record scanning shared by the text metrics: periods, version headings, metric lines.

Periods: v1 is before the cutoff, v2 from it. A version heading without a date
takes the period of its nearest dated neighbours (before and after it in file
order) when both agree; otherwise it goes to "undated".
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any, Sequence

CUTOFF = date(2026, 10, 25)
PERIODS = ("v1", "v2", "undated")

# A level 1 or 2 markdown heading ends the current section or entry.
_HEADING = re.compile(r"#{1,2}\s")
_PAREN = re.compile(r"\([^()]*\)")


def to_date(text: str | None) -> date | None:
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def period_of(day: date) -> str:
    return "v1" if day < CUTOFF else "v2"


def assign_periods(days: Sequence[date | None]) -> list[str]:
    known = [period_of(d) if d is not None else None for d in days]
    out: list[str] = []
    for i, period in enumerate(known):
        if period is not None:
            out.append(period)
            continue
        before = next((known[j] for j in range(i - 1, -1, -1) if known[j] is not None), None)
        after = next((known[j] for j in range(i + 1, len(known)) if known[j] is not None), None)
        out.append(before if before is not None and before == after else "undated")
    return out


def strip_parentheses(line: str) -> str:
    """Remove parenthesised text, innermost first, so notes after a number are ignored."""
    previous = None
    while previous != line:
        previous = line
        line = _PAREN.sub("", line)
    return line


@dataclass
class Version:
    day: date | None
    reverted: bool
    status: str | None
    item_reverts: int = 0


def scan_versions(lines: Sequence[str], cfg: dict[str, Any]) -> list[Version]:
    versions: list[Version] = []
    current: Version | None = None
    revert_version = cfg.get("revert_version")
    revert_item = cfg.get("revert_item")
    status_rx = cfg.get("status")
    for line in lines:
        if cfg["version_heading"].search(line):
            found = cfg["date"].search(line)
            day = to_date(found.group("date")) if found else None
            status = None
            if status_rx is not None:
                st = status_rx.search(line)
                status = st.group("status").strip() if st else None
            current = Version(
                day=day,
                reverted=bool(revert_version and revert_version.search(line)),
                status=status,
            )
            versions.append(current)
        elif _HEADING.match(line):
            current = None
        elif current is not None and revert_item is not None and revert_item.search(line):
            current.item_reverts += 1
    return versions


@dataclass
class MetricLine:
    period: str
    values: dict[str, int | None]


def scan_metric_lines(
    lines: Sequence[str], cfg: dict[str, Any], mid: str
) -> tuple[list[MetricLine], Counter]:
    """Per-task metric lines under dated entry headings.

    Session lines, lines with none of the metric's numbers and lines under an
    undated heading are reported in the returned warnings, never guessed.
    """
    tag = mid.lower()
    rows: list[MetricLine] = []
    warnings: Counter = Counter()
    session_rx = cfg.get("session_line")
    day: date | None = None
    for line in lines:
        if _HEADING.match(line):
            found = cfg["entry_heading"].search(line)
            day = to_date(found.group("date")) if found else None
            continue
        if session_rx is not None and session_rx.search(line):
            warnings[f"{tag}_session_line"] += 1
            continue
        if not cfg["task_line"].search(line):
            continue
        text = strip_parentheses(line)
        values: dict[str, int | None] = {}
        for name, rx in cfg["fields"].items():
            hit = rx.search(text)
            values[name] = int(hit.group("n")) if hit else None
        if all(v is None for v in values.values()):
            warnings[f"{tag}_line_without_number"] += 1
            continue
        for name, value in values.items():
            if value is None:
                warnings[f"{tag}_missing_{name}"] += 1
        if day is None:
            warnings[f"{tag}_undated_line"] += 1
            period = "undated"
        else:
            period = period_of(day)
        rows.append(MetricLine(period, values))
    return rows, warnings
