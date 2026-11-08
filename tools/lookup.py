"""Readers for the decision, lesson, audit, task and log records (T-42, DEC-050).

Standard library and `tools` only. Each public function takes the project root, reads one record
through the record map of `.sdlc/project.md` (`tools.records`) and returns a plain dict. Nothing is
written. The MCP server wraps these functions; `python tools/lookup.py --root <folder> <record>`
prints the same dict as JSON.

Record paths come from the map and are checked here: the path must sit inside the root after
`..`, separators, drive letters and case are resolved (the guard's `relative_to_root`) and after
the path is resolved on disk (a link pointing outside is refused). A refused or missing path gives
an answer with an `error` text and no items.

Limits (T-44). A record file or report is read in full only up to MAX_BYTES (2 MB); a larger or
non-regular file gives an `error` answer. An audits folder with more than AUDIT_ENTRIES (200)
entries gives an `error` answer; one call reads at most AUDIT_TOTAL_BYTES of reports and counts the
rest as unreadable. A report with more than REPORT_FINDINGS findings or rows is unreadable. An
answer is cut to ANSWER_LIMIT characters of JSON by dropping trailing entries (`truncated` is true).

Entry shapes. Headings of level 2 and 3 open an entry; a heading of level 1 to 3 ends one. A
field is a line at the start of the line that reads `- Label: value`; indented lines after it
belong to the value.
- decisions: `## DEC-001 Title`, fields `Date` (first date in the value), `Outcome`.
- lessons: `### YYYY-MM-DD - title` or `## title` with a `Date` field; fields Problem, Cause,
  Fix, Lesson. The format example (`YYYY-MM-DD` or `<...>` in the title) is counted as a template.
- tasks: `### [x] T-41 [H] Title` blocks with a `Result` field, and `- [x] T-41 [H] text` list
  lines (used for tasks that have no block); `## NOW NEXT` is returned as text.
- log: `## YYYY-MM-DD (N) - title`.
- audits: one report per `YYYY-MM-DD_name.md` in the folder. `### P-1 Title` is a finding with a
  `Severity` field. A table row whose first cell starts with an ID and whose last cell starts with
  OPEN, CLOSED, PARTIAL or DEFERRED is a re-verify row: it links to the latest other report on or
  before its date that has the finding, and the latest row wins. Rows with other status words
  (PASS, ...) are check rows and are not read. The verdict line is the first line under a
  `Verdict` heading, or a `Gate verdict:` line.

A heading that opens an entry but cannot be read (no ID, no valid date, a report file with no date
in its name) is counted in `unreadable` and named in `unreadable_headings`, never dropped.
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterator, NamedTuple, Sequence

if __package__ in (None, ""):  # started as a script: make `tools` importable
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.records import TooLarge, read_inside, read_records  # noqa: E402
from tools.scope_guard import relative_to_root  # noqa: E402

ID_LIMIT = 40
QUERY_LIMIT = 100
ITEM_LIMIT = 100
LOG_MIN, LOG_MAX = 1, 20
TEXT_LIMIT = 4000  # one field or one log entry
SHORT_LIMIT = 160  # a result line in a task list
TITLE_LIMIT = 200
FIELD_LIMIT = 30  # fields of one entry in an answer
ANSWER_LIMIT = 150_000  # characters of JSON text in one answer; trailing entries are dropped past it
MAX_BYTES = 2_000_000  # one record file, one report
AUDIT_ENTRIES = 200  # entries in the audits folder
AUDIT_TOTAL_BYTES = 10_000_000  # all reports of one call
REPORT_FINDINGS = 1000  # findings, and again re-verify rows, in one report
NAMED_HEADINGS = 10
STATUSES = ("open", "closed", "partial", "deferred")
SEVERITIES = ("critical", "high", "medium", "low")


class RecordPathError(ValueError):
    """A record path from the map is not allowed. The message does not repeat the path."""


# --- arguments ---------------------------------------------------------------------------

_ID_KEY = re.compile(r"^([A-Za-z]+)-0*(\d+)([A-Za-z]*)$")
_ID_TOKEN = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]+)-(\d+)(?![A-Za-z0-9])")


def _id_key(text: str) -> tuple[str, int, str] | None:
    hit = _ID_KEY.match(text.strip())
    return (hit.group(1).upper(), int(hit.group(2)), hit.group(3).lower()) if hit else None


def check_id(value: object, example: str = "DEC-12") -> tuple[str, int, str] | None:
    """The comparable key of an ID argument; None when it is empty. ValueError for a bad one."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if not isinstance(value, str):
        raise ValueError(f"id: must be text such as {example}")
    if len(value.strip()) > ID_LIMIT:
        raise ValueError(f"id: at most {ID_LIMIT} characters")
    key = _id_key(value)
    if key is None:
        raise ValueError(f"id: must look like {example} (letters, a hyphen, digits)")
    return key


def check_text(value: object, name: str) -> str | None:
    """A trimmed free-text argument (`query`, `report`); None when empty."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name}: must be text")
    value = value.strip()
    if len(value) > QUERY_LIMIT:
        raise ValueError(f"{name}: at most {QUERY_LIMIT} characters")
    return value or None


def check_status(value: object) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    allowed = (*STATUSES, "none")
    if not isinstance(value, str) or value.strip().lower() not in allowed:
        raise ValueError("status: must be one of " + ", ".join(allowed))
    return value.strip().lower()


def check_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not LOG_MIN <= value <= LOG_MAX:
        raise ValueError(f"count: must be a whole number from {LOG_MIN} to {LOG_MAX}")
    return value


# --- reading a record --------------------------------------------------------------------

def resolve_in_root(root: Path, raw: object, casefold: bool | None = None) -> Path:
    """The absolute path for a map entry; RecordPathError when it leaves the root."""
    fold = (os.name == "nt") if casefold is None else casefold
    base = Path(root).resolve()
    if not isinstance(raw, str) or not raw.strip() or "\0" in raw:
        raise RecordPathError("the record path is not usable")
    rel = relative_to_root(str(base), raw.strip(), fold)
    if rel is None:
        raise RecordPathError("the record path is outside the project root")
    try:
        full = (base / rel).resolve()
        full.relative_to(base)
    except (OSError, ValueError):
        raise RecordPathError("the record path resolves outside the project root") from None
    return full


def _source(root: Path, key: str, casefold: bool | None) -> tuple[Path | None, str, str]:
    """(path, name relative to the root, error) for one record-map key."""
    base = Path(root).resolve()
    try:
        full = resolve_in_root(base, read_records(base).get(key, ""), casefold)
    except RecordPathError as exc:
        return None, "", f"{key}: {exc}"
    return full, full.relative_to(base).as_posix(), ""


def _read_file(root: Path, key: str, casefold: bool | None) -> tuple[str, str, str]:
    """(name, text, error) of the file the map names for `key`."""
    path, name, error = _source(root, key, casefold)
    if path is None:
        return "", "", error
    try:
        data = read_inside(Path(root).resolve(), name, MAX_BYTES)
    except FileNotFoundError:
        return name, "", f"the {key} file does not exist"
    except TooLarge:
        return name, "", f"the {key} file is larger than {MAX_BYTES} bytes"
    except OSError:  # a folder, a device name, a link out of the root, no permission
        return name, "", f"the {key} file could not be read"
    return name, data.decode("utf-8-sig", errors="replace"), ""


# --- parsing helpers ----------------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,3})[ \t]+(.+)$")  # the title is stripped by the caller; a lazy trailing-blank pattern is quadratic
_FENCE = re.compile(r"^ {0,3}(```|~~~)")
_FIELD = re.compile(r"^[-*][ \t]+([A-Za-z][A-Za-z0-9 _/'-]{0,40}?):(?:[ \t]+(.*)|[ \t]*)$")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_PLACEHOLDER = re.compile(r"^<[^<>]*>$")


class Section(NamedTuple):
    level: int
    title: str
    body: list[str]
    line: int


def _lines(text: str) -> Iterator[tuple[int, str, bool]]:
    """(line number, text, inside a code fence) for each line."""
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        mark = _FENCE.match(line)
        if mark:
            if fence is None:
                fence = mark.group(1)
            elif fence == mark.group(1):
                fence = None
            yield number, line, True
            continue
        yield number, line, fence is not None


def sections(text: str) -> list[Section]:
    """Headings of level 1 to 3 with the lines under each; headings in code fences are text."""
    out: list[tuple[int, str, list[str], int]] = []
    for number, line, fenced in _lines(text):
        head = None if fenced else _HEADING.match(line)
        if head:
            out.append((len(head.group(1)), head.group(2).strip(), [], number))
        elif out:
            out[-1][2].append(line)
    return [Section(*item) for item in out]


def _entries(text: str) -> list[Section]:
    return [s for s in sections(text) if s.level in (2, 3)]


def parse_fields(body: Sequence[str]) -> dict[str, str]:
    """`- Label: value` lines at the start of a line; the first line with a label wins."""
    out: dict[str, str] = {}
    label: str | None = None
    parts: list[str] = []

    def flush() -> None:
        if label is not None and label not in out:
            out[label] = "\n".join(p for p in parts if p).strip()

    for line in body:
        hit = _FIELD.match(line)
        if hit:
            flush()
            label, parts = hit.group(1).strip(), [(hit.group(2) or "").strip()]
        elif label is not None and line.strip() and line[:1] in " \t":
            parts.append(line.strip())
        else:
            flush()
            label, parts = None, []
    flush()
    return out


def _get(fields: dict[str, str], name: str) -> str:
    for label, value in fields.items():
        if label.lower() == name:
            return value
    return ""


def _has(fields: dict[str, str], *names: str) -> bool:
    return any(label.lower() in names for label in fields)


def _valid_date(text: str) -> str | None:
    """The first YYYY-MM-DD in `text` when it is a real date."""
    hit = _DATE.search(text)
    if not hit:
        return None
    try:
        date.fromisoformat(hit.group(0))
    except ValueError:
        return None
    return hit.group(0)


def _clip(text: str, limit: int = TEXT_LIMIT) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[: limit - 3].rstrip() + "...", True


def _matches(query: str | None, text: str) -> bool:
    """True when every word of the query is in the text (case-insensitive)."""
    if not query:
        return True
    low = text.lower()
    return all(word in low for word in query.lower().split())


def _text_of(section: Section) -> str:
    return section.title + "\n" + "\n".join(section.body)


def _cap(items: list[Any]) -> tuple[list[Any], bool]:
    return items[:ITEM_LIMIT], len(items) > ITEM_LIMIT


def _title(text: str) -> str:
    return _clip(text.strip(), TITLE_LIMIT)[0]


def _clipped_fields(fields: dict[str, str]) -> tuple[dict[str, str], bool]:
    """At most FIELD_LIMIT fields, each cut to TEXT_LIMIT; True when anything was cut or dropped."""
    pairs = list(fields.items())
    cut = len(pairs) > FIELD_LIMIT
    out: dict[str, str] = {}
    for label, value in pairs[:FIELD_LIMIT]:
        out[label], was_cut = _clip(value)
        cut = cut or was_cut
    return out, cut


def _fit(out: dict[str, Any], key: str) -> dict[str, Any]:
    """Drop trailing entries of `out[key]` until the answer is at most ANSWER_LIMIT characters of JSON."""
    rows = out[key]
    total = len(json.dumps(out)) - len(json.dumps(rows))
    keep = 0
    for row in rows:
        total += len(json.dumps(row)) + 2
        if total > ANSWER_LIMIT:
            break
        keep += 1
    if keep < len(rows):
        out[key] = rows[:keep]
        out["truncated"] = True
    return out


def _bad(headings: list[str]) -> dict[str, Any]:
    return {"unreadable": len(headings),
            "unreadable_headings": [_clip(h, 80)[0] for h in headings[:NAMED_HEADINGS]]}


def _head(source: str, error: str) -> dict[str, Any]:
    return {"source": source, "error": error}


def _empty(source: str, error: str, **extra: Any) -> dict[str, Any]:
    out = _head(source, error)
    out.update(extra)
    out.update({"total": 0, **_bad([]), "matched": 0, "truncated": False, "items": []})
    return out


# --- decisions ---------------------------------------------------------------------------

_DEC_HEAD = re.compile(r"^([A-Za-z]{1,20}-\d{1,9})(?:[ \t]+(.*))?$")


def parse_decisions(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """(entries in file order, headings that open an entry but cannot be read)."""
    entries: list[dict[str, Any]] = []
    bad: list[str] = []
    for sec in _entries(text):
        fields = parse_fields(sec.body)
        head = _DEC_HEAD.match(sec.title)
        day = _valid_date(_get(fields, "date"))
        if head is None:
            if _has(fields, "date", "decision", "options", "outcome"):
                bad.append(sec.title)
            continue
        if day is None:
            bad.append(sec.title)
            continue
        outcome = _get(fields, "outcome")
        full = _text_of(sec)
        entries.append({
            "id": head.group(1), "key": _id_key(head.group(1)), "title": _title(head.group(2) or ""),
            "date": day, "outcome_filled": bool(outcome) and not _PLACEHOLDER.match(outcome),
            "fields": fields, "text": full,
            "mentions": {(p.upper(), int(n), "") for p, n in _ID_TOKEN.findall(full)},
        })
    named: dict[Any, list[int]] = {}  # ID key -> positions of the entries that mention it, ascending
    for position, entry in enumerate(entries):
        for key in entry["mentions"]:
            named.setdefault(key, []).append(position)
    for position, entry in enumerate(entries):
        later = named.get(entry["key"], [])
        first = bisect.bisect_right(later, position)
        entry["named_by"] = [entries[i]["id"] for i in later[first:first + ITEM_LIMIT]]
    return entries, bad


def _decision_item(entry: dict[str, Any], detail: bool) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": entry["id"], "title": entry["title"], "date": entry["date"],
        "outcome_filled": entry["outcome_filled"], "named_by": entry["named_by"],
    }
    if detail:
        item["fields"], item["cut"] = _clipped_fields(entry["fields"])
    return item


def decisions(root: Path, id: object = None, query: object = None, casefold: bool | None = None) -> dict[str, Any]:
    """One decision by ID (all its fields), or the list filtered by a query. Reads only."""
    key = check_id(id, "DEC-12")
    words = check_text(query, "query")
    name, text, error = _read_file(root, "decisions", casefold)
    extra = {"id": id.strip() if key and isinstance(id, str) else None, "query": words}
    if error:
        return _empty(name, error, **extra)
    entries, bad = parse_decisions(text)
    hits = [e for e in entries if (key is None or e["key"] == key) and _matches(words, e["text"])]
    shown, truncated = _cap(hits)
    out = _head(name, "")
    out.update(extra)
    out.update({"total": len(entries), **_bad(bad), "matched": len(hits), "truncated": truncated,
                "items": [_decision_item(e, key is not None) for e in shown]})
    return _fit(out, "items")


# --- lessons -----------------------------------------------------------------------------

_LESSON_HEAD = re.compile(r"^(\d{4}-\d{2}-\d{2})[ \t]*[-–—:][ \t]*(.+)$")


def parse_lessons(text: str) -> tuple[list[dict[str, Any]], list[str], int]:
    """(entries, unreadable headings, format examples skipped)."""
    entries: list[dict[str, Any]] = []
    bad: list[str] = []
    templates = 0
    for sec in _entries(text):
        fields = parse_fields(sec.body)
        if sec.title.upper().startswith("YYYY-MM-DD") or sec.title.startswith("<"):
            templates += 1
            continue
        head = _LESSON_HEAD.match(sec.title)
        dated = re.match(r"^\d{4}-\d{2}-\d{2}\b", sec.title)
        if not (head or dated or _has(fields, "date", "problem", "cause", "fix", "lesson", "project")):
            continue  # a section heading, not an entry
        day = _valid_date(head.group(1)) if head else (None if dated else _valid_date(_get(fields, "date")))
        if day is None:
            bad.append(sec.title)
            continue
        entries.append({"title": _title(head.group(2) if head else sec.title), "date": day,
                        "fields": fields, "text": _text_of(sec)})
    return entries, bad, templates


def lessons(root: Path, query: object = None, casefold: bool | None = None) -> dict[str, Any]:
    """Lesson entries (title, date, fields), filtered by a query. Reads only."""
    words = check_text(query, "query")
    name, text, error = _read_file(root, "lessons", casefold)
    if error:
        return _empty(name, error, query=words, template_entries=0)
    entries, bad, templates = parse_lessons(text)
    hits = [e for e in entries if _matches(words, e["text"])]
    shown, truncated = _cap(hits)
    items = []
    for entry in shown:
        fields, cut = _clipped_fields(entry["fields"])
        items.append({"title": entry["title"], "date": entry["date"], "fields": fields, "cut": cut})
    out = _head(name, "")
    out.update({"query": words, "template_entries": templates, "total": len(entries), **_bad(bad),
                "matched": len(hits), "truncated": truncated, "items": items})
    return _fit(out, "items")


# --- tasks -------------------------------------------------------------------------------

_BOX = re.compile(r"^\[([ xX])\][ \t]+(.*)$")
_TASK_REST = re.compile(r"^([A-Za-z]{1,20}-\d{1,9}[A-Za-z]{0,5})(?![A-Za-z0-9])[ \t]*(?:\[([A-Za-z])\])?[ \t]*(.*)$")
_LIST_LINE = re.compile(r"^[-*][ \t]+(\[[ xX]\][ \t]+.*)$")


def _task_item(box: re.Match[str], line: int, result: str, kind: str) -> dict[str, Any] | None:
    rest = _TASK_REST.match(box.group(2))
    if rest is None:
        return None
    return {"id": rest.group(1), "key": _id_key(rest.group(1)), "size": (rest.group(2) or "").upper(),
            "done": box.group(1) in "xX", "title": _title(rest.group(3)), "result": result,
            "kind": kind, "line": line}


def parse_tasks(text: str) -> tuple[list[dict[str, Any]], list[str], str]:
    """(tasks in file order, unreadable headings, the NOW NEXT text)."""
    found: list[dict[str, Any]] = []
    bad: list[str] = []
    now_next = ""
    for sec in sections(text):
        if sec.level == 2 and sec.title.strip().lower() == "now next":
            now_next = "\n".join(sec.body).strip()
        if sec.level not in (2, 3):
            continue
        box = _BOX.match(sec.title)
        if box is None:
            continue
        item = _task_item(box, sec.line, _get(parse_fields(sec.body), "result"), "block")
        if item is None:
            bad.append(sec.title)
        else:
            found.append(item)
    blocked = {t["key"] for t in found}
    seen: set[Any] = set()
    for number, line, fenced in _lines(text):
        hit = None if fenced else _LIST_LINE.match(line)
        box = _BOX.match(hit.group(1)) if hit else None
        if box is None:
            continue
        item = _task_item(box, number, "", "list")
        if item is None:
            bad.append(hit.group(1) if hit else line)
        elif item["key"] not in blocked and item["key"] not in seen:
            seen.add(item["key"])
            found.append(item)
    found.sort(key=lambda t: t["line"])
    return found, bad, now_next


def tasks(root: Path, id: object = None, casefold: bool | None = None) -> dict[str, Any]:
    """Tasks (ID, size tag, done or open, title, result line) and the NOW NEXT text. Reads only."""
    key = check_id(id, "T-42")
    name, text, error = _read_file(root, "tasks", casefold)
    extra = {"id": id.strip() if key and isinstance(id, str) else None}
    if error:
        return _empty(name, error, **extra, now_next="", now_next_cut=False)
    found, bad, now_next = parse_tasks(text)
    hits = [t for t in found if key is None or t["key"] == key]
    shown, truncated = _cap(hits)
    items = []
    for task in shown:
        result, cut = _clip(task["result"], TEXT_LIMIT if key else SHORT_LIMIT)
        items.append({"id": task["id"], "size": task["size"], "done": task["done"], "title": task["title"],
                      "result": result, "cut": cut})
    note, note_cut = _clip(now_next)
    out = _head(name, "")
    out.update(extra)
    out.update({"now_next": note, "now_next_cut": note_cut, "total": len(found), **_bad(bad),
                "matched": len(hits), "truncated": truncated, "items": items})
    return _fit(out, "items")


# --- log ---------------------------------------------------------------------------------

_LOG_HEAD = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[ \t]*\((\d{1,9})\))?[ \t]*[-–—][ \t]*(.+)$")


def parse_log(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """(entries in file order, headings that are not `YYYY-MM-DD (N) - title`)."""
    entries: list[dict[str, Any]] = []
    bad: list[str] = []
    for sec in _entries(text):
        head = _LOG_HEAD.match(sec.title)
        day = _valid_date(head.group(1)) if head else None
        if head is None or day is None:
            bad.append(sec.title)
            continue
        entries.append({"date": day, "n": int(head.group(2) or 0), "title": _title(head.group(3)),
                        "text": "\n".join(sec.body).strip()})
    return entries, bad


def log(root: Path, count: object = 5, casefold: bool | None = None) -> dict[str, Any]:
    """The newest `count` (1 to 20) log entries, newest first. Reads only."""
    wanted = check_count(count)
    name, text, error = _read_file(root, "log", casefold)
    if error:
        return _empty(name, error, count=wanted)
    entries, bad = parse_log(text)
    newest = sorted(entries, key=lambda e: (e["date"], e["n"]), reverse=True)
    items = []
    for entry in newest[:wanted]:
        body, cut = _clip(entry["text"])
        items.append({"date": entry["date"], "n": entry["n"], "title": entry["title"], "text": body, "cut": cut})
    out = _head(name, "")
    out.update({"count": wanted, "total": len(entries), **_bad(bad), "matched": len(entries),
                "truncated": len(entries) > wanted, "items": items})
    return _fit(out, "items")


# --- audit findings ----------------------------------------------------------------------

_FINDING_HEAD = re.compile(r"^([A-Za-z]{1,20}-\d{1,9})[ \t]+(.+)$")
_ROW_ID = re.compile(r"^([A-Za-z]{1,20}-\d{1,9})(?![A-Za-z0-9])")
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_VERDICT_HEAD = re.compile(r"^(?:\d+\.\s*)?verdict(?:\s+line)?$", re.IGNORECASE)
_GATE_VERDICT = re.compile(r"^gate verdict:\s*(.*)$", re.IGNORECASE)
_FILE_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _row(line: str) -> tuple[str, str, str] | None:
    """(ID, claim, status word) of a re-verify row, else None."""
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    cells = [c.strip() for c in _CELL_SPLIT.split(stripped)[1:-1]]
    if len(cells) < 2:
        return None
    ident = _ROW_ID.match(cells[0])
    words = re.split(r"[\s,.;:(]+", cells[-1].strip("*` "))
    word = words[0].lower() if words else ""
    if ident is None or word not in STATUSES:
        return None
    return ident.group(1), cells[1] if len(cells) > 2 else "", word.upper()


def parse_report(name: str, text: str) -> dict[str, Any] | None:
    """One audit or re-verify report; None when the file name has no valid date or the report has more
    than REPORT_FINDINGS findings or rows."""
    stamp = _FILE_DATE.match(name)
    day = _valid_date(stamp.group(0)) if stamp else None
    if day is None:
        return None
    found: list[dict[str, Any]] = []
    bad: list[str] = []
    verdict = ""
    for sec in _entries(text):
        if sec.level == 2 and _VERDICT_HEAD.match(sec.title) and not verdict:
            verdict = next((ln.strip() for ln in sec.body if ln.strip()), "")
        head = _FINDING_HEAD.match(sec.title) if sec.level == 3 else None
        fields = parse_fields(sec.body)
        if head:
            word = (_get(fields, "severity").split() or [""])[0].strip("*`.,;:").lower()
            found.append({"id": head.group(1), "key": _id_key(head.group(1)), "title": _title(head.group(2)),
                          "severity": word if word in SEVERITIES else "unrated"})
        elif _has(fields, "severity"):
            bad.append(sec.title)
    rows: list[dict[str, Any]] = []
    for _number, line, fenced in _lines(text):
        got = None if fenced else _row(line)
        if got:
            rows.append({"id": got[0], "key": _id_key(got[0]), "claim": got[1], "status": got[2]})
        elif not verdict and not fenced and _GATE_VERDICT.match(line.strip()):
            verdict = line.strip()
    if len(found) > REPORT_FINDINGS or len(rows) > REPORT_FINDINGS:
        return None
    return {"name": name, "date": day, "verdict": _clip(verdict, 300)[0], "findings": found, "rows": rows, "bad": bad}


def findings(root: Path, status: object = None, report: object = None, casefold: bool | None = None) -> dict[str, Any]:
    """Findings per audit report with re-verify rows and the latest status of each. Reads only."""
    want = check_status(status)
    part = check_text(report, "report")
    extra = {"status": want, "report": part}
    base = Path(root).resolve()
    folder, name, error = _source(base, "audits", casefold)
    if folder is None:
        return _empty(name, error, **extra, reports=[], unlinked_rows=0)
    try:
        files = _report_files(folder)
    except FileNotFoundError:
        return _empty(name, "the audits folder does not exist", **extra, reports=[], unlinked_rows=0)
    except OSError:
        return _empty(name, "the audits folder could not be read", **extra, reports=[], unlinked_rows=0)
    if files is None:
        return _empty(name, f"the audits folder holds more than {AUDIT_ENTRIES} entries", **extra,
                      reports=[], unlinked_rows=0)
    reports: list[dict[str, Any]] = []
    bad: list[str] = []
    spent = 0
    for path in files:
        raw = None
        room = min(MAX_BYTES, AUDIT_TOTAL_BYTES - spent)
        if room > 0:
            try:
                data = read_inside(base, f"{name}/{path.name}", room)
                spent += len(data)
                raw = data.decode("utf-8-sig", errors="replace")
            except OSError:  # a link out of the root, a folder, too large, or the call's byte budget is used up
                raw = None
        parsed = parse_report(path.name, raw) if raw is not None else None
        if parsed is None:
            bad.append(path.name)
            continue
        bad.extend(parsed["bad"])
        reports.append(parsed)
    latest, unlinked = _link_rows(reports)
    shown: list[dict[str, Any]] = []
    matched = 0
    for rep in reports:
        if part and part.lower() not in rep["name"].lower():
            continue
        found = [{"id": f["id"], "title": f["title"], "severity": f["severity"],
                  "status": latest.get((rep["name"], f["key"]), "none")} for f in rep["findings"]]
        rows = [{"id": r["id"], "status": r["status"], "claim": _clip(r["claim"], 300)[0],
                 "finding_report": r["linked"]} for r in rep["rows"]]
        if want:
            found = [f for f in found if f["status"].lower() == want]
            rows = [r for r in rows if r["status"].lower() == want]
            if not found and not rows:
                continue
        matched += len(found) + len(rows)
        room = ITEM_LIMIT - sum(len(s["findings"]) + len(s["rows"]) for s in shown)
        if room <= 0:
            continue
        found, rows = found[:room], rows[: max(room - len(found[:room]), 0)]
        shown.append({"report": rep["name"], "date": rep["date"], "verdict": rep["verdict"],
                      "findings": found, "rows": rows})
    out = _head(name, "")
    out.update(extra)
    out.update({"total": len(reports), **_bad(bad), "unlinked_rows": unlinked, "matched": matched,
                "truncated": matched > sum(len(s["findings"]) + len(s["rows"]) for s in shown),
                "reports": shown})
    return _fit(out, "reports")


def _report_files(folder: Path) -> list[Path] | None:
    """The `.md` files of the folder in name order; None when the folder holds more than AUDIT_ENTRIES entries."""
    files: list[Path] = []
    seen = 0
    with os.scandir(folder) as entries:
        for entry in entries:
            seen += 1
            if seen > AUDIT_ENTRIES:
                return None
            if entry.name.lower().endswith(".md") and entry.is_file():
                files.append(Path(entry.path))
    return sorted(files)


def _link_rows(reports: list[dict[str, Any]]) -> tuple[dict[tuple[str, Any], str], int]:
    """Latest status per (report name, finding key), and how many rows found no finding."""
    where: dict[Any, set[tuple[str, str]]] = {}  # a set: many findings with one ID in one report count once
    for rep in reports:
        for f in rep["findings"]:
            where.setdefault(f["key"], set()).add((rep["date"], rep["name"]))
    events: dict[tuple[str, Any], list[tuple[str, str, int, str]]] = {}
    unlinked = 0
    seq = 0
    for rep in reports:
        for row in rep["rows"]:
            seq += 1
            options = [w for w in where.get(row["key"], []) if w[0] <= rep["date"] and w[1] != rep["name"]]
            if not options:
                row["linked"] = ""
                unlinked += 1
                continue
            target = max(options)
            row["linked"] = target[1]
            events.setdefault((target[1], row["key"]), []).append((rep["date"], rep["name"], seq, row["status"]))
    return {k: max(v)[3] for k, v in events.items()}, unlinked


# --- command line ------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lookup", description="Read decisions, lessons, findings, tasks and the log.")
    parser.add_argument("--root", default=".", help="project folder (default: the current folder)")
    sub = parser.add_subparsers(dest="record", required=True)
    p = sub.add_parser("decisions")
    p.add_argument("--id")
    p.add_argument("--query")
    p = sub.add_parser("lessons")
    p.add_argument("--query")
    p = sub.add_parser("findings")
    p.add_argument("--status")
    p.add_argument("--report")
    p = sub.add_parser("tasks")
    p.add_argument("--id")
    p = sub.add_parser("log")
    p.add_argument("--count", type=int, default=5)
    args = parser.parse_args(argv)
    root = Path(args.root)
    try:
        if args.record == "decisions":
            answer = decisions(root, args.id, args.query)
        elif args.record == "lessons":
            answer = lessons(root, args.query)
        elif args.record == "findings":
            answer = findings(root, args.status, args.report)
        elif args.record == "tasks":
            answer = tasks(root, args.id)
        else:
            answer = log(root, args.count)
    except ValueError as exc:
        sys.stderr.write(f"lookup: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(answer, indent=2) + "\n")
    return 1 if answer["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
