#!/usr/bin/env python3
"""Run the 30 frozen eval questions through `claude -p`, with and without the sdlc server (DEC-012, DEC-054).

Usage:  python tools/eval_run.py --label pilot-1 --budget-usd 3 --questions pilot --repeats 1

Every run is one `claude -p` call in a fresh copy of `eval/repo/` outside the kit repository, so the
model under test cannot reach `questions.jsonl`, the keys or the kit. The two conditions get the same
prompt and the same flags; the server condition adds one `--mcp-config` whose server root is the copy.
Raw stream output and the per-run records go to an output folder outside the repository. Only totals,
with fixed keys, numbers and labels, go to `eval/results/<label>.json`.

The runs use the subscription login, not `--bare` and not an API key: `ANTHROPIC_API_KEY` and
`ANTHROPIC_AUTH_TOKEN` are removed from the child environment, and a run whose init event reports an
API key as the credential stops the whole run. `cost_usd` is the CLI's list-price estimate, not a bill;
the runs count against the subscription usage limits.
Standard library only; Python 3.10 or newer. The server needs the `mcp` package in the same interpreter.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

KIT_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = KIT_ROOT / "eval"
EVAL_REPO = EVAL_DIR / "repo"
QUESTIONS_FILE = EVAL_DIR / "questions.jsonl"
SERVER_MAIN = KIT_ROOT / "server" / "main.py"
DEFAULT_RESULTS = EVAL_DIR / "results"
RAW_OK_INSIDE_KIT = KIT_ROOT / "evidence" / "raw"  # already ignored by .gitignore

SERVER_NAME = "sdlc"
SERVER_TOOLS = (
    "status", "scope_check", "contract", "changed_outside", "guard_events",
    "decisions", "lessons", "findings", "tasks", "log",
)
BASE_TOOLS = ("Read",)  # Grep, Glob and ToolSearch are not offered by this CLI build (docs/toolchain.md V-16)
SETTING_SOURCES = "project,local"
DROPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_ROOT")
CONDITIONS = ("server", "no-server")
SCHEMA = 1
LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
WORD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
ANSWER_RE = re.compile(r"^[\s*_`>#-]*answer\s*[:=][\s*_`]*(.+?)[\s*_`]*$", re.IGNORECASE)
HINTS = {
    "yes-no": "<value> is yes or no.",
    "number": "<value> is a whole number written in digits.",
    "token": "<value> is one ID, word or date, with no other text.",
    "set": "<value> lists the items separated by commas.",
}


def _load_score() -> Any:
    spec = importlib.util.spec_from_file_location("eval_score_runner", EVAL_DIR / "score.py")
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError("eval/score.py cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


score_mod = _load_score()


@dataclass
class Config:
    label: str
    budget_usd: float
    models: list[str] = field(default_factory=lambda: ["haiku", "sonnet"])
    conditions: list[str] = field(default_factory=lambda: list(CONDITIONS))
    repeats: int = 1
    question_spec: str = "all"
    max_turns: int = 12
    max_run_usd: float = 0.25
    timeout_s: int = 300
    max_failed_calls: int = 3
    restricted: bool = True
    keep_workspaces: bool = False
    resume: bool = False
    claude: str = "claude"
    out_dir: Path = Path(".")
    work_dir: Path = Path(".")
    results_dir: Path = DEFAULT_RESULTS


@dataclass
class InvokeResult:
    returncode: int | None
    stdout: str
    timed_out: bool = False


Invoke = Callable[[list, Path, dict, int], InvokeResult]


def default_invoke(argv: list, cwd: Path, env: dict, timeout: int) -> InvokeResult:
    try:
        done = subprocess.run(
            argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        return InvokeResult(None, partial, True)
    except OSError:
        return InvokeResult(None, "", False)
    return InvokeResult(done.returncode, done.stdout or "")


# ---------------------------------------------------------------- questions

def questions_hash(path: Path = QUESTIONS_FILE) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def select_questions(questions: Sequence[dict], spec: str) -> list[dict]:
    """`all`, `pilot` (the first question of each of the 5 largest categories) or a comma list of IDs."""
    if spec == "all":
        return list(questions)
    if spec == "pilot":
        counts: dict[str, int] = {}
        for q in questions:
            counts[q["category"]] = counts.get(q["category"], 0) + 1
        order = list(counts)
        top = sorted(order, key=lambda name: (-counts[name], order.index(name)))[:5]
        firsts = {}
        for q in questions:
            if q["category"] in top and q["category"] not in firsts:
                firsts[q["category"]] = q["id"]
        wanted = set(firsts.values())
        return [q for q in questions if q["id"] in wanted]
    ids = [part.strip() for part in spec.split(",") if part.strip()]
    by_id = {q["id"]: q for q in questions}
    unknown = [i for i in ids if i not in by_id]
    if unknown or not ids:
        raise ValueError("unknown question ID: " + ", ".join(unknown or ["(none given)"]))
    return [by_id[i] for i in dict.fromkeys(ids)]


def workspace_files(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def build_prompt(question: dict, files: Sequence[str]) -> str:
    """The same text in both conditions; it never mentions the server."""
    return (
        "Answer one question about the project records in the current folder. "
        "Use only these files: " + ", ".join(files) + ".\n"
        "Question: " + question["question"] + "\n"
        "Finish with one last line in exactly this form: ANSWER: <value>\n"
        + HINTS.get(question["answer_type"], "")
    ).rstrip()


def parse_answer(text: str) -> str | None:
    """The value of the last `ANSWER: <value>` line, or None."""
    found = None
    for line in text.splitlines():
        match = ANSWER_RE.match(line)
        if match:
            found = match.group(1).strip()
    if found is None:
        return None
    if found.startswith("[") and found.endswith("]"):
        found = found[1:-1].strip()
    return found or None


# ---------------------------------------------------------------- the CLI call

def allowed_tools() -> str:
    """The same list in both conditions; the server names are harmless when no server is attached."""
    return ",".join(list(BASE_TOOLS) + [f"mcp__{SERVER_NAME}__{name}" for name in SERVER_TOOLS])


def build_argv(cfg: Config, model: str, condition: str, prompt: str, mcp_config: Path | None) -> list:
    argv: list = [
        cfg.claude, "-p", prompt, "--strict-mcp-config", "--setting-sources", SETTING_SOURCES,
        "--model", model,
        "--tools", ",".join(BASE_TOOLS),
        "--allowedTools", allowed_tools(),
        "--permission-mode", "dontAsk",
        "--max-turns", str(cfg.max_turns),
        "--max-budget-usd", f"{cfg.max_run_usd:g}",
        "--output-format", "stream-json", "--verbose", "--no-session-persistence",
    ]
    if cfg.restricted:
        argv.append("--restricted")
    if condition == "server":
        if mcp_config is None:
            raise ValueError("the server condition needs an MCP config")
        argv += ["--mcp-config", str(mcp_config)]
    return argv


def write_mcp_config(path: Path, workspace: Path) -> None:
    config = {"mcpServers": {SERVER_NAME: {
        "command": sys.executable,
        "args": [str(SERVER_MAIN)],
        "env": {"CLAUDE_PROJECT_DIR": str(workspace)},
    }}}
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")


@dataclass
class Parsed:
    init_model: str = ""
    api_key_source: str = ""
    server_status: str = ""
    tool_calls: dict[str, int] = field(default_factory=dict)
    result: dict | None = None
    last_text: str = ""


def parse_stream(text: str) -> Parsed:
    parsed = Parsed()
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            parsed.init_model = str(event.get("model") or "")
            parsed.api_key_source = str(event.get("apiKeySource") or "")
            for server in event.get("mcp_servers") or []:
                if isinstance(server, dict) and server.get("name") == SERVER_NAME:
                    parsed.server_status = str(server.get("status") or "")
        elif kind == "assistant":
            content = (event.get("message") or {}).get("content") or []
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and isinstance(block.get("name"), str):
                    parsed.tool_calls[block["name"]] = parsed.tool_calls.get(block["name"], 0) + 1
                elif block.get("type") == "text" and isinstance(block.get("text"), str):
                    parsed.last_text = block["text"]
        elif kind == "result":
            parsed.result = event
    return parsed


def _label(value: Any) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value).lower()).strip("_")[:40]


def _num(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def build_record(base: dict, question: dict, condition: str, res: InvokeResult) -> dict:
    """One run record from the CLI output; `error` is a short label, empty when the call went well."""
    parsed = parse_stream(res.stdout)
    result = parsed.result or {}
    usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
    model_usage = result.get("modelUsage") if isinstance(result.get("modelUsage"), dict) else {}
    model_id = ",".join(sorted(model_usage)) or parsed.init_model
    text = result.get("result") if isinstance(result.get("result"), str) else ""
    answer = parse_answer(text or parsed.last_text)
    if res.timed_out:
        error = "timeout"
    elif parsed.result is None:
        error = f"exit_{res.returncode}" if res.returncode not in (0, None) else "no_result"
    elif result.get("is_error"):
        error = _label(result.get("terminal_reason") or result.get("subtype") or "is_error") or "is_error"
    elif str(result.get("subtype", "success")).startswith("error"):
        error = _label(result.get("subtype"))
    elif condition == "server" and parsed.server_status != "connected":
        error = "mcp_not_connected"
    else:
        error = ""
    answer_matched = answer is not None and bool(score_mod.is_correct(question, answer))
    correct = answer_matched and not error
    record = dict(base)
    record.update({
        "model_id": model_id,
        "api_key_source": parsed.api_key_source,
        "correct": bool(correct),
        "answer_matched": answer_matched,
        "answer_found": answer is not None,
        "answer": answer or "",
        "duration_ms": int(_num(result.get("duration_ms"))),
        "turns": int(_num(result.get("num_turns"))),
        "input_tokens": int(_num(usage.get("input_tokens"))),
        "cache_read_tokens": int(_num(usage.get("cache_read_input_tokens"))),
        "cache_creation_tokens": int(_num(usage.get("cache_creation_input_tokens"))),
        "output_tokens": int(_num(usage.get("output_tokens"))),
        "cost_usd": _num(result.get("total_cost_usd")),
        "tool_calls": dict(sorted(parsed.tool_calls.items())),
        "error": error,
    })
    return record


# ---------------------------------------------------------------- totals

def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def build_totals(cfg: Config, meta: dict, runs: Sequence[dict], planned: int, stopped: str, spent: float) -> dict:
    groups = []
    for model in cfg.models:
        for condition in cfg.conditions:
            mine = [r for r in runs if r["model"] == model and r["condition"] == condition]
            if not mine:
                continue
            per_repeat: dict[int, list[bool]] = {}
            for r in mine:
                per_repeat.setdefault(r["repeat"], []).append(r["correct"])
            accuracy = [sum(v) / len(v) for v in per_repeat.values()]
            by_category: dict[str, dict[str, int]] = {}
            tools: dict[str, int] = {}
            for r in mine:
                tally = by_category.setdefault(r["category"], {"correct": 0, "total": 0})
                tally["correct"] += 1 if r["correct"] else 0
                tally["total"] += 1
                for name, count in r["tool_calls"].items():
                    tools[name] = tools.get(name, 0) + count
            groups.append({
                "model": model,
                "model_id": ",".join(sorted({r["model_id"] for r in mine if r["model_id"]})),
                "condition": condition,
                "runs": len(mine),
                "correct": sum(1 for r in mine if r["correct"]),
                "accuracy_mean": round(sum(accuracy) / len(accuracy), 6),
                "accuracy_min": round(min(accuracy), 6),
                "accuracy_max": round(max(accuracy), 6),
                "by_category": dict(sorted(by_category.items())),
                "cost_usd": round(sum(r["cost_usd"] for r in mine), 6),
                "cost_usd_per_run": _mean([r["cost_usd"] for r in mine]),
                "input_tokens": sum(r["input_tokens"] for r in mine),
                "cache_read_tokens": sum(r["cache_read_tokens"] for r in mine),
                "cache_creation_tokens": sum(r["cache_creation_tokens"] for r in mine),
                "output_tokens": sum(r["output_tokens"] for r in mine),
                "duration_ms": sum(r["duration_ms"] for r in mine),
                "duration_ms_per_run": _mean([r["duration_ms"] for r in mine]),
                "turns_per_run": _mean([r["turns"] for r in mine]),
                "tool_calls_total": sum(tools.values()),
                "tool_calls": dict(sorted(tools.items())),
                "errors": sum(1 for r in mine if r["error"]),
                "unparsed": sum(1 for r in mine if not r["answer_found"]),
            })
    return {
        "schema": SCHEMA,
        "label": cfg.label,
        "date": meta["date"],
        "cli_version": meta["cli_version"],
        "eval_set_sha256": meta["eval_set_sha256"],
        "question_ids": meta["question_ids"],
        "repeats": cfg.repeats,
        "settings": {
            "max_turns": cfg.max_turns, "max_run_usd": cfg.max_run_usd, "timeout_s": cfg.timeout_s,
            "tools": ",".join(BASE_TOOLS), "restricted": cfg.restricted, "setting_sources": SETTING_SOURCES,
        },
        "planned_runs": planned,
        "done_runs": len(runs),
        "complete": len(runs) == planned,
        "stopped": stopped,
        "budget_usd": cfg.budget_usd,
        "spent_usd": round(spent, 6),
        "groups": groups,
    }


# ---------------------------------------------------------------- the run loop

def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def check_paths(cfg: Config) -> str | None:
    if _inside(cfg.work_dir, KIT_ROOT):
        return "the work folder must be outside the kit repository"
    if _inside(cfg.out_dir, KIT_ROOT) and not _inside(cfg.out_dir, RAW_OK_INSIDE_KIT):
        return "the output folder must be outside the kit repository (or under evidence/raw)"
    return None


def load_runs(path: Path) -> list[dict]:
    runs = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                runs.append(json.loads(line))
    return runs


def run_eval(cfg: Config, invoke: Invoke, env: dict, out=None) -> int:
    stream = out if out is not None else sys.stdout

    def say(text: str) -> None:
        stream.write(text + "\n")
        stream.flush()

    problem = check_paths(cfg)
    if problem:
        say(f"eval_run: {problem}")
        return 2
    questions = select_questions(score_mod.load_questions(QUESTIONS_FILE), cfg.question_spec)
    runs_file = cfg.out_dir / "runs.jsonl"
    totals_file = cfg.results_dir / f"{cfg.label}.json"
    if not cfg.resume and (runs_file.exists() or totals_file.exists()):
        say("eval_run: this label already has output; pick a new label or use --resume")
        return 2
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    (cfg.out_dir / "raw").mkdir(exist_ok=True)
    cfg.work_dir.mkdir(parents=True, exist_ok=True)
    cfg.results_dir.mkdir(parents=True, exist_ok=True)

    child_env = {k: v for k, v in env.items() if k not in DROPPED_ENV}
    dropped = [k for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN") if env.get(k)]
    if dropped:
        say("eval_run: " + " and ".join(dropped) + " removed from the CLI environment; the runs use the subscription login")
    version = invoke([cfg.claude, "--version"], cfg.work_dir, child_env, 60).stdout.strip().splitlines()
    meta = {
        "date": dt.date.today().isoformat(),
        "cli_version": version[0][:60] if version else "unknown",
        "eval_set_sha256": questions_hash(),
        "question_ids": [q["id"] for q in questions],
    }

    plan = [
        (repeat, q, model, condition)
        for repeat in range(1, cfg.repeats + 1)
        for q in questions
        for model in cfg.models
        for condition in cfg.conditions
    ]
    runs = load_runs(runs_file) if cfg.resume else []
    done = {(r["repeat"], r["question"], r["model"], r["condition"]) for r in runs}
    spent = sum(r["cost_usd"] for r in runs)
    failed_in_a_row = 0
    stopped = ""
    planned = len(plan)
    say(f"eval_run: label {cfg.label}, {planned} runs planned, budget {cfg.budget_usd:.2f} USD (list-price estimate), "
        f"per-run cap {cfg.max_run_usd:g} USD, {len(done)} already done")

    try:
        for index, (repeat, q, model, condition) in enumerate(plan, start=1):
            if (repeat, q["id"], model, condition) in done:
                continue
            estimate = cfg.max_run_usd
            if spent + estimate > cfg.budget_usd:
                stopped = "budget"
                say(f"eval_run: stopped before run {index}/{planned}: spent {spent:.4f} USD plus "
                    f"an estimated {estimate:.4f} USD would pass the budget of {cfg.budget_usd:.2f} USD")
                break
            run_id = f"{model}-{condition}-{q['id']}-r{repeat}"
            run_dir = cfg.work_dir / run_id
            if run_dir.exists():
                shutil.rmtree(run_dir, ignore_errors=True)
            workspace = run_dir / "ws"
            shutil.copytree(EVAL_REPO, workspace, ignore=shutil.ignore_patterns("__pycache__"))
            mcp_config = None
            if condition == "server":
                mcp_config = run_dir / "mcp.json"
                write_mcp_config(mcp_config, workspace)
            prompt = build_prompt(q, workspace_files(workspace))
            argv = build_argv(cfg, model, condition, prompt, mcp_config)
            try:
                res = invoke(argv, workspace, child_env, cfg.timeout_s)
            finally:
                if not cfg.keep_workspaces:
                    shutil.rmtree(run_dir, ignore_errors=True)
            (cfg.out_dir / "raw" / f"{run_id}.jsonl").write_text(res.stdout, encoding="utf-8")
            base = {"run_id": run_id, "model": model, "condition": condition, "question": q["id"],
                    "category": q["category"], "repeat": repeat}
            record = build_record(base, q, condition, res)
            with runs_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            runs.append(record)
            spent += record["cost_usd"]
            status = "ok" if record["correct"] else ("error " + record["error"] if record["error"] else "wrong")
            say(f"[{len(runs)}/{planned}] {q['id']} {model} {condition}: {status}, "
                f"{record['cost_usd']:.4f} USD, spent {spent:.4f}")
            if record["api_key_source"] not in ("", "none"):
                stopped = "auth"
                say("eval_run: stopped: the CLI reports an API key as its credential; the runs must use the "
                    "subscription login. Remove ANTHROPIC_API_KEY from the window and check /status in claude")
                break
            failed_in_a_row = failed_in_a_row + 1 if (record["error"] and record["cost_usd"] == 0) else 0
            if failed_in_a_row >= cfg.max_failed_calls:
                stopped = "errors"
                say(f"eval_run: stopped: {failed_in_a_row} calls in a row failed with no cost "
                    f"(last error: {record['error']}); check the login, the usage limit and the CLI")
                break
    except KeyboardInterrupt:
        stopped = "interrupted"
        say("eval_run: interrupted; totals so far are written; --resume continues")

    totals = build_totals(cfg, meta, runs, planned, stopped, spent)
    totals_file.write_text(json.dumps(totals, indent=2) + "\n", encoding="utf-8")
    for group in totals["groups"]:
        say(f"{group['model']} {group['condition']}: {group['correct']}/{group['runs']} correct, "
            f"{group['cost_usd']:.4f} USD, {group['tool_calls_total']} tool calls, "
            f"{group['errors']} errors, {group['unparsed']} unparsed")
    errors = sum(g["errors"] for g in totals["groups"])
    unparsed = sum(g["unparsed"] for g in totals["groups"])
    say(f"done: {len(runs)}/{planned} runs, spent {spent:.4f} of {cfg.budget_usd:.2f} USD, "
        f"stopped: {stopped or 'no'}, errors {errors}, unparsed {unparsed}")
    say(f"totals: {totals_file.name}")
    return 130 if stopped == "interrupted" else (1 if stopped else 0)


def _csv(value: str, allowed: Sequence[str] | None, what: str) -> list[str]:
    items = [part.strip() for part in value.split(",") if part.strip()]
    if not items:
        raise ValueError(f"{what}: nothing given")
    for item in items:
        if not WORD_RE.match(item) or (allowed is not None and item not in allowed):
            raise ValueError(f"{what}: not usable: {item}")
    return list(dict.fromkeys(items))


def main(argv: Sequence[str] | None = None, invoke: Invoke | None = None, env: dict | None = None, out=None) -> int:
    parser = argparse.ArgumentParser(prog="eval_run", description="Run the eval questions through claude -p on the subscription login.")
    parser.add_argument("--label", required=True, help="name of the totals file eval/results/<label>.json")
    parser.add_argument("--budget-usd", required=True, type=float, help="total budget in estimated USD; a call starts only if spent plus --max-run-usd stays within it (the CLI checks its cap between turns, so one run can pass the cap by the cost of its last turn)")
    parser.add_argument("--models", default="haiku,sonnet")
    parser.add_argument("--conditions", default=",".join(CONDITIONS), help="server, no-server or both")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--questions", default="all", help="all, pilot, or a comma list of IDs such as Q01,Q09")
    parser.add_argument("--max-turns", type=int, default=12)
    parser.add_argument("--max-run-usd", type=float, default=0.25, help="cap per run (--max-budget-usd of the CLI)")
    parser.add_argument("--timeout-s", type=int, default=300)
    parser.add_argument("--max-failed-calls", type=int, default=3, help="stop after this many zero-cost errors in a row")
    parser.add_argument("--no-restricted", action="store_true", help="do not pass --restricted to the CLI")
    parser.add_argument("--keep-workspaces", action="store_true")
    parser.add_argument("--resume", action="store_true", help="continue a label: skip runs already in runs.jsonl")
    parser.add_argument("--claude", default=None, help="path of the claude executable (default: found on PATH)")
    parser.add_argument("--out", type=Path, default=None, help="raw output folder (default: system temp)")
    parser.add_argument("--work-dir", type=Path, default=None, help="folder for the per-run copies (default: system temp)")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args(argv)
    stream = out if out is not None else sys.stdout

    def fail(message: str) -> int:
        stream.write(f"eval_run: {message}\n")
        return 2

    if not LABEL_RE.match(args.label):
        return fail("label: letters, digits, dot, dash and underscore only")
    if args.budget_usd <= 0 or args.repeats < 1 or args.max_turns < 1 or args.max_run_usd <= 0 or args.timeout_s < 1:
        return fail("budget, repeats, max-turns, max-run-usd and timeout-s must be positive")
    try:
        models = _csv(args.models, None, "models")
        conditions = _csv(args.conditions, CONDITIONS, "conditions")
        select_questions(score_mod.load_questions(QUESTIONS_FILE), args.questions)
    except ValueError as exc:
        return fail(str(exc))
    env = dict(os.environ if env is None else env)
    claude = args.claude or shutil.which("claude")
    if invoke is None and not claude:
        return fail("claude was not found on PATH")
    temp = Path(tempfile.gettempdir())
    cfg = Config(
        label=args.label, budget_usd=args.budget_usd, models=models, conditions=conditions,
        repeats=args.repeats, question_spec=args.questions, max_turns=args.max_turns,
        max_run_usd=args.max_run_usd, timeout_s=args.timeout_s, max_failed_calls=args.max_failed_calls,
        restricted=not args.no_restricted, keep_workspaces=args.keep_workspaces, resume=args.resume,
        claude=claude or "claude",
        out_dir=args.out or temp / "sdlc-eval-out" / args.label,
        work_dir=args.work_dir or temp / "sdlc-eval-work" / args.label,
        results_dir=args.results_dir,
    )
    return run_eval(cfg, invoke or default_invoke, env, stream)


if __name__ == "__main__":
    sys.exit(main())
