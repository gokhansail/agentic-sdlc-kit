"""Tests for tools/eval_run.py (T-46b, DEC-053): no model call, no network.

A fake `claude` function is injected. It checks the flags it receives, looks at the workspace it
is started in, and returns stream-json lines like the real CLI (shape measured in docs/toolchain.md).
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import eval_run as er  # noqa: E402

KEY_VALUE = "dummy-key-value"
SENTINEL = "SENTINEL-WRONG-ANSWER-TEXT"
QUESTIONS = er.score_mod.load_questions(er.QUESTIONS_FILE)
BY_PROMPT = {q["question"]: q for q in QUESTIONS}
REPO_FILES = sorted(p.relative_to(er.EVAL_REPO).as_posix() for p in er.EVAL_REPO.rglob("*") if p.is_file())


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


def stream(model_id="claude-fake-1", answer="x", cost=0.01, tools=(), server="connected", error=None,
           subtype="success", turns=2, api_key_source="none") -> str:
    init = {"type": "system", "subtype": "init", "model": model_id, "mcp_servers": [], "apiKeySource": api_key_source}
    if server is not None:
        init["mcp_servers"] = [{"name": "sdlc", "status": server}]
    lines = [init]
    for name in tools:
        lines.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": {}}]}})
    text = error or f"Looked at it.\nANSWER: {answer}"
    lines.append({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
    lines.append({
        "type": "result", "subtype": subtype, "is_error": error is not None, "result": text,
        "duration_ms": 1500, "num_turns": turns, "total_cost_usd": 0 if error else cost,
        "terminal_reason": "api_error" if error else "completed",
        "usage": {"input_tokens": 0 if error else 100, "output_tokens": 0 if error else 20,
                  "cache_read_input_tokens": 0 if error else 300, "cache_creation_input_tokens": 0 if error else 50},
        "modelUsage": {} if error else {model_id: {"costUSD": cost}},
    })
    return "\n".join(json.dumps(line) for line in lines) + "\n"


class Fake:
    """A claude stand-in. `behave(question, condition, call_number)` returns an InvokeResult or a stream text."""

    def __init__(self, behave=None):
        self.behave = behave
        self.calls: list[dict] = []
        self.envs: list[dict] = []

    def __call__(self, argv, cwd, env, timeout):
        if argv[1] == "--version":
            return er.InvokeResult(0, "2.1.319 (Claude Code)\n")
        flags = flags_of(argv)
        prompt = argv[2]
        assert argv[0] == "fake-claude" and argv[1] == "-p"
        for needed in ("--strict-mcp-config", "--verbose", "--no-session-persistence", "--restricted"):
            assert flags.get(needed) is True, needed
        assert "--bare" not in flags  # the runs use the subscription login, which --bare does not
        assert "ANTHROPIC_API_KEY" not in env and "ANTHROPIC_AUTH_TOKEN" not in env
        assert flags["--tools"] == "Read"
        assert flags["--setting-sources"] == "project,local"
        assert flags["--permission-mode"] == "dontAsk"
        assert flags["--output-format"] == "stream-json"
        assert int(flags["--max-turns"]) >= 1 and float(flags["--max-budget-usd"]) > 0
        assert "Read" in flags["--allowedTools"].split(",")
        condition = "server" if "--mcp-config" in flags else "no-server"
        if condition == "server":
            config = json.loads(Path(flags["--mcp-config"]).read_text(encoding="utf-8"))
            entry = config["mcpServers"]["sdlc"]
            assert Path(entry["env"]["CLAUDE_PROJECT_DIR"]) == cwd
            assert Path(entry["args"][0]) == er.SERVER_MAIN
            assert not er._inside(Path(flags["--mcp-config"]), cwd)  # the model cannot read the config
        # the workspace: a copy outside the kit, equal to eval/repo, nothing else
        assert not er._inside(cwd, er.KIT_ROOT)
        assert sorted(p.relative_to(cwd).as_posix() for p in cwd.rglob("*") if p.is_file()) == REPO_FILES
        question = next(q for text, q in BY_PROMPT.items() if text in prompt)
        self.calls.append({"argv": argv, "flags": flags, "condition": condition, "question": question["id"],
                           "prompt": prompt, "cwd": cwd, "model": flags["--model"]})
        self.envs.append(env)
        number = len(self.calls)
        out = self.behave(question, condition, number) if self.behave else stream(answer=str(question["key"]))
        return out if isinstance(out, er.InvokeResult) else er.InvokeResult(0, out)


def argv_for(tmp: Path, *extra: str, label="t1", budget="5") -> list:
    return ["--label", label, "--budget-usd", budget, "--claude", "fake-claude",
            "--out", str(tmp / "out"), "--work-dir", str(tmp / "work"), "--results-dir", str(tmp / "results"), *extra]


def run(tmp: Path, fake: Fake, *extra: str, **kw):
    out = io.StringIO()
    code = er.main(argv_for(tmp, *extra, **kw), invoke=fake,
                   env={"ANTHROPIC_API_KEY": KEY_VALUE, "ANTHROPIC_AUTH_TOKEN": KEY_VALUE,
                        "CLAUDE_PROJECT_DIR": "elsewhere", "PATH": "x"}, out=out)
    return code, out.getvalue()


def totals(tmp: Path, label="t1") -> dict:
    return json.loads((tmp / "results" / f"{label}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- flags and isolation

def test_flags_equal_in_both_conditions_except_the_server(tmp_path):
    fake = Fake()
    code, _ = run(tmp_path, fake, "--questions", "Q01", "--models", "haiku")
    assert code == 0
    by_cond = {c["condition"]: c["argv"] for c in fake.calls}
    assert set(by_cond) == {"server", "no-server"}
    server_argv, plain_argv = by_cond["server"], by_cond["no-server"]
    i = server_argv.index("--mcp-config")
    assert server_argv[:i] + server_argv[i + 2:] == plain_argv  # prompt, flags and order all equal
    assert "--mcp-config" not in plain_argv and "--strict-mcp-config" in plain_argv


def test_allowed_tools_name_every_server_tool():
    text = (er.SERVER_MAIN).read_text(encoding="utf-8")
    registered = re.findall(r'name="([a-z_]+)"', text)
    assert sorted(registered) == sorted(er.SERVER_TOOLS)
    allowed = er.allowed_tools().split(",")
    assert allowed[0] == "Read" and all(f"mcp__sdlc__{name}" in allowed for name in registered)


def test_prompt_is_equal_in_both_conditions_and_does_not_name_the_server(tmp_path):
    fake = Fake()
    run(tmp_path, fake, "--questions", "Q12", "--models", "haiku")
    prompts = {c["prompt"] for c in fake.calls}
    assert len(prompts) == 1
    prompt = prompts.pop()
    assert "Q12" not in prompt and "mcp" not in prompt.lower() and "sdlc" not in prompt.lower().replace(".sdlc/", "")
    assert "ANSWER: <value>" in prompt and "whole number" in prompt
    assert all(name in prompt for name in ("DECISIONS.md", ".sdlc/active-contract.md"))


def test_workspace_holds_no_question_file_or_key(tmp_path):
    seen = []

    def behave(question, condition, number):
        cwd = fake.calls[-1]["cwd"]
        names = {p.name for p in cwd.rglob("*")}
        assert "questions.jsonl" not in names and "score.py" not in names
        for path in cwd.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                assert KEY_VALUE not in text and '"answer_type"' not in text
        seen.append(cwd)
        return stream(answer=str(question["key"]))

    fake = Fake(behave)
    code, _ = run(tmp_path, fake, "--questions", "Q01,Q09", "--models", "haiku")
    assert code == 0 and len(seen) == 4
    assert all(not p.exists() for p in seen)  # copies are removed after the run
    assert er.KIT_ROOT not in Path(seen[0]).parents


def test_the_child_env_has_no_api_key_token_or_project_dir_but_keeps_the_rest(tmp_path):
    fake = Fake()
    code, text = run(tmp_path, fake, "--questions", "Q01", "--models", "haiku", "--conditions", "no-server")
    assert code == 0 and len(fake.envs) == 1
    assert fake.envs[0] == {"PATH": "x"}  # the legal case: other variables pass
    assert "ANTHROPIC_API_KEY and ANTHROPIC_AUTH_TOKEN removed" in text and KEY_VALUE not in text


def test_a_run_reporting_an_api_key_as_credential_stops_everything(tmp_path):
    fake = Fake(lambda q, c, n: stream(answer=str(q["key"]), api_key_source="ANTHROPIC_API_KEY"))
    code, text = run(tmp_path, fake, "--questions", "all", "--models", "haiku")
    assert len(fake.calls) == 1 and code == 1
    assert totals(tmp_path)["stopped"] == "auth" and "subscription login" in text
    ok = Fake()  # the legal case: the login reports none
    (tmp_path / "two").mkdir()
    assert run(tmp_path / "two", ok, "--questions", "Q01", "--models", "haiku")[0] == 0


def test_keep_workspaces_leaves_the_copies(tmp_path):
    fake = Fake()
    run(tmp_path, fake, "--questions", "Q01", "--models", "haiku", "--conditions", "server", "--keep-workspaces")
    assert (tmp_path / "work" / "haiku-server-Q01-r1" / "ws" / "TASKS.md").is_file()


# ---------------------------------------------------------------- paths

def test_work_and_out_folders_inside_the_kit_are_refused(tmp_path):
    for flag in ("--work-dir", "--out"):
        argv = argv_for(tmp_path, "--questions", "Q01")
        argv[argv.index(flag) + 1] = str(er.KIT_ROOT / "somewhere")
        out = io.StringIO()
        code = er.main(argv, invoke=Fake(), env={"ANTHROPIC_API_KEY": KEY_VALUE}, out=out)
        assert code == 2 and "outside the kit" in out.getvalue()
        assert not (er.KIT_ROOT / "somewhere").exists()


def test_a_dotdot_path_that_lands_in_the_kit_is_refused(tmp_path):
    argv = argv_for(tmp_path, "--questions", "Q01")
    argv[argv.index("--work-dir") + 1] = str(er.KIT_ROOT / "tests" / ".." / "elsewhere")
    out = io.StringIO()
    assert er.main(argv, invoke=Fake(), env={"ANTHROPIC_API_KEY": KEY_VALUE}, out=out) == 2
    assert "outside the kit" in out.getvalue()


def test_out_folder_under_evidence_raw_is_the_one_legal_place_inside_the_kit(tmp_path):
    cfg = er.Config(label="x", budget_usd=1, out_dir=er.KIT_ROOT / "evidence" / "raw" / "x", work_dir=tmp_path)
    assert er.check_paths(cfg) is None  # out under evidence/raw passes, work folder outside passes
    cfg.out_dir = er.KIT_ROOT / "eval" / "raw"
    assert "outside the kit" in er.check_paths(cfg)
    cfg.out_dir = tmp_path / "out"
    cfg.work_dir = er.KIT_ROOT / "eval" / "repo"
    assert "outside the kit" in er.check_paths(cfg)
    cfg.work_dir = tmp_path / "work"
    assert er.check_paths(cfg) is None


# ---------------------------------------------------------------- parse and score

@pytest.mark.parametrize("text,want", [
    ("blah\nANSWER: DEC-007", "DEC-007"),
    ("**ANSWER:** DEC-007", "DEC-007"),
    ("`ANSWER: yes`", "yes"),
    ("answer = 3.\n", "3."),
    ("ANSWER: [C-1, S-1]", "C-1, S-1"),
    ("ANSWER: no\nthen more words\nANSWER: yes", "yes"),
    ("The answer is 3", None),
    ("ANSWER:", None),
    ("", None),
])
def test_parse_answer(text, want):
    assert er.parse_answer(text) == want


def test_scoring_uses_the_eval_scorer_and_an_unparsed_answer_is_wrong_and_counted(tmp_path):
    def behave(question, condition, number):
        if question["id"] == "Q01":
            return stream(answer="YES.")                      # right after normalisation
        if question["id"] == "Q09":
            return stream(answer=SENTINEL)                    # parsed, wrong
        return stream(answer="x").replace("ANSWER: x", "no final line here")  # unparsed

    fake = Fake(behave)
    code, text = run(tmp_path, fake, "--questions", "Q01,Q09,Q15", "--models", "haiku", "--conditions", "no-server")
    assert code == 0
    group = totals(tmp_path)["groups"][0]
    assert (group["runs"], group["correct"], group["unparsed"], group["errors"]) == (3, 1, 1, 0)
    assert group["accuracy_mean"] == pytest.approx(1 / 3)
    assert group["by_category"]["scope"] == {"correct": 1, "total": 1}
    assert "unparsed 1" in text


def test_a_run_with_an_error_subtype_and_a_right_answer_is_not_correct(tmp_path):
    fake = Fake(lambda q, c, n: stream(answer=str(q["key"]), subtype="error_max_turns"))
    run(tmp_path, fake, "--questions", "Q01", "--models", "haiku", "--conditions", "no-server")
    group = totals(tmp_path)["groups"][0]
    assert (group["runs"], group["correct"], group["errors"]) == (1, 0, 1)
    assert group["accuracy_mean"] == 0
    raw = (tmp_path / "out" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
    record = json.loads(raw[0])
    assert record["correct"] is False and record["answer_matched"] is True and record["error"]


def test_set_answer_is_scored_as_a_set(tmp_path):
    fake = Fake(lambda q, c, n: stream(answer="DEC-009, dec-008"))
    run(tmp_path, fake, "--questions", "Q13", "--models", "haiku", "--conditions", "no-server")
    assert totals(tmp_path)["groups"][0]["correct"] == 1


# ---------------------------------------------------------------- totals

GROUP_KEYS = {
    "model", "model_id", "condition", "runs", "correct", "accuracy_mean", "accuracy_min", "accuracy_max",
    "by_category", "cost_usd", "cost_usd_per_run", "input_tokens", "cache_read_tokens", "cache_creation_tokens",
    "output_tokens", "duration_ms", "duration_ms_per_run", "turns_per_run", "tool_calls_total", "tool_calls",
    "errors", "unparsed",
}
TOP_KEYS = {
    "schema", "label", "date", "cli_version", "eval_set_sha256", "question_ids", "repeats", "settings",
    "planned_runs", "done_runs", "complete", "stopped", "budget_usd", "spent_usd", "groups",
}


def test_totals_have_fixed_keys_and_no_answer_text(tmp_path):
    def behave(question, condition, number):
        tools = ("mcp__sdlc__decisions", "Read") if condition == "server" else ("Read", "Read", "Read")
        return stream(answer=SENTINEL, tools=tools, cost=0.02)

    code, _ = run(tmp_path, Fake(behave), "--questions", "Q09,Q12", "--models", "haiku,sonnet", "--repeats", "2")
    assert code == 0
    data = totals(tmp_path)
    assert set(data) == TOP_KEYS
    assert data["planned_runs"] == data["done_runs"] == 16 and data["complete"] is True and data["stopped"] == ""
    assert data["eval_set_sha256"] == er.questions_hash()
    assert data["cli_version"].startswith("2.1.319")
    assert len(data["groups"]) == 4
    for group in data["groups"]:
        assert set(group) == GROUP_KEYS
        assert group["runs"] == 4 and group["model_id"] == "claude-fake-1"
        assert group["cost_usd"] == pytest.approx(0.08)
        assert group["input_tokens"] == 400 and group["output_tokens"] == 80
        assert group["cache_read_tokens"] == 1200 and group["cache_creation_tokens"] == 200
        assert group["duration_ms"] == 6000 and group["turns_per_run"] == 2
    server = next(g for g in data["groups"] if g["condition"] == "server")
    plain = next(g for g in data["groups"] if g["condition"] == "no-server")
    assert server["tool_calls"] == {"Read": 4, "mcp__sdlc__decisions": 4} and server["tool_calls_total"] == 8
    assert plain["tool_calls"] == {"Read": 12} and plain["tool_calls_total"] == 12
    assert SENTINEL not in (tmp_path / "results" / "t1.json").read_text(encoding="utf-8")
    raw = list((tmp_path / "out" / "raw").glob("*.jsonl"))
    assert len(raw) == 16 and SENTINEL in raw[0].read_text(encoding="utf-8")  # raw text stays in the output folder
    records = (tmp_path / "out" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(records) == 16


def test_repeats_give_min_mean_max_of_the_per_repeat_accuracy(tmp_path):
    def behave(question, condition, number):
        good = number > 2  # the first repeat of 2 questions (2 conditions x 1 model) is wrong, the second right
        return stream(answer=str(question["key"]) if good else "zzz")

    run(tmp_path, Fake(behave), "--questions", "Q09,Q11", "--models", "haiku", "--conditions", "no-server",
        "--repeats", "2")
    group = totals(tmp_path)["groups"][0]
    assert (group["accuracy_min"], group["accuracy_max"], group["accuracy_mean"]) == (0.0, 1.0, 0.5)


def test_order_covers_all_models_and_conditions_of_a_question_first(tmp_path):
    fake = Fake()
    run(tmp_path, fake, "--questions", "Q01,Q09", "--models", "haiku,sonnet")
    first_four = {(c["question"], c["model"], c["condition"]) for c in fake.calls[:4]}
    assert {q for q, _, _ in first_four} == {"Q01"} and len(first_four) == 4


def test_pilot_is_one_question_from_each_of_the_five_largest_categories():
    picked = er.select_questions(QUESTIONS, "pilot")
    assert [q["category"] for q in picked] == ["scope", "decisions", "findings", "tasks", "guard"]
    assert [q["id"] for q in picked] == ["Q01", "Q09", "Q15", "Q21", "Q26"]
    assert len(er.select_questions(QUESTIONS, "all")) == 30
    assert [q["id"] for q in er.select_questions(QUESTIONS, "Q30, Q02,Q30")] == ["Q30", "Q02"]
    with pytest.raises(ValueError):
        er.select_questions(QUESTIONS, "Q99")


# ---------------------------------------------------------------- budget stop

def test_run_stops_before_a_call_that_would_pass_the_budget(tmp_path):
    fake = Fake(lambda q, c, n: stream(answer=str(q["key"]), cost=0.10))
    code, text = run(tmp_path, fake, "--questions", "all", "--models", "haiku", "--conditions", "no-server",
                     "--max-run-usd", "0.25", budget="0.35")
    assert len(fake.calls) == 2  # every call is estimated at the 0.25 cap: 0 and 0.10 spent fit, 0.20 does not
    data = totals(tmp_path)
    assert data["stopped"] == "budget" and data["complete"] is False and data["done_runs"] == 2
    assert data["spent_usd"] == pytest.approx(0.20) and data["spent_usd"] <= data["budget_usd"]
    assert code == 1 and "stopped before run 3/30" in text and "stopped: budget" in text


def test_a_cheap_first_run_does_not_lower_the_estimate_of_the_next_call(tmp_path):
    costs = {1: 0.10, 2: 0.25}
    fake = Fake(lambda q, c, n: stream(answer=str(q["key"]), cost=costs.get(n, 0.25)))
    code, _ = run(tmp_path, fake, "--questions", "all", "--models", "haiku", "--conditions", "no-server",
                  "--max-run-usd", "0.25", budget="0.30")
    assert len(fake.calls) == 1  # 0.10 spent + 0.25 cap passes 0.30
    data = totals(tmp_path)
    assert code == 1 and data["stopped"] == "budget" and data["spent_usd"] <= data["budget_usd"]


def test_the_first_call_uses_the_per_run_cap_as_its_estimate(tmp_path):
    fake = Fake()
    code, text = run(tmp_path, fake, "--questions", "Q01", "--max-run-usd", "0.25", budget="0.20")
    assert fake.calls == [] and code == 1 and "stopped before run 1/" in text
    assert totals(tmp_path)["done_runs"] == 0 and totals(tmp_path)["groups"] == []


def test_resume_continues_a_stopped_label_without_repeating_runs(tmp_path):
    fake = Fake(lambda q, c, n: stream(answer=str(q["key"]), cost=0.10))
    args = ("--questions", "Q01,Q09", "--models", "haiku", "--conditions", "no-server", "--max-run-usd", "0.10")
    code, _ = run(tmp_path, fake, *args, budget="0.15")
    assert code == 1 and len(fake.calls) == 1  # 0.10 fits, then 0.10 spent + 0.10 estimated passes 0.15
    fake2 = Fake(lambda q, c, n: stream(answer=str(q["key"]), cost=0.10))
    code, _ = run(tmp_path, fake2, *args, "--resume", budget="5")
    data = totals(tmp_path)
    assert code == 0 and data["done_runs"] == 2 and data["complete"] is True
    assert data["spent_usd"] == pytest.approx(0.20)
    assert {c["question"] for c in fake2.calls} == {"Q09"}


def test_an_existing_label_is_not_overwritten_without_resume(tmp_path):
    run(tmp_path, Fake(), "--questions", "Q01", "--models", "haiku")
    before = (tmp_path / "results" / "t1.json").read_text(encoding="utf-8")
    code, text = run(tmp_path, Fake(), "--questions", "Q01", "--models", "haiku")
    assert code == 2 and "already has output" in text
    assert (tmp_path / "results" / "t1.json").read_text(encoding="utf-8") == before


# ---------------------------------------------------------------- failed calls

def credit_error(question, condition, number):
    return er.InvokeResult(1, stream(error="Credit balance is too low", subtype="success"))


def test_a_failed_call_is_counted_scored_wrong_and_the_run_goes_on(tmp_path):
    def behave(question, condition, number):
        return credit_error(question, condition, number) if number == 1 else stream(answer=str(question["key"]))

    code, _ = run(tmp_path, Fake(behave), "--questions", "Q01,Q09", "--models", "haiku", "--conditions", "no-server")
    group = totals(tmp_path)["groups"][0]
    assert (group["runs"], group["errors"], group["unparsed"], group["correct"]) == (2, 1, 1, 1)
    assert code == 0
    records = [json.loads(x) for x in (tmp_path / "out" / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert records[0]["error"] == "api_error" and records[0]["correct"] is False and records[1]["error"] == ""


def test_three_zero_cost_failures_in_a_row_stop_the_run(tmp_path):
    fake = Fake(credit_error)
    code, text = run(tmp_path, fake, "--questions", "all", "--models", "haiku")
    assert len(fake.calls) == 3 and code == 1
    data = totals(tmp_path)
    assert data["stopped"] == "errors" and data["done_runs"] == 3
    assert sum(g["errors"] for g in data["groups"]) == 3 and "failed with no cost" in text


def test_timeout_missing_result_and_server_not_connected_are_errors(tmp_path):
    def behave(question, condition, number):
        if number == 1:
            return er.InvokeResult(None, "", True)
        if number == 2:
            return er.InvokeResult(0, '{"type": "system", "subtype": "init"}\n')
        if number == 3:
            return er.InvokeResult(3, "")
        return stream(answer=str(question["key"]), server="failed")

    run(tmp_path, Fake(behave), "--questions", "Q01,Q09,Q15,Q21", "--models", "haiku", "--conditions", "server",
        "--max-failed-calls", "9")
    errors = [json.loads(x)["error"] for x in (tmp_path / "out" / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert errors == ["timeout", "no_result", "exit_3", "mcp_not_connected"]
    assert totals(tmp_path)["groups"][0]["errors"] == 4


def test_interrupt_writes_the_totals_so_far(tmp_path):
    def behave(question, condition, number):
        if number == 3:
            raise KeyboardInterrupt
        return stream(answer=str(question["key"]))

    code, text = run(tmp_path, Fake(behave), "--questions", "Q01,Q09", "--models", "haiku")
    data = totals(tmp_path)
    assert code == 130 and data["stopped"] == "interrupted" and data["done_runs"] == 2 and "--resume" in text


# ---------------------------------------------------------------- arguments

def test_bad_arguments_are_refused_before_any_call_and_no_key_is_needed(tmp_path):
    fake = Fake()
    env = {"PATH": "x"}
    for bad in (["--label", "../x"], ["--questions", "Q99"], ["--conditions", "both"], ["--models", "a b"],
                ["--repeats", "0"]):
        argv = argv_for(tmp_path) + bad
        assert er.main(argv, invoke=fake, env=env, out=io.StringIO()) == 2
    assert fake.calls == []
    assert er.main(argv_for(tmp_path, "--questions", "Q01", "--models", "haiku"), invoke=fake, env=env,
                   out=io.StringIO()) == 0


def test_the_budget_is_required():
    with pytest.raises(SystemExit):
        er.main(["--label", "x"], invoke=Fake(), env={"ANTHROPIC_API_KEY": KEY_VALUE}, out=io.StringIO())


def test_default_invoke_runs_a_process_and_stops_a_slow_one(tmp_path):
    env = dict(os.environ)
    ok = er.default_invoke([sys.executable, "-c", "print('hi')"], tmp_path, env, 30)
    assert ok.returncode == 0 and ok.stdout.strip() == "hi" and not ok.timed_out
    slow = er.default_invoke([sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, env, 1)
    assert slow.timed_out and slow.returncode is None
    assert er.default_invoke([str(tmp_path / "no-such-program")], tmp_path, env, 5).returncode is None
