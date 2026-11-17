"""Render bench totals files into a marked block of a Markdown document (T-57).

    python tools/bench_table.py --doc docs/bench-results.md bench/results/full-1.json [more.json ...]

Only the text between `<!-- bench-table:start -->` and `<!-- bench-table:end -->` is rewritten;
the rest of the document stays byte for byte. The block holds one header line per totals file,
table 1 (one row per file and arm) and table 2 (one row per file, task and arm). Files keep the
order given on the command line, arms run plain then kit, tasks follow `task_ids`. A second run
on the same inputs gives the same bytes. Exit 2 and nothing written when: a file cannot be read
as JSON, `schema` is not 1, `complete` is not true, a key is missing, or the markers are not
exactly one pair. The output holds numbers only: no verdict, ratio or category.

Number formats (fixed): counts as integers, written "n of total" where a total exists; cost total
and spent USD 3 decimals; cost per run 4 decimals; wall time per run in seconds, 1 decimal; turns
per run 2 decimals; kit commit 7 characters; bench hash 12 characters. `runs_with_test_changes`
may be absent in files written before T-59f: the cell shows `-`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

START = "<!-- bench-table:start -->"
END = "<!-- bench-table:end -->"
SCHEMA = 1
ARM_ORDER = {"plain": 0, "kit": 1}

TOP_KEYS = ("schema", "label", "date", "cli_version", "kit_commit", "bench_sha256", "planned_runs",
            "done_runs", "spent_usd", "complete", "task_ids", "arms", "tasks")
ARM_KEYS = ("runs", "full_pass", "hidden_passed", "hidden_total", "visible_ok", "runs_with_out_of_scope",
            "hidden_reads", "guard_deny", "subagents_spawned", "cost_usd", "cost_usd_per_run",
            "wall_s_per_run", "turns_per_run")
TASK_KEYS = ("runs", "full_pass", "hidden_passed", "hidden_total", "cost_usd_per_run")


class TableError(ValueError):
    pass


def check(data: Any, name: str) -> None:
    if not isinstance(data, dict):
        raise TableError(f"{name}: not a JSON object")
    if data.get("schema") != SCHEMA:
        raise TableError(f"{name}: schema is {data.get('schema')!r}, expected {SCHEMA}")
    if data.get("complete") is not True:
        raise TableError(f"{name}: the totals file is not complete")
    for key in TOP_KEYS:
        if key not in data:
            raise TableError(f"{name}: missing key: {key}")
    arms, tasks, task_ids = data["arms"], data["tasks"], data["task_ids"]
    if not isinstance(arms, dict) or not arms:
        raise TableError(f"{name}: arms is empty or not an object")
    if not isinstance(task_ids, list) or not isinstance(tasks, dict):
        raise TableError(f"{name}: task_ids or tasks has the wrong type")
    for arm, cell in arms.items():
        _check_cell(cell, ARM_KEYS, f"{name}: arm {arm}")
    for task in task_ids:
        per_arm = tasks.get(task)
        if not isinstance(per_arm, dict):
            raise TableError(f"{name}: missing key: tasks.{task}")
        for arm in arms:
            _check_cell(per_arm.get(arm), TASK_KEYS, f"{name}: task {task} arm {arm}")


def _check_cell(cell: Any, keys: Sequence[str], where: str) -> None:
    if not isinstance(cell, dict):
        raise TableError(f"{where}: missing")
    for key in keys:
        if key not in cell:
            raise TableError(f"{where}: missing key: {key}")


def _arms(data: dict[str, Any]) -> list[str]:
    return sorted(data["arms"], key=lambda a: (ARM_ORDER.get(a, 9), a))


def _row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def header_line(data: dict[str, Any]) -> str:
    return (f"Label {data['label']}; date {data['date']}; CLI {data['cli_version']}; "
            f"kit commit {str(data['kit_commit'])[:7]}; bench hash {str(data['bench_sha256'])[:12]}; "
            f"runs {data['done_runs']} of {data['planned_runs']}; spent USD {data['spent_usd']:.3f}.")


def table_one(files: Sequence[dict[str, Any]]) -> str:
    head = ["File", "Arm", "Full pass", "Hidden passed", "Visible green", "Runs with out-of-scope files",
            "Runs with test changes", "Hidden reads", "Guard denies", "Sub-agents spawned", "Cost USD",
            "Cost USD per run", "Wall per run (s)", "Turns per run"]
    lines = [_row(head), "|" + "---|" * len(head)]
    for data in files:
        for arm in _arms(data):
            a = data["arms"][arm]
            n = a["runs"]
            tests = f"{a['runs_with_test_changes']} of {n}" if "runs_with_test_changes" in a else "-"
            lines.append(_row([
                str(data["label"]), arm, f"{a['full_pass']} of {n}",
                f"{a['hidden_passed']} of {a['hidden_total']}", f"{a['visible_ok']} of {n}",
                f"{a['runs_with_out_of_scope']} of {n}", tests, str(a["hidden_reads"]),
                str(a["guard_deny"]), str(a["subagents_spawned"]),
                f"{a['cost_usd']:.3f}", f"{a['cost_usd_per_run']:.4f}",
                f"{a['wall_s_per_run']:.1f}", f"{a['turns_per_run']:.2f}",
            ]))
    return "\n".join(lines)


def table_two(files: Sequence[dict[str, Any]]) -> str:
    head = ["File", "Task", "Arm", "Full pass", "Hidden passed", "Cost USD per run"]
    lines = [_row(head), "|" + "---|" * len(head)]
    for data in files:
        for task in data["task_ids"]:
            for arm in _arms(data):
                c = data["tasks"][task][arm]
                lines.append(_row([
                    str(data["label"]), str(task), arm, f"{c['full_pass']} of {c['runs']}",
                    f"{c['hidden_passed']} of {c['hidden_total']}", f"{c['cost_usd_per_run']:.4f}",
                ]))
    return "\n".join(lines)


def render_block(files: Sequence[dict[str, Any]]) -> str:
    parts = [header_line(d) for d in files] + [table_one(files), table_two(files)]
    return "\n\n".join(parts)


def rewrite(doc: str, block: str) -> str:
    if doc.count(START) != 1 or doc.count(END) != 1:
        raise TableError("the document needs exactly one start marker and one end marker")
    start, stop = doc.index(START), doc.index(END)
    if stop < start:
        raise TableError("the end marker comes before the start marker")
    eol = "\r\n" if "\r\n" in doc else "\n"
    return doc[: start + len(START)] + eol + block.replace("\n", eol) + eol + doc[stop:]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bench_table.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--doc", required=True, help="Markdown file with the two marker lines")
    parser.add_argument("totals", nargs="+", help="bench totals JSON files (schema 1)")
    args = parser.parse_args(argv)
    try:
        files = []
        for path in args.totals:
            try:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                raise TableError(f"{Path(path).name}: cannot be read as JSON")
            check(data, Path(path).name)
            files.append(data)
        doc_path = Path(args.doc)
        try:
            doc = doc_path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            raise TableError("--doc cannot be read as UTF-8 text")
        new = rewrite(doc, render_block(files))
    except TableError as err:
        print(f"bench_table: {err}", file=sys.stderr)
        return 2
    if new != doc:
        doc_path.write_bytes(new.encode("utf-8"))
    print(f"bench_table: {doc_path.name} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
