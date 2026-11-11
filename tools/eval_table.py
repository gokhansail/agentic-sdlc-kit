"""Render the eval totals file into a marked block of a Markdown document (T-46f).

    python tools/eval_table.py --doc docs/eval-results.md eval/results/full-2.json

Only the text between `<!-- eval-table:start -->` and `<!-- eval-table:end -->` is rewritten;
the rest of the document stays byte for byte. The block holds a header line, table 1 (one row
per model and condition) and table 2 (correct of total per category). A second run on the same
inputs gives the same bytes. Exit 2 and nothing written when: the file cannot be read as JSON,
`schema` is not 2, `complete` is not true, a key is missing, or the markers are not exactly one pair.

Number formats (fixed): accuracy 3 decimals; cost total 3 decimals; cost per run 4 decimals;
duration per run in seconds, 1 decimal; turns per run 2 decimals; counts as integers.
Server tool calls are the calls whose name starts with `mcp__`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

START = "<!-- eval-table:start -->"
END = "<!-- eval-table:end -->"
SCHEMA = 2
CONDITION_ORDER = {"no-server": 0, "server": 1}

TOP_KEYS = ("schema", "label", "date", "cli_version", "git_commit", "git_dirty", "repeats",
            "settings", "complete", "groups")
GROUP_KEYS = ("model", "condition", "runs", "correct", "accuracy_mean", "accuracy_min",
              "accuracy_max", "by_category", "cost_usd", "cost_usd_per_run", "output_tokens",
              "duration_ms_per_run", "turns_per_run", "tool_calls_total", "tool_calls",
              "errors", "unparsed")


class TableError(ValueError):
    pass


def check(data: Any) -> None:
    if not isinstance(data, dict):
        raise TableError("the totals file is not a JSON object")
    if data.get("schema") != SCHEMA:
        raise TableError(f"schema is {data.get('schema')!r}, expected {SCHEMA}")
    if data.get("complete") is not True:
        raise TableError("the totals file is not complete")
    for key in TOP_KEYS:
        if key not in data:
            raise TableError(f"missing key: {key}")
    groups = data["groups"]
    if not isinstance(groups, list) or not groups:
        raise TableError("groups is empty or not a list")
    for i, group in enumerate(groups):
        if not isinstance(group, dict):
            raise TableError(f"group {i} is not an object")
        for key in GROUP_KEYS:
            if key not in group:
                raise TableError(f"missing key in group {i}: {key}")


def _value(v: Any) -> str:
    return str(v).lower() if isinstance(v, bool) else str(v)


def header_line(data: dict[str, Any]) -> str:
    settings = ", ".join(f"{k} {_value(v)}" for k, v in sorted(data["settings"].items()))
    return (f"Label {data['label']}; date {data['date']}; CLI {data['cli_version']}; "
            f"runner commit {str(data['git_commit'])[:12]}; git_dirty {_value(data['git_dirty'])}; "
            f"repeats {data['repeats']}; settings: {settings}.")


def _sorted_groups(data: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(data["groups"], key=lambda g: (g["model"], CONDITION_ORDER.get(g["condition"], 9), g["condition"]))


def _row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def table_one(data: dict[str, Any]) -> str:
    head = ["Model", "Condition", "Runs", "Correct", "Accuracy mean", "Accuracy min", "Accuracy max",
            "Errors", "Unparsed", "Cost USD", "Cost USD per run", "Output tokens",
            "Duration per run (s)", "Turns per run", "Tool calls", "Server tool calls", "Read calls"]
    lines = [_row(head), "|" + "---|" * len(head)]
    for g in _sorted_groups(data):
        calls = g["tool_calls"]
        server = sum(n for name, n in calls.items() if name.startswith("mcp__"))
        lines.append(_row([
            g["model"], g["condition"], str(g["runs"]), str(g["correct"]),
            f"{g['accuracy_mean']:.3f}", f"{g['accuracy_min']:.3f}", f"{g['accuracy_max']:.3f}",
            str(g["errors"]), str(g["unparsed"]),
            f"{g['cost_usd']:.3f}", f"{g['cost_usd_per_run']:.4f}", str(g["output_tokens"]),
            f"{g['duration_ms_per_run'] / 1000:.1f}", f"{g['turns_per_run']:.2f}",
            str(g["tool_calls_total"]), str(server), str(calls.get("Read", 0)),
        ]))
    return "\n".join(lines)


def table_two(data: dict[str, Any]) -> str:
    groups = _sorted_groups(data)
    cats = sorted({c for g in groups for c in g["by_category"]})
    lines = [_row(["Model", "Condition"] + cats), "|" + "---|" * (2 + len(cats))]
    for g in groups:
        cells = []
        for c in cats:
            cell = g["by_category"].get(c)
            cells.append(f"{cell['correct']} of {cell['total']}" if cell else "-")
        lines.append(_row([g["model"], g["condition"]] + cells))
    return "\n".join(lines)


def render_block(data: dict[str, Any]) -> str:
    return "\n\n".join([header_line(data), table_one(data), table_two(data)])


def rewrite(doc: str, block: str) -> str:
    if doc.count(START) != 1 or doc.count(END) != 1:
        raise TableError("the document needs exactly one start marker and one end marker")
    start, stop = doc.index(START), doc.index(END)
    if stop < start:
        raise TableError("the end marker comes before the start marker")
    eol = "\r\n" if "\r\n" in doc else "\n"
    return doc[: start + len(START)] + eol + block.replace("\n", eol) + eol + doc[stop:]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval_table.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--doc", required=True, help="Markdown file with the two marker lines")
    parser.add_argument("totals", help="eval totals JSON file (schema 2)")
    args = parser.parse_args(argv)
    try:
        try:
            data = json.loads(Path(args.totals).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise TableError("the totals file cannot be read as JSON")
        check(data)
        doc_path = Path(args.doc)
        try:
            doc = doc_path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            raise TableError("--doc cannot be read as UTF-8 text")
        new = rewrite(doc, render_block(data))
    except TableError as err:
        print(f"eval_table: {err}", file=sys.stderr)
        return 2
    if new != doc:
        doc_path.write_bytes(new.encode("utf-8"))
    print(f"eval_table: {doc_path.name} ({len(data['groups'])} groups)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
