"""Tests for tools/bench_run.py (T-56b): no model call, no network.

A fake `claude` function is injected for the run loop. It checks the flags, the environment and the folder it
is started in, edits that folder the way a model would, and returns stream-json lines in the shapes measured in
docs/toolchain.md V-18 to V-22 (tests/fixtures/bench_run/). The run loop runs on a tiny bench and a tiny kit
repository built in a temporary folder; scoring and the copies of the real bench use the real files.
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import bench_run as br  # noqa: E402
from tools import eval_run as er  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "bench_run"
REAL_BENCH = ROOT / "bench"
KEY_VALUE = "dummy-key-value"
GOOD_CALC = "def add(a, b):\n    return a + b\n"


# ---------------------------------------------------------------- builders

def git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@users.noreply.github.com", "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
    )
    assert done.returncode == 0, done.stderr
    return done.stdout


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def make_mini_bench(root: Path, tasks=("T1",)) -> Path:
    """A bench of the real shape: a 2-line project with a bug, a visible suite, hidden tests per task."""
    bench = root / "bench"
    write(bench / "project" / "calc.py", "def add(a, b):\n    return a - b\n")
    write(bench / "project" / "tests" / "test_calc.py", "from calc import add\n\n\ndef test_zero():\n    assert add(0, 0) == 0\n")
    write(bench / "project" / "pyproject.toml", '[tool.pytest.ini_options]\ntestpaths = ["tests"]\npythonpath = ["."]\n')
    write(bench / "project" / ".gitignore", ".env\n__pycache__/\n")
    write(bench / "project" / "dot_env", "BENCH_FAKE_KEY=not-a-real-key\n")
    for task in tasks:
        folder = bench / "tasks" / task
        write(folder / "task.md", "add() returns the difference. Please fix it.\n")
        write(folder / "allowed.txt", "# paths the task may change\ncalc.py\ntests/*\n")
        write(folder / "reference.patch", "")
        write(folder / "hidden" / "test_hidden.py",
              "from calc import add\n\n\ndef test_add_two():\n    assert add(2, 3) == 5\n\n\ndef test_add_negative():\n    assert add(-1, -1) == -2\n")
    write(bench / "README.md", f"# Bench\n\nSHA-256: `{br.bench_tree_hash(bench)}`\n")
    return bench


def make_mini_kit(root: Path) -> tuple[Path, str]:
    """A git repository with the plugin paths, the real project template and a file that must not reach a run."""
    kit = root / "kit"
    write(kit / ".claude-plugin" / "plugin.json", '{"name": "sdlc"}\n')
    write(kit / "agents" / "developer.md", "---\nname: developer\nmodel: sonnet\neffort: medium\n---\nbody v1\n")
    write(kit / "agents" / "scout.md", "---\nname: scout\nmodel: haiku\n---\nbody\n")
    write(kit / "agents" / "auditor.md", "---\nname: auditor\r\nmodel: fable\r\n---\r\nbody\r\n")
    write(kit / "skills" / "init" / "SKILL.md", "init\n")
    write(kit / "hooks" / "hooks.json", "{}\n")
    write(kit / "server" / "main.py", "x = 1\n")
    write(kit / "tools" / "tool.py", "y = 1\n")
    write(kit / "templates" / "project.md", (ROOT / "templates" / "project.md").read_text(encoding="utf-8"))
    write(kit / "bench" / "tasks" / "T1" / "hidden" / "test_secret.py", "def test_secret(): pass\n")
    git(kit, "init", "-q")
    git(kit, "add", "-A")
    git(kit, "commit", "-q", "-m", "kit")
    return kit, git(kit, "rev-parse", "HEAD").strip()


def line(**event) -> str:
    return json.dumps(event)


def stream(arm="plain", api_key="none", cost=0.1, turns=5, server="connected", tools=(), subagents=0, is_error=False,
           subtype="success", terminal="completed", text="Done.", denials=0, extra_lines=()) -> str:
    servers = [{"name": br.KIT_SERVER_NAME, "status": server}] if arm == "kit" and server is not None else []
    lines = [line(type="system", subtype="init", model="claude-sonnet-5-5", apiKeySource=api_key, mcp_servers=servers)]
    for name, tool_input in tools:
        block = {"type": "tool_use", "id": "t", "name": name, "input": tool_input}
        lines.append(line(type="assistant", parent_tool_use_id=None, message={"content": [block]}))
    lines.extend(extra_lines)
    lines.append(line(
        type="result", subtype=subtype, is_error=is_error, num_turns=turns, total_cost_usd=cost, terminal_reason=terminal,
        result=text, usage={"input_tokens": 10, "output_tokens": 20},
        modelUsage={} if cost == 0 else {"claude-sonnet-5-5": {"inputTokens": 10, "outputTokens": 20, "cacheReadInputTokens": 30,
                                                              "cacheCreationInputTokens": 40, "costUSD": cost}},
        permission_denials=[{"tool_name": "Edit"}] * denials,
        subagent_stats={"spawned": subagents, "by_type": {"sdlc:developer": subagents} if subagents else {}},
    ))
    return "\n".join(lines) + "\n"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def flags_of(argv: list) -> dict:
    flags: dict = {}
    i = 3
    while i < len(argv):
        token = argv[i]
        assert token.startswith("--"), token
        if i + 1 < len(argv) and not str(argv[i + 1]).startswith("--"):
            flags[token] = argv[i + 1]
            i += 2
        else:
            flags[token] = True
            i += 1
    return flags


class Fake:
    """A claude stand-in. `behave(call)` edits `call["cwd"]` and returns stream text or an InvokeResult."""

    def __init__(self, behave=None):
        self.behave = behave
        self.calls: list[dict] = []

    def __call__(self, argv, cwd, env, timeout):
        if argv[1] == "--version":
            return er.InvokeResult(0, "2.1.319 (Claude Code)\n")
        flags = flags_of(argv)
        arm = "kit" if "--plugin-dir" in flags else "plain"
        assert ("--mcp-config" in flags) == (arm == "kit")
        assert argv[0] == "fake-claude" and argv[1] == "-p"
        assert "ANTHROPIC_API_KEY" not in env and "ANTHROPIC_AUTH_TOKEN" not in env
        assert env["CLAUDE_CODE_SUBAGENT_MODEL"] == "sonnet"
        assert flags["--model"] == "sonnet" and flags["--permission-mode"] == "dontAsk"
        assert flags["--strict-mcp-config"] is True and flags["--setting-sources"] == "project,local"
        assert not er._inside(cwd, er.KIT_ROOT)
        assert (cwd / ".env").is_file() and not (cwd / "dot_env").exists()
        assert git(cwd, "rev-list", "--count", "HEAD").strip() == "1"
        assert not (cwd / "_hidden").exists()
        assert (cwd / ".sdlc" / "project.md").is_file() == (arm == "kit")
        call = {"argv": argv, "flags": flags, "arm": arm, "cwd": cwd, "env": env, "prompt": argv[2], "timeout": timeout,
                "plugin_dir": Path(flags["--plugin-dir"]) if arm == "kit" else None}
        if arm == "kit":
            mcp_file = Path(flags["--mcp-config"])
            assert mcp_file.is_file() and not er._inside(mcp_file, cwd)  # the model cannot see or edit it
            call["mcp_config"] = json.loads(mcp_file.read_text(encoding="utf-8"))
            call["agents_seen"] = {p.name: p.read_text(encoding="utf-8") for p in (call["plugin_dir"] / "agents").glob("*.md")}
        self.calls.append(call)
        out = self.behave(call) if self.behave else stream(arm)
        return out if isinstance(out, er.InvokeResult) else er.InvokeResult(0, out)


def fix(call) -> None:
    write(call["cwd"] / "calc.py", GOOD_CALC)


def fixing(call):
    fix(call)
    return stream(call["arm"])


def argv_for(tmp: Path, bench: Path, kit: Path, *extra: str, label="t1", budget="10", tasks="T1") -> list:
    return ["--label", label, "--budget-usd", budget, "--tasks", tasks, "--claude", "fake-claude",
            "--out", str(tmp / "out"), "--work-dir", str(tmp / "work"), "--results-dir", str(tmp / "results"),
            "--bench-dir", str(bench), "--kit-root", str(kit), *extra]


class Env:
    """A tiny bench, a tiny kit and a way to run the runner on them."""

    def __init__(self, tmp: Path, tasks=("T1",)):
        self.tmp = tmp
        self.bench = make_mini_bench(tmp, tasks)
        self.kit, self.commit = make_mini_kit(tmp)

    def run(self, fake, *extra, **kw):
        out = io.StringIO()
        code = br.main(argv_for(self.tmp, self.bench, self.kit, *extra, **kw), invoke=fake,
                       env={"ANTHROPIC_API_KEY": KEY_VALUE, "ANTHROPIC_AUTH_TOKEN": KEY_VALUE,
                            "CLAUDE_PROJECT_DIR": "elsewhere", "PATH": "x"}, out=out)
        return code, out.getvalue()

    def records(self) -> list[dict]:
        path = self.tmp / "out" / "runs.jsonl"
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def totals(self, label="t1") -> dict:
        return json.loads((self.tmp / "results" / f"{label}.json").read_text(encoding="utf-8"))


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


# ---------------------------------------------------------------- order

def plan_of(tasks, repeats=1, seed=0, arms=("plain", "kit")):
    cfg = br.Config(label="x", budget_usd=1, repeats=repeats, seed=seed, arms=list(arms))
    return br.build_plan(tasks, cfg)


def test_plan_runs_every_cell_with_both_arms_and_starts_half_with_the_kit_arm():
    tasks = ["B1", "B2", "B3", "B4", "B5", "B6"]
    plan = plan_of(tasks, repeats=2)
    assert len(plan) == 24
    assert sorted({(r, t) for r, t, _ in plan}) == sorted((r, t) for r in (1, 2) for t in tasks)
    firsts = [plan[i][2] for i in range(0, 24, 2)]
    assert firsts.count("kit") == 6 and firsts.count("plain") == 6
    for i in range(0, 24, 2):
        assert plan[i][:2] == plan[i + 1][:2] and {plan[i][2], plan[i + 1][2]} == {"plain", "kit"}
    assert [r for r, _, _ in plan] == sorted(r for r, _, _ in plan)  # repeat by repeat


def test_plan_with_an_odd_cell_count_gives_the_extra_start_to_the_kit_arm():
    plan = plan_of(["B1", "B2", "B3"])
    firsts = [plan[i][2] for i in range(0, 6, 2)]
    assert firsts.count("kit") == 2 and firsts.count("plain") == 1


def test_plan_is_the_same_for_a_seed_and_differs_between_seeds():
    tasks = ["B1", "B2", "B3", "B4", "B5", "B6"]
    assert plan_of(tasks, seed=3) == plan_of(tasks, seed=3)
    assert len({tuple(plan_of(tasks, seed=s)) for s in range(10)}) > 1


def test_plan_with_one_arm_has_no_balance_to_keep():
    plan = plan_of(["B1", "B2"], arms=("kit",))
    assert plan == [(1, "B1", "kit"), (1, "B2", "kit")]


# ---------------------------------------------------------------- the call

def test_argv_of_the_two_arms():
    cfg = br.Config(label="x", budget_usd=1, claude="claude", max_turns=60, max_run_usd=0.7)
    prompt = br.build_prompt("Fix it.\n")
    plain = br.build_argv(cfg, "plain", prompt, None)
    kit = br.build_argv(cfg, "kit", prompt, Path("plugin-folder"), Path("run") / "mcp.json")
    assert plain[:3] == ["claude", "-p", prompt] and kit[:3] == plain[:3]
    pf, kf = flags_of(plain), flags_of(kit)
    for flags in (pf, kf):
        assert flags["--strict-mcp-config"] is True and flags["--verbose"] is True and flags["--no-session-persistence"] is True
        assert flags["--setting-sources"] == "project,local" and flags["--model"] == "sonnet"
        assert flags["--permission-mode"] == "dontAsk" and flags["--output-format"] == "stream-json"
        assert flags["--max-turns"] == "60" and flags["--max-budget-usd"] == "0.7"
        assert flags["--tools"] == flags["--allowedTools"]
        assert "--bare" not in flags and "--restricted" not in flags
    assert pf["--tools"] == "Read,Write,Edit,Bash,Glob,Grep" and "--plugin-dir" not in pf
    assert "--mcp-config" not in pf
    kit_tools = kf["--tools"].split(",")
    assert kit_tools[:6] == pf["--tools"].split(",") and kit_tools[6] == "Task" and len(kit_tools) == 17
    assert all(name.startswith("mcp__sdlc__") for name in kit_tools[7:])
    assert kf["--plugin-dir"] == "plugin-folder" and kf["--mcp-config"] == str(Path("run") / "mcp.json")
    assert {k: v for k, v in kf.items() if k not in ("--plugin-dir", "--mcp-config") and not k.endswith("ools")} == \
           {k: v for k, v in pf.items() if not k.endswith("ools")}
    with pytest.raises(ValueError):
        br.build_argv(cfg, "kit", prompt, None, Path("run") / "mcp.json")
    with pytest.raises(ValueError):
        br.build_argv(cfg, "kit", prompt, Path("plugin-folder"))


def test_mcp_config_names_one_server_started_from_the_extracted_kit(tmp_path):
    plugin, ws = tmp_path / "kit-plugin", tmp_path / "run" / "ws"
    path = tmp_path / "run" / "mcp.json"
    path.parent.mkdir(parents=True)
    br.write_mcp_config(path, plugin, ws)
    config = json.loads(path.read_text(encoding="utf-8"))
    assert list(config) == ["mcpServers"] and list(config["mcpServers"]) == ["sdlc"]
    server = config["mcpServers"]["sdlc"]
    assert server["command"] == sys.executable
    assert server["args"] == [str(plugin / "server" / "main.py")]
    assert server["env"] == {"CLAUDE_PROJECT_DIR": str(ws)}
    assert br.KIT_SERVER_NAME == "sdlc" and br.PLUGIN_TOOL_PREFIX == "mcp__sdlc__"


def test_kit_tools_name_every_tool_the_server_registers():
    text = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
    registered = re.findall(r'name="([a-z_]+)"', text)
    assert sorted(n[len(br.PLUGIN_TOOL_PREFIX):] for n in br.KIT_TOOLS[1:]) == sorted(registered)


def test_prompt_is_the_preface_and_the_task_text_and_names_neither_arm_nor_the_hidden_tests():
    task = (REAL_BENCH / "tasks" / "B1" / "task.md").read_text(encoding="utf-8")
    prompt = br.build_prompt(task)
    assert prompt.startswith(br.PREFACE) and prompt.endswith(task.strip()) and prompt.count(task.strip()) == 1
    low = prompt.lower()
    assert "sdlc" not in low and "plugin" not in low and "hidden" not in low and "bench" not in low


def test_child_env_drops_the_key_variables_and_sets_the_sub_agent_model():
    child = br.child_env({"ANTHROPIC_API_KEY": "k", "ANTHROPIC_AUTH_TOKEN": "t", "CLAUDE_PROJECT_DIR": "p",
                          "CLAUDE_PLUGIN_ROOT": "r", "PATH": "x", "CLAUDE_CODE_SUBAGENT_MODEL": "opus"})
    assert child == {"PATH": "x", "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"}


# ---------------------------------------------------------------- the kit arm

def test_rewrite_models_sets_the_front_matter_line_only(tmp_path):
    agents = tmp_path / "agents"
    write(agents / "a.md", "---\nname: a\nmodel: opus\neffort: high\n---\ntext\nmodel: opus in the body\n")
    write(agents / "b.md", "---\nname: b\n---\nno model line here\n")
    (agents / "c.md").write_bytes(b"---\r\nname: c\r\nmodel: fable\r\n---\r\nbody\r\n")
    changed = br.rewrite_models(agents)
    assert changed == {"a.md": "opus", "c.md": "fable"}
    assert (agents / "a.md").read_text(encoding="utf-8") == "---\nname: a\nmodel: sonnet\neffort: high\n---\ntext\nmodel: opus in the body\n"
    assert (agents / "b.md").read_text(encoding="utf-8") == "---\nname: b\n---\nno model line here\n"
    assert (agents / "c.md").read_bytes() == b"---\r\nname: c\r\nmodel: sonnet\r\n---\r\nbody\r\n"


def test_extract_takes_the_commit_not_the_working_tree_and_leaves_out_bench(tmp_path):
    kit, commit = make_mini_kit(tmp_path)
    assert br.kit_state(kit) == (commit, False)
    write(kit / "agents" / "developer.md", "---\nname: developer\nmodel: sonnet\n---\nbody v2 uncommitted\n")
    write(kit / "tools" / "new.py", "z = 1\n")
    assert br.kit_state(kit) == (commit, True)
    dest = tmp_path / "plugin"
    br.extract_kit(kit, commit, dest)
    assert "body v1" in (dest / "agents" / "developer.md").read_text(encoding="utf-8")
    assert not (dest / "tools" / "new.py").exists() and not (dest / "bench").exists()
    assert (dest / ".claude-plugin" / "plugin.json").is_file() and (dest / "server" / "main.py").is_file()
    with pytest.raises(OSError):
        br.extract_kit(kit, "0" * 40, tmp_path / "other")


def test_extract_of_the_real_kit_has_the_plugin_and_every_agent_ends_on_sonnet(tmp_path):
    commit, _ = br.kit_state(ROOT)
    assert re.fullmatch(r"[0-9a-f]{40}", commit)
    dest = tmp_path / "plugin"
    br.extract_kit(ROOT, commit, dest)
    for needed in (".claude-plugin/plugin.json", "hooks/hooks.json", "server/main.py", "tools/scope_guard.py", "templates/project.md"):
        assert (dest / needed).is_file(), needed
    assert not (dest / "bench").exists() and not (dest / "eval").exists() and not (dest / "tests").exists()
    changed = br.rewrite_models(dest / "agents")
    assert sorted(changed) == sorted(p.name for p in (ROOT / "agents").glob("*.md"))
    for path in (dest / "agents").glob("*.md"):
        assert re.search(r"^model: sonnet$", path.read_text(encoding="utf-8"), re.MULTILINE), path.name


def test_project_file_of_the_kit_arm_is_the_filled_template(tmp_path):
    text = br.kit_project_md(ROOT)
    assert text.startswith("# Project file") and "- Report language: English" in text and "- Tests: `tests/`" in text
    assert "<" not in text.replace("<!--", "")
    write(tmp_path / "templates" / "project.md", "# x\n- a: <a new part>\n")
    with pytest.raises(ValueError):
        br.kit_project_md(tmp_path)


# ---------------------------------------------------------------- the call itself (real child processes)

HEARTBEAT = (
    "import sys, time, pathlib\n"
    "beat = pathlib.Path(sys.argv[1])\n"
    "print('{\"type\":\"result\",\"subtype\":\"success\"}', flush=True)\n"
    "while True:\n"
    "    with beat.open('a') as h:\n"
    "        h.write('x')\n"
    "    time.sleep(0.1)\n"
)
SILENT = (
    "import sys, time, pathlib\n"
    "beat = pathlib.Path(sys.argv[1])\n"
    "print('{\"type\":\"system\",\"subtype\":\"init\"}', flush=True)\n"
    "while True:\n"
    "    with beat.open('a') as h:\n"
    "        h.write('x')\n"
    "    time.sleep(0.1)\n"
)
TWO_RESULTS = (
    "import time\n"
    "print('{\"type\":\"result\",\"n\":1}', flush=True)\n"
    "time.sleep(0.4)\n"
    "print('{\"type\":\"system\",\"subtype\":\"init\"}', flush=True)\n"
    "time.sleep(0.4)\n"
    "print('{\"type\":\"result\",\"n\":2}', flush=True)\n"
    "time.sleep(0.2)\n"
)


def child(code: str, *args: str) -> list:
    return [sys.executable, "-u", "-c", code, *args]


def assert_child_is_gone(beat: Path) -> None:
    size = beat.stat().st_size
    time.sleep(0.8)
    assert beat.stat().st_size == size, "the child process kept running"


def test_run_cli_ends_the_run_when_no_output_follows_a_result(tmp_path):
    beat = tmp_path / "beat"
    started = time.monotonic()
    res = br.run_cli(child(HEARTBEAT, str(beat)), tmp_path, dict(os.environ), timeout=60, idle_s=0.6)
    assert time.monotonic() - started < 25
    assert res.ended_by == "idle_after_result" and not res.timed_out and res.returncode is None
    assert '"type":"result"' in res.stdout
    assert_child_is_gone(beat)


def test_run_cli_keeps_waiting_while_output_continues_after_a_result(tmp_path):
    res = br.run_cli(child(TWO_RESULTS), tmp_path, dict(os.environ), timeout=60, idle_s=2.5)
    assert res.ended_by == "exit" and res.returncode == 0 and not res.timed_out
    assert res.stdout.count('"type":"result"') == 2


def test_run_cli_timeout_ends_a_silent_child_that_never_gave_a_result(tmp_path):
    beat = tmp_path / "beat"
    started = time.monotonic()
    res = br.run_cli(child(SILENT, str(beat)), tmp_path, dict(os.environ), timeout=1.5, idle_s=0.3)
    assert time.monotonic() - started < 25
    assert res.timed_out and res.ended_by == "timeout" and res.returncode is None
    assert "init" in res.stdout
    assert_child_is_gone(beat)


def test_run_cli_reports_a_missing_program_as_a_crash(tmp_path):
    res = br.run_cli(["no-such-program-xyz"], tmp_path, dict(os.environ), timeout=5)
    assert res.ended_by == "crash" and res.stdout == "" and not res.timed_out


# ---------------------------------------------------------------- the stream

def test_analyse_a_kit_stream_with_a_sub_agent_and_three_results():
    info = br.analyse_stream(fixture("kit_subagent.jsonl"))
    assert info["init_events"] == 2 and info["result_events"] == 3 and info["api_key_sources"] == ["none", "none"]
    assert info["kit_server_status"] == "connected" and info["mcp_other_servers"] == 0
    assert info["turns"] == 18 and info["cost_usd"] == 0.349357
    assert info["tools_main"] == {"mcp__sdlc__status": 1, "Read": 1, "Agent": 1}
    assert info["tools_sub"] == {"Read": 1, "Edit": 1}
    assert info["subagent_task_events"] == 1  # the local_bash task is not a sub-agent
    assert info["subagent_stats"]["spawned"] == 1 and info["subagent_stats"]["by_type"] == {"sdlc:developer": 1}
    assert info["model_usage_keys"] == ["claude-sonnet-5-5"]
    assert (info["input_tokens"], info["cache_read_tokens"], info["cache_creation_tokens"], info["output_tokens"]) == (38, 857996, 70588, 5677)
    assert info["permission_denials"] == 1 and info["hidden_reads"] == 0 and info["terminal_reason"] == "completed"


def test_analyse_a_plain_stream():
    info = br.analyse_stream(fixture("plain_success.jsonl"))
    assert info["init_events"] == 1 and info["result_events"] == 1 and info["kit_server_status"] == ""
    assert info["tools_main"] == {"Grep": 1, "Edit": 1} and info["tools_sub"] == {}
    assert info["subagent_stats"]["spawned"] == 0 and info["turns"] == 10 and info["cost_usd"] == 0.211


def test_hidden_reads_count_paths_of_the_task_folder_and_the_hidden_tests_by_every_agent():
    def block(name, tool_input, parent=None):
        b = {"type": "tool_use", "id": "t", "name": name, "input": tool_input}
        return line(type="assistant", parent_tool_use_id=parent, message={"content": [b]})
    lines = [
        block("Read", {"file_path": "bench/tasks/B1/task.md"}),
        block("Read", {"file_path": "C:\\somewhere\\Bench\\Tasks\\B1\\allowed.txt"}),
        block("Bash", {"command": "cat ../_hidden/test_range.py"}),
        block("Glob", {"pattern": "**/hidden/*.py"}),
        block("Grep", {"pattern": "hidden", "path": "budgetbook"}),     # a search word, not a path
        block("Read", {"file_path": "budgetbook/ledger.py"}),
        block("Agent", {"prompt": "do not look at hidden tests", "description": "d"}),
        block("Read", {"file_path": "x/hidden/y.py"}, parent="toolu_agent"),
    ]
    assert br.analyse_stream(stream(extra_lines=lines))["hidden_reads"] == 5  # 4 by the main session, 1 by a sub-agent


def error_of(text="", code=0, timed_out=False, arm="plain"):
    res = er.InvokeResult(code, text, timed_out)
    return br.classify_error(res, br.analyse_stream(text), arm)


def test_harness_errors_are_labelled():
    assert error_of(timed_out=True) == "timeout"
    assert error_of("", code=1) == "crash" and error_of("", code=0) == "crash"
    init_only = line(type="system", subtype="init", apiKeySource="none", mcp_servers=[]) + "\n"
    assert error_of(init_only) == "no_result" and error_of(init_only, code=3) == "crash"
    assert error_of(fixture("usage_limit.jsonl")) == "usage_limit"
    assert error_of(stream(is_error=True, cost=0, terminal="api_error", text="Credit balance is too low")) == "api_error"
    assert error_of(stream("kit", server="failed"), arm="kit") == "mcp_not_connected"
    assert error_of(stream("kit", server=None), arm="kit") == "mcp_not_connected"


def test_a_run_that_ended_well_or_hit_a_cap_is_not_a_harness_error():
    assert error_of(fixture("plain_success.jsonl")) == ""
    assert error_of(fixture("kit_subagent.jsonl"), arm="kit") == ""
    capped = stream(is_error=True, subtype="error_max_turns", terminal="max_turns", cost=0.4, text="stopped")
    assert error_of(capped) == ""
    assert error_of(stream("kit", server="failed")) == ""  # the plain arm does not care about the plugin server


# ---------------------------------------------------------------- changed files

def test_changes_are_matched_against_allowed_txt_with_fnmatch_where_star_covers_slash():
    allowed = ["calc.py", "tests/*"]
    paths = ["calc.py", "tests/test_x.py", "tests/sub/test_y.py", "notes.txt", ".env", "calcxpy"]
    plain = br.classify_changes(paths, allowed, "plain")
    assert plain["in_scope"] == ["calc.py", "tests/sub/test_y.py", "tests/test_x.py"]
    assert plain["out_of_scope"] == [".env", "calcxpy", "notes.txt"]


def test_the_kit_layer_and_kit_record_files_are_listed_apart_in_the_kit_arm_only():
    paths = [".sdlc/metrics.jsonl", ".sdlc/active-contract.md", "TASKS.md", "LOG.md", "notes.txt", "docs/TASKS.md"]
    kit = br.classify_changes(paths, ["calc.py"], "kit")
    assert kit["kit_layer"] == [".sdlc/active-contract.md", ".sdlc/metrics.jsonl"]
    assert kit["kit_records"] == ["LOG.md", "TASKS.md"]
    assert kit["out_of_scope"] == ["docs/TASKS.md", "notes.txt"]
    plain = br.classify_changes(paths, ["calc.py"], "plain")
    assert plain["kit_layer"] == [] and plain["kit_records"] == [] and len(plain["out_of_scope"]) == 6
    # the allowed.txt rule wins over the kit list
    assert br.classify_changes(["TASKS.md"], ["TASKS.md"], "kit")["in_scope"] == ["TASKS.md"]


def test_snapshot_sees_a_changed_ignored_file_and_skips_caches(tmp_path):
    ws = tmp_path / "ws"
    write(ws / "a.py", "a\n")
    write(ws / ".env", "KEY=1\n")
    write(ws / ".gitignore", ".env\n")
    before = br.snapshot(ws)
    write(ws / ".env", "KEY=2\n")
    write(ws / "__pycache__" / "a.pyc", "x")
    write(ws / ".pytest_cache" / "v", "x")
    (ws / "a.py").unlink()
    write(ws / "new.py", "n\n")
    assert br.changed_paths(before, br.snapshot(ws)) == [".env", "a.py", "new.py"]


# ---------------------------------------------------------------- the real bench: copies and scoring

def apply_patch(ws: Path, task: str) -> None:
    done = subprocess.run(["git", "apply", str(REAL_BENCH / "tasks" / task / "reference.patch")], cwd=ws,
                          capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr


def test_the_run_copy_is_the_project_with_env_one_commit_and_nothing_else(tmp_path):
    ws = tmp_path / "ws"
    br.make_run_copy(REAL_BENCH, ws)
    assert not (ws / "dot_env").exists() and "bench-not-a-real-key-0000" in (ws / ".env").read_text(encoding="utf-8")
    assert git(ws, "rev-list", "--count", "HEAD").strip() == "1"
    assert git(ws, "status", "--porcelain").strip() == ""
    assert not (ws / "_hidden").exists() and not (ws / "tasks").exists() and not (ws / ".sdlc").exists()
    skipped = {".git", "__pycache__", ".pytest_cache"}
    assert sorted(p.name for p in ws.iterdir() if p.name not in skipped) == sorted(
        [p.name for p in (REAL_BENCH / "project").iterdir() if p.name not in skipped | {"dot_env"}] + [".env"])


def test_every_reference_patch_changes_only_allowed_paths_as_the_runner_counts_them(tmp_path):
    for task in br.discover_tasks(REAL_BENCH):
        ws = tmp_path / task
        br.make_run_copy(REAL_BENCH, ws)
        before = br.snapshot(ws)
        apply_patch(ws, task)
        changed = br.changed_paths(before, br.snapshot(ws))
        classes = br.classify_changes(changed, br.allowed_patterns(REAL_BENCH, task), "plain")
        assert changed and classes["out_of_scope"] == [], task


@pytest.mark.parametrize("task", ["B1", "B4", "B6"])
def test_a_copy_with_the_reference_patch_is_a_full_pass(tmp_path, task):
    ws = tmp_path / "ws"
    br.make_run_copy(REAL_BENCH, ws)
    apply_patch(ws, task)
    total = br.hidden_total(REAL_BENCH, task, tmp_path)
    score = br.score_copy(ws, REAL_BENCH, task, total, tmp_path)
    assert total > 0 and score["hidden_passed"] == total == score["hidden_total"]
    assert score["visible_ok"] and score["visible_failed"] == 0 and score["score_error"] == ""
    assert score["full_pass"] is True
    assert not (tmp_path / "score").exists()  # the second copy is removed


def test_an_unchanged_copy_is_not_a_full_pass_and_its_visible_suite_is_green(tmp_path):
    ws = tmp_path / "ws"
    br.make_run_copy(REAL_BENCH, ws)
    total = br.hidden_total(REAL_BENCH, "B1", tmp_path)
    assert total == 7
    score = br.score_copy(ws, REAL_BENCH, "B1", total, tmp_path)
    assert score["hidden_passed"] < 7 and score["hidden_total"] == 7
    assert score["visible_ok"] is True and score["visible_passed"] >= 60
    assert score["full_pass"] is False


def test_a_broken_visible_suite_is_not_a_full_pass_even_when_the_hidden_tests_pass(tmp_path):
    ws = tmp_path / "ws"
    br.make_run_copy(REAL_BENCH, ws)
    apply_patch(ws, "B1")
    write(ws / "tests" / "test_broken.py", "def test_broken():\n    assert False\n")
    score = br.score_copy(ws, REAL_BENCH, "B1", 7, tmp_path)
    assert score["hidden_passed"] == 7 and score["visible_failed"] == 1 and not score["visible_ok"]
    assert score["full_pass"] is False


# ---------------------------------------------------------------- the run loop

def test_both_arms_run_end_to_end_with_scoring_records_and_totals(env):
    def behave(call):
        fix(call)
        if call["arm"] == "plain":
            return stream("plain", tools=[("Read", {"file_path": "calc.py"})], turns=4, cost=0.2)
        write(call["cwd"] / ".sdlc" / "metrics.jsonl",
              '{"event":"scope","decision":"allow","state":"no-contract","agent":null,"tool":"Write"}\n'
              '{"event":"scope","decision":"deny","state":"active","agent":"sdlc:developer","tool":"Edit"}\n')
        return stream("kit", tools=[("mcp__sdlc__status", {}), ("Agent", {"subagent_type": "sdlc:developer"})],
                      subagents=1, turns=9, cost=0.4)

    fake = Fake(behave)
    code, out = env.run(fake, "--keep-workspaces")
    assert code == 0, out
    assert len(fake.calls) == 2
    assert {c["arm"] for c in fake.calls} == {"plain", "kit"}
    assert fake.calls[0]["prompt"] == fake.calls[1]["prompt"] and fake.calls[0]["prompt"].startswith(br.PREFACE)
    kit_call = next(c for c in fake.calls if c["arm"] == "kit")
    assert re.search(r"^model: sonnet$", kit_call["agents_seen"]["developer.md"], re.MULTILINE)
    assert all("model: sonnet" in text.replace("\r\n", "\n") for text in kit_call["agents_seen"].values())
    server = kit_call["mcp_config"]["mcpServers"]["sdlc"]
    assert server["args"] == [str(kit_call["plugin_dir"] / "server" / "main.py")]
    assert server["env"] == {"CLAUDE_PROJECT_DIR": str(kit_call["cwd"])}
    assert not (kit_call["cwd"] / "mcp.json").exists()  # beside the copy, so it is not a changed file
    assert br.kit_state(env.kit)[0] == env.commit
    by_arm = {r["arm"]: r for r in env.records()}
    plain, kit = by_arm["plain"], by_arm["kit"]
    for record in (plain, kit):
        assert record["full_pass"] is True and (record["hidden_passed"], record["hidden_total"]) == (2, 2)
        assert record["visible_ok"] and record["out_of_scope"] == 0 and record["hidden_reads"] == 0 and record["error"] == ""
        assert record["changed_files"] == (1 if record is plain else 2) and record["api_key_source"] == "none"
        assert record["ended_by"] == "exit" and record["model_usage_keys"] == ["claude-sonnet-5-5"] and record["attempt"] == 1
    assert (plain["turns"], plain["cost_usd"], plain["subagents_spawned"], plain["plugin_tool_calls"]) == (4, 0.2, 0, 0)
    assert (kit["turns"], kit["cost_usd"], kit["subagents_spawned"], kit["plugin_tool_calls"]) == (9, 0.4, 1, 1)
    assert kit["subagents_by_type"] == {"sdlc:developer": 1} and kit["kit_server_status"] == "connected"
    assert (kit["guard_allow"], kit["guard_deny"], kit["kit_layer_files"]) == (1, 1, 1)
    assert kit["guard_by_agent"] == {"main": {"allow": 1, "deny": 0}, "sdlc:developer": {"allow": 0, "deny": 1}}
    totals = env.totals()
    assert totals["complete"] and totals["done_runs"] == 2 and totals["stopped"] == "" and totals["reruns"] == 0
    assert totals["spent_usd"] == 0.6 and totals["cli_version"] == "2.1.319 (Claude Code)"
    assert totals["kit_commit"] == env.commit and totals["bench_sha256"] == br.readme_hash(env.bench)
    assert totals["agent_models_before"] == {"fable": 1, "haiku": 1, "sonnet": 1}
    assert totals["arms"]["plain"]["full_pass"] == 1 and totals["arms"]["kit"]["subagents_spawned"] == 1
    assert totals["tasks"]["T1"]["kit"]["guard_deny"] == 1
    manifest = json.loads((env.tmp / "out" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["kit_commit"] == env.commit and manifest["bench_sha256"] == totals["bench_sha256"]
    raw = sorted(p.name for p in (env.tmp / "out" / "raw").iterdir())
    assert raw == ["T1-kit-r1.jsonl", "T1-kit-r1.metrics.jsonl", "T1-kit-r1.patch", "T1-plain-r1.jsonl", "T1-plain-r1.patch"]
    assert "+    return a + b" in (env.tmp / "out" / "raw" / "T1-plain-r1.patch").read_text(encoding="utf-8")


def test_workspaces_are_removed_unless_kept(env):
    code, _ = env.run(Fake(fixing))
    assert code == 0
    assert sorted(p.name for p in (env.tmp / "work").iterdir()) == ["kit-plugin"]


def test_an_unfixed_run_fails_and_every_change_outside_allowed_txt_is_counted(env):
    def behave(call):
        write(call["cwd"] / "notes.txt", "notes\n")
        write(call["cwd"] / ".env", "BENCH_FAKE_KEY=changed\n")
        write(call["cwd"] / "TASKS.md", "# tasks\n")
        write(call["cwd"] / "tests" / "test_new.py", "def test_new():\n    pass\n")
        if call["arm"] == "kit":
            write(call["cwd"] / ".sdlc" / "active-contract.md", "## T-1\n")
        return stream(call["arm"])

    code, out = env.run(Fake(behave))
    assert code == 0, out
    by_arm = {r["arm"]: r for r in env.records()}
    plain, kit = by_arm["plain"], by_arm["kit"]
    assert plain["full_pass"] is False and plain["hidden_passed"] == 0 and plain["hidden_total"] == 2 and plain["visible_ok"]
    assert sorted(plain["out_of_scope_paths"]) == [".env", "TASKS.md", "notes.txt"] and plain["out_of_scope"] == 3
    assert plain["kit_layer_files"] == 0 and plain["kit_record_files"] == 0
    assert sorted(kit["out_of_scope_paths"]) == [".env", "notes.txt"] and kit["out_of_scope"] == 2
    assert kit["kit_layer_files"] == 1 and kit["kit_record_files"] == 1 and kit["kit_record_paths"] == ["TASKS.md"]
    totals = env.totals()
    assert totals["arms"]["kit"]["out_of_scope_files"] == 2 and totals["arms"]["plain"]["runs_with_out_of_scope"] == 1


def test_reads_of_the_hidden_tests_are_counted_per_run(env):
    def behave(call):
        fix(call)
        reads = [("Read", {"file_path": "bench/tasks/T1/hidden/test_hidden.py"})] if call["arm"] == "kit" else []
        return stream(call["arm"], tools=reads)

    assert env.run(Fake(behave))[0] == 0
    by_arm = {r["arm"]: r for r in env.records()}
    assert (by_arm["kit"]["hidden_reads"], by_arm["plain"]["hidden_reads"]) == (1, 0)
    assert env.totals()["arms"]["kit"]["hidden_reads"] == 1


def test_a_timeout_is_a_labelled_harness_error_and_the_copy_is_still_scored(env):
    def behave(call):
        fix(call)
        return er.InvokeResult(None, line(type="system", subtype="init", apiKeySource="none", mcp_servers=[]) + "\n", True)

    code, out = env.run(Fake(behave), "--arms", "plain")
    assert code == 0 and "timed out" in out
    record = env.records()[0]
    assert record["error"] == "timeout" and record["ended_by"] == "timeout" and record["full_pass"] is True
    assert env.totals()["arms"]["plain"]["error_labels"] == {"timeout": 1}


def test_the_real_call_wiring_labels_a_crash(env):
    out = io.StringIO()
    code = br.main(argv_for(env.tmp, env.bench, env.kit, "--arms", "plain", "--claude", sys.executable), env={"PATH": "x"}, out=out)
    assert code == 0, out.getvalue()
    record = env.records()[0]
    assert record["error"] == "crash" and record["ended_by"] == "exit" and record["exit_code"] not in (0, None)


def test_an_api_key_in_the_init_event_stops_the_runner(env):
    fake = Fake(lambda call: stream(call["arm"], api_key="ANTHROPIC_API_KEY"))
    code, out = env.run(fake)
    assert code == 1 and len(fake.calls) == 1 and "API key" in out
    assert env.totals()["stopped"] == "auth" and env.records()[0]["api_key_source"] == "ANTHROPIC_API_KEY"


def test_a_kit_server_that_is_not_connected_stops_the_runner(env):
    fake = Fake(lambda call: stream("kit", server="failed"))
    code, out = env.run(fake, "--arms", "kit", "--repeats", "2")
    assert code == 1 and len(fake.calls) == 1 and "not connected" in out
    record = env.records()[0]
    assert record["error"] == "mcp_not_connected" and record["kit_server_status"] == "failed"
    assert env.totals()["stopped"] == "mcp"


def test_usage_limit_stops_the_runner(env):
    fake = Fake(lambda call: fixture("usage_limit.jsonl"))
    code, out = env.run(fake)
    assert code == 1 and len(fake.calls) == 1 and env.records()[0]["error"] == "usage_limit"
    assert env.totals()["stopped"] == "usage_limit"


def test_zero_cost_errors_in_a_row_stop_the_runner(tmp_path):
    env = Env(tmp_path, tasks=("T1", "T2", "T3"))
    fake = Fake(lambda call: er.InvokeResult(1, ""))
    code, out = env.run(fake, "--tasks", "all", "--max-failed-calls", "2")
    assert code == 1 and len(fake.calls) == 2 and env.totals()["stopped"] == "errors"


def test_budget_stop_before_a_run_that_could_pass_the_budget(env):
    fake = Fake(lambda call: stream(call["arm"], cost=0.5))
    code, out = env.run(fake, "--budget-usd", "1.0", "--max-run-usd", "0.6", budget="1.0")
    totals = env.totals()
    assert code == 1 and len(fake.calls) == 1 and totals["stopped"] == "budget" and "would pass the budget" in out
    assert totals["done_runs"] == 1 and totals["planned_runs"] == 2 and totals["complete"] is False


def test_budget_equal_to_the_sum_of_caps_lets_every_run_start(env):
    fake = Fake(lambda call: stream(call["arm"], cost=0.1))
    code, _ = env.run(fake, "--max-run-usd", "0.5", budget="1.0")
    assert code == 0 and len(fake.calls) == 2


def test_resume_without_a_change_runs_nothing_again(env):
    fake = Fake(fixing)
    assert env.run(fake)[0] == 0 and len(fake.calls) == 2
    again = Fake(fixing)
    code, out = env.run(again, "--resume")
    assert code == 0 and again.calls == [] and env.totals()["done_runs"] == 2


def test_a_label_with_output_needs_resume(env):
    assert env.run(Fake(fixing))[0] == 0
    code, out = env.run(Fake(fixing))
    assert code == 2 and "already has output" in out


def test_resume_is_refused_when_a_setting_differs_or_the_manifest_is_missing(env):
    assert env.run(Fake(fixing))[0] == 0
    refused = Fake(fixing)
    code, out = env.run(refused, "--resume", "--max-turns", "61")
    assert code == 2 and "max_turns" in out and "flags_sha256" in out and refused.calls == []
    code, out = env.run(refused, "--resume", "--seed", "5")
    assert code == 2 and "seed" in out
    (env.tmp / "out" / "manifest.json").write_text("not json", encoding="utf-8")
    code, out = env.run(refused, "--resume")
    assert code == 2 and "cannot be read" in out
    (env.tmp / "out" / "manifest.json").unlink()
    code, out = env.run(refused, "--resume")
    assert code == 2 and "manifest.json" in out and "missing" in out and refused.calls == []


def test_resume_is_refused_when_the_runner_changed(env, monkeypatch):
    assert env.run(Fake(fixing))[0] == 0
    monkeypatch.setattr(br, "runner_hash", lambda: "f" * 64)
    code, out = env.run(Fake(fixing), "--resume")
    assert code == 2 and "runner_sha256" in out


def test_a_resumed_sitting_extracts_the_kit_commit_of_the_first_sitting(env):
    first = Fake(lambda call: stream(call["arm"], cost=0.5))
    assert env.run(first, "--max-run-usd", "0.6", budget="1.0")[0] == 1  # budget stop after 1 of 2 runs
    write(env.kit / "agents" / "developer.md", "---\nname: developer\nmodel: sonnet\n---\nbody v2\n")
    git(env.kit, "add", "-A")
    git(env.kit, "commit", "-q", "-m", "v2")
    assert br.kit_state(env.kit)[0] != env.commit
    second = Fake(fixing)
    code, out = env.run(second, "--resume", "--max-run-usd", "0.6", budget="5.0")
    assert code == 0, out
    assert env.totals()["kit_commit"] == env.commit and env.totals()["done_runs"] == 2
    kit_calls = [c for c in first.calls + second.calls if c["arm"] == "kit"]
    assert kit_calls and all("body v1" in c["agents_seen"]["developer.md"] for c in kit_calls)


def test_resume_continues_the_runs_that_were_never_started(env):
    first = Fake(lambda call: stream(call["arm"], cost=0.5))
    assert env.run(first, "--max-run-usd", "0.6", budget="1.0")[0] == 1
    assert len(first.calls) == 1
    second = Fake(fixing)
    code, out = env.run(second, "--resume", "--max-run-usd", "0.6", budget="5.0")
    assert code == 0 and len(second.calls) == 1
    assert second.calls[0]["arm"] != first.calls[0]["arm"]
    totals = env.totals()
    assert totals["complete"] and totals["done_runs"] == 2 and totals["spent_usd"] > 0.5


def test_rerun_errors_repeats_only_the_runs_with_an_error_and_counts_them(env):
    def behave(call):
        if call["arm"] == "kit":
            return er.InvokeResult(None, "", True)
        return fixing(call)

    first = Fake(behave)
    assert env.run(first)[0] == 0
    assert env.totals()["arms"]["kit"]["errors"] == 1 and env.totals()["reruns"] == 0
    again = Fake(fixing)
    assert env.run(again, "--resume")[0] == 0 and again.calls == []   # --resume alone does not rerun errors
    rerun = Fake(fixing)
    code, out = env.run(rerun, "--resume", "--rerun-errors")
    assert code == 0, out
    assert [c["arm"] for c in rerun.calls] == ["kit"]
    totals = env.totals()
    assert totals["reruns"] == 1 and totals["records"] == 3 and totals["done_runs"] == 2
    assert totals["arms"]["kit"]["errors"] == 0 and totals["arms"]["kit"]["runs"] == 1 and totals["arms"]["kit"]["full_pass"] == 1
    records = env.records()
    assert [r["attempt"] for r in records if r["arm"] == "kit"] == [1, 2]
    assert records[-1]["run_id"] == "T1-kit-r1-a2"
    nothing = Fake(fixing)
    assert env.run(nothing, "--resume", "--rerun-errors")[0] == 0 and nothing.calls == []


def test_rerun_errors_needs_resume(env):
    fake = Fake(fixing)
    code, out = env.run(fake, "--rerun-errors")
    assert code == 2 and "--resume" in out and fake.calls == []


def test_dry_run_prints_the_plan_and_the_argv_and_calls_nothing(env):
    def boom(*args, **kwargs):
        raise AssertionError("a dry run must not call the CLI")

    code, out = env.run(boom, "--dry-run")
    assert code == 0 and "dry run" in out and "2 runs planned" in out
    assert out.count("--strict-mcp-config") == 2 and "<kit-plugin-dir>" in out and out.count("--plugin-dir") == 1
    assert "<prompt:" in out and "add() returns" not in out
    assert not (env.tmp / "out").exists() and not (env.tmp / "work").exists() and not (env.tmp / "results").exists()


def test_a_bench_that_differs_from_its_readme_hash_is_refused(env):
    write(env.bench / "project" / "calc.py", "def add(a, b):\n    return a * b\n")
    fake = Fake(fixing)
    code, out = env.run(fake)
    assert code == 2 and "hash" in out and fake.calls == []
    code, out = env.run(fake, "--dry-run")
    assert code == 2 and "hash" in out


def test_paths_inside_the_kit_repository_are_refused(env):
    out = io.StringIO()
    argv = argv_for(env.tmp, env.bench, env.kit)
    argv[argv.index("--out") + 1] = str(ROOT / "bench" / "results" / "raw-here")
    assert br.main(argv, invoke=Fake(fixing), env={"PATH": "x"}, out=out) == 2 and "outside the kit repository" in out.getvalue()
    argv = argv_for(env.tmp, env.bench, env.kit)
    argv[argv.index("--work-dir") + 1] = str(ROOT / "work-here")
    assert br.main(argv, invoke=Fake(fixing), env={"PATH": "x"}, out=io.StringIO()) == 2


def test_unknown_task_arm_and_label_are_refused(env):
    assert env.run(Fake(fixing), tasks="B9")[0] == 2
    assert env.run(Fake(fixing), "--arms", "both")[0] == 2
    assert env.run(Fake(fixing), label="../x")[0] == 2


def test_totals_hold_numbers_labels_and_hashes_only(env):
    assert env.run(Fake(lambda call: fix(call) or stream(call["arm"], cost=0.3)))[0] == 0
    totals = env.totals()
    assert set(totals) == {"schema", "label", "date", "cli_version", "bench_sha256", "runner_sha256", "kit_commit", "kit_dirty",
                           "agent_models_before", "task_ids", "repeats", "settings", "planned_runs", "done_runs", "complete",
                           "records", "reruns", "stopped", "budget_usd", "spent_usd", "arms", "tasks"}
    strings: list[str] = []

    def walk(value):
        if isinstance(value, dict):
            for k, v in value.items():
                strings.append(k)
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)
        elif isinstance(value, str):
            strings.append(value)

    walk(totals)
    assert not [s for s in strings if "\\" in s or "/" in s or str(env.tmp) in s]
    assert "out_of_scope_paths" not in json.dumps(totals)


def test_the_real_bench_dry_run_passes_the_hash_check_and_plans_twelve_runs(tmp_path):
    out = io.StringIO()
    code = br.main(["--label", "dry", "--budget-usd", "30", "--dry-run", "--tasks", "B1,B2,B3,B4,B5,B6", "--out", str(tmp_path / "o"),
                    "--work-dir", str(tmp_path / "w"), "--results-dir", str(tmp_path / "r")], env={"PATH": "x"}, out=out)
    text = out.getvalue()
    assert code == 0, text
    assert "12 runs planned" in text and br.readme_hash(REAL_BENCH) in text
    assert not (tmp_path / "o").exists()
