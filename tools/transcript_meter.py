#!/usr/bin/env python3
"""Meter one bench arm from Claude Code transcripts: tokens, USD, time, human turns, writes (T-63).

Usage:
    python tools/transcript_meter.py --transcripts <dir> --effort-log <csv> --texts <json> --arm <label> \\
        --out <json> --raw-out <dir> [--model <id>] [--cost-state <file>] [--prices <json>]

Input: every `*.jsonl` under `--transcripts` (main sessions, resumed sessions and sub-agent files), the effort
log (columns and actions of plan section 6.3, rows of `--arm` only), the frozen texts and the price file
(default `bench/build/prices.json`). Read only.

What it counts:
- Each assistant `message.id` once across all files, keeping the line with the largest output tokens (one message
  is written over several lines). Lines with no id are counted one by one and reported.
- Tokens by type (input, cache write 5m, 1h, unsplit, cache read, output) per step, agent (`main` or
  `sub:<agent type>`) and model; USD at list price. A model without a price, or a message with fast speed, gives
  `usd: null` and is listed. A Haiku message over its prompt-token threshold uses the higher price row.
- Steps come from the effort log: a step owns the events from the end of the previous step (or the start of the
  log) to its own `end_step`, so a session launched before `paste_step` belongs to the step it starts. Wall
  minutes run from `paste_step` to `end_step`. Active minutes are summed per human turn: its timestamp to the
  last event before the next human turn. Maintainer minutes are the `minutes` of the `end_step` rows.
- Human turns of the main sessions (not tool results, not sub-agent prompts): matched verbatim, after whitespace
  normalisation, to `--texts` (a JSON object `{"<id>": {"type": "step|fix|answer|approval|resume", "text": "..."}}`;
  several texts pasted in one message match as the joined sequence). A slash command is `command`, anything else
  is `other` (a deviation, listed by hash).
- Sub-agents by type, compactions, session starts, Edit and Write calls by actor, writes into a `memory` folder.
  Shell writes cannot be attributed.

Output: `--out` holds numbers, labels and SHA-256 hashes only (`schema: 1`, sorted keys, no run timestamps, so a
second run is byte-equal). The raw per-message, per-turn and per-write tables go to `--raw-out`, which must be
outside this repository. Exit 2 and nothing written when an input is unreadable, the price file is missing or
invalid, the effort log or the texts file is bad, or `--raw-out` is inside the repository.

`--cost-state` reads the CLI's own per-model totals and prints them beside the meter's. Its field map is a guess
from key names seen in transcripts and is marked unverified in the code and the output until the dev test (T-67).
Standard library only; Python 3.10 or newer.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

KIT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRICES = KIT_ROOT / "bench" / "build" / "prices.json"
SCHEMA = 1
NO_STEP = "(none)"
ARM_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
EFFORT_COLUMNS = ("ts_start", "ts_end", "arm", "step", "action", "text_id", "count", "minutes", "note")
ACTIONS = ("setup", "login", "launch", "exit", "paste_step", "paste_answer", "paste_fix", "paste_resume",
           "permission_click", "typed_command", "score", "end_step", "wait_limit", "restart", "deviation")
TURN_TYPES = ("step", "fix", "answer", "approval", "resume")
TOKEN_KEYS = ("input", "cache_write_5m", "cache_write_1h", "cache_write_unsplit", "cache_read", "output")
PRICE_KEYS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
EVENT_TYPES = ("assistant", "user", "system", "attachment")
COMMAND_TAG_RE = re.compile(r"^\s*<command-(name|message)>")
SLASH_RE = re.compile(r"^/[A-Za-z][\w:.-]*(\s|$)")
MODEL_DATE_SUFFIX_RE = re.compile(r"-\d{8}$")
MILLION = Decimal(1_000_000)
USD_QUANT = Decimal("0.000001")
COST_STATE_FIELDS = {  # UNVERIFIED: key names seen in transcript cost-state lines; confirmed in the dev test (T-67)
    "input": ("inputTokens", "input_tokens"),
    "output": ("outputTokens", "output_tokens"),
    "cache_read": ("cacheReadInputTokens", "cache_read_input_tokens"),
    "cache_write": ("cacheCreationInputTokens", "cache_creation_input_tokens"),
    "usd": ("costUSD", "cost_usd", "usd"),
}


class MeterError(ValueError):
    pass


# ----------------------------------------------------------------------------------------------- basic readers

def read_bytes(path: Path, what: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        raise MeterError(f"{what} cannot be read")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path, what: str, **kwargs: Any) -> tuple[Any, str]:
    raw = read_bytes(path, what)
    try:
        return json.loads(raw.decode("utf-8-sig"), **kwargs), sha256(raw)
    except (UnicodeDecodeError, ValueError):
        raise MeterError(f"{what} is not valid JSON")


def parse_ts(value: Any) -> dt.datetime | None:
    """ISO 8601 to an aware UTC datetime; a time with no offset is taken as UTC."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text[-1] in "Zz":
        text = text[:-1] + "+00:00"
    text = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], text, count=1)
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def micros(delta: dt.timedelta) -> int:
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def minutes(us: int) -> float:
    return round(us / 60_000_000, 2)


def norm_text(text: str) -> str:
    return " ".join(text.split())


def quant(value: Decimal) -> float:
    return float(value.quantize(USD_QUANT))


# ----------------------------------------------------------------------------------------------- prices

@dataclass
class Prices:
    read_on: str
    sha256: str
    models: dict[str, dict[str, Any]]

    def find(self, model: str | None) -> dict[str, Any] | None:
        if not model:
            return None
        if model in self.models:
            return self.models[model]
        return self.models.get(MODEL_DATE_SUFFIX_RE.sub("", model))


def _price_row(row: Any, where: str) -> dict[str, Decimal]:
    if not isinstance(row, dict):
        raise MeterError(f"price file: {where} is not an object")
    out = {}
    for key in PRICE_KEYS:
        value = row.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)) or value < 0:
            raise MeterError(f"price file: {where}.{key} is missing or not a non-negative number")
        out[key] = Decimal(str(value))
    return out


def load_prices(path: Path) -> Prices:
    data, digest = read_json(path, "the price file", parse_float=Decimal)
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise MeterError(f"price file: schema must be {SCHEMA}")
    read_on = data.get("read_on")
    if not isinstance(read_on, str) or not read_on.strip():
        raise MeterError("price file: read_on (the date the prices were read) is missing")
    models = data.get("models")
    if not isinstance(models, dict) or not models:
        raise MeterError("price file: models is missing or empty")
    parsed: dict[str, dict[str, Any]] = {}
    for name, row in models.items():
        entry: dict[str, Any] = {"prices": _price_row(row, name)}
        long_ctx = row.get("long_context")
        if long_ctx is not None:
            threshold = long_ctx.get("threshold_prompt_tokens") if isinstance(long_ctx, dict) else None
            if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold <= 0:
                raise MeterError(f"price file: {name}.long_context.threshold_prompt_tokens is not a positive integer")
            entry["threshold"] = threshold
            entry["long_prices"] = _price_row(long_ctx.get("prices"), f"{name}.long_context.prices")
        parsed[name] = entry
    return Prices(read_on=read_on, sha256=digest, models=parsed)


def message_usd(tokens: dict[str, int], speed: str, entry: dict[str, Any] | None) -> Decimal | None:
    """USD of one message at list price; None when it needs a price that does not exist."""
    if not any(tokens.values()):
        return Decimal(0)
    if entry is None or speed == "fast":
        return None
    prices = entry["prices"]
    prompt = tokens["input"] + tokens["cache_read"] + tokens["cache_write_5m"] + tokens["cache_write_1h"] \
        + tokens["cache_write_unsplit"]
    if "threshold" in entry and prompt > entry["threshold"]:
        prices = entry["long_prices"]
    return (Decimal(tokens["input"]) * prices["input"]
            + Decimal(tokens["cache_write_5m"] + tokens["cache_write_unsplit"]) * prices["cache_write_5m"]
            + Decimal(tokens["cache_write_1h"]) * prices["cache_write_1h"]
            + Decimal(tokens["cache_read"]) * prices["cache_read"]
            + Decimal(tokens["output"]) * prices["output"]) / MILLION


# ----------------------------------------------------------------------------------------------- effort log, texts

@dataclass
class EffortRow:
    ts: dt.datetime
    arm: str
    step: str
    action: str
    count: int | None
    minutes: float | None


def load_effort(path: Path) -> tuple[list[EffortRow], str]:
    raw = read_bytes(path, "--effort-log")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise MeterError("--effort-log is not UTF-8 text")
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header is None:
        raise MeterError("--effort-log is empty")
    header = [h.strip() for h in header]
    if sorted(header) != sorted(EFFORT_COLUMNS):
        raise MeterError("--effort-log columns must be: " + ", ".join(EFFORT_COLUMNS))
    index = {name: i for i, name in enumerate(header)}
    rows: list[EffortRow] = []
    for number, record in enumerate(reader, start=2):
        if not any(cell.strip() for cell in record):
            continue
        if len(record) != len(header):
            raise MeterError(f"--effort-log row {number}: expected {len(header)} fields, got {len(record)}")

        def cell(name: str) -> str:
            return record[index[name]].strip()

        ts = parse_ts(cell("ts_start"))
        if ts is None:
            raise MeterError(f"--effort-log row {number}: ts_start is not an ISO 8601 time")
        if cell("ts_end") and parse_ts(cell("ts_end")) is None:
            raise MeterError(f"--effort-log row {number}: ts_end is not an ISO 8601 time")
        action = cell("action")
        if action not in ACTIONS:
            raise MeterError(f"--effort-log row {number}: unknown action {action!r}")
        count: int | None = None
        if cell("count"):
            try:
                count = int(cell("count"))
            except ValueError:
                raise MeterError(f"--effort-log row {number}: count is not an integer")
            if count < 0:
                raise MeterError(f"--effort-log row {number}: count is negative")
        spent: float | None = None
        if cell("minutes"):
            try:
                spent = float(cell("minutes"))
            except ValueError:
                raise MeterError(f"--effort-log row {number}: minutes is not a number")
            if spent < 0 or spent != spent:
                raise MeterError(f"--effort-log row {number}: minutes is negative")
        rows.append(EffortRow(ts, cell("arm"), cell("step"), action, count, spent))
    return rows, sha256(raw)


@dataclass
class Texts:
    types: dict[str, str]
    by_norm: list[tuple[str, str]]  # (normalised text, id) sorted by id
    sha256: str


def load_texts(path: Path) -> Texts:
    data, digest = read_json(path, "--texts")
    if not isinstance(data, dict) or not data:
        raise MeterError("--texts must be a non-empty JSON object of id to {type, text}")
    types: dict[str, str] = {}
    seen: dict[str, str] = {}
    for text_id in sorted(data):
        item = data[text_id]
        if not isinstance(item, dict) or item.get("type") not in TURN_TYPES or not isinstance(item.get("text"), str):
            raise MeterError(f"--texts: {text_id!r} needs a type ({', '.join(TURN_TYPES)}) and a text")
        flat = norm_text(item["text"])
        if not flat:
            raise MeterError(f"--texts: {text_id!r} has an empty text")
        if flat in seen:
            raise MeterError(f"--texts: {text_id!r} and {seen[flat]!r} have the same text after whitespace normalisation")
        seen[flat] = text_id
        types[text_id] = item["type"]
    return Texts(types, sorted(((t, i) for t, i in seen.items()), key=lambda pair: pair[1]), digest)


def match_texts(flat: str, texts: Texts) -> tuple[str, ...] | None:
    """The ids whose normalised texts, joined by single spaces, are exactly `flat` (one or several pasted)."""
    @lru_cache(maxsize=None)
    def walk(start: int) -> tuple[str, ...] | None:
        for text, text_id in texts.by_norm:
            if not flat.startswith(text, start):
                continue
            end = start + len(text)
            if end == len(flat):
                return (text_id,)
            if flat[end] == " ":
                rest = walk(end + 1)
                if rest is not None:
                    return (text_id,) + rest
        return None

    return walk(0) if flat else None


def classify_turn(text: str, texts: Texts) -> tuple[str, tuple[str, ...]]:
    flat = norm_text(text)
    ids = match_texts(flat, texts)
    if ids:
        kinds = {texts.types[i] for i in ids}
        if len(kinds) == 1:
            return kinds.pop(), ids
        return "other", ()
    if COMMAND_TAG_RE.match(text) or SLASH_RE.match(flat):
        return "command", ()
    return "other", ()


# ----------------------------------------------------------------------------------------------- transcripts

@dataclass
class Rec:
    rel: str
    number: int
    data: dict[str, Any]
    ts: dt.datetime | None
    sub: bool
    agent: str
    unit: str | None


def load_transcripts(root: Path) -> tuple[list[Rec], str, int]:
    if not root.is_dir():
        raise MeterError("--transcripts is not a folder")
    files = sorted((p for p in root.rglob("*.jsonl") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    if not files:
        raise MeterError("--transcripts holds no .jsonl file")
    recs: list[Rec] = []
    digests: list[str] = []
    for path in files:
        rel_parts = path.relative_to(root).parts
        rel = "/".join(rel_parts)
        raw = read_bytes(path, f"transcript {rel}")
        digests.append(f"{rel}:{sha256(raw)}")
        try:
            lines = raw.decode("utf-8-sig").splitlines()
        except UnicodeDecodeError:
            raise MeterError(f"transcript {rel} is not UTF-8 text")
        in_sub_dir = "subagents" in rel_parts[:-1]
        meta_type = _meta_agent_type(path) if in_sub_dir else ""
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except ValueError:
                raise MeterError(f"transcript {rel} line {number} is not valid JSON")
            if not isinstance(data, dict):
                raise MeterError(f"transcript {rel} line {number} is not a JSON object")
            sub = in_sub_dir or data.get("isSidechain") is True
            if sub:
                kind = meta_type or str(data.get("agentType") or data.get("agent_type") or "") or "unknown"
                agent = "sub:" + kind
                unit = str(data.get("agentId") or (path.stem if in_sub_dir else rel + "#sidechain"))
            else:
                agent, unit = "main", None
            recs.append(Rec(rel, number, data, parse_ts(data.get("timestamp")), sub, agent, unit))
    return recs, sha256("\n".join(digests).encode("utf-8")), len(files)


def _meta_agent_type(path: Path) -> str:
    try:
        meta = json.loads(path.with_name(path.stem + ".meta.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return ""
    value = meta.get("agentType") if isinstance(meta, dict) else None
    return value if isinstance(value, str) else ""


def parse_usage(usage: Any) -> dict[str, int] | None:
    if not isinstance(usage, dict):
        return None

    def num(value: Any) -> int:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    total_write = num(usage.get("cache_creation_input_tokens"))
    write_5m = write_1h = 0
    unsplit = total_write
    split = usage.get("cache_creation")
    if isinstance(split, dict) and ("ephemeral_5m_input_tokens" in split or "ephemeral_1h_input_tokens" in split):
        write_5m = num(split.get("ephemeral_5m_input_tokens"))
        write_1h = num(split.get("ephemeral_1h_input_tokens"))
        unsplit = max(total_write - write_5m - write_1h, 0)
    return {"input": num(usage.get("input_tokens")), "cache_write_5m": write_5m, "cache_write_1h": write_1h,
            "cache_write_unsplit": unsplit, "cache_read": num(usage.get("cache_read_input_tokens")),
            "output": num(usage.get("output_tokens"))}


def user_text(message: Any) -> str | None:
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        parts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"
                 and isinstance(b.get("text"), str)]
        return "\n".join(parts) if parts else None
    return None


# ----------------------------------------------------------------------------------------------- steps

@dataclass
class Window:
    label: str
    start: dt.datetime
    end: dt.datetime | None      # the end_step time, None when the step was never closed
    limit: dt.datetime | None    # events up to here belong to the step; None means open ended
    order: int


def build_windows(rows: Sequence[EffortRow], arm: str) -> list[Window]:
    starts: dict[str, dt.datetime] = {}
    ends: dict[str, dt.datetime] = {}
    for row in rows:
        if row.arm != arm or row.action not in ("paste_step", "end_step"):
            continue
        if not row.step:
            raise MeterError(f"--effort-log: a {row.action} row of arm {arm} has no step")
        target = starts if row.action == "paste_step" else ends
        if row.step not in target or (row.action == "paste_step") == (row.ts < target[row.step]):
            target[row.step] = row.ts
    if not starts:
        raise MeterError(f"--effort-log has no paste_step row for arm {arm}")
    for label in ends:
        if label not in starts:
            raise MeterError(f"--effort-log: step {label} of arm {arm} has end_step but no paste_step")
    ordered = sorted(starts, key=lambda label: (starts[label], label))
    windows: list[Window] = []
    for i, label in enumerate(ordered):
        following = starts[ordered[i + 1]] if i + 1 < len(ordered) else None
        limit = ends.get(label, following)
        windows.append(Window(label, starts[label], ends.get(label), limit, i))
    return windows


def step_of(windows: Sequence[Window], ts: dt.datetime | None) -> str:
    if ts is None:
        return NO_STEP
    for window in windows:
        if window.limit is None or ts <= window.limit:
            return window.label
    return NO_STEP


# ----------------------------------------------------------------------------------------------- aggregation

@dataclass
class Counted:
    mid: str | None
    rec: Rec
    model: str | None
    speed: str
    tokens: dict[str, int]
    step: str
    usd: Decimal | None


def zero_tokens() -> dict[str, int]:
    return {key: 0 for key in TOKEN_KEYS}


def count_messages(recs: Sequence[Rec], prices: Prices, windows: Sequence[Window]) -> tuple[list[Counted], dict[str, int]]:
    best: dict[str, Rec] = {}
    stats = {"assistant_lines": 0, "no_id_lines": 0, "no_usage_lines": 0}
    singles: list[Rec] = []
    for rec in recs:
        if rec.data.get("type") != "assistant" or not isinstance(rec.data.get("message"), dict):
            continue
        stats["assistant_lines"] += 1
        message = rec.data["message"]
        if parse_usage(message.get("usage")) is None:
            stats["no_usage_lines"] += 1
            continue
        mid = message.get("id")
        if not isinstance(mid, str) or not mid:
            stats["no_id_lines"] += 1
            singles.append(rec)
            continue
        current = best.get(mid)
        if current is None or _out(rec) > _out(current):
            best[mid] = rec
    chosen = [(mid, rec) for mid, rec in best.items()] + [(None, rec) for rec in singles]
    counted = []
    for mid, rec in chosen:
        message = rec.data["message"]
        tokens = parse_usage(message.get("usage")) or zero_tokens()
        model = message.get("model") if isinstance(message.get("model"), str) else None
        speed = "fast" if str(message["usage"].get("speed") or "").lower() == "fast" else "standard"
        usd = message_usd(tokens, speed, prices.find(model))
        counted.append(Counted(mid, rec, model, speed, tokens, step_of(windows, rec.ts), usd))
    counted.sort(key=lambda c: (c.rec.ts or dt.datetime.min.replace(tzinfo=dt.timezone.utc), c.rec.rel, c.rec.number))
    stats["unique_ids"] = len(best)
    stats["counted"] = len(counted)
    stats["duplicate_lines_dropped"] = stats["assistant_lines"] - stats["no_usage_lines"] - len(counted)
    return counted, stats


def _out(rec: Rec) -> int:
    usage = parse_usage(rec.data["message"].get("usage")) or zero_tokens()
    return usage["output"]


def group_rows(counted: Sequence[Counted], order: dict[str, int]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[Counted]] = defaultdict(list)
    for c in counted:
        groups[(c.step, c.rec.agent, c.model or "(none)", c.speed)].append(c)
    rows = []
    for (step, agent, model, speed), items in groups.items():
        tokens = zero_tokens()
        for c in items:
            for key in TOKEN_KEYS:
                tokens[key] += c.tokens[key]
        usd = None if any(c.usd is None for c in items) else quant(sum((c.usd for c in items), Decimal(0)))
        rows.append({"step": step, "agent": agent, "model": model, "speed": speed, "messages": len(items),
                     "tokens": tokens, "usd": usd})
    rows.sort(key=lambda r: (order.get(r["step"], 999), r["agent"], r["model"], r["speed"]))
    return rows


def roll_up(rows: Sequence[dict[str, Any]], key: str) -> dict[str, Any]:
    acc: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = acc.setdefault(row[key], {"messages": 0, "tokens": zero_tokens(), "sum": Decimal(0), "priced": 0, "unpriced": 0})
        item["messages"] += row["messages"]
        for token_key in TOKEN_KEYS:
            item["tokens"][token_key] += row["tokens"][token_key]
        if row["usd"] is None:
            item["unpriced"] += 1
        else:
            item["priced"] += 1
            item["sum"] += Decimal(str(row["usd"]))
    return {name: finish(item) for name, item in acc.items()}


def finish(item: dict[str, Any]) -> dict[str, Any]:
    usd = None if item["unpriced"] and not item["priced"] else quant(item["sum"])
    return {"messages": item["messages"], "tokens": item["tokens"], "usd": usd, "usd_complete": item["unpriced"] == 0}


def total_of(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return roll_up([dict(r, all="all") for r in rows], "all").get("all") or finish(
        {"messages": 0, "tokens": zero_tokens(), "sum": Decimal(0), "priced": 0, "unpriced": 0})


# ----------------------------------------------------------------------------------------------- cost state

def read_cost_state(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    """UNVERIFIED reader: per-model totals of the CLI, from a JSON file or from cost-state lines (JSONL)."""
    raw = read_bytes(path, "--cost-state")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise MeterError("--cost-state is not UTF-8 text")
    try:
        items: list[Any] = [json.loads(text)]
    except ValueError:
        try:
            items = [json.loads(line) for line in text.splitlines() if line.strip()]
        except ValueError:
            raise MeterError("--cost-state is neither JSON nor JSON lines")
    flat: list[Any] = []
    for item in items:
        flat.extend(item if isinstance(item, list) else [item])
    sessions: dict[str, dict[str, Any]] = {}
    for position, item in enumerate(flat):
        if not isinstance(item, dict):
            raise MeterError("--cost-state: an entry is not a JSON object")
        if "modelUsage" in item or "model_usage" in item:
            usage = item.get("modelUsage", item.get("model_usage"))
            key = str(item.get("sessionId") or f"#{position}")
        elif item and all(isinstance(v, dict) for v in item.values()):
            usage, key = item, f"#{position}"
        else:
            continue
        if not isinstance(usage, dict):
            raise MeterError("--cost-state: modelUsage is not an object")
        sessions[key] = usage
    if not sessions:
        raise MeterError("--cost-state holds no per-model usage map")
    totals: dict[str, dict[str, Any]] = {}
    for usage in sessions.values():
        for model, fields in usage.items():
            if not isinstance(fields, dict):
                raise MeterError("--cost-state: a model entry is not an object")
            row = totals.setdefault(model, {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "usd": Decimal(0)})
            for name, keys in COST_STATE_FIELDS.items():
                value = next((fields[k] for k in keys if k in fields), None)
                if value is None:
                    continue
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise MeterError(f"--cost-state: {name} of {model} is not a number")
                row[name] += Decimal(str(value)) if name == "usd" else int(value)
    return totals, sha256(raw)


def cost_state_block(path: Path, by_model: dict[str, Any]) -> dict[str, Any]:
    totals, digest = read_cost_state(path)
    models: dict[str, Any] = {}
    for model in sorted(set(totals) | set(by_model)):
        cli, meter = totals.get(model), by_model.get(model)
        entry: dict[str, Any] = {}
        if cli is not None:
            entry["cli"] = {"input": cli["input"], "output": cli["output"], "cache_read": cli["cache_read"],
                            "cache_write": cli["cache_write"], "usd": quant(cli["usd"])}
        if meter is not None:
            tokens = meter["tokens"]
            entry["meter"] = {"input": tokens["input"], "output": tokens["output"], "cache_read": tokens["cache_read"],
                              "cache_write": tokens["cache_write_5m"] + tokens["cache_write_1h"] + tokens["cache_write_unsplit"],
                              "usd": meter["usd"]}
        if cli is not None and meter is not None and meter["usd"] is not None:
            entry["meter_minus_cli_usd"] = round(meter["usd"] - quant(cli["usd"]), 6)
        models[model] = entry
    return {"verified": False, "source_sha256": digest, "models": models,
            "note": "field map unverified until the dev test (T-67); the CLI state may cover fewer sessions than the arm"}


# ----------------------------------------------------------------------------------------------- the meter

def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


def analyse(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, str]]:
    prices = load_prices(Path(args.prices))
    efforts, effort_hash = load_effort(Path(args.effort_log))
    texts = load_texts(Path(args.texts))
    cost_path = Path(args.cost_state) if args.cost_state else None
    recs, transcripts_hash, file_count = load_transcripts(Path(args.transcripts))
    windows = build_windows(efforts, args.arm)
    order = {w.label: w.order for w in windows}

    counted, msg_stats = count_messages(recs, prices, windows)
    rows = group_rows(counted, order)

    steps: dict[str, dict[str, Any]] = {}

    def step(label: str) -> dict[str, Any]:
        return steps.setdefault(label, {
            "human_turns": defaultdict(int), "text_ids": defaultdict(int), "other_turns": [], "compactions": 0,
            "session_starts": 0, "subagents": defaultdict(int), "active_us": 0,
            "writes": defaultdict(lambda: defaultdict(int))})

    for window in windows:
        step(window.label)

    # human turns of the main sessions, once per uuid
    seen_uuid: set[str] = set()
    turns: list[dict[str, Any]] = []
    events: list[dt.datetime] = []
    for rec in recs:
        data = rec.data
        if rec.ts is not None and data.get("type") in EVENT_TYPES:
            events.append(rec.ts)
        if rec.sub or data.get("type") != "user":
            continue
        uuid = data.get("uuid")
        if isinstance(uuid, str):
            if uuid in seen_uuid:
                continue
            seen_uuid.add(uuid)
        if data.get("isMeta") or data.get("isCompactSummary") or data.get("promptSource") == "system":
            continue
        text = user_text(data.get("message"))
        if text is None or not text.strip() or text.lstrip().startswith("<local-command-") or rec.ts is None:
            continue
        kind, ids = classify_turn(text, texts)
        turns.append({"ts": rec.ts, "kind": kind, "ids": ids, "hash": sha256(norm_text(text).encode("utf-8")),
                      "step": step_of(windows, rec.ts), "rec": rec})
    turns.sort(key=lambda t: (t["ts"], t["rec"].rel, t["rec"].number))
    events.sort()
    for i, turn in enumerate(turns):
        nxt = turns[i + 1]["ts"] if i + 1 < len(turns) else None
        stop = len(events) if nxt is None else bisect.bisect_left(events, nxt)
        last = events[stop - 1] if stop else turn["ts"]
        info = step(turn["step"])
        info["active_us"] += micros(max(last, turn["ts"]) - turn["ts"])
        info["human_turns"][turn["kind"]] += 1
        for text_id in turn["ids"]:
            info["text_ids"][text_id] += 1
        if turn["kind"] == "other":
            info["other_turns"].append({"index": info["human_turns"]["other"], "sha256": turn["hash"]})

    # sub-agent units, session starts, compactions, writes
    units: dict[tuple[str, str], dt.datetime | None] = {}
    session_first: dict[str, dt.datetime] = {}
    boundaries: dict[str, list[dt.datetime | None]] = defaultdict(list)
    summaries: dict[str, list[dt.datetime | None]] = defaultdict(list)
    seen_tool: set[str] = set()
    seen_event: set[str] = set()
    memory_writes: list[dict[str, str]] = []
    raw_writes: list[list[str]] = []
    by_actor: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for rec in recs:
        data = rec.data
        if rec.sub:
            key = (rec.agent, rec.unit or "")
            if key not in units or (rec.ts is not None and (units[key] is None or rec.ts < units[key])):
                units[key] = rec.ts
        else:
            uuid = data.get("uuid")
            first_time = not (isinstance(uuid, str) and uuid in seen_event)
            if isinstance(uuid, str):
                seen_event.add(uuid)
            if first_time and rec.ts is not None:
                session = str(data.get("sessionId") or "")
                if session not in session_first or rec.ts < session_first[session]:
                    session_first[session] = rec.ts
            if first_time:
                session = str(data.get("sessionId") or "")
                if data.get("type") == "system" and data.get("subtype") == "compact_boundary":
                    boundaries[session].append(rec.ts)
                elif data.get("type") == "user" and data.get("isCompactSummary") is True:
                    summaries[session].append(rec.ts)
        message = data.get("message")
        if data.get("type") == "assistant" and isinstance(message, dict) and isinstance(message.get("content"), list):
            for index, block in enumerate(message["content"]):
                if not isinstance(block, dict) or block.get("type") != "tool_use" or block.get("name") not in WRITE_TOOLS:
                    continue
                tool_id = block.get("id") if isinstance(block.get("id"), str) and block.get("id") else f"{rec.rel}:{rec.number}:{index}"
                if tool_id in seen_tool:
                    continue
                seen_tool.add(tool_id)
                label = step_of(windows, rec.ts)
                tool = block["name"]
                step(label)["writes"][rec.agent][tool] += 1
                by_actor[rec.agent][tool] += 1
                target = block.get("input") if isinstance(block.get("input"), dict) else {}
                path_text = str(target.get("file_path") or target.get("notebook_path") or "")
                raw_writes.append([label, rec.agent, tool, rec.ts.isoformat() if rec.ts else "", path_text])
                segments = [s.lower() for s in path_text.replace("\\", "/").split("/")]
                if "memory" in segments[:-1]:
                    memory_writes.append({"step": label, "actor": rec.agent, "tool": tool,
                                          "path_sha256": sha256(path_text.encode("utf-8"))})
    for session, ts in session_first.items():
        step(step_of(windows, ts))["session_starts"] += 1
    for session in set(boundaries) | set(summaries):
        stamps = boundaries[session] if len(boundaries[session]) >= len(summaries[session]) else summaries[session]
        for ts in stamps:
            step(step_of(windows, ts))["compactions"] += 1
    sub_counts: dict[str, int] = defaultdict(int)
    for (agent, _unit), ts in units.items():
        step(step_of(windows, ts))["subagents"][agent[len("sub:"):]] += 1
        sub_counts[agent[len("sub:"):]] += 1

    # effort log per step
    for window in windows:
        info = step(window.label)
        actions: dict[str, int] = defaultdict(int)
        clicks = 0
        spent = 0.0
        for row in efforts:
            if row.arm != args.arm or row.step != window.label:
                continue
            actions[row.action] += 1
            if row.action == "permission_click":
                clicks += 1 if row.count is None else row.count
            if row.action == "end_step" and row.minutes is not None:
                spent += row.minutes
        info["actions"] = actions
        info["permission_clicks"] = clicks
        info["maintainer_minutes"] = round(spent, 2)
        info["closed"] = window.end is not None
        info["order"] = window.order
        info["wall_minutes"] = minutes(micros(window.end - window.start)) if window.end is not None else None

    by_step_money = roll_up(rows, "step")
    for label, info in steps.items():
        info["active_minutes"] = minutes(info.pop("active_us"))
        wall = info.get("wall_minutes")
        info["idle_minutes"] = round(wall - info["active_minutes"], 2) if wall is not None else None
        info["order"] = info.get("order", 999)
        info["usage"] = by_step_money.get(label, finish({"messages": 0, "tokens": zero_tokens(), "sum": Decimal(0), "priced": 0, "unpriced": 0}))

    by_model = roll_up(rows, "model")
    off_model: list[dict[str, Any]] = []
    if args.model:
        off: dict[tuple[str, str], int] = defaultdict(int)
        for c in counted:
            if c.rec.agent == "main" and c.model != args.model:
                off[(c.step, c.model or "(none)")] += 1
        off_model = [{"step": s, "model": m, "messages": n} for (s, m), n in sorted(off.items(), key=lambda kv: (order.get(kv[0][0], 999), kv[0][1]))]
    unpriced: dict[tuple[str, str], int] = defaultdict(int)
    for c in counted:
        if c.usd is None:
            unpriced[(c.model or "(none)", "fast speed" if c.speed == "fast" and prices.find(c.model) is not None else "no price")] += 1

    turn_totals: dict[str, int] = defaultdict(int)
    id_totals: dict[str, int] = defaultdict(int)
    for info in steps.values():
        for kind, n in info["human_turns"].items():
            turn_totals[kind] += n
        for text_id, n in info["text_ids"].items():
            id_totals[text_id] += n

    result: dict[str, Any] = {
        "schema": SCHEMA,
        "arm": args.arm,
        "fixed_model": args.model,
        "prices": {"read_on": prices.read_on, "sha256": prices.sha256, "unit": "USD per MTok, list price"},
        "inputs": {"transcript_files": file_count, "transcripts_sha256": transcripts_hash,
                   "effort_log_sha256": effort_hash, "texts_sha256": texts.sha256},
        "messages": {k: msg_stats[k] for k in ("assistant_lines", "counted", "duplicate_lines_dropped", "no_id_lines",
                                               "no_usage_lines", "unique_ids")},
        "rows": rows,
        "totals": total_of(rows),
        "by_model": by_model,
        "by_agent": roll_up(rows, "agent"),
        "unpriced": [{"model": m, "reason": r, "messages": n} for (m, r), n in sorted(unpriced.items())],
        "off_model": off_model,
        "steps": steps,
        "human_turns": turn_totals,
        "text_ids": id_totals,
        "subagents": sub_counts,
        "session_starts": sum(i["session_starts"] for i in steps.values()),
        "compactions": sum(i["compactions"] for i in steps.values()),
        "writes": {"by_actor": by_actor, "memory": memory_writes, "shell_writes": "not attributed"},
    }
    if cost_path is not None:
        result["cost_state"] = cost_state_block(cost_path, by_model)
    raw = raw_tables(counted, turns, raw_writes)
    return plain(result), raw


def raw_tables(counted: Sequence[Counted], turns: Sequence[dict[str, Any]], writes: Sequence[Sequence[str]]) -> dict[str, str]:
    def render(header: Sequence[str], body: Sequence[Sequence[Any]]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(body)
        return buffer.getvalue()

    messages = [[c.step, c.rec.agent, c.model or "(none)", c.speed, c.mid or "", c.rec.ts.isoformat() if c.rec.ts else "",
                 *[c.tokens[k] for k in TOKEN_KEYS], "" if c.usd is None else f"{c.usd:.8f}", c.rec.rel, c.rec.number]
                for c in counted]
    human = [[t["step"], t["ts"].isoformat(), t["kind"], " ".join(t["ids"]), t["hash"], t["rec"].rel, t["rec"].number]
             for t in turns]
    return {
        "messages.csv": render(["step", "agent", "model", "speed", "message_id", "timestamp", *TOKEN_KEYS, "usd", "file", "line"], messages),
        "human-turns.csv": render(["step", "timestamp", "type", "text_ids", "sha256", "file", "line"], human),
        "writes.csv": render(["step", "actor", "tool", "timestamp", "path"], writes),
    }


# ----------------------------------------------------------------------------------------------- command line

def check_raw_out(raw_out: Path) -> Path:
    resolved = raw_out.resolve()
    root = KIT_ROOT.resolve()
    if resolved == root or root in resolved.parents:
        raise MeterError("--raw-out is inside the repository: raw tables must stay outside it")
    if resolved.exists() and not resolved.is_dir():
        raise MeterError("--raw-out exists and is not a folder")
    return resolved


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="transcript_meter.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--transcripts", required=True, help="folder with the arm's transcript JSONL files")
    parser.add_argument("--effort-log", required=True, help="effort log CSV (plan 6.3)")
    parser.add_argument("--texts", required=True, help="JSON: id to {type, text}")
    parser.add_argument("--arm", required=True, help="arm label as written in the effort log")
    parser.add_argument("--out", required=True, help="totals JSON (numbers, labels, hashes)")
    parser.add_argument("--raw-out", required=True, help="folder for the raw tables, outside the repository")
    parser.add_argument("--model", default=None, help="the arm's fixed main model id")
    parser.add_argument("--cost-state", default=None, help="the CLI's own cost state (field map unverified)")
    parser.add_argument("--prices", default=str(DEFAULT_PRICES), help="price file (default bench/build/prices.json)")
    args = parser.parse_args(argv)
    try:
        if not ARM_RE.match(args.arm):
            raise MeterError("--arm may hold letters, digits, dot, dash and underscore only")
        raw_dir = check_raw_out(Path(args.raw_out))
        result, raw = analyse(args)
    except MeterError as err:
        print(f"transcript_meter: {err}", file=sys.stderr)
        return 2
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    try:
        raw_dir.mkdir(parents=True, exist_ok=True)
        for name, body in raw.items():
            (raw_dir / f"{args.arm}-{name}").write_bytes(body.encode("utf-8"))
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))
    except OSError:
        print("transcript_meter: an output file cannot be written", file=sys.stderr)
        return 2
    totals, msgs = result["totals"], result["messages"]
    state = "complete" if totals["usd_complete"] else "incomplete, see unpriced"
    print(f"transcript_meter: arm {args.arm}; {msgs['counted']} messages counted ({msgs['duplicate_lines_dropped']} "
          f"duplicate lines dropped, {msgs['no_id_lines']} without id); usd {totals['usd']} ({state}); "
          f"prices read {prices_date(result)}" + ("; cost-state unverified" if "cost_state" in result else ""))
    return 0


def prices_date(result: dict[str, Any]) -> str:
    return result["prices"]["read_on"]


if __name__ == "__main__":
    sys.exit(main())
