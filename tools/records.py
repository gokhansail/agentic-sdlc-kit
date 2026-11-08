"""Record names from the `## Records` section of `.sdlc/project.md`.

Standard library only. `read_records(root)` returns one dict: every key the template
names, filled from the project file when it has the line and from the template default
when it does not (no project file, no section, no line, or a placeholder in angle
brackets). Extra lines in the section are kept under their own key.

CLI: `python tools/records.py --root <folder>` or `python -m tools.records --root <folder>`
prints the dict as JSON.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # started as a script: make `tools` importable
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.scope_guard import _HEADING, PROJECT_FILE, backticked  # noqa: E402

# Keys and defaults follow templates/project.md.
DEFAULTS: dict[str, str] = {
    "status": "STATUS.md",
    "tasks": "TASKS.md",
    "log": "LOG.md",
    "decisions": "DECISIONS.md",
    "lessons": "LESSONS.md",
    "audits": "audits/",
    "changelog": "CHANGELOG.md",
    "developer_rules": "DEV_RULES.md",
    "report_language": "English",
}

_ITEM = re.compile(r"^\s*[-*+]\s+([^:`]+?)\s*:\s*(.*?)\s*$")
_PLACEHOLDER = re.compile(r"^<[^<>]*>$")


def _key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def parse_records(text: str) -> dict[str, str]:
    """The record map for one project file text. Defaults fill what the text lacks."""
    found: dict[str, str] = {}
    inside = False
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            inside = heading.group(1).strip().lower() == "records"
            continue
        if not inside:
            continue
        item = _ITEM.match(line)
        if not item:
            continue
        key = _key(item.group(1))
        ticked = backticked(item.group(2))
        value = ticked[0].strip() if ticked else item.group(2).strip()
        if key and value and not _PLACEHOLDER.match(value) and key not in found:
            found[key] = value
    out = dict(DEFAULTS)
    out.update(found)
    return out


def read_records(root: Path) -> dict[str, str]:
    """Record map for the project at `root`; template defaults when the file is missing."""
    try:
        text = (root / PROJECT_FILE).read_bytes().decode("utf-8-sig", errors="replace")
    except OSError:
        return dict(DEFAULTS)
    return parse_records(text)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="records")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    json.dump(read_records(Path(args.root)), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
