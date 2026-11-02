"""Text metrics M1, M2, M5, M6, counted from the folded record files.

Each metric returns {"status": "no data"} or {"status": "ok", "v1", "v2",
"undated"}. A period cell with no items holds {"n": 0} only: a rate over nothing
is not written as 0.

M1  reverted versions: version-level revert headings / all version headings;
    item-level reverts are a separate count (DEC-028).
M2  versions still marked to be tested / all version headings; headings with
    the no-change marker are counted apart.
M5  distribution of review rounds 0, 1, 2, 3+ over per-task metric lines.
M6  share of tasks with questions back >= 1, and with out-of-scope files >= 1,
    each over the tasks that carry that field.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Mapping

from .fold import folded_lines
from .profile import Profile
from .records import PERIODS, assign_periods, scan_metric_lines, scan_versions

NO_DATA = {"status": "no data"}
BUCKETS = ("0", "1", "2", "3+")


def _bucket(rounds: int) -> str:
    return "3+" if rounds >= 3 else str(rounds)


def _finish(cells: dict[str, dict[str, Any]], total: Callable[[dict[str, Any]], int]) -> dict[str, Any]:
    if sum(total(c) for c in cells.values()) == 0:
        return dict(NO_DATA)
    out: dict[str, Any] = {"status": "ok"}
    for period in PERIODS:
        out[period] = cells[period]
    return out


def _empty_n(cell: dict[str, Any]) -> dict[str, Any]:
    return cell if cell["n"] > 0 else {"n": 0}


def m1(lines: list[str], cfg: dict[str, Any]) -> tuple[dict[str, Any], Counter]:
    warnings: Counter = Counter()
    cells = {p: {"n": 0, "count": 0, "items": 0} for p in PERIODS}
    versions = scan_versions(lines, cfg)
    for version, period in zip(versions, assign_periods([v.day for v in versions])):
        if period == "undated":
            warnings["m1_undated_heading"] += 1
        cell = cells[period]
        cell["n"] += 1
        cell["count"] += int(version.reverted)
        cell["items"] += version.item_reverts
    cells = {p: _empty_n(c) for p, c in cells.items()}
    return _finish(cells, lambda c: c["n"]), warnings


def m2(lines: list[str], cfg: dict[str, Any]) -> tuple[dict[str, Any], Counter]:
    warnings: Counter = Counter()
    cells = {p: {"n": 0, "count": 0, "no_change": 0} for p in PERIODS}
    pending, no_change = cfg["to_be_tested"], cfg.get("no_change")
    versions = scan_versions(lines, cfg)
    for version, period in zip(versions, assign_periods([v.day for v in versions])):
        if period == "undated":
            warnings["m2_undated_heading"] += 1
        cell = cells[period]
        cell["n"] += 1
        status = version.status or ""
        cell["count"] += int(bool(pending.search(status)))
        cell["no_change"] += int(bool(no_change and no_change.search(status)))
    cells = {p: _empty_n(c) for p, c in cells.items()}
    return _finish(cells, lambda c: c["n"]), warnings


def m5(lines: list[str], cfg: dict[str, Any]) -> tuple[dict[str, Any], Counter]:
    rows, warnings = scan_metric_lines(lines, cfg, "M5")
    cells = {p: {"n": 0, "distribution": {b: 0 for b in BUCKETS}} for p in PERIODS}
    for row in rows:
        rounds = row.values.get("review_rounds")
        if rounds is None:
            continue
        cell = cells[row.period]
        cell["n"] += 1
        cell["distribution"][_bucket(rounds)] += 1
    cells = {p: _empty_n(c) for p, c in cells.items()}
    return _finish(cells, lambda c: c["n"]), warnings


def m6(lines: list[str], cfg: dict[str, Any]) -> tuple[dict[str, Any], Counter]:
    rows, warnings = scan_metric_lines(lines, cfg, "M6")
    names = ("questions_back", "out_of_scope")
    cells = {p: {k: {"n": 0, "count": 0} for k in names} for p in PERIODS}
    for row in rows:
        for name in names:
            value = row.values.get(name)
            if value is None:
                continue
            sub = cells[row.period][name]
            sub["n"] += 1
            sub["count"] += int(value >= 1)
    cells = {p: {k: _empty_n(sub) for k, sub in c.items()} for p, c in cells.items()}
    return _finish(cells, lambda c: sum(sub["n"] for sub in c.values())), warnings


METRICS: dict[str, Callable[[list[str], dict[str, Any]], tuple[dict[str, Any], Counter]]] = {
    "M1": m1,
    "M2": m2,
    "M5": m5,
    "M6": m6,
}


def compute(profile: Profile, texts: Mapping[str, str | None]) -> tuple[dict[str, Any], Counter]:
    """Return ({metric id: result}, warnings). A missing file or empty entry is "no data"."""
    results: dict[str, Any] = {}
    warnings: Counter = Counter()
    folded: dict[str, list[str]] = {}
    for mid, fn in METRICS.items():
        cfg = profile.metrics.get(mid)
        text = texts.get(cfg["file"]) if cfg else None
        if cfg is None or text is None:
            results[mid] = dict(NO_DATA)
            continue
        if cfg["file"] not in folded:
            folded[cfg["file"]] = folded_lines(text)
        result, found = fn(folded[cfg["file"]], cfg)
        results[mid] = result
        warnings.update(found)
    return results, warnings
