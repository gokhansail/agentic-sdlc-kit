"""Tests for tools/transcript_meter.py (T-63): synthetic transcripts only, no model call, no network."""
from __future__ import annotations

import json
import shutil
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import transcript_meter as tm  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "transcripts"
SONNET = "claude-sonnet-5-5"
SIMPLE_LOG = (
    "ts_start,ts_end,arm,step,action,text_id,count,minutes,note\n"
    "2026-01-01T09:00:00Z,,plain,1,paste_step,S1,,,\n"
    "2026-01-01T10:00:00Z,,plain,1,end_step,,,5,\n"
)
FIXTURE_STRINGS = ("Build the thing", "step one", "Use option two", "Keep the current names", "nobody scripted",
                   "fixture", "src/app.py", "memory/note.md", "Please continue", "Fix the failing")


# ----------------------------------------------------------------------------------------------- helpers

def copy_fixture(tmp_path: Path) -> Path:
    target = tmp_path / "fx"
    shutil.copytree(FIX, target)
    return target


def run_meter(tmp_path: Path, fx: Path | None = None, **over: Any) -> tuple[int, dict[str, Any] | None, Path, Path]:
    """Run the meter on the fixture (or a copy); returns exit code, parsed output (None when not written), paths."""
    fx = fx or FIX
    out = over.pop("out", tmp_path / "out" / "totals.json")
    raw = over.pop("raw", tmp_path / "raw")
    args = {
        "transcripts": fx / "arm", "effort-log": fx / "effort-log.csv", "texts": fx / "texts.json",
        "arm": "plain", "model": SONNET, "prices": fx / "prices-test.json", "out": out, "raw-out": raw,
    }
    args.update({k.replace("_", "-"): v for k, v in over.items()})
    argv: list[str] = []
    for key, value in args.items():
        if value is not None:
            argv += [f"--{key}", str(value)]
    code = tm.main(argv)
    parsed = json.loads(out.read_text(encoding="utf-8")) if Path(out).exists() else None
    return code, parsed, Path(out), Path(raw)


def write_arm(tmp_path: Path, files: dict[str, list[dict[str, Any]]], log: str = SIMPLE_LOG) -> dict[str, Path]:
    root = tmp_path / "syn"
    for name, lines in files.items():
        path = root / "arm" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    (root / "effort-log.csv").write_text(log, encoding="utf-8")
    (root / "texts.json").write_text(json.dumps({"S1": {"type": "step", "text": "Go."}}), encoding="utf-8")
    return {"transcripts": root / "arm", "effort_log": root / "effort-log.csv", "texts": root / "texts.json"}


def assistant(uuid: str, ts: str, mid: str | None, out: int, **extra: Any) -> dict[str, Any]:
    message: dict[str, Any] = {"model": extra.pop("model", SONNET), "role": "assistant", "content": [],
                               "usage": {"input_tokens": 1, "output_tokens": out}}
    if mid is not None:
        message["id"] = mid
    return {"type": "assistant", "uuid": uuid, "timestamp": ts, "sessionId": "s", "isSidechain": False,
            "message": message, **extra}


def user(uuid: str, ts: str, content: Any, **extra: Any) -> dict[str, Any]:
    return {"type": "user", "uuid": uuid, "timestamp": ts, "sessionId": "s", "isSidechain": False,
            "message": {"role": "user", "content": content}, **extra}


def run_syn(tmp_path: Path, files: dict[str, list[dict[str, Any]]], log: str = SIMPLE_LOG, **over: Any):
    paths = write_arm(tmp_path, files, log)
    return run_meter(tmp_path, FIX, **{**paths, **over})


def row(result: dict[str, Any], **match: Any) -> dict[str, Any]:
    found = [r for r in result["rows"] if all(r[k] == v for k, v in match.items())]
    assert len(found) == 1, (match, found)
    return found[0]


# ----------------------------------------------------------------------------------------------- dedup

def test_one_message_split_over_three_lines_is_counted_once(tmp_path: Path) -> None:
    lines = [assistant("a1", "2026-01-01T09:01:00Z", "m1", 5), assistant("a2", "2026-01-01T09:01:01Z", "m1", 20),
             assistant("a3", "2026-01-01T09:01:02Z", "m1", 50)]
    code, result, _, _ = run_syn(tmp_path, {"main.jsonl": lines})
    assert code == 0 and result is not None
    assert result["messages"]["counted"] == 1 and result["messages"]["duplicate_lines_dropped"] == 2
    tokens = result["totals"]["tokens"]
    assert tokens["output"] == 50 and tokens["input"] == 1  # the largest output line, not the sum of 3 lines


def test_the_same_id_in_a_resumed_file_is_counted_once(tmp_path: Path) -> None:
    first = [assistant("a1", "2026-01-01T09:01:00Z", "m1", 30)]
    resumed = [assistant("a1", "2026-01-01T09:01:00Z", "m1", 30), assistant("a2", "2026-01-01T09:02:00Z", "m2", 7)]
    code, result, _, _ = run_syn(tmp_path, {"one.jsonl": first, "two.jsonl": resumed})
    assert code == 0 and result is not None
    assert result["messages"]["counted"] == 2 and result["totals"]["tokens"]["output"] == 37


def test_resumed_fixture_counts_each_message_once() -> None:
    result = run_fixture()
    # msg-1 (3 lines, replayed in the resumed file) and msg-2 (replayed) count once each
    assert row(result, agent="main", model=SONNET, speed="standard", step="1")["tokens"]["output"] == 50 + 30 + 1 + 4
    assert result["messages"] == {"assistant_lines": 17, "counted": 10, "duplicate_lines_dropped": 7,
                                  "no_id_lines": 1, "no_usage_lines": 0, "unique_ids": 9}


def test_lines_without_an_id_are_counted_one_by_one_and_reported(tmp_path: Path) -> None:
    lines = [assistant("a1", "2026-01-01T09:01:00Z", None, 4), assistant("a2", "2026-01-01T09:01:01Z", None, 4)]
    code, result, _, _ = run_syn(tmp_path, {"main.jsonl": lines})
    assert code == 0 and result is not None
    assert result["messages"]["no_id_lines"] == 2 and result["messages"]["counted"] == 2
    assert result["totals"]["tokens"]["output"] == 8


# ----------------------------------------------------------------------------------------------- agents

def test_sidechain_messages_are_split_by_agent_type() -> None:
    result = run_fixture()
    assert set(result["by_agent"]) == {"main", "sub:developer", "sub:scout"}
    assert result["by_agent"]["sub:developer"]["tokens"]["input"] == 61000
    assert result["by_agent"]["sub:scout"]["messages"] == 1
    assert result["subagents"] == {"developer": 1, "scout": 1}
    assert result["steps"]["1"]["subagents"] == {"developer": 1} and result["steps"]["2"]["subagents"] == {"scout": 1}


def test_sidechain_lines_in_a_main_file_take_the_type_from_the_line(tmp_path: Path) -> None:
    side = assistant("a2", "2026-01-01T09:02:00Z", "m2", 9, isSidechain=True, agentId="x1", agentType="reviewer")
    unknown = assistant("a3", "2026-01-01T09:03:00Z", "m3", 3, isSidechain=True, agentId="x2")
    lines = [assistant("a1", "2026-01-01T09:01:00Z", "m1", 4), side, unknown]
    code, result, _, _ = run_syn(tmp_path, {"main.jsonl": lines})
    assert code == 0 and result is not None
    assert set(result["by_agent"]) == {"main", "sub:reviewer", "sub:unknown"}
    assert result["subagents"] == {"reviewer": 1, "unknown": 1}


# ----------------------------------------------------------------------------------------------- human turns

def test_each_human_turn_type_is_counted() -> None:
    result = run_fixture()
    # tool results (u2) and the sub-agent prompt (same words as the step text) are not human turns
    assert result["human_turns"] == {"answer": 2, "approval": 1, "command": 1, "fix": 1, "other": 1, "resume": 1, "step": 2}
    assert result["text_ids"] == {"A1": 1, "A2": 2, "A3": 1, "A9": 1, "F1": 1, "S1": 1, "S2": 1}
    assert result["steps"]["1"]["human_turns"] == {"answer": 1, "command": 1, "other": 1, "step": 1}
    assert result["steps"]["2"]["human_turns"] == {"answer": 1, "approval": 1, "fix": 1, "resume": 1, "step": 1}


def test_an_unmatched_turn_is_listed_by_hash_only() -> None:
    result = run_fixture()
    listed = result["steps"]["1"]["other_turns"]
    assert len(listed) == 1 and listed[0]["index"] == 1 and len(listed[0]["sha256"]) == 64
    assert listed[0]["sha256"] == tm.sha256(b"Do something nobody scripted.")


def test_two_texts_pasted_in_one_message_match_as_a_sequence() -> None:
    result = run_fixture()
    assert result["steps"]["2"]["text_ids"]["A2"] == 1 and result["steps"]["2"]["text_ids"]["A3"] == 1
    texts = tm.Texts({"A": "answer", "B": "answer", "C": "fix"}, [("one", "A"), ("two", "B"), ("three", "C")], "")
    assert tm.classify_turn("one \n two", texts) == ("answer", ("A", "B"))
    assert tm.classify_turn("one", texts) == ("answer", ("A",))
    assert tm.classify_turn("one three", texts) == ("other", ())  # mixed types are a deviation
    assert tm.classify_turn("one twothree", texts) == ("other", ())  # no word boundary: not a match


def test_non_human_user_lines_and_slash_text(tmp_path: Path) -> None:
    lines = [
        assistant("a1", "2026-01-01T09:00:30Z", "m1", 1),
        user("u1", "2026-01-01T09:01:00Z", "Go."),
        user("u2", "2026-01-01T09:02:00Z", "injected note", isMeta=True),
        user("u3", "2026-01-01T09:03:00Z", "<local-command-stdout>ok</local-command-stdout>"),
        user("u4", "2026-01-01T09:04:00Z", "handback", promptSource="system"),
        user("u5", "2026-01-01T09:05:00Z", "summary", isCompactSummary=True),
        user("u6", "2026-01-01T09:06:00Z", "/exit"),
        user("u7", "2026-01-01T09:07:00Z", [{"type": "tool_result", "tool_use_id": "t", "content": "Go."}]),
        user("u8", "2026-01-01T09:08:00Z", "   "),
    ]
    code, result, _, _ = run_syn(tmp_path, {"main.jsonl": lines})
    assert code == 0 and result is not None
    assert result["human_turns"] == {"command": 1, "step": 1}


# ----------------------------------------------------------------------------------------------- USD

def test_an_unpriced_model_gives_tokens_and_null_usd() -> None:
    result = run_fixture()
    unknown = row(result, model="claude-unknown-9")
    assert unknown["usd"] is None and unknown["tokens"]["input"] == 7 and unknown["tokens"]["output"] == 9
    assert result["by_model"]["claude-unknown-9"]["usd"] is None
    assert {"messages": 1, "model": "claude-unknown-9", "reason": "no price"} in result["unpriced"]
    assert result["totals"]["usd_complete"] is False


def test_fast_speed_gives_null_usd_and_a_row_of_its_own() -> None:
    result = run_fixture()
    fast = row(result, speed="fast")
    assert fast["usd"] is None and fast["tokens"]["cache_write_unsplit"] == 20
    assert {"messages": 1, "model": SONNET, "reason": "fast speed"} in result["unpriced"]
    assert row(result, model=SONNET, speed="standard", step="2", agent="main")["usd"] == 0.000108


def test_priced_totals_are_exact() -> None:
    result = run_fixture()
    assert row(result, model=SONNET, agent="main", step="1")["usd"] == 0.001788  # 5m, 1h, read and output rows
    assert result["totals"]["usd"] == 0.037206
    assert result["prices"]["read_on"] == "2026-01-01"


def test_a_haiku_message_over_100000_prompt_tokens_uses_the_higher_row() -> None:
    result = run_fixture()
    # 60000 input + 50000 read = 110000 > 100000: higher row (0.50, 0.05, 2.50); the other message is under it
    assert row(result, model="claude-haiku-5-5")["usd"] == 0.03517
    prices = tm.load_prices(FIX / "prices-test.json")
    entry = prices.find("claude-haiku-5-5")
    base = {key: 0 for key in tm.TOKEN_KEYS}
    at_limit = dict(base, input=60000, cache_read=40000, output=1000)
    over = dict(base, input=60000, cache_read=40001, output=1000)
    assert message_cost(at_limit, entry) == Decimal("0.0069")    # exactly 100000 is not over: 6000 + 400 + 500 micro-USD
    assert message_cost(over, entry) == Decimal("0.0345")        # 30000 + 2000.05 + 2500 micro-USD
    cache_write = dict(base, cache_write_5m=60000, cache_write_unsplit=40001)  # cache writes count as prompt tokens
    assert tm.message_usd(cache_write, "standard", entry) == Decimal("0.062500625")


def message_cost(tokens: dict[str, int], entry: dict[str, Any]) -> Decimal:
    value = tm.message_usd(tokens, "standard", entry)
    assert value is not None
    return value.quantize(Decimal("0.0001"))


def test_a_model_id_with_a_date_suffix_finds_its_price() -> None:
    prices = tm.load_prices(FIX / "prices-test.json")
    assert prices.find("claude-sonnet-5-5-20260101") is prices.find(SONNET)
    assert prices.find("claude-nothing-1") is None and prices.find(None) is None


def test_the_real_price_file_holds_the_contract_rows() -> None:
    prices = tm.load_prices(tm.DEFAULT_PRICES)
    assert prices.read_on == "2026-11-21"
    sonnet = prices.find("claude-sonnet-5-5")["prices"]
    assert (sonnet["input"], sonnet["cache_write_5m"], sonnet["cache_write_1h"], sonnet["cache_read"], sonnet["output"]) \
        == (Decimal(2), Decimal("2.5"), Decimal(4), Decimal("0.1"), Decimal(10))
    opus = prices.find("claude-opus-5-5")["prices"]
    assert (opus["input"], opus["cache_write_5m"], opus["cache_write_1h"], opus["cache_read"], opus["output"]) \
        == (Decimal(4), Decimal(5), Decimal(8), Decimal("0.2"), Decimal(20))
    fable = prices.find("claude-fable-5-2")["prices"]
    assert (fable["input"], fable["output"]) == (Decimal(8), Decimal(40))
    haiku = prices.find("claude-haiku-5-5")
    assert haiku["threshold"] == 100000 and haiku["prices"]["input"] == Decimal("0.1")
    assert haiku["long_prices"]["input"] == Decimal("0.5") and haiku["long_prices"]["output"] == Decimal("2.5")


# ----------------------------------------------------------------------------------------------- model, time, other counts

def test_a_main_message_off_the_fixed_model_is_listed() -> None:
    result = run_fixture()
    assert result["fixed_model"] == SONNET
    assert result["off_model"] == [{"messages": 1, "model": "claude-unknown-9", "step": "1"}]  # sub-agents are not listed


def test_without_a_fixed_model_nothing_is_listed_and_the_output_says_so(tmp_path: Path) -> None:
    code, result, _, _ = run_meter(tmp_path, model=None)
    assert code == 0 and result is not None
    assert result["fixed_model"] is None and result["off_model"] == []


def test_wall_active_and_maintainer_minutes_per_step() -> None:
    steps = run_fixture()["steps"]
    assert steps["1"]["wall_minutes"] == 9.0 and steps["2"]["wall_minutes"] == 10.0
    assert steps["1"]["active_minutes"] == 4.67 and steps["2"]["active_minutes"] == 3.5
    assert steps["1"]["idle_minutes"] == 4.33 and steps["2"]["idle_minutes"] == 6.5
    assert steps["1"]["maintainer_minutes"] == 6.5 and steps["2"]["maintainer_minutes"] == 4.0
    assert steps["1"]["permission_clicks"] == 2 and steps["2"]["permission_clicks"] == 0
    assert steps["1"]["actions"]["score"] == 1 and steps["1"]["closed"] is True


def test_rows_of_other_arms_are_ignored() -> None:
    assert "kit" not in json.dumps(run_fixture()["steps"]) and len(run_fixture()["steps"]) == 2


def test_a_step_with_no_end_mark_has_no_wall_time(tmp_path: Path) -> None:
    fx = copy_fixture(tmp_path)
    log = (fx / "effort-log.csv").read_text(encoding="utf-8").replace("2026-01-01T09:31:00Z,,plain,2,end_step,,,4,\n", "")
    (fx / "effort-log.csv").write_text(log, encoding="utf-8")
    code, result, _, _ = run_meter(tmp_path, fx)
    assert code == 0 and result is not None
    step2 = result["steps"]["2"]
    assert step2["closed"] is False and step2["wall_minutes"] is None and step2["idle_minutes"] is None
    assert step2["active_minutes"] == 3.5


def test_compactions_and_session_starts_are_counted_per_step() -> None:
    result = run_fixture()
    # the boundary and its summary are one compaction; the resumed file repeats the boundary (same uuid)
    assert result["compactions"] == 1 and result["steps"]["1"]["compactions"] == 1
    # a session launched before paste_step belongs to the step it starts; the resumed copies start no session
    assert result["session_starts"] == 2
    assert result["steps"]["1"]["session_starts"] == 1 and result["steps"]["2"]["session_starts"] == 1


def test_writes_by_actor_and_memory_folder_writes() -> None:
    writes = run_fixture()["writes"]
    assert writes["by_actor"] == {"main": {"Edit": 2, "Write": 1}, "sub:developer": {"Write": 1}}
    assert writes["shell_writes"] == "not attributed"
    assert len(writes["memory"]) == 1
    note = writes["memory"][0]
    assert (note["actor"], note["tool"], note["step"]) == ("sub:developer", "Write", "1")
    assert note["path_sha256"] == tm.sha256(b".claude/projects/x/memory/note.md")


# ----------------------------------------------------------------------------------------------- cost state

def test_cost_state_prints_both_totals_per_model(tmp_path: Path) -> None:
    code, result, _, _ = run_meter(tmp_path, cost_state=FIX / "cost-state.json")
    assert code == 0 and result is not None
    block = result["cost_state"]
    assert block["verified"] is False and "unverified" in block["note"]
    sonnet = block["models"][SONNET]
    assert sonnet["cli"] == {"cache_read": 3310, "cache_write": 220, "input": 45, "output": 108, "usd": 0.002}
    assert sonnet["meter"]["cache_write"] == 220 and sonnet["meter"]["usd"] == 0.002036
    assert sonnet["meter_minus_cli_usd"] == 0.000036
    assert "cli" not in block["models"]["claude-unknown-9"]


def test_cost_state_in_json_lines_sums_the_last_state_of_each_session(tmp_path: Path) -> None:
    states = [
        {"type": "cost-state", "sessionId": "one", "modelUsage": {SONNET: {"inputTokens": 1, "costUSD": 1}}},
        {"type": "cost-state", "sessionId": "one", "modelUsage": {SONNET: {"inputTokens": 5, "costUSD": 2}}},
        {"type": "cost-state", "sessionId": "two", "modelUsage": {SONNET: {"input_tokens": 3, "cost_usd": 0.5}}},
    ]
    path = tmp_path / "states.jsonl"
    path.write_text("\n".join(json.dumps(s) for s in states) + "\n", encoding="utf-8")
    code, result, _, _ = run_meter(tmp_path, cost_state=path)
    assert code == 0 and result is not None
    assert result["cost_state"]["models"][SONNET]["cli"]["input"] == 8
    assert result["cost_state"]["models"][SONNET]["cli"]["usd"] == 2.5


# ----------------------------------------------------------------------------------------------- output rules

def test_a_second_run_is_byte_equal(tmp_path: Path) -> None:
    code1, _, out1, raw1 = run_meter(tmp_path / "a", cost_state=FIX / "cost-state.json")
    code2, _, out2, raw2 = run_meter(tmp_path / "b", cost_state=FIX / "cost-state.json")
    assert code1 == code2 == 0
    assert out1.read_bytes() == out2.read_bytes()
    names = sorted(p.name for p in raw1.iterdir())
    assert names == sorted(p.name for p in raw2.iterdir()) and len(names) == 3
    for name in names:
        assert (raw1 / name).read_bytes() == (raw2 / name).read_bytes()


def test_the_committed_output_holds_no_fixture_text_and_no_path(tmp_path: Path) -> None:
    code, result, out, _ = run_meter(tmp_path, cost_state=FIX / "cost-state.json")
    assert code == 0 and result is not None
    text = out.read_text(encoding="utf-8")
    for word in FIXTURE_STRINGS:
        assert word not in text
    assert "/" not in text and "\\" not in text and str(tmp_path) not in text and "tests" not in text
    assert result["schema"] == 1 and text.endswith("\n")
    assert text == json.dumps(result, sort_keys=True, indent=2) + "\n"


def test_the_raw_tables_go_to_a_folder_outside_the_repository(tmp_path: Path) -> None:
    code, _, _, raw = run_meter(tmp_path)
    assert code == 0
    lines = (raw / "plain-messages.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 + 10 and lines[0].startswith("step,agent,model,speed,message_id")
    assert any("msg-s1" in line for line in lines)  # the raw table keeps ids and file names
    assert len((raw / "plain-human-turns.csv").read_text(encoding="utf-8").splitlines()) == 1 + 9
    assert "src/app.py" in (raw / "plain-writes.csv").read_text(encoding="utf-8")


def test_raw_out_inside_the_repository_is_refused(tmp_path: Path) -> None:
    inside = ROOT / "tests" / "fixtures" / "transcripts" / "raw-must-not-exist"
    code, result, out, _ = run_meter(tmp_path, raw=inside)
    assert code == 2 and result is None and not out.exists() and not inside.exists()
    assert tm.check_raw_out(tmp_path / "ok") == (tmp_path / "ok").resolve()  # the legal case passes
    with pytest.raises(tm.MeterError):
        tm.check_raw_out(ROOT / "bench" / ".." / "tools" / "x")  # a `..` segment cannot hide the repository


# ----------------------------------------------------------------------------------------------- exit 2

def bad_effort(tmp_path: Path, text: str) -> dict[str, Any]:
    fx = copy_fixture(tmp_path)
    (fx / "effort-log.csv").write_text(text, encoding="utf-8")
    return {"fx": fx}


EFFORT_HEADER = "ts_start,ts_end,arm,step,action,text_id,count,minutes,note\n"


@pytest.mark.parametrize("case", [
    "missing_transcripts", "no_jsonl", "bad_json_line", "json_line_not_an_object",
    "missing_prices", "prices_not_json", "prices_no_date", "prices_negative", "prices_no_models",
    "missing_effort_log", "effort_columns", "effort_unknown_action", "effort_bad_time", "effort_bad_count",
    "effort_no_step_for_arm", "effort_end_without_start",
    "texts_missing", "texts_bad_type", "texts_duplicate", "texts_not_json",
    "cost_state_missing", "cost_state_no_map", "bad_arm",
])
def test_unreadable_or_bad_input_exits_2_and_writes_nothing(tmp_path: Path, case: str) -> None:
    fx = copy_fixture(tmp_path)
    over: dict[str, Any] = {}
    effort = {
        "effort_columns": "ts_start,arm,step\n2026-01-01T09:00:00Z,plain,1\n",
        "effort_unknown_action": EFFORT_HEADER + "2026-01-01T09:00:00Z,,plain,1,dance,,,,\n",
        "effort_bad_time": EFFORT_HEADER + "yesterday,,plain,1,paste_step,S1,,,\n",
        "effort_bad_count": EFFORT_HEADER + "2026-01-01T09:00:00Z,,plain,1,paste_step,S1,two,,\n",
        "effort_no_step_for_arm": EFFORT_HEADER + "2026-01-01T09:00:00Z,,kit,1,paste_step,S1,,,\n",
        "effort_end_without_start": EFFORT_HEADER + "2026-01-01T09:00:00Z,,plain,1,paste_step,S1,,,\n"
                                    "2026-01-01T09:10:00Z,,plain,2,end_step,,,3,\n",
    }
    if case in effort:
        (fx / "effort-log.csv").write_text(effort[case], encoding="utf-8")
    elif case == "missing_transcripts":
        over["transcripts"] = fx / "nowhere"
    elif case == "no_jsonl":
        empty = tmp_path / "empty"
        empty.mkdir()
        over["transcripts"] = empty
    elif case == "bad_json_line":
        with (fx / "arm" / "projects" / "proj" / "s2.jsonl").open("a", encoding="utf-8") as handle:
            handle.write("{not json\n")
    elif case == "json_line_not_an_object":
        with (fx / "arm" / "projects" / "proj" / "s2.jsonl").open("a", encoding="utf-8") as handle:
            handle.write("[1, 2]\n")
    elif case == "missing_prices":
        over["prices"] = tmp_path / "no-prices.json"
    elif case in ("prices_not_json", "prices_no_date", "prices_negative", "prices_no_models"):
        data = json.loads((fx / "prices-test.json").read_text(encoding="utf-8"))
        if case == "prices_no_date":
            del data["read_on"]
        elif case == "prices_negative":
            data["models"][SONNET]["output"] = -1
        elif case == "prices_no_models":
            data["models"] = {}
        bad = tmp_path / "bad-prices.json"
        bad.write_text("not json" if case == "prices_not_json" else json.dumps(data), encoding="utf-8")
        over["prices"] = bad
    elif case == "missing_effort_log":
        over["effort_log"] = tmp_path / "no-log.csv"
    elif case == "texts_missing":
        over["texts"] = tmp_path / "no-texts.json"
    elif case in ("texts_bad_type", "texts_duplicate", "texts_not_json"):
        bad = tmp_path / "bad-texts.json"
        content = {
            "texts_bad_type": json.dumps({"S1": {"type": "chat", "text": "x"}}),
            "texts_duplicate": json.dumps({"S1": {"type": "step", "text": "go on"}, "S2": {"type": "step", "text": "go  on"}}),
            "texts_not_json": "{",
        }[case]
        bad.write_text(content, encoding="utf-8")
        over["texts"] = bad
    elif case == "cost_state_missing":
        over["cost_state"] = tmp_path / "no-state.json"
    elif case == "cost_state_no_map":
        bad = tmp_path / "state.json"
        bad.write_text(json.dumps({"totalCostUSD": 1.5}), encoding="utf-8")
        over["cost_state"] = bad
    elif case == "bad_arm":
        over["arm"] = "../x"
    code, result, out, raw = run_meter(tmp_path, fx, **over)
    assert code == 2
    assert result is None and not out.exists() and not raw.exists()


def test_the_legal_inputs_of_the_same_cases_pass(tmp_path: Path) -> None:
    code, result, out, raw = run_meter(tmp_path, cost_state=FIX / "cost-state.json")
    assert code == 0 and result is not None and out.exists() and raw.is_dir()


def test_an_effort_log_with_a_bom_and_extra_blank_lines_is_read(tmp_path: Path) -> None:
    fx = copy_fixture(tmp_path)
    text = (fx / "effort-log.csv").read_text(encoding="utf-8")
    (fx / "effort-log.csv").write_bytes(b"\xef\xbb\xbf" + (text + "\n\n").encode("utf-8"))
    code, result, _, _ = run_meter(tmp_path, fx)
    assert code == 0 and result is not None and result["steps"]["1"]["wall_minutes"] == 9.0


# ----------------------------------------------------------------------------------------------- fixture run

_CACHE: dict[str, Any] = {}


def run_fixture() -> dict[str, Any]:
    """The meter on the committed fixture, once per test session (read-only use)."""
    if "result" not in _CACHE:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            code, result, _, _ = run_meter(Path(tmp))
        assert code == 0 and result is not None
        _CACHE["result"] = result
    return json.loads(json.dumps(_CACHE["result"]))
