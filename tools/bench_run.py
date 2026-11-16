#!/usr/bin/env python3
"""Run the 2 bench arms (plain, kit) on `bench/` through `claude -p` and score every run by machine (DEC-065, DEC-066).

Usage:  python tools/bench_run.py --label full-1 --budget-usd 40 --repeats 2

Every run is one `claude -p` call in a fresh copy of `bench/project/` outside the kit repository, with one
baseline commit. The plain arm gets the task text and nothing else. The kit arm also gets `.sdlc/project.md`
(what `/sdlc:init` writes) and `--plugin-dir` set to a `git archive` extract of the recorded kit commit whose
`agents/*.md` `model:` lines are set to `sonnet`. Both arms run Sonnet, with `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`.
After a run the result is copied again, the hidden tests are added as `_hidden/`, and the hidden tests and the
visible suite run with this interpreter. Raw streams, run records and the manifest go to `--out`, outside the
repository. Only totals (numbers, labels, hashes) go to `bench/results/<label>.json`.

The runs use the subscription login: `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are removed from the child
environment and an init event whose `apiKeySource` is not `none` stops the runner. `cost_usd` is the CLI's
list-price estimate. A full run is meant to be started in sittings: `--resume` continues a label,
`--resume --rerun-errors` repeats only the runs that ended in a harness error.
Standard library only; Python 3.10 or newer. Reuses `tools/eval_run.py` by import.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import io
import json
import os
import random
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

if __package__ in (None, ""):  # started as a script: make `tools` importable
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import eval_run as er  # noqa: E402
from tools import events as guard_events  # noqa: E402

KIT_ROOT = er.KIT_ROOT
BENCH_DIR = KIT_ROOT / "bench"
DEFAULT_RESULTS = BENCH_DIR / "results"

MODEL = "sonnet"
ARMS = ("plain", "kit")
BASE_TOOLS = ("Read", "Write", "Edit", "Bash", "Glob", "Grep")
KIT_SERVER_NAME = er.SERVER_NAME  # DEC-069: started through --mcp-config, so the tools are mcp__sdlc__*
PLUGIN_TOOL_PREFIX = f"mcp__{KIT_SERVER_NAME}__"
KIT_TOOLS = ("Task",) + tuple(PLUGIN_TOOL_PREFIX + name for name in er.SERVER_TOOLS)
SETTING_SOURCES = er.SETTING_SOURCES
SUBAGENT_MODEL_ENV = "CLAUDE_CODE_SUBAGENT_MODEL"
SCHEMA = 1
IDLE_AFTER_RESULT_S = 60          # V-22: the CLI can stay open for minutes after its final result event
PLUGIN_PATHS = (".claude-plugin", "agents", "skills", "hooks", "server", "tools", "templates")
# Files /sdlc:init and the kit's skills create at the project root. Listed apart, not counted as out of scope,
# in the kit arm only; a pattern of the task's allowed.txt wins over this list.
KIT_RECORD_FILES = ("TASKS.md", "DECISIONS.md", "LOG.md", "STATUS.md", "LESSONS.md", "CHANGELOG.md")
KIT_LAYER_DIR = ".sdlc"
SNAPSHOT_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache"}
COPY_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc")
SCORE_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", ".git", KIT_LAYER_DIR)
PYTEST_TIMEOUT_S = 600
LABEL_RE = er.LABEL_RE
HASH_LINE = re.compile(r"^SHA-256: `([0-9a-f]{64})`$", re.MULTILINE)
HIDDEN_RE = re.compile(r"bench[/\\]tasks|hidden", re.IGNORECASE)
PATH_FIELDS = {
    "Read": ("file_path",), "Write": ("file_path",), "Edit": ("file_path",), "NotebookEdit": ("notebook_path",),
    "Glob": ("path", "pattern"), "Grep": ("path", "glob"), "Bash": ("command",),
}
USAGE_LIMIT_RE = re.compile(r"usage limit|limit reached|rate limit|weekly limit|session limit|limit will reset", re.IGNORECASE)
RESUME_IGNORED = ("kit_dirty",)
GIT_IDENTITY = ("-c", "user.name=bench", "-c", "user.email=bench@users.noreply.github.com", "-c", "commit.gpgsign=false")

# The same text in both arms, put before task.md. It says what an arm cannot find out for itself in `-p`.
PREFACE = (
    "You work in the project in the current folder. The go-ahead for this one task is given: make the change "
    "in the files now and stop when it is done. The customer who owns the project cannot be reached and cannot "
    "answer questions, so do not ask any; decide yourself and say in your last message what you did.\n\n"
)


@dataclass
class Config:
    label: str
    budget_usd: float
    tasks: list[str] = field(default_factory=list)
    arms: list[str] = field(default_factory=lambda: list(ARMS))
    repeats: int = 1
    seed: int = 0
    max_turns: int = 60
    max_run_usd: float = 2.0
    timeout_s: int = 2700
    idle_s: float = IDLE_AFTER_RESULT_S
    max_failed_calls: int = 3
    keep_workspaces: bool = False
    resume: bool = False
    rerun_errors: bool = False
    dry_run: bool = False
    claude: str = "claude"
    out_dir: Path = Path(".")
    work_dir: Path = Path(".")
    results_dir: Path = DEFAULT_RESULTS
    bench_dir: Path = BENCH_DIR
    kit_root: Path = KIT_ROOT


@dataclass
class BenchResult(er.InvokeResult):
    ended_by: str = ""      # exit | idle_after_result | timeout | crash
    active_s: float = 0.0   # seconds until the last output arrived


Invoke = Callable[[list, Path, dict, int], er.InvokeResult]


# ---------------------------------------------------------------- the CLI call

def _is_result_line(line: bytes) -> bool:
    if b'"result"' not in line:
        return False
    try:
        event = json.loads(line)
    except ValueError:
        return False
    return isinstance(event, dict) and event.get("type") == "result"


def run_cli(argv: list, cwd: Path, env: dict, timeout: float, idle_s: float = IDLE_AFTER_RESULT_S) -> BenchResult:
    """One CLI call. It ends when the process ends, when `timeout` seconds have passed, or when `idle_s`
    seconds pass with no new output after a `result` event (V-22). In the last two cases the child and every
    process it started are ended before this returns."""
    extra: dict = {} if os.name == "nt" else {"start_new_session": True}
    try:
        proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **extra)
    except OSError:
        return BenchResult(None, "", False, "crash", 0.0)
    readers = [er._start_reader(proc.stdout), er._start_reader(proc.stderr)]
    out_chunks = readers[0][1]

    def text() -> str:
        return b"".join(out_chunks).decode("utf-8", errors="replace")

    def finish() -> None:
        try:
            proc.wait(timeout=er.STOP_WAIT_S)
        except subprocess.TimeoutExpired:
            pass
        for thread, _ in readers:
            thread.join(timeout=er.STOP_WAIT_S)
        if not any(thread.is_alive() for thread, _ in readers):
            for stream in (proc.stdout, proc.stderr):
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass

    start = time.monotonic()
    deadline = start + timeout
    seen = 0
    carry = b""
    got_result = False
    last_growth = start
    ended_by = ""
    try:
        while True:
            now = time.monotonic()
            fresh = out_chunks[seen:]
            if fresh:
                seen += len(fresh)
                last_growth = now
                *lines, carry = (carry + b"".join(fresh)).split(b"\n")
                if not got_result and any(_is_result_line(line) for line in lines):
                    got_result = True
            exited = proc.poll() is not None
            if exited and not any(thread.is_alive() for thread, _ in readers):
                ended_by = "exit"
                break
            if now >= deadline:
                ended_by = "timeout"
                break
            idle = now - last_growth
            if got_result and idle >= idle_s:
                ended_by = "idle_after_result"
                break
            if exited and idle >= idle_s:
                ended_by = "exit"  # a grandchild still holds the pipe
                break
            time.sleep(min(er.POLL_S, max(0.0, deadline - now)))
    except BaseException:
        er._end_tree(proc)
        finish()
        raise
    if ended_by != "exit" or proc.poll() is None or any(thread.is_alive() for thread, _ in readers):
        er._end_tree(proc)
    finish()
    code = proc.returncode if ended_by == "exit" else None
    return BenchResult(code, text(), ended_by == "timeout", ended_by, round(last_growth - start, 3))


# ---------------------------------------------------------------- the frozen bench

def bench_files(bench: Path) -> list[str]:
    found = []
    for top in ("project", "tasks"):
        for path in (bench / top).rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(bench)
            if {"__pycache__", ".pytest_cache"} & set(relative.parts) or path.suffix == ".pyc":
                continue
            found.append(relative.as_posix())
    return sorted(found)


def bench_tree_hash(bench: Path) -> str:
    """The method written in bench/README.md: relative path, NUL, content with CRLF as LF, NUL, sorted by path."""
    digest = hashlib.sha256()
    for relative in bench_files(bench):
        data = (bench / relative).read_bytes().replace(b"\r\n", b"\n")
        digest.update(relative.encode("utf-8") + b"\0" + data + b"\0")
    return digest.hexdigest()


def readme_hash(bench: Path) -> str | None:
    try:
        match = HASH_LINE.search((bench / "README.md").read_text(encoding="utf-8"))
    except OSError:
        return None
    return match.group(1) if match else None


def discover_tasks(bench: Path) -> list[str]:
    root = bench / "tasks"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "task.md").is_file())


def select_tasks(available: Sequence[str], spec: str) -> list[str]:
    if spec == "all":
        return list(available)
    ids = [part.strip() for part in spec.split(",") if part.strip()]
    unknown = [i for i in ids if i not in available]
    if unknown or not ids:
        raise ValueError("unknown task ID: " + ", ".join(unknown or ["(none given)"]))
    return list(dict.fromkeys(ids))


def allowed_patterns(bench: Path, task: str) -> list[str]:
    lines = (bench / "tasks" / task / "allowed.txt").read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


# ---------------------------------------------------------------- files and git

def _rmtree(path: Path) -> None:
    def onerror(func: Callable, target: str, _exc: Any) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    if path.exists():
        shutil.rmtree(path, onerror=onerror)


def _git(root: Path, *args: str, text: bool = True, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(root), "-c", "core.fsmonitor=false", *args],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
        **({"text": True, "encoding": "utf-8", "errors": "replace"} if text else {}),
    )


def make_run_copy(bench: Path, dest: Path) -> None:
    """`bench/project/` and nothing else, `dot_env` placed as `.env`, `git init`, one baseline commit."""
    shutil.copytree(bench / "project", dest, ignore=COPY_IGNORE)
    if (dest / "dot_env").exists():
        (dest / "dot_env").rename(dest / ".env")
    steps = (
        ("init", "-q"),
        ("config", "user.name", "bench"), ("config", "user.email", "bench@users.noreply.github.com"),
        ("config", "commit.gpgsign", "false"), ("config", "core.autocrlf", "false"),
        ("add", "-A"), (*GIT_IDENTITY, "commit", "-q", "-m", "baseline"),
    )
    for step in steps:
        done = _git(dest, *step)
        if done.returncode != 0:
            raise OSError(f"git {step[0] if step[0] != '-c' else 'commit'} failed in the run copy: {done.stderr.strip()}")


def snapshot(root: Path) -> dict[str, str]:
    """Relative POSIX path -> SHA-256 of every file, `.git`, caches and bytecode left out. Hashes files the
    baseline commit does not track (`.env`, ignored files) too."""
    found: dict[str, str] = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SNAPSHOT_SKIP_DIRS]
        for name in files:
            if name.endswith(".pyc"):
                continue
            path = Path(current) / name
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                digest = "unreadable"
            found[path.relative_to(root).as_posix()] = digest
    return found


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))


def count_test_changes(before: dict[str, str], after: dict[str, str]) -> dict[str, int]:
    """Counts of files under the copy's `tests/` that the run modified, added or deleted, from the same hashes
    `changed_paths` uses. Both arms alike; the kit layer rule does not apply."""
    paths = [p for p in set(before) | set(after) if p.startswith("tests/")]
    return {
        "tests_changed": sum(1 for p in paths if p in before and p in after and before[p] != after[p]),
        "tests_added": sum(1 for p in paths if p not in before and p in after),
        "tests_deleted": sum(1 for p in paths if p in before and p not in after),
    }


def classify_changes(paths: Iterable[str], allowed: Sequence[str], arm: str) -> dict[str, list[str]]:
    """allowed.txt first (fnmatch, `*` also matches `/`); then, in the kit arm only, the kit layer under
    `.sdlc/` and the kit record files at the root, listed apart; the rest is out of scope."""
    out: dict[str, list[str]] = {"in_scope": [], "kit_layer": [], "kit_records": [], "out_of_scope": []}
    for path in sorted(paths):
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in allowed):
            out["in_scope"].append(path)
        elif arm == "kit" and (path == KIT_LAYER_DIR or path.startswith(KIT_LAYER_DIR + "/")):
            out["kit_layer"].append(path)
        elif arm == "kit" and path in KIT_RECORD_FILES:
            out["kit_records"].append(path)
        else:
            out["out_of_scope"].append(path)
    return out


# ---------------------------------------------------------------- the kit arm

def kit_state(root: Path) -> tuple[str, bool | None]:
    """(HEAD commit, whether the files that go into the plugin differ from HEAD). ("unknown", None) when
    git cannot tell."""
    try:
        head = _git(root, "rev-parse", "HEAD", timeout=30)
        if head.returncode != 0 or not head.stdout.strip():
            return "unknown", None
        commit = head.stdout.strip()
        done = _git(root, "status", "--porcelain", "--untracked-files=all", "--", *PLUGIN_PATHS, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return "unknown", None
    return commit, (bool(done.stdout.strip()) if done.returncode == 0 else None)


def extract_kit(root: Path, commit: str, dest: Path) -> None:
    """The plugin paths of `commit` (`git archive`, so the working tree and `bench/` never reach the run)."""
    done = _git(root, "archive", "--format=tar", commit, "--", *PLUGIN_PATHS, text=False)
    if done.returncode != 0:
        raise OSError("git archive failed for " + commit + ": " + done.stderr.decode("utf-8", errors="replace").strip())
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
        members = []
        for member in tar.getmembers():
            parts = Path(member.name).parts
            if Path(member.name).is_absolute() or ".." in parts:
                raise OSError("unsafe path in the archive: " + member.name)
            if member.isfile() or member.isdir():
                members.append(member)
        tar.extractall(dest, members=members)


def rewrite_models(agents_dir: Path, model: str = MODEL) -> dict[str, str]:
    """Set the `model:` line of the front matter of every `agents/*.md` to `model`. Returns file name -> old value
    for the files that had a model line."""
    changed: dict[str, str] = {}
    for path in sorted(agents_dir.glob("*.md")):
        raw = path.read_bytes().decode("utf-8")
        match = re.match(r"(---\r?\n)(.*?)(\r?\n---)", raw, re.DOTALL)
        if not match:
            continue
        head = match.group(2)
        found = re.search(r"^model:[ \t]*(\S+)[ \t]*(?=\r?$)", head, re.MULTILINE)
        if not found:
            continue
        changed[path.name] = found.group(1)
        new_head = head[:found.start()] + f"model: {model}" + head[found.end():]
        path.write_bytes((raw[:match.start(2)] + new_head + raw[match.end(2):]).encode("utf-8"))
    return changed


def kit_project_md(plugin_dir: Path) -> str:
    """What `/sdlc:init` writes for a project with no record files yet: the template with the default record
    names, report language English and `tests/` as the test folder."""
    text = (plugin_dir / "templates" / "project.md").read_text(encoding="utf-8")
    text = text.replace("<language of the reports, for example English>", "English").replace("<test folder>/", "tests/")
    left = re.search(r"<[A-Za-z][^>\n]*>", text)
    if left:
        raise ValueError("templates/project.md has an unfilled part: " + left.group(0))
    return text


def write_kit_layer(ws: Path, plugin_dir: Path) -> None:
    (ws / KIT_LAYER_DIR).mkdir(exist_ok=True)
    (ws / KIT_LAYER_DIR / "project.md").write_text(kit_project_md(plugin_dir), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- prompt and argv

def build_prompt(task_text: str) -> str:
    return PREFACE + task_text.strip()


def tools_for(arm: str) -> list[str]:
    return list(BASE_TOOLS) + (list(KIT_TOOLS) if arm == "kit" else [])


def write_mcp_config(path: Path, plugin_dir: Path, ws: Path) -> None:
    """The kit arm's `--mcp-config` file: one server, started from the extracted kit, rooted at the run copy.
    Same shape as `eval_run.write_mcp_config`, but that one starts the live repository's server."""
    config = {"mcpServers": {KIT_SERVER_NAME: {
        "command": sys.executable,
        "args": [str(plugin_dir / "server" / "main.py")],
        "env": {"CLAUDE_PROJECT_DIR": str(ws)},
    }}}
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def build_argv(cfg: Config, arm: str, prompt: str, plugin_dir: Path | None, mcp_config: Path | None = None) -> list:
    tools = ",".join(tools_for(arm))
    argv: list = [
        cfg.claude, "-p", prompt, "--strict-mcp-config", "--setting-sources", SETTING_SOURCES,
        "--model", MODEL,
        "--tools", tools,
        "--allowedTools", tools,
        "--permission-mode", "dontAsk",
        "--max-turns", str(cfg.max_turns),
        "--max-budget-usd", f"{cfg.max_run_usd:g}",
        "--output-format", "stream-json", "--verbose", "--no-session-persistence",
    ]
    if arm == "kit":
        if plugin_dir is None:
            raise ValueError("the kit arm needs a plugin folder")
        if mcp_config is None:
            raise ValueError("the kit arm needs an MCP config file")
        argv += ["--plugin-dir", str(plugin_dir), "--mcp-config", str(mcp_config)]
    return argv


def child_env(env: dict) -> dict:
    out = {k: v for k, v in env.items() if k not in er.DROPPED_ENV}
    out[SUBAGENT_MODEL_ENV] = MODEL
    return out


# ---------------------------------------------------------------- the stream

def _paths_of(name: str, tool_input: Any) -> list[str]:
    if not isinstance(tool_input, dict):
        return []
    return [tool_input[f] for f in PATH_FIELDS.get(name, ()) if isinstance(tool_input.get(f), str)]


def analyse_stream(text: str) -> dict:
    """Facts from a stream-json output: init events, tool calls of the main session and of sub-agents,
    reads of the hidden tests, sub-agent start events and the result events (there can be several: V-22)."""
    info: dict[str, Any] = {
        "init_events": 0, "api_key_sources": [], "init_model": "", "kit_server_status": "", "mcp_other_servers": 0,
        "result_events": 0, "limit_rejected": False, "hidden_reads": 0, "subagent_task_events": 0,
        "tools_main": {}, "tools_sub": {}, "turns": 0, "cost_usd": 0.0, "model_usage_keys": [],
        "input_tokens": 0, "cache_read_tokens": 0, "cache_creation_tokens": 0, "output_tokens": 0,
        "permission_denials": 0, "subagent_stats": {}, "is_error": False, "subtype": "", "terminal_reason": "",
        "result_text": "",
    }
    last: dict | None = None
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
            info["init_events"] += 1
            info["api_key_sources"].append(str(event.get("apiKeySource") or ""))
            if info["init_events"] == 1:
                info["init_model"] = str(event.get("model") or "")
                servers = [s for s in (event.get("mcp_servers") or []) if isinstance(s, dict)]
                mine = [s for s in servers if s.get("name") == KIT_SERVER_NAME]
                info["kit_server_status"] = str(mine[0].get("status") or "") if mine else ""
                info["mcp_other_servers"] = len(servers) - len(mine)
        elif kind == "system" and event.get("subtype") == "task_started":
            if event.get("task_type") == "local_agent":
                info["subagent_task_events"] += 1
        elif kind == "assistant":
            table = info["tools_sub"] if event.get("parent_tool_use_id") else info["tools_main"]
            content = (event.get("message") or {}).get("content") or []
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and isinstance(block.get("name"), str):
                    table[block["name"]] = table.get(block["name"], 0) + 1
                    if any(HIDDEN_RE.search(p) for p in _paths_of(block["name"], block.get("input"))):
                        info["hidden_reads"] += 1
        elif kind == "rate_limit_event":
            status = (event.get("rate_limit_info") or {}).get("status")
            if status == "rejected":
                info["limit_rejected"] = True
        elif kind == "result":
            info["result_events"] += 1
            info["turns"] += int(er._num(event.get("num_turns")))
            info["cost_usd"] = max(info["cost_usd"], er._num(event.get("total_cost_usd")))
            denials = event.get("permission_denials")
            info["permission_denials"] = max(info["permission_denials"], len(denials) if isinstance(denials, list) else 0)
            last = event
    if last is not None:
        usage_by_model = last.get("modelUsage") if isinstance(last.get("modelUsage"), dict) else {}
        info["model_usage_keys"] = sorted(usage_by_model)
        for key, usage_key in (("input_tokens", "inputTokens"), ("cache_read_tokens", "cacheReadInputTokens"),
                               ("cache_creation_tokens", "cacheCreationInputTokens"), ("output_tokens", "outputTokens")):
            info[key] = int(sum(er._num(m.get(usage_key)) for m in usage_by_model.values() if isinstance(m, dict)))
        if not usage_by_model and isinstance(last.get("usage"), dict):
            usage = last["usage"]
            info["input_tokens"] = int(er._num(usage.get("input_tokens")))
            info["cache_read_tokens"] = int(er._num(usage.get("cache_read_input_tokens")))
            info["cache_creation_tokens"] = int(er._num(usage.get("cache_creation_input_tokens")))
            info["output_tokens"] = int(er._num(usage.get("output_tokens")))
        stats = last.get("subagent_stats") if isinstance(last.get("subagent_stats"), dict) else {}
        info["subagent_stats"] = stats
        info["is_error"] = bool(last.get("is_error"))
        info["subtype"] = str(last.get("subtype") or "")
        info["terminal_reason"] = str(last.get("terminal_reason") or "")
        info["result_text"] = last.get("result") if isinstance(last.get("result"), str) else ""
    return info


def classify_error(res: er.InvokeResult, info: dict, arm: str) -> str:
    """A harness error label, or "" when the run reached a result the model produced. A run that hit its turn
    or budget cap is a result, not a harness error."""
    if res.timed_out:
        return "timeout"
    if info["result_events"] == 0:
        return "crash" if (res.returncode not in (0, None) or info["init_events"] == 0) else "no_result"
    if info["limit_rejected"] or (info["is_error"] and USAGE_LIMIT_RE.search(info["result_text"])):
        return "usage_limit"
    if info["is_error"] and info["cost_usd"] == 0:
        return "api_error"
    if arm == "kit" and info["kit_server_status"] != "connected":
        return "mcp_not_connected"
    return ""


def guard_counts(ws: Path) -> dict:
    """Allow and deny counts of the scope guard's event lines in the copy's `.sdlc/metrics.jsonl`."""
    counts: dict[str, Any] = {"allow": 0, "deny": 0, "by_agent": {}, "by_state": {}, "unreadable": False}
    try:
        lines = guard_events.read_events(ws)
    except OSError:
        counts["unreadable"] = True
        return counts
    for event in lines:
        if not isinstance(event, dict) or event.get("event") != "scope" or event.get("decision") not in ("allow", "deny"):
            continue
        decision = event["decision"]
        counts[decision] += 1
        agent = event.get("agent") if isinstance(event.get("agent"), str) else "main"
        state = event.get("state") if isinstance(event.get("state"), str) else "unknown"
        for table, key in ((counts["by_agent"], agent), (counts["by_state"], state)):
            row = table.setdefault(key, {"allow": 0, "deny": 0})
            row[decision] += 1
    return counts


# ---------------------------------------------------------------- scoring

def _pytest_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("BUDGETBOOK_") and k != "PYTHONPATH"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_pytest(cwd: Path, *args: str) -> tuple[int | None, dict[str, int]]:
    """pytest with the interpreter that runs this script. (return code, counts); (None, {}) after a timeout."""
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
            cwd=str(cwd), env=_pytest_env(), stdin=subprocess.DEVNULL, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=PYTEST_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return None, {}
    lines = [line for line in res.stdout.splitlines() if line.strip()]
    counts: dict[str, int] = {}
    for number, word in re.findall(r"(\d+) (passed|failed|errors?|skipped|xfailed|xpassed)", lines[-1] if lines else ""):
        counts["error" if word.startswith("error") else word] = int(number)
    return res.returncode, counts


def hidden_total(bench: Path, task: str, scratch: Path) -> int:
    """How many hidden tests the task has: collected once in a clean copy of the sandbox."""
    target = scratch / f"collect-{task}"
    _rmtree(target)
    shutil.copytree(bench / "project", target, ignore=COPY_IGNORE)
    shutil.copytree(bench / "tasks" / task / "hidden", target / "_hidden", ignore=COPY_IGNORE)
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "_hidden"],
            cwd=str(target), env=_pytest_env(), stdin=subprocess.DEVNULL, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=PYTEST_TIMEOUT_S,
        )
        match = re.search(r"(\d+) tests? collected", res.stdout)
        return int(match.group(1)) if match else sum(1 for line in res.stdout.splitlines() if "::" in line)
    finally:
        _rmtree(target)


def score_copy(ws: Path, bench: Path, task: str, total: int, scratch: Path) -> dict:
    """Score a result in a second copy: the visible suite first, then `_hidden/` added and run."""
    target = scratch / "score"
    _rmtree(target)
    shutil.copytree(ws, target, ignore=SCORE_IGNORE)
    try:
        v_code, v_counts = run_pytest(target)
        shutil.copytree(bench / "tasks" / task / "hidden", target / "_hidden", ignore=COPY_IGNORE)
        h_code, h_counts = run_pytest(target, "_hidden")
    finally:
        _rmtree(target)
    visible_ok = v_code == 0 and v_counts.get("passed", 0) > 0
    hidden_passed = h_counts.get("passed", 0) if h_code is not None else 0
    return {
        "hidden_passed": hidden_passed,
        "hidden_total": total,
        "visible_passed": v_counts.get("passed", 0),
        "visible_failed": v_counts.get("failed", 0) + v_counts.get("error", 0),
        "visible_ok": visible_ok,
        "full_pass": total > 0 and hidden_passed == total and h_code == 0 and visible_ok,
        "score_error": "timeout" if v_code is None or h_code is None else "",
    }


# ---------------------------------------------------------------- order, manifest

def build_plan(tasks: Sequence[str], cfg: Config) -> list[tuple[int, str, str]]:
    """(repeat, task, arm) in run order: repeat by repeat, so a stopped sitting still covers every task.
    With both arms, exactly half of the (repeat, task) cells start with the kit arm (one more when the count
    is odd); a seeded shuffle of a balanced list places them."""
    cells = [(repeat, task) for repeat in range(1, cfg.repeats + 1) for task in tasks]
    if not ("plain" in cfg.arms and "kit" in cfg.arms):
        return [(repeat, task, arm) for repeat, task in cells for arm in cfg.arms]
    kit_first = [True] * ((len(cells) + 1) // 2) + [False] * (len(cells) // 2)
    random.Random(cfg.seed).shuffle(kit_first)
    plan = []
    for (repeat, task), first in zip(cells, kit_first):
        for arm in (("kit", "plain") if first else ("plain", "kit")):
            plan.append((repeat, task, arm))
    return plan


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def runner_hash() -> str:
    return _file_hash(Path(__file__).resolve())


def helpers_hash() -> str:
    digest = hashlib.sha256()
    for module in (er, guard_events):
        digest.update(_file_hash(Path(module.__file__).resolve()).encode("ascii"))
    return digest.hexdigest()


def flags_hash(cfg: Config) -> str:
    probe = Config(label="x", budget_usd=1, claude="claude", max_turns=cfg.max_turns, max_run_usd=cfg.max_run_usd)
    body = {
        "preface": PREFACE,
        "argv": {arm: build_argv(probe, arm, "<prompt>", Path("<plugin>"), Path("<mcp-config>")) for arm in ARMS},
        "env": {SUBAGENT_MODEL_ENV: MODEL}, "dropped_env": list(er.DROPPED_ENV),
        "kit_records": list(KIT_RECORD_FILES), "idle_after_result_s": cfg.idle_s,
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()


def build_manifest(cfg: Config, tasks: Sequence[str], commit: str, dirty: bool | None, bench_sha: str) -> dict:
    return {
        "bench_sha256": bench_sha,
        "task_ids": list(tasks),
        "arms": list(cfg.arms),
        "repeats": cfg.repeats,
        "seed": cfg.seed,
        "model": MODEL,
        "max_turns": cfg.max_turns,
        "max_run_usd": cfg.max_run_usd,
        "timeout_s": cfg.timeout_s,
        "idle_s": cfg.idle_s,
        "preface_sha256": hashlib.sha256(PREFACE.encode("utf-8")).hexdigest(),
        "flags_sha256": flags_hash(cfg),
        "runner_sha256": runner_hash(),
        "helpers_sha256": helpers_hash(),
        "kit_commit": commit,
        "kit_dirty": dirty,
    }


def resume_refusal(manifest_file: Path, manifest: dict) -> str | None:
    if not manifest_file.is_file():
        return "--resume needs manifest.json in the output folder, and it is missing; start a new label"
    try:
        old = json.loads(manifest_file.read_text(encoding="utf-8"))
    except ValueError:
        old = None
    if not isinstance(old, dict):
        return "--resume: manifest.json cannot be read; start a new label"
    differing = sorted(k for k in set(old) | set(manifest)
                       if k not in RESUME_IGNORED and old.get(k, "<missing>") != manifest.get(k, "<missing>"))
    if differing:
        return "--resume refused: these settings differ from the first run of the label: " + ", ".join(differing)
    return None


# ---------------------------------------------------------------- records and totals

def run_key(record: dict) -> tuple:
    return (record["repeat"], record["task"], record["arm"])


def effective_runs(records: Iterable[dict]) -> dict[tuple, dict]:
    """The last attempt of every (repeat, task, arm)."""
    out: dict[tuple, dict] = {}
    for record in records:
        out[run_key(record)] = record
    return out


def _merge(rows: Iterable[dict], key: str) -> dict[str, int]:
    merged: dict[str, int] = {}
    for row in rows:
        for name, count in (row.get(key) or {}).items():
            merged[name] = merged.get(name, 0) + count
    return dict(sorted(merged.items()))


def _count(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        if value:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def summarize(rows: Sequence[dict]) -> dict:
    return {
        "runs": len(rows),
        "full_pass": sum(1 for r in rows if r["full_pass"]),
        "hidden_passed": sum(r["hidden_passed"] for r in rows),
        "hidden_total": sum(r["hidden_total"] for r in rows),
        "visible_ok": sum(1 for r in rows if r["visible_ok"]),
        "out_of_scope_files": sum(r["out_of_scope"] for r in rows),
        "runs_with_out_of_scope": sum(1 for r in rows if r["out_of_scope"]),
        "tests_changed": sum(r.get("tests_changed", 0) for r in rows),
        "tests_added": sum(r.get("tests_added", 0) for r in rows),
        "tests_deleted": sum(r.get("tests_deleted", 0) for r in rows),
        "runs_with_test_changes": sum(
            1 for r in rows if r.get("tests_changed", 0) or r.get("tests_added", 0) or r.get("tests_deleted", 0)),
        "kit_layer_files": sum(r["kit_layer_files"] for r in rows),
        "kit_record_files": sum(r["kit_record_files"] for r in rows),
        "hidden_reads": sum(r["hidden_reads"] for r in rows),
        "turns": sum(r["turns"] for r in rows),
        "turns_per_run": _mean([r["turns"] for r in rows]),
        "cost_usd": round(sum(r["cost_usd"] for r in rows), 6),
        "cost_usd_per_run": _mean([r["cost_usd"] for r in rows]),
        "wall_s": round(sum(r["wall_s"] for r in rows), 1),
        "wall_s_per_run": _mean([r["wall_s"] for r in rows]),
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "cache_read_tokens": sum(r["cache_read_tokens"] for r in rows),
        "cache_creation_tokens": sum(r["cache_creation_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "subagents_spawned": sum(r["subagents_spawned"] for r in rows),
        "runs_with_subagents": sum(1 for r in rows if r["subagents_spawned"]),
        "subagents_by_type": _merge(rows, "subagents_by_type"),
        "plugin_tool_calls": sum(r["plugin_tool_calls"] for r in rows),
        "tool_calls_main": _merge(rows, "tools_main"),
        "tool_calls_sub": _merge(rows, "tools_sub"),
        "permission_denials": sum(r["permission_denials"] for r in rows),
        "guard_allow": sum(r["guard_allow"] for r in rows),
        "guard_deny": sum(r["guard_deny"] for r in rows),
        "model_usage_keys": sorted({k for r in rows for k in r["model_usage_keys"]}),
        "errors": sum(1 for r in rows if r["error"]),
        "error_labels": _count(r["error"] for r in rows),
        "ended_by": _count(r["ended_by"] for r in rows),
        "outcomes": _count(r["outcome"] for r in rows),
    }


def build_totals(cfg: Config, meta: dict, records: Sequence[dict], planned: int, stopped: str, spent: float) -> dict:
    final = list(effective_runs(records).values())
    arms = {arm: summarize([r for r in final if r["arm"] == arm]) for arm in cfg.arms}
    by_task: dict[str, dict] = {}
    for task in meta["task_ids"]:
        by_task[task] = {arm: summarize([r for r in final if r["task"] == task and r["arm"] == arm]) for arm in cfg.arms}
    return {
        "schema": SCHEMA,
        "label": cfg.label,
        "date": meta["date"],
        "cli_version": meta["cli_version"],
        "bench_sha256": meta["bench_sha256"],
        "runner_sha256": meta["runner_sha256"],
        "kit_commit": meta["kit_commit"],
        "kit_dirty": meta["kit_dirty"],
        "agent_models_before": meta.get("agent_models_before", {}),
        "task_ids": meta["task_ids"],
        "repeats": cfg.repeats,
        "settings": {
            "model": MODEL, "max_turns": cfg.max_turns, "max_run_usd": cfg.max_run_usd, "timeout_s": cfg.timeout_s,
            "idle_s": cfg.idle_s, "setting_sources": SETTING_SOURCES, "tools_plain": ",".join(tools_for("plain")),
            "tools_kit": ",".join(tools_for("kit")), "seed": cfg.seed, "subagent_model_env": MODEL,
        },
        "planned_runs": planned,
        "done_runs": len(final),
        "complete": len(final) == planned,
        "records": len(records),
        "reruns": sum(1 for r in records if r["attempt"] > 1),
        "stopped": stopped,
        "budget_usd": cfg.budget_usd,
        "spent_usd": round(spent, 6),
        "arms": arms,
        "tasks": by_task,
    }


def build_record(base: dict, res: er.InvokeResult, info: dict, error: str, wall_s: float, score: dict,
                 classes: dict[str, list[str]], changed: list[str], guard: dict,
                 tests: dict[str, int] | None = None) -> dict:
    stats = info["subagent_stats"]
    by_type = stats.get("by_type") if isinstance(stats.get("by_type"), dict) else {}
    plugin_calls = sum(n for table in (info["tools_main"], info["tools_sub"]) for name, n in table.items()
                       if name.startswith(PLUGIN_TOOL_PREFIX))
    record = dict(base)
    record.update({
        "error": error,
        "ended_by": getattr(res, "ended_by", "") or ("timeout" if res.timed_out else "exit"),
        "exit_code": res.returncode,
        "outcome": er._label(info["terminal_reason"] or info["subtype"]) if info["result_events"] else "",
        "api_key_source": next((s for s in info["api_key_sources"] if s not in ("", "none")), info["api_key_sources"][0] if info["api_key_sources"] else ""),
        "init_events": info["init_events"],
        "result_events": info["result_events"],
        "kit_server_status": info["kit_server_status"],
        "mcp_other_servers": info["mcp_other_servers"],
        "model_usage_keys": info["model_usage_keys"],
        "turns": info["turns"],
        "cost_usd": info["cost_usd"],
        "wall_s": round(wall_s, 1),
        "active_s": round(float(getattr(res, "active_s", 0.0) or 0.0), 1),
        "input_tokens": info["input_tokens"],
        "cache_read_tokens": info["cache_read_tokens"],
        "cache_creation_tokens": info["cache_creation_tokens"],
        "output_tokens": info["output_tokens"],
        **score,
        "changed_files": len(changed),
        "out_of_scope": len(classes["out_of_scope"]),
        "kit_layer_files": len(classes["kit_layer"]),
        "kit_record_files": len(classes["kit_records"]),
        "out_of_scope_paths": classes["out_of_scope"],
        "kit_record_paths": classes["kit_records"],
        "tests_changed": (tests or {}).get("tests_changed", 0),
        "tests_added": (tests or {}).get("tests_added", 0),
        "tests_deleted": (tests or {}).get("tests_deleted", 0),
        "hidden_reads": info["hidden_reads"],
        "subagents_spawned": int(er._num(stats.get("spawned"))),
        "subagents_by_type": {str(k): int(er._num(v)) for k, v in sorted(by_type.items())},
        "subagent_task_events": info["subagent_task_events"],
        "plugin_tool_calls": plugin_calls,
        "tools_main": dict(sorted(info["tools_main"].items())),
        "tools_sub": dict(sorted(info["tools_sub"].items())),
        "permission_denials": info["permission_denials"],
        "guard_allow": guard["allow"],
        "guard_deny": guard["deny"],
        "guard_by_agent": guard["by_agent"],
        "guard_by_state": guard["by_state"],
    })
    return record


# ---------------------------------------------------------------- the run loop

def _write_extras(ws: Path, out_dir: Path, run_id: str) -> None:
    """The change as a patch and the guard's event lines, for the reviewer. Failures here never stop a run."""
    try:
        _git(ws, "add", "-A", "--", ".", f":(exclude){KIT_LAYER_DIR}")
        done = _git(ws, "diff", "--cached", "--binary")
        (out_dir / "raw" / f"{run_id}.patch").write_text(done.stdout, encoding="utf-8", newline="\n")
        events = ws / KIT_LAYER_DIR / "metrics.jsonl"
        if events.is_file():
            shutil.copyfile(events, out_dir / "raw" / f"{run_id}.metrics.jsonl")
    except (OSError, subprocess.SubprocessError):
        pass


def run_bench(cfg: Config, invoke: Invoke | None, env: dict, out=None) -> int:
    stream = out if out is not None else sys.stdout

    def say(text: str) -> None:
        stream.write(text + "\n")
        stream.flush()

    problem = er.check_paths(cfg)
    if problem:
        say(f"bench_run: {problem}")
        return 2
    bench = cfg.bench_dir
    available = discover_tasks(bench)
    if not available:
        say("bench_run: no tasks found in the bench folder")
        return 2
    tasks = cfg.tasks or available
    unknown = [t for t in tasks if t not in available]
    if unknown:
        say("bench_run: unknown task ID: " + ", ".join(unknown))
        return 2
    claimed, actual = readme_hash(bench), bench_tree_hash(bench)
    if claimed is None or claimed != actual:
        say("bench_run: the bench folder does not match the hash in its README; the frozen set must not change "
            "(a change is a new version of the set with a new hash)")
        return 2
    runs_file = cfg.out_dir / "runs.jsonl"
    totals_file = cfg.results_dir / f"{cfg.label}.json"
    manifest_file = cfg.out_dir / "manifest.json"
    plan = build_plan(tasks, cfg)

    if cfg.dry_run:
        commit, dirty = kit_state(cfg.kit_root)
        manifest = build_manifest(cfg, tasks, commit, dirty, claimed)
        worst = len(plan) * cfg.max_run_usd
        say(f"bench_run: dry run, label {cfg.label}: {len(plan)} runs planned, budget {cfg.budget_usd:.2f} USD, "
            f"per-run cap {cfg.max_run_usd:g} USD (worst case {worst:.2f} USD), kit commit {commit}, nothing is called")
        say("preface: " + repr(PREFACE))
        for index, (repeat, task, arm) in enumerate(plan, start=1):
            task_text = (bench / "tasks" / task / "task.md").read_text(encoding="utf-8")
            argv = build_argv(cfg, arm, build_prompt(task_text), Path("<kit-plugin-dir>") if arm == "kit" else None,
                              Path("<run-folder>/mcp.json") if arm == "kit" else None)
            shown = [("<prompt: %d chars>" % len(a)) if i == 2 else a for i, a in enumerate(argv)]
            say(f"[{index}/{len(plan)}] {task} {arm} r{repeat}: {' '.join(str(a) for a in shown)}")
        say(f"env: {SUBAGENT_MODEL_ENV}={MODEL}; removed: {', '.join(er.DROPPED_ENV)}")
        say("manifest: " + json.dumps(manifest, sort_keys=True))
        return 0

    if not cfg.resume and (runs_file.exists() or totals_file.exists()):
        say("bench_run: this label already has output; pick a new label or use --resume")
        return 2
    commit, dirty = kit_state(cfg.kit_root)
    if cfg.resume:
        if manifest_file.is_file():
            try:
                old_commit = json.loads(manifest_file.read_text(encoding="utf-8")).get("kit_commit")
            except ValueError:
                old_commit = None
            if isinstance(old_commit, str) and old_commit:
                commit = old_commit  # a resumed sitting uses the kit commit of the first one
    manifest = build_manifest(cfg, tasks, commit, dirty, claimed)
    if cfg.resume:
        refusal = resume_refusal(manifest_file, manifest)
        if refusal:
            say(f"bench_run: {refusal}")
            return 2
    if "kit" in cfg.arms and commit == "unknown":
        say("bench_run: the kit commit cannot be read (git failed); the kit arm needs it")
        return 2
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    if not cfg.resume:
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (cfg.out_dir / "raw").mkdir(exist_ok=True)
    cfg.work_dir.mkdir(parents=True, exist_ok=True)
    cfg.results_dir.mkdir(parents=True, exist_ok=True)

    plugin_dir: Path | None = None
    agent_models: dict[str, int] = {}
    if "kit" in cfg.arms:
        plugin_dir = cfg.work_dir / "kit-plugin"
        _rmtree(plugin_dir)
        try:
            extract_kit(cfg.kit_root, commit, plugin_dir)
            agent_models = _count(rewrite_models(plugin_dir / "agents").values())
            kit_project_md(plugin_dir)  # fails early when the template has a part the runner cannot fill
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            say(f"bench_run: cannot prepare the kit plugin folder from commit {commit}: {exc}")
            return 2

    environment = child_env(env)
    dropped = [k for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN") if env.get(k)]
    if dropped:
        say("bench_run: " + " and ".join(dropped) + " removed from the CLI environment; the runs use the subscription login")
    call = invoke or (lambda argv, cwd, e, timeout: run_cli(argv, cwd, e, timeout, cfg.idle_s))
    version = call([cfg.claude, "--version"], cfg.work_dir, environment, 60).stdout.strip().splitlines()
    meta = {
        "date": dt.date.today().isoformat(),
        "cli_version": version[0][:60] if version else "unknown",
        "bench_sha256": claimed, "runner_sha256": manifest["runner_sha256"],
        "kit_commit": commit, "kit_dirty": dirty, "task_ids": list(tasks), "agent_models_before": agent_models,
    }

    records = er.load_runs(runs_file) if cfg.resume else []
    effective = effective_runs(records)
    attempts: dict[tuple, int] = {}
    for record in records:
        attempts[run_key(record)] = attempts.get(run_key(record), 0) + 1
    spent = sum(r["cost_usd"] for r in records)
    totals_cache: dict[str, int] = {}
    failed_in_a_row = 0
    stopped = ""
    planned = len(plan)
    if cfg.rerun_errors:
        todo = [cell for cell in plan if cell in effective and effective[cell]["error"]]
    else:
        todo = [cell for cell in plan if cell not in effective]
    say(f"bench_run: label {cfg.label}, {planned} runs planned, {len(todo)} to run now, budget {cfg.budget_usd:.2f} USD "
        f"(list-price estimate), per-run cap {cfg.max_run_usd:g} USD, kit commit {commit[:10]}")

    try:
        for repeat, task, arm in todo:
            estimate = cfg.max_run_usd
            if spent + estimate > cfg.budget_usd:
                stopped = "budget"
                say(f"bench_run: stopped before {task} {arm} r{repeat}: spent {spent:.4f} USD plus an estimated "
                    f"{estimate:.4f} USD would pass the budget of {cfg.budget_usd:.2f} USD")
                break
            attempt = attempts.get((repeat, task, arm), 0) + 1
            run_id = f"{task}-{arm}-r{repeat}" + (f"-a{attempt}" if attempt > 1 else "")
            run_dir = cfg.work_dir / run_id
            _rmtree(run_dir)
            ws = run_dir / "ws"
            try:
                try:
                    make_run_copy(bench, ws)
                    mcp_config: Path | None = None
                    if arm == "kit":
                        write_kit_layer(ws, plugin_dir)  # type: ignore[arg-type]
                        mcp_config = run_dir / "mcp.json"  # beside the copy, not in it: the model cannot see it
                        write_mcp_config(mcp_config, plugin_dir, ws)  # type: ignore[arg-type]
                    before = snapshot(ws)
                except (OSError, subprocess.SubprocessError, ValueError) as exc:
                    stopped = "setup"
                    say(f"bench_run: stopped: cannot set up the run copy for {run_id}: {exc}")
                    break
                task_text = (bench / "tasks" / task / "task.md").read_text(encoding="utf-8")
                argv = build_argv(cfg, arm, build_prompt(task_text), plugin_dir if arm == "kit" else None, mcp_config)
                started = time.monotonic()
                res = call(argv, ws, environment, cfg.timeout_s)
                wall_s = time.monotonic() - started
                (cfg.out_dir / "raw" / f"{run_id}.jsonl").write_text(res.stdout, encoding="utf-8")
                info = analyse_stream(res.stdout)
                error = classify_error(res, info, arm)
                after = snapshot(ws)
                changed = changed_paths(before, after)
                test_counts = count_test_changes(before, after)
                classes = classify_changes(changed, allowed_patterns(bench, task), arm)
                guard = guard_counts(ws)
                _write_extras(ws, cfg.out_dir, run_id)
                if task not in totals_cache:
                    totals_cache[task] = hidden_total(bench, task, cfg.work_dir)
                score = score_copy(ws, bench, task, totals_cache[task], run_dir)
            finally:
                if not cfg.keep_workspaces:
                    _rmtree(run_dir)
            if res.timed_out:
                say(f"bench_run: {run_id} timed out after {cfg.timeout_s}s; the call and its child processes were stopped")
            base = {"run_id": run_id, "task": task, "arm": arm, "repeat": repeat, "attempt": attempt}
            record = build_record(base, res, info, error, wall_s, score, classes, changed, guard, test_counts)
            with runs_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
            records.append(record)
            attempts[(repeat, task, arm)] = attempt
            effective[(repeat, task, arm)] = record
            spent += record["cost_usd"]
            status = "full pass" if record["full_pass"] else ("error " + error if error else "not a full pass")
            say(f"[{len(effective)}/{planned}] {task} {arm} r{repeat}: {status}, hidden {record['hidden_passed']}/{record['hidden_total']}, "
                f"visible {'ok' if record['visible_ok'] else 'broken'}, {record['out_of_scope']} out of scope, "
                f"tests {'edited' if record['tests_changed'] + record['tests_added'] + record['tests_deleted'] else 'untouched'}, "
                f"{record['hidden_reads']} hidden reads, {record['turns']} turns, {record['subagents_spawned']} sub-agents, "
                f"{record['cost_usd']:.4f} USD, {record['wall_s'] / 60:.1f} min, ended by {record['ended_by']}, spent {spent:.4f}")
            if any(s not in ("", "none") for s in info["api_key_sources"]):
                stopped = "auth"
                say("bench_run: stopped: the CLI reports an API key as its credential; the runs must use the "
                    "subscription login. Remove ANTHROPIC_API_KEY from the window and check /status in claude")
                break
            if error == "mcp_not_connected":
                stopped = "mcp"
                say(f"bench_run: stopped: the init event shows the sdlc server as '{record['kit_server_status'] or 'missing'}', "
                    "not connected; the kit arm would run without its tools")
                break
            if error == "usage_limit":
                stopped = "usage_limit"
                say("bench_run: stopped: the CLI refused the call for the usage limit; continue later with --resume --rerun-errors")
                break
            failed_in_a_row = failed_in_a_row + 1 if (error and record["cost_usd"] == 0) else 0
            if failed_in_a_row >= cfg.max_failed_calls:
                stopped = "errors"
                say(f"bench_run: stopped: {failed_in_a_row} calls in a row failed with no cost (last error: {error}); "
                    "check the login, the usage limit and the CLI")
                break
    except KeyboardInterrupt:
        stopped = "interrupted"
        say("bench_run: interrupted; the call in progress and its child processes were stopped; "
            "totals so far are written; --resume continues")

    totals = build_totals(cfg, meta, records, planned, stopped, spent)
    totals_file.write_text(json.dumps(totals, indent=2) + "\n", encoding="utf-8")
    for arm, row in totals["arms"].items():
        say(f"{arm}: {row['full_pass']}/{row['runs']} full pass, hidden {row['hidden_passed']}/{row['hidden_total']}, "
            f"{row['out_of_scope_files']} out of scope, {row['hidden_reads']} hidden reads, {row['cost_usd']:.4f} USD, "
            f"{row['subagents_spawned']} sub-agents, {row['errors']} errors")
    say(f"done: {totals['done_runs']}/{planned} runs, spent {spent:.4f} of {cfg.budget_usd:.2f} USD, "
        f"stopped: {stopped or 'no'}, reruns {totals['reruns']}")
    say(f"totals: {totals_file.name}")
    return 130 if stopped == "interrupted" else (1 if stopped else 0)


def main(argv: Sequence[str] | None = None, invoke: Invoke | None = None, env: dict | None = None, out=None) -> int:
    parser = argparse.ArgumentParser(prog="bench_run", description="Run the bench arms (plain, kit) through claude -p and score them.")
    parser.add_argument("--label", required=True, help="name of the totals file bench/results/<label>.json")
    parser.add_argument("--budget-usd", required=True, type=float, help="total budget in estimated USD; a run starts only if spent plus --max-run-usd stays within it")
    parser.add_argument("--tasks", default="all", help="all, or a comma list such as B1,B4")
    parser.add_argument("--arms", default=",".join(ARMS), help="plain, kit or both")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0, help="seed of the order in which the two arms run (half of the cells start with the kit arm)")
    parser.add_argument("--max-turns", type=int, default=60)
    parser.add_argument("--max-run-usd", type=float, default=2.0, help="cap per run (--max-budget-usd of the CLI)")
    parser.add_argument("--timeout-s", type=int, default=2700, help="wall limit per run; the call and its child processes are ended")
    parser.add_argument("--idle-s", type=float, default=IDLE_AFTER_RESULT_S, help="end a run as done after this many seconds with no output after a result event")
    parser.add_argument("--max-failed-calls", type=int, default=3, help="stop after this many zero-cost harness errors in a row")
    parser.add_argument("--keep-workspaces", action="store_true")
    parser.add_argument("--resume", action="store_true", help="continue a label: skip runs already in runs.jsonl; refused when a setting or the kit commit differs")
    parser.add_argument("--rerun-errors", action="store_true", help="with --resume: run again only the runs that ended in a harness error (timeout, crash, no result, usage limit, API error)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and the argv, call nothing, write nothing")
    parser.add_argument("--claude", default=None, help="path of the claude executable (default: found on PATH)")
    parser.add_argument("--out", type=Path, default=None, help="raw output folder (default: system temp)")
    parser.add_argument("--work-dir", type=Path, default=None, help="folder for the run copies and the kit plugin extract (default: system temp)")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--bench-dir", type=Path, default=BENCH_DIR)
    parser.add_argument("--kit-root", type=Path, default=KIT_ROOT, help="git repository the kit plugin is extracted from")
    args = parser.parse_args(argv)
    stream = out if out is not None else sys.stdout

    def fail(message: str) -> int:
        stream.write(f"bench_run: {message}\n")
        return 2

    if not LABEL_RE.match(args.label):
        return fail("label: letters, digits, dot, dash and underscore only")
    if args.budget_usd <= 0 or args.repeats < 1 or args.max_turns < 1 or args.max_run_usd <= 0 or args.timeout_s < 1 or args.idle_s <= 0:
        return fail("budget, repeats, max-turns, max-run-usd, timeout-s and idle-s must be positive")
    if args.rerun_errors and not args.resume:
        return fail("--rerun-errors needs --resume")
    arms = [part.strip() for part in args.arms.split(",") if part.strip()]
    if not arms or any(a not in ARMS for a in arms):
        return fail("arms: plain, kit or both")
    try:
        tasks = select_tasks(discover_tasks(args.bench_dir), args.tasks)
    except ValueError as exc:
        return fail(str(exc))
    environment = dict(os.environ if env is None else env)
    claude = args.claude or shutil.which("claude")
    if invoke is None and not claude and not args.dry_run:
        return fail("claude was not found on PATH")
    temp = Path(tempfile.gettempdir())
    cfg = Config(
        label=args.label, budget_usd=args.budget_usd, tasks=tasks, arms=list(dict.fromkeys(arms)), repeats=args.repeats,
        seed=args.seed, max_turns=args.max_turns, max_run_usd=args.max_run_usd, timeout_s=args.timeout_s,
        idle_s=args.idle_s, max_failed_calls=args.max_failed_calls, keep_workspaces=args.keep_workspaces,
        resume=args.resume, rerun_errors=args.rerun_errors, dry_run=args.dry_run, claude=claude or "claude",
        out_dir=args.out or temp / "sdlc-bench-out" / args.label,
        work_dir=args.work_dir or temp / "sdlc-bench-work" / args.label,
        results_dir=args.results_dir, bench_dir=args.bench_dir, kit_root=args.kit_root,
    )
    return run_bench(cfg, invoke, environment, stream)


if __name__ == "__main__":
    sys.exit(main())
