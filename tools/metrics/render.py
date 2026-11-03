"""Render metric result files into a marked block of a Markdown document.

    python -m tools.metrics.render --doc FILE RESULT.json [RESULT.json ...]

Each RESULT is checked with the output validator, so a file that carries free
text is refused. Only the text between the two marker lines of the document is
rewritten; everything outside them is left byte for byte as it was. A missing
or repeated marker is refused. One table per metric; the columns are the source
(the result label) and the periods. Rendering the same inputs twice gives the
same document.

Small cells (DEC-025): a cell with fewer than 5 items shows counts and no rate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from . import inputs, output

REPO_ROOT = Path(__file__).resolve().parents[2]
BEGIN = "<!-- metrics:begin -->"
END = "<!-- metrics:end -->"
MIN_ITEMS = 5
PERIOD_ORDER = ("v1", "v2", "undated")
TITLES = {
    "M1": "Reverted versions",
    "M2": "Versions marked to be tested",
    "M3": "Test attributes at the last commit of the last week",
    "M5": "Review rounds per task",
    "M6": "Tasks with questions back and with out-of-scope files",
    "M8": "Audit findings",
    "M9": "Decisions with an outcome filled",
    "M12": "Commits and versions per ISO week",
    "M13": "Tasks by size tag",
}


class RenderError(ValueError):
    pass


def percent(count: int, total: int) -> str:
    """Whole percent, halves rounded up, integer arithmetic only."""
    return f"{(200 * count + total) // (2 * total)}%"


def share(count: int, total: int) -> str:
    """'count of total', with a percentage when total reaches the small-cell limit."""
    text = f"{count} of {total}"
    return f"{text} ({percent(count, total)})" if total >= MIN_ITEMS else text


def per_week(count: int, weeks: int) -> str:
    """Two decimals, halves rounded up."""
    hundredths = (200 * count + weeks) // (2 * weeks) if weeks else 0
    return f"{hundredths // 100}.{hundredths % 100:02d}"


def _table(cell: dict[str, int], keys: Sequence[str]) -> str:
    return ", ".join(f"{key} {cell.get(key, 0)}" for key in keys)


def _m1(c: dict[str, Any]) -> str:
    return f"{share(c['count'], c['n'])}; item reverts {c['items']}"


def _m2(c: dict[str, Any]) -> str:
    return f"{share(c['count'], c['n'])}; no change {c['no_change']}"


def _m3(c: dict[str, Any]) -> str:
    last = max(c["weeks"])
    return f"{c['count']} in {last}; {c['n']} weeks"


def _m5(c: dict[str, Any]) -> str:
    parts = []
    for bucket in ("0", "1", "2", "3+"):
        number = c["distribution"][bucket]
        text = f"{bucket}: {number}"
        parts.append(f"{text} ({percent(number, c['n'])})" if c["n"] >= MIN_ITEMS else text)
    return f"{'; '.join(parts)}; n {c['n']}"


def _m6(c: dict[str, Any]) -> str:
    parts = []
    for key, label in (("questions_back", "questions back"), ("out_of_scope", "out of scope")):
        sub = c[key]
        parts.append(f"{label} {share(sub['count'], sub['n'])}" if sub["n"] else f"{label} n 0")
    return "; ".join(parts)


def _m8(c: dict[str, Any]) -> str:
    return (
        f"{c['n']} findings; severity {_table(c['severity'], ('critical', 'high', 'medium', 'low', 'unrated'))}"
        f"; latest {_table(c['latest'], ('closed', 'partial', 'open', 'deferred', 'none'))}"
        f"; days to closed {_table(c['days_to_closed'], ('0', '1-3', '4-7', '8+'))}"
    )


def _m9(c: dict[str, Any]) -> str:
    return share(c["count"], c["n"])


def _m12(c: dict[str, Any]) -> str:
    parts = []
    for key, label in (("count", "commits"), ("versions", "versions")):
        if key not in c:
            continue
        number = c[key]
        # The rate needs 5 items of that kind and of the cell as a whole.
        rate = f" ({per_week(number, c['weeks'])} per week)" if c["n"] >= MIN_ITEMS and number >= MIN_ITEMS and c["weeks"] else ""
        parts.append(f"{label} {number}{rate}")
    return f"{'; '.join(parts)}; {c['weeks']} weeks"


def _m13(c: dict[str, Any]) -> str:
    dist = c["distribution"]
    hard = f"hard {share(dist['H'], c['n'])}"
    return f"{hard}; E {dist['E']}, M {dist['M']}, H {dist['H']}; done {c['done']}"


FORMATTERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "M1": _m1, "M2": _m2, "M3": _m3, "M5": _m5, "M6": _m6, "M8": _m8,
    "M9": _m9, "M12": _m12, "M13": _m13,
}


def items_in(cell: dict[str, Any] | None) -> int:
    """Items in a period cell: its n, or the sum of the n of its sub-cells (M6)."""
    if not cell:
        return 0
    if "n" in cell:
        return cell["n"]
    return sum(sub.get("n", 0) for sub in cell.values() if isinstance(sub, dict))


def _cell_text(mid: str, entry: dict[str, Any], period: str) -> str:
    if entry.get("status") != "ok":
        return "no data"
    cell = entry.get(period)
    if cell is None:
        return "-"
    return FORMATTERS[mid](cell) if items_in(cell) else "no items"


def _metric_sort_key(mid: str) -> int:
    return int(mid[1:])


def render_block(results: Sequence[dict[str, Any]]) -> str:
    labels = [r["label"] for r in results]
    if len(set(labels)) != len(labels):
        raise RenderError("two result files carry the same label")
    ids = sorted({mid for r in results for mid in r["metrics"]}, key=_metric_sort_key)
    blocks = []
    for mid in ids:
        if mid not in FORMATTERS:
            raise RenderError(f"no table layout for metric {mid}")
        entries = {r["label"]: r["metrics"].get(mid, {"status": "no data"}) for r in results}
        periods = [
            p for p in PERIOD_ORDER
            if p in ("v1", "v2") or any(items_in(e.get(p)) for e in entries.values())
        ]
        lines = [
            f"{mid}: {TITLES[mid]}",
            "",
            "| Source | " + " | ".join(periods) + " |",
            "|---|" + "---|" * len(periods),
        ]
        for label in labels:
            cells = [_cell_text(mid, entries[label], p) for p in periods]
            lines.append(f"| {label} | " + " | ".join(cells) + " |")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def rewrite(doc: str, block: str) -> str:
    """Replace the text between the markers; refuse a missing or repeated marker."""
    if doc.count(BEGIN) != 1 or doc.count(END) != 1:
        raise RenderError("the document needs exactly one begin marker and one end marker")
    start = doc.index(BEGIN)
    stop = doc.index(END)
    if stop < start:
        raise RenderError("the end marker comes before the begin marker")
    eol = "\r\n" if "\r\n" in doc else "\n"
    body = block.replace("\n", eol)
    return doc[: start + len(BEGIN)] + eol + body + eol + doc[stop:]


def load_result(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="ascii"))
    except (OSError, ValueError):
        raise RenderError("a result file cannot be read as JSON")
    try:
        output.validate_result(data)
    except output.OutputError as err:
        raise RenderError(str(err))
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.metrics.render", description=__doc__.split("\n\n")[0])
    parser.add_argument("--doc", required=True, help="Markdown file with the two marker lines")
    parser.add_argument("results", nargs="+", help="result JSON files, in the column order wanted")
    return parser


def main(argv: Sequence[str] | None = None, root: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    base = (root or REPO_ROOT).resolve()
    try:
        doc_path = inputs.resolve_inside(base, Path.cwd() / args.doc, "--doc", allow_absolute=True)
        paths = [inputs.resolve_inside(base, Path.cwd() / p, "result file", allow_absolute=True) for p in args.results]
        results = [load_result(p) for p in paths]
        try:
            doc = doc_path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            raise RenderError("--doc cannot be read as UTF-8 text")
        new = rewrite(doc, render_block(results))
    except (inputs.InputError, RenderError) as err:
        print(f"render: {err}", file=sys.stderr)
        return 2
    if new != doc:
        doc_path.write_bytes(new.encode("utf-8"))
    print(f"render: {doc_path.relative_to(base).as_posix()} ({len(results)} sources)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
