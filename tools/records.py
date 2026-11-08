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
import stat
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # started as a script: make `tools` importable
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.scope_guard import PROJECT_FILE, backticked  # noqa: E402

MAX_BYTES = 2_000_000

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

_PLACEHOLDER = re.compile(r"^<[^<>]*>$")
_HASHES = re.compile(r" {0,3}#{1,6}(?=\s)")


class UnsafeFile(OSError):
    """A fixed file is a link out of the root, not a regular file, or too large. The text has no path."""


class TooLarge(UnsafeFile):
    """The file is larger than the limit given to `read_inside`."""


def read_inside(root: Path, rel: str, limit: int = MAX_BYTES) -> bytes:
    """The bytes of the file `rel` under `root`.

    FileNotFoundError when it is missing. UnsafeFile when it resolves outside the root (a link or
    junction), is not a regular file (a device name such as NUL, a folder) or is larger than `limit`.
    """
    base = Path(root).resolve()
    try:
        full = (base / rel).resolve()
        full.relative_to(base)
    except (OSError, ValueError):
        raise UnsafeFile("resolves outside the project root") from None
    if not stat.S_ISREG(full.stat().st_mode):
        raise UnsafeFile("is not a regular file")
    with open(full, "rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise TooLarge(f"is larger than {limit} bytes")
    return data


def _heading(line: str) -> str | None:
    """The heading text of a markdown heading line (level 1 to 6), else None. Linear time."""
    found = _HASHES.match(line)
    if found is None:
        return None
    return line[found.end():].strip().rstrip("#").strip()


def _item(line: str) -> tuple[str, str] | None:
    """(label, value) of a `- Label: value` line, else None. Linear time."""
    text = line.lstrip()
    if len(text) < 2 or text[0] not in "-*+" or not text[1].isspace():
        return None
    label, colon, value = text[1:].partition(":")
    label = label.strip()
    if not colon or not label or "`" in label:
        return None
    return label, value.strip()


def _key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def parse_records(text: str) -> dict[str, str]:
    """The record map for one project file text. Defaults fill what the text lacks."""
    found: dict[str, str] = {}
    inside = False
    for line in text.splitlines():
        heading = _heading(line)
        if heading is not None:
            inside = heading.lower() == "records"
            continue
        if not inside:
            continue
        item = _item(line)
        if item is None:
            continue
        key = _key(item[0])
        ticked = backticked(item[1])
        value = ticked[0].strip() if ticked else item[1]
        if key and value and not _PLACEHOLDER.match(value) and key not in found:
            found[key] = value
    out = dict(DEFAULTS)
    out.update(found)
    return out


def read_records(root: Path) -> dict[str, str]:
    """Record map for the project at `root`; template defaults when the file is missing, unsafe or too large."""
    try:
        text = read_inside(root, PROJECT_FILE).decode("utf-8-sig", errors="replace")
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
