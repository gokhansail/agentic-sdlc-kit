"""Tests for the build bench environment kit (T-65, tools/build_run.py). Temporary folders, a stub `claude` on PATH,
the clipboard replaced; no model, no network, no install."""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_run as br  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "build_run"
METER_FIX = ROOT / "tests" / "fixtures" / "transcripts"
TEXTS = json.loads((ROOT / "bench" / "build" / "texts.json").read_text(encoding="utf-8"))
PIN = "2.1.332 (Claude Code)"
SECRET_VALUE = "hunter2-do-not-print"
BASE_ARGV = ["--model", "opus", "--permission-mode", "auto", "--effort", "medium"]


# ----------------------------------------------------------------------------------------------- helpers

@pytest.fixture
def env(tmp_path, monkeypatch):
    """A sandbox: a stub claude first on PATH, a clean environment, a fake home, the clipboard recorded."""
    for name in list(os.environ):
        if name.startswith(("ANTHROPIC", "CLAUDE", "STUB_")):
            monkeypatch.delenv(name)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = FIX / "claude_stub.py"
    if os.name == "nt":
        (bin_dir / "claude.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{stub}" %*\r\n', encoding="utf-8")
    else:
        wrapper = bin_dir / "claude"
        wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{stub}" "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("STUB_OUT", str(tmp_path / "stub-out.json"))
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    monkeypatch.setattr(br, "user_home", lambda: tmp_path / "home")
    monkeypatch.setattr(br, "WALK_FLOOR", sandbox)
    clip: list[str] = []
    monkeypatch.setattr(br, "set_clipboard", clip.append)
    monkeypatch.setattr(br, "SCORE_SCRIPT", FIX / "score_stub.py")

    class Env:
        pass

    e = Env()
    e.sandbox, e.clip, e.tmp, e.monkeypatch = sandbox, clip, tmp_path, monkeypatch
    return e


def make_setup(env, name: str = "bench") -> Path:
    root = env.sandbox / name
    assert br.main(["setup", "--root", str(root)]) == 0
    return root


def run(root: Path, *argv: str) -> int:
    return br.main([argv[0], "--root", str(root), *argv[1:]])


def state(root: Path) -> dict:
    return json.loads((root / "runlog" / "run-state.json").read_text(encoding="utf-8"))


def setup_json(root: Path) -> dict:
    return json.loads((root / "runlog" / "setup.json").read_text(encoding="utf-8"))


def goto(root: Path, arm: str, step: str) -> None:
    data = state(root)
    data["index"] = next(i for i, it in enumerate(data["sequence"]) if it["arm"] == arm and it["step"] == step)
    (root / "runlog" / "run-state.json").write_text(json.dumps(data), encoding="utf-8")


def effort(root: Path) -> list[dict[str, str]]:
    with (root / "runlog" / "effort-log.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def git_out(folder: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=folder, capture_output=True, text=True, check=True).stdout.strip()


# ----------------------------------------------------------------------------------------------- setup

def test_setup_layout_and_first_commits(env):
    before = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    root = make_setup(env)
    for name in ("w1/guitar", "w2/guitar", "p1/guitar", "c0", "c1", "c2", "kit", "runlog", "private", "remotes/w1.git",
                 "remotes/w2.git", "remotes/p1.git"):
        assert (root / name).is_dir(), name
    assert (root / "run.ps1").is_file()
    for label in ("w1", "w2", "p1"):
        arm = root / label / "guitar"
        assert git_out(arm, "rev-list", "--count", "HEAD") == "1"
        assert git_out(arm, "ls-tree", "-r", "--name-only", "HEAD") == "SPEC.md"
        assert git_out(arm, "log", "-1", "--format=%an <%ae>") == "Bench User <bench@example.invalid>"
        assert Path(git_out(arm, "remote", "get-url", "origin")) == root / "remotes" / f"{label}.git"
        assert git_out(root / "remotes" / f"{label}.git", "rev-parse", "--is-bare-repository") == "true"
    assert (root / "w1" / "guitar" / "SPEC.md").read_bytes() == (ROOT / "bench" / "build" / "SPEC.md").read_bytes()
    after = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    assert before == after


def test_setup_record_and_key(env, capsys):
    root = make_setup(env)
    out = capsys.readouterr().out
    key = (root / "private" / "fake-key.txt").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"sk-[A-Za-z0-9]{40}", key)
    assert key not in out
    record = setup_json(root)
    assert key not in json.dumps(record)
    assert sorted(record["arms"]) == ["kit", "pilot", "plain"]
    assert sorted(record["arms"].values()) == ["p1", "w1", "w2"]
    assert record["cli_version"] == PIN and record["kit_tag"] == "v0.1.0"
    assert re.fullmatch(r"[0-9a-f]{64}", record["kit_tree_sha256"])
    assert (root / "kit" / ".claude-plugin" / "plugin.json").is_file()
    with (root / "runlog" / "effort-log.csv").open(encoding="utf-8") as handle:
        assert next(csv.reader(handle)) == list(br.EFFORT_COLUMNS)
    assert [r["action"] for r in effort(root)] == ["setup"]


def test_push_to_the_bare_remote(env):
    root = make_setup(env)
    arm = root / "w1" / "guitar"
    (arm / "a.txt").write_text("hi", encoding="utf-8")
    git_out(arm, "add", "a.txt")
    git_out(arm, "commit", "-q", "-m", "x")
    git_out(arm, "push", "-q", "origin", "HEAD:main")
    assert git_out(root / "remotes" / "w1.git", "rev-parse", "main") == git_out(arm, "rev-parse", "HEAD")


def test_extract_hash_equal_on_two_setups(env):
    first, second = make_setup(env, "a"), make_setup(env, "b")
    assert setup_json(first)["kit_tree_sha256"] == setup_json(second)["kit_tree_sha256"]
    assert br.tree_hash(first / "kit") == setup_json(first)["kit_tree_sha256"]
    keys = {(r / "private" / "fake-key.txt").read_text() for r in (first, second)}
    assert len(keys) == 2


def test_setup_refuses_planted_instruction_file_in_a_parent(env, capsys):
    parent = env.sandbox / "parent"
    parent.mkdir()
    (parent / "CLAUDE.md").write_text("planted", encoding="utf-8")
    root = parent / "bench"
    assert br.main(["setup", "--root", str(root)]) == 2
    assert "CLAUDE.md" in capsys.readouterr().err
    assert not root.exists()
    (parent / "CLAUDE.md").unlink()
    (parent / ".claude").mkdir()
    assert br.main(["setup", "--root", str(root)]) == 2
    (parent / ".claude").rmdir()
    assert br.main(["setup", "--root", str(root)]) == 0  # the legal case


def test_setup_refuses_home_repository_and_used_root(env, capsys):
    home_root = env.tmp / "home" / "bench"
    assert br.main(["setup", "--root", str(home_root)]) == 2
    assert not home_root.exists()
    assert br.main(["setup", "--root", str(ROOT / "bench-out")]) == 2
    assert not (ROOT / "bench-out").exists()
    used = env.sandbox / "used"
    used.mkdir()
    (used / "x.txt").write_text("x", encoding="utf-8")
    assert br.main(["setup", "--root", str(used)]) == 2
    root = make_setup(env)
    assert run(root, "status") == 0
    assert br.main(["status", "--root", str(ROOT)]) == 2


# ----------------------------------------------------------------------------------------------- launch

def test_launch_arguments_and_environment(env, capsys):
    root = make_setup(env)
    env.monkeypatch.setenv("CLAUDE_PROJECT_DIR", SECRET_VALUE)
    env.monkeypatch.setenv("CLAUDE_CODE_SUBAGENT_MODEL", SECRET_VALUE)
    env.monkeypatch.setenv("CLAUDE_FOO", SECRET_VALUE)
    goto(root, "kit", "0")
    assert run(root, "launch") == 0
    out = capsys.readouterr().out
    assert SECRET_VALUE not in out
    assert "CLAUDE_FOO" in out
    seen = json.loads((env.tmp / "stub-out.json").read_text(encoding="utf-8"))
    assert seen["argv"] == [*BASE_ARGV, "--plugin-dir", str(root / "kit")]
    assert "CLAUDE_PROJECT_DIR" not in seen["names"] and "CLAUDE_CODE_SUBAGENT_MODEL" not in seen["names"]
    assert Path(seen["config_dir"]) == root / setup_json(root)["arms"]["kit"].replace("w", "c")
    assert Path(seen["cwd"]) == root / setup_json(root)["arms"]["kit"] / "guitar"
    assert [r["action"] for r in effort(root)][-2:] == ["launch", "exit"]
    goto(root, "plain", "2")
    assert run(root, "launch") == 0
    seen = json.loads((env.tmp / "stub-out.json").read_text(encoding="utf-8"))
    assert seen["argv"] == [*BASE_ARGV, "--continue"]
    assert run(root, "launch", "--fresh") == 0
    assert json.loads((env.tmp / "stub-out.json").read_text(encoding="utf-8"))["argv"] == BASE_ARGV


def test_launch_sets_the_connector_variable_and_prints_the_flags(env, capsys):
    root = make_setup(env)
    seen_env: list[dict[str, str]] = []
    real_run = subprocess.run

    def spy(command, *args, **kwargs):
        if "--version" not in command:
            seen_env.append(dict(kwargs["env"]))
        return real_run(command, *args, **kwargs)

    env.monkeypatch.setattr(br.subprocess, "run", spy)
    goto(root, "plain", "1")
    capsys.readouterr()
    assert run(root, "launch") == 0
    out = capsys.readouterr().out
    assert seen_env[-1]["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert "--permission-mode auto --effort medium" in out and "ENABLE_CLAUDEAI_MCP_SERVERS=false" in out


def test_setup_disables_the_connectors_in_all_config_folders(env):
    root = make_setup(env)
    for name in ("c0", "c1", "c2"):
        data = json.loads((root / name / "settings.json").read_text(encoding="utf-8"))
        assert data == {"disableClaudeAiConnectors": True}


def test_disable_connectors_merges_into_an_existing_file_and_refuses_a_bad_one(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
    br.disable_connectors(tmp_path)
    assert json.loads((tmp_path / "settings.json").read_text(encoding="utf-8")) == {
        "theme": "dark", "disableClaudeAiConnectors": True}
    (tmp_path / "settings.json").write_text("{", encoding="utf-8")
    with pytest.raises(br.BenchError):
        br.disable_connectors(tmp_path)


def test_launch_refuses_a_visible_key_and_never_prints_it(env, capsys):
    root = make_setup(env)
    goto(root, "plain", "1")
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        env.monkeypatch.setenv(name, SECRET_VALUE)
        assert run(root, "launch") == 2
        captured = capsys.readouterr()
        assert SECRET_VALUE not in captured.out + captured.err
        assert name in captured.err
        env.monkeypatch.delenv(name)
        assert not (env.tmp / "stub-out.json").exists()
    assert run(root, "launch") == 0  # the legal case


def test_launch_refuses_a_wrong_pin(env, capsys):
    root = make_setup(env)
    goto(root, "plain", "1")
    env.monkeypatch.setenv("STUB_VERSION", "9.9.9 (Claude Code)")
    assert run(root, "launch") == 2
    assert "pin" in capsys.readouterr().err
    assert not (env.tmp / "stub-out.json").exists()
    env.monkeypatch.setenv("STUB_VERSION", PIN)
    assert run(root, "launch") == 0


def test_launch_copies_the_cost_state(env):
    root = make_setup(env)
    goto(root, "plain", "1")
    config = root / setup_json(root)["arms"]["plain"].replace("w", "c")
    (config / ".claude.json").write_text(json.dumps({"oauthAccount": {"email": "x@y"}, "projects": {"p": {"lastCost": 1}}}),
                                         encoding="utf-8")
    assert run(root, "launch") == 0
    copied = json.loads((root / "runlog" / "cost-state" / "plain-001.json").read_text(encoding="utf-8"))
    assert copied == {"projects": {"p": {"lastCost": 1}}}


# ----------------------------------------------------------------------------------------------- next, status

def test_abba_order_and_modes(env, capsys):
    root = make_setup(env)
    seq = [(i["arm"], i["step"], i["mode"]) for i in state(root)["sequence"]]
    assert seq[:2] == [("pilot", "1", "fresh"), ("pilot", "2", "continue")]
    order = [f"{'K' if a == 'kit' else 'P'}{s}" for a, s, _ in seq[2:]]
    assert order == ("K0 P1 K1 K2 P2 P3 K3 K4 P4 P5 K5 K6 P6 P7 K7 K8 P8").split()
    assert {s: m for _, s, m in seq[2:]}["1"] == "fresh" and {s: m for _, s, m in seq[2:]}["2"] == "continue"
    assert [f"{'K' if a == 'kit' else 'P'}{s}" for a, s, m in seq[2:] if m == "fresh"] == "K0 P1 K1 K4 P4 P7 K7".split()
    goto(root, "kit", "0")
    capsys.readouterr()
    assert run(root, "next") == 0
    out = capsys.readouterr().out
    assert "arm: kit" in out and "step: 0" in out and "mode: fresh" in out and "START" in out
    assert "none yet" in out


def test_next_stops_at_the_ceiling(env, capsys):
    root = make_setup(env)
    data = state(root)
    data["ceiling"], data["projection"] = 10.0, {"plain": 1.0, "kit": 2.5}
    (root / "runlog" / "run-state.json").write_text(json.dumps(data), encoding="utf-8")
    goto(root, "plain", "1")
    meter = root / "runlog" / "meter"
    meter.mkdir()
    (meter / "plain.json").write_text(json.dumps({"totals": {"usd": 6.0}, "steps": {}}), encoding="utf-8")
    assert run(root, "next") == 0  # 6 + 3 = 9 <= 10
    (meter / "plain.json").write_text(json.dumps({"totals": {"usd": 7.5}, "steps": {}}), encoding="utf-8")
    capsys.readouterr()
    assert run(root, "next") == 1  # 7.5 + 3 > 10
    assert "STOP" in capsys.readouterr().out
    assert run(root, "status") == 0


# ----------------------------------------------------------------------------------------------- copy, log

def test_copy_replaces_the_key_and_logs(env, capsys):
    root = make_setup(env)
    key = (root / "private" / "fake-key.txt").read_text(encoding="utf-8").strip()
    goto(root, "plain", "8")
    assert run(root, "copy", "step") == 0
    assert env.clip[-1] == TEXTS["S8"]["text"].replace("{FAKE_KEY}", key)
    assert key in env.clip[-1] and "{FAKE_KEY}" not in env.clip[-1]
    assert key not in capsys.readouterr().out
    assert run(root, "copy", "A2", "A1") == 0
    assert env.clip[-1] == TEXTS["A2"]["text"] + " " + TEXTS["A1"]["text"]
    assert run(root, "copy", "A9") == 0
    rows = effort(root)[-3:]
    assert [(r["arm"], r["step"], r["action"], r["text_id"]) for r in rows] == [
        ("plain", "8", "paste_step", "S8"), ("plain", "8", "paste_answer", "A2 A1"), ("plain", "8", "paste_resume", "A9")]
    assert run(root, "copy", "ZZ") == 2
    assert len(env.clip) == 3


def test_log_click_and_actions(env):
    root = make_setup(env)
    goto(root, "kit", "3")
    assert run(root, "log", "click") == 0
    assert run(root, "log", "limit", "weekly", "window") == 0
    assert run(root, "log", "usage", "42") == 0
    assert run(root, "log", "bogus") == 2
    rows = effort(root)[-2:]
    assert (rows[0]["action"], rows[0]["count"], rows[0]["arm"], rows[0]["step"]) == ("permission_click", "1", "kit", "3")
    assert (rows[1]["action"], rows[1]["note"]) == ("wait_limit", "weekly window")
    assert "42" in (root / "runlog" / "usage.csv").read_text(encoding="utf-8")
    assert not any(r["action"] == "usage" for r in effort(root))


# ----------------------------------------------------------------------------------------------- score, end-step

def test_score_pass_and_fix_prompts(env, capsys, monkeypatch):
    root = make_setup(env)
    goto(root, "plain", "2")
    assert run(root, "score") == 0
    assert env.clip == []
    assert "10 passed" in capsys.readouterr().out
    monkeypatch.setenv("STUB_FAIL", "1")
    for number in (1, 2, 3):
        assert run(root, "score") == 1
        assert env.clip[-1] == "Fix this please.\n"
        assert f"fix prompt {number} of 3" in capsys.readouterr().out
    assert run(root, "score") == 1
    assert len(env.clip) == 3
    assert "no more" in capsys.readouterr().out
    actions = [r["action"] for r in effort(root)]
    assert actions.count("paste_fix") == 3 and actions.count("score") == 5
    assert run(root, "score") == 1 and len(env.clip) == 3


def test_score_passes_earlier_steps_as_baselines_and_refuses_step_0(env, monkeypatch):
    root = make_setup(env)
    goto(root, "plain", "1")
    assert run(root, "score") == 0
    goto(root, "plain", "2")
    assert run(root, "score") == 0
    result = json.loads((root / "runlog" / "scores" / "plain-2.json").read_text(encoding="utf-8"))
    assert result["baselines"] == ["plain-1.json"]
    goto(root, "kit", "0")
    assert run(root, "score") == 2


def test_end_step_snapshot_meter_and_state(env, capsys, monkeypatch):
    root = make_setup(env)
    arm = setup_json(root)["arms"]["plain"]
    goto(root, "plain", "1")
    run(root, "copy", "step")
    shutil.copytree(METER_FIX / "arm" / "projects", root / arm.replace("w", "c") / "projects")
    answers = iter(["12.5", "2"])
    monkeypatch.setattr(br, "ask", lambda question: next(answers))
    capsys.readouterr()
    assert run(root, "end-step") == 0
    out = capsys.readouterr().out
    assert "remote holds no commits" in out and "meter: written" in out
    assert (root / "runlog" / "snapshots" / "plain-1.bundle").is_file()
    assert (root / "runlog" / "meter" / "plain.json").is_file()
    rows = effort(root)
    assert [(r["action"], r["count"], r["minutes"]) for r in rows[-2:]] == [("permission_click", "2", ""), ("end_step", "", "12.5")]
    data = state(root)
    assert data["index"] == 4 and data["done"][-1]["step"] == "1"
    assert "next: kit step 1" in out
    # the effort log the script wrote is read by the real meter
    done = subprocess.run([sys.executable, str(ROOT / "tools" / "transcript_meter.py"), "--transcripts",
                           str(root / arm.replace("w", "c") / "projects"), "--effort-log", str(root / "runlog" / "effort-log.csv"),
                           "--texts", str(ROOT / "bench" / "build" / "texts.json"), "--arm", "plain", "--out",
                           str(root / "m.json"), "--raw-out", str(root / "raw")], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_end_step_rejects_a_bad_number_and_reports_a_pushed_head(env, monkeypatch, capsys):
    root = make_setup(env)
    goto(root, "plain", "1")
    monkeypatch.setattr(br, "ask", lambda question: "abc")
    assert run(root, "end-step") == 2
    assert state(root)["index"] == 3
    arm = root / setup_json(root)["arms"]["plain"] / "guitar"
    git_out(arm, "push", "-q", "origin", "HEAD:main")
    monkeypatch.setattr(br, "ask", lambda question: "1")
    capsys.readouterr()
    assert run(root, "end-step") == 0
    assert "remote holds the local HEAD" in capsys.readouterr().out


def test_end_step_of_the_pilot_sets_ceiling_and_projections(env, monkeypatch):
    root = make_setup(env)
    meter = root / "runlog" / "meter"
    meter.mkdir()
    (meter / "pilot.json").write_text(json.dumps({"totals": {"usd": 2.0}, "steps": {}}), encoding="utf-8")
    monkeypatch.setattr(br, "ask", lambda question: "0")
    goto(root, "pilot", "1")
    assert run(root, "end-step") == 0
    assert state(root)["ceiling"] is None
    assert run(root, "end-step") == 0
    data = state(root)
    assert data["pilot_spent"] == 2.0
    assert data["projection"] == {"plain": 1.0, "kit": 2.5}
    assert data["ceiling"] == 43.0  # min(3 x 28 x 1, 65 - 2 - 15 - 5)
    assert current_arm(data) == "kit"


def test_end_step_of_session_0_logs_no_end_step_row(env, monkeypatch):
    root = make_setup(env)
    goto(root, "kit", "0")
    monkeypatch.setattr(br, "ask", lambda question: "3")
    assert run(root, "end-step") == 0
    assert effort(root)[-1]["action"] == "exit" and float(effort(root)[-1]["minutes"]) == 3.0
    assert not any(r["action"] == "end_step" for r in effort(root))


def current_arm(data: dict) -> str:
    return data["sequence"][data["index"]]["arm"]


def test_run_ps1_forwards_to_the_script():
    text = (ROOT / "bench" / "build" / "env" / "run.ps1").read_text(encoding="utf-8")
    assert "build_run.py" in text and "@args" in text and "--root" in text and "exit $LASTEXITCODE" in text
