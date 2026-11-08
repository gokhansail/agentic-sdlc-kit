"""Tests for the DEC-012 eval set: questions, answer keys, scorer, synthetic repository.

The key file (eval/questions.jsonl) is the source. These tests check that it is well formed,
that the scope keys equal what tools.scope_guard decides on eval/repo/, that number and
token keys follow from the records, that the scorer behaves, and that the frozen hash holds.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import scope_guard as sg  # noqa: E402

EVAL = ROOT / "eval"
REPO = EVAL / "repo"
QUESTIONS = EVAL / "questions.jsonl"

_spec = importlib.util.spec_from_file_location("eval_score", EVAL / "score.py")
assert _spec and _spec.loader
score_mod = importlib.util.module_from_spec(_spec)
sys.modules["eval_score"] = score_mod
_spec.loader.exec_module(score_mod)

CATEGORIES = {"scope": 8, "decisions": 6, "findings": 6, "tasks": 5, "guard": 3, "lessons": 2}
FIELDS = {"id", "category", "question", "answer_type", "key", "sources"}


def questions() -> list[dict]:
    return score_mod.load_questions(QUESTIONS)


def read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def answers_from_key(qs: list[dict]) -> dict:
    return {q["id"]: q["key"] for q in qs}


def write_answers(path: Path, answers: dict) -> Path:
    path.write_text("".join(json.dumps({"id": k, "answer": v}) + "\n" for k, v in answers.items()), encoding="utf-8")
    return path


# --- the question set -----------------------------------------------------------

def test_thirty_questions_with_the_fixed_fields():
    qs = questions()
    assert len(qs) == 30
    assert [q["id"] for q in qs] == [f"Q{i:02d}" for i in range(1, 31)]
    for q in qs:
        assert FIELDS <= set(q), q["id"]
        assert q["answer_type"] in score_mod.ANSWER_TYPES
        assert q["question"].strip() and q["sources"]


def test_category_counts():
    counts: dict[str, int] = {}
    for q in questions():
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    assert counts == CATEGORIES


def test_at_least_eight_questions_need_two_files():
    assert sum(1 for q in questions() if len(q["sources"]) >= 2) >= 8


def test_every_source_file_exists_in_the_eval_repository():
    for q in questions():
        for source in q["sources"]:
            assert (REPO / source).is_file(), (q["id"], source)


def test_key_types_match_answer_types():
    for q in questions():
        key = q["key"]
        kind = q["answer_type"]
        if kind == "yes-no":
            assert key in ("yes", "no")
        elif kind == "number":
            assert isinstance(key, int) and not isinstance(key, bool)
        elif kind == "set":
            assert isinstance(key, list) and len(key) >= 2
        else:
            assert isinstance(key, str) and key


def test_questions_do_not_name_the_kit_or_a_server():
    for q in questions():
        assert not re.search(r"\b(mcp|server|tool call|agentic-sdlc-kit)\b", q["question"], re.I), q["id"]


# --- scope keys follow from the guard --------------------------------------------

def scope_questions() -> list[dict]:
    return [q for q in questions() if q["category"] == "scope"]


@pytest.mark.parametrize("q", scope_questions(), ids=lambda q: q["id"])
def test_scope_key_equals_the_guard_decision(q):
    check = q["check"]
    assert check["actor"] in ("main", "sub-agent")
    decision = sg.check(REPO, check["path"], check["actor"] == "sub-agent", casefold=False)
    assert decision is not None, "eval/repo must be opted in"
    assert ("yes" if decision.allow else "no") == q["key"]


def test_scope_questions_cover_both_outcomes_and_the_tricky_cases():
    qs = scope_questions()
    assert {q["key"] for q in qs} == {"yes", "no"}
    paths = {q["check"]["path"] for q in qs}
    assert "DEV_RULES.md" in paths                       # rules file, no exact path in Files in
    assert any(".." in p for p in paths)                  # outside the root
    assert any(p == "src/billing/invoice_pdf.py" for p in paths)  # Files in glob and Files out
    assert any(p == "src/api/schemas/invoices.py" for p in paths)  # brace expansion


# --- the synthetic repository ----------------------------------------------------

def test_repository_is_opted_in_with_a_parsable_contract():
    assert (REPO / ".sdlc" / "project.md").is_file()
    state, contract, always, broken = sg.load_state(REPO)
    assert state == sg.ACTIVE and not broken
    assert contract.task_id == "T-7"
    assert "src/api/routes/invoices.py" in contract.files_in and "src/api/schemas/invoices.py" in contract.files_in
    assert sg.matches("src/billing/invoice_pdf.py", contract.files_in, False)
    assert sg.matches("src/billing/invoice_pdf.py", contract.files_out, False)
    assert sg.load_developer_rules(REPO) == "DEV_RULES.md"
    assert "DEV_RULES.md" not in contract.files_in_raw
    assert "audits/**" in always or "audits/" in always


def test_eval_files_are_not_git_ignored():
    done = subprocess.run(
        ["git", "check-ignore", "-v", "eval/repo/.sdlc/metrics.jsonl", "eval/repo/.sdlc/active-contract.md"],
        cwd=ROOT, capture_output=True, text=True)
    if done.returncode == 128:
        pytest.skip("not a git work tree")
    assert done.returncode == 1, done.stdout


def test_decision_records_follow_the_template():
    sections = re.split(r"^## ", read("DECISIONS.md"), flags=re.M)[1:]
    assert len(sections) == 9
    for section in sections:
        assert re.match(r"DEC-\d{3} \S", section)
        labels = re.findall(r"^- ([A-Za-z ]+):", section, flags=re.M)
        assert labels == ["Date", "Raised in", "Options", "Decision", "Reason", "Consequences", "Outcome"]


def test_lesson_entries_follow_the_template():
    sections = re.split(r"^## ", read("LESSONS.md"), flags=re.M)[1:]
    assert len(sections) == 4
    for section in sections:
        labels = re.findall(r"^- ([A-Za-z ]+):", section, flags=re.M)
        assert labels == ["Date", "Project", "Problem", "Cause", "Fix", "Lesson"]


def test_task_contracts_in_tasks_follow_the_template():
    sections = re.split(r"^## ", read("TASKS.md"), flags=re.M)
    contracts = [s for s in sections if re.match(r"T-\d+ ", s)]
    assert len(contracts) == 2
    for section in contracts:
        labels = re.findall(r"^- ([A-Za-z ]+):", section, flags=re.M)
        assert labels == ["Size", "Goal", "Files in", "Files out", "Acceptance", "Tests",
                          "Design reference", "Flag", "Customer test"]
        assert len(section.strip().splitlines()) <= 15


def test_active_contract_has_the_template_fields_and_at_most_15_lines():
    text = read(".sdlc/active-contract.md")
    assert len(text.strip().splitlines()) <= 15
    labels = re.findall(r"^- ([A-Za-z ]+):", text, flags=re.M)
    assert labels == ["Size", "Goal", "Files in", "Files out", "Acceptance", "Tests",
                      "Design reference", "Flag", "Customer test"]


def test_audit_report_and_reverify_table_follow_the_templates():
    report = read("audits/2026-10-20_gate2.md")
    assert report.startswith("# Audit report")
    assert "## Audit G2\n- Read:" in report and "## Findings" in report and "## Verdict line" in report
    for block in re.split(r"^### ", report, flags=re.M)[1:]:
        labels = re.findall(r"^- ([A-Za-z ]+):", block.split("\n## ")[0], flags=re.M)
        assert labels == ["Type", "Severity", "Claim", "Evidence"]
    table = read("audits/2026-10-24_gate2_reverify.md")
    assert table.startswith("# Re-verify table")
    assert "| Finding | Claim | Evidence | Status |" in table
    assert re.search(r"^Gate verdict: (accept|conditional|reject)$", table, flags=re.M)


def test_project_and_rules_files_follow_the_templates():
    project = read(".sdlc/project.md")
    assert "## Records" in project and "## Always allowed" in project
    rules = read("DEV_RULES.md")
    for heading in ("## Reading", "## Rules", "## Enforcement"):
        assert heading in rules
    assert len(rules.splitlines()) <= 40


def test_metrics_lines_have_the_guard_event_shape():
    lines = read(".sdlc/metrics.jsonl").splitlines()
    assert len(lines) == 24
    for line in lines:
        event = json.loads(line)
        assert set(event) == {"agent", "date", "decision", "event", "state", "task", "tool"}
        assert event["event"] == "scope" and event["decision"] in ("allow", "deny")


def test_eval_files_hold_no_absolute_path_or_address():
    pattern = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]|(?<![\w.])/(?:home|Users)/\w|[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)
    for path in EVAL.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".jsonl", ".py"):
            assert not pattern.search(path.read_text(encoding="utf-8")), path


# --- keys that follow from the records --------------------------------------------

def key_of(qid: str):
    return next(q["key"] for q in questions() if q["id"] == qid)


def decisions() -> dict[str, dict[str, str]]:
    out = {}
    for section in re.split(r"^## ", read("DECISIONS.md"), flags=re.M)[1:]:
        dec_id = section.split()[0]
        out[dec_id] = {m.group(1): m.group(2).strip() for m in re.finditer(r"^- ([A-Za-z ]+):(.*)$", section, flags=re.M)}
    return out


def audit_rows() -> dict[str, dict[str, str]]:
    severity = {}
    for block in re.split(r"^### ", read("audits/2026-10-20_gate2.md"), flags=re.M)[1:]:
        severity[block.split()[0]] = re.search(r"^- Severity: (\w+)", block, flags=re.M).group(1)
    status = {}
    for m in re.finditer(r"^\| ([A-Z]-\d+) \|.*\| (CLOSED|OPEN|PARTIAL) \|$", read("audits/2026-10-24_gate2_reverify.md"), flags=re.M):
        status[m.group(1)] = m.group(2)
    return {fid: {"severity": severity[fid], "status": status[fid]} for fid in severity}


def metrics() -> list[dict]:
    return [json.loads(line) for line in read(".sdlc/metrics.jsonl").splitlines()]


def test_decision_keys_follow_from_the_records():
    decs = decisions()
    assert re.search(r"Replaced by (DEC-\d+)", decs["DEC-004"]["Outcome"]).group(1) == key_of("Q09")
    assert decs["DEC-001"]["Outcome"].startswith("Replaced by") and key_of("Q10") == "no"
    assert sum(1 for d in decs.values() if not d["Outcome"]) == key_of("Q12")
    task = sg.parse_contract(read(".sdlc/active-contract.md")).task_id
    assert sorted(k for k, d in decs.items() if re.search(rf"\b{task}\b", d["Raised in"])) == sorted(key_of("Q13"))
    replacer = re.search(r"Replaced by (DEC-\d+)", decs["DEC-001"]["Outcome"]).group(1)
    assert decs[replacer]["Date"] == key_of("Q14")
    assert "postgres" in decs[replacer]["Decision"].lower() and key_of("Q11") == "postgres"


def test_finding_keys_follow_from_the_records():
    rows = audit_rows()
    assert len(rows) == key_of("Q18")
    assert sorted(f for f, r in rows.items() if r["status"] != "CLOSED") == sorted(key_of("Q15"))
    open_ids = [f for f, r in rows.items() if r["status"] == "OPEN"]
    assert len(open_ids) == 1 and rows[open_ids[0]]["severity"] == key_of("Q16")
    assert (rows["D-1"]["status"] == "CLOSED") == (key_of("Q17") == "yes")
    assert sum(1 for r in rows.values() if r["severity"] == "high" and r["status"] == "CLOSED") == key_of("Q20")
    verdict = re.search(r"^Gate verdict: (\w+)$", read("audits/2026-10-24_gate2_reverify.md"), flags=re.M).group(1)
    assert verdict == key_of("Q19")


def test_task_and_status_keys_follow_from_the_records():
    tasks = read("TASKS.md")
    done_tasks = set(re.findall(r"^- \[x\] (T-\d+a?) ", tasks, flags=re.M))
    open_tasks = re.findall(r"^- \[ \] (T-\d+a?) ", tasks, flags=re.M)
    status_done = set(re.findall(r"^- (T-\d+a?) ", read("STATUS.md"), flags=re.M))
    assert done_tasks - status_done == {key_of("Q21")}
    assert len(open_tasks) == key_of("Q23")
    assert re.search(r"Next after T-7: (T-\d+)", tasks).group(1) == key_of("Q22")
    contract = sg.parse_contract(read(".sdlc/active-contract.md"))
    assert contract.task_id == "T-7" and open_tasks[0] == contract.task_id
    tag = re.search(rf"^- \[ \] {contract.task_id} \[(\w)\]", tasks, flags=re.M).group(1)
    assert tag == key_of("Q24")
    assert int(re.search(r"Phase (\d) \S+ open", read("STATUS.md")).group(1)) == key_of("Q25")


def test_guard_event_keys_follow_from_the_metrics_file():
    events = metrics()
    assert sum(1 for e in events if e["task"] == "T-7" and e["decision"] == "deny") == key_of("Q26")
    deny: dict[str, int] = {}
    for e in events:
        if e["task"]:
            deny[e["task"]] = deny.get(e["task"], 0) + (e["decision"] == "deny")
    assert max(deny, key=deny.get) == key_of("Q27")
    assert sorted(deny.values())[-1] > sorted(deny.values())[-2]
    assert sum(1 for e in events if e["task"] == "T-7" and e["agent"] is None) == key_of("Q28")


def test_lesson_keys_follow_from_the_records():
    lessons = {}
    for section in re.split(r"^## ", read("LESSONS.md"), flags=re.M)[1:]:
        lessons[section.splitlines()[0]] = re.search(r"^- Date: (\S+)", section, flags=re.M).group(1)
    migration = next(d for t, d in lessons.items() if "migration" in t.lower())
    assert migration == key_of("Q29")
    when = decisions()["DEC-006"]["Date"]
    assert sum(1 for d in lessons.values() if d > when) == key_of("Q30")


# --- the scorer -------------------------------------------------------------------

def test_scorer_gives_30_of_30_on_the_key(tmp_path):
    qs = questions()
    result = score_mod.score(qs, answers_from_key(qs))
    assert (result["correct"], result["total"]) == (30, 30)
    path = write_answers(tmp_path / "answers.jsonl", answers_from_key(qs))
    buffer = io.StringIO()
    assert score_mod.main([str(path)], out=buffer) == 0
    assert buffer.getvalue().rstrip().endswith("total: 30/30")


def test_scorer_gives_zero_on_an_empty_answer_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    buffer = io.StringIO()
    assert score_mod.main([str(path)], out=buffer) == 0
    assert buffer.getvalue().rstrip().endswith("total: 0/30")


def test_scorer_cli_runs_as_a_script(tmp_path):
    path = write_answers(tmp_path / "answers.jsonl", answers_from_key(questions()))
    done = subprocess.run([sys.executable, str(EVAL / "score.py"), str(path)], capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0 and done.stdout.rstrip().endswith("total: 30/30")


def test_scorer_reports_a_missing_answers_file(tmp_path):
    assert score_mod.main([str(tmp_path / "nope.jsonl")], out=io.StringIO()) == 1


@pytest.mark.parametrize("answer_type,key,given,ok", [
    ("token", "DEC-007", "  dec-007. ", True),
    ("token", "DEC-007", "`DEC-007`", True),
    ("token", "DEC-007", "DEC-008", False),
    ("yes-no", "yes", "Yes.", True),
    ("yes-no", "yes", "TRUE", True),
    ("yes-no", "yes", True, True),
    ("yes-no", "no", "n", True),
    ("yes-no", "no", "maybe", False),
    ("number", 3, "3", True),
    ("number", 3, 3.0, True),
    ("number", 3, " 3 ", True),
    ("number", 3, "three", False),
    ("number", 3, True, False),
    ("set", ["C-1", "S-1"], ["s-1", "C-1"], True),
    ("set", ["C-1", "S-1"], "S-1, c-1", True),
    ("set", ["C-1", "S-1"], "S-1 and C-1", True),
    ("set", ["C-1", "S-1"], ["C-1"], False),
    ("set", ["C-1", "S-1"], ["C-1", "S-1", "D-1"], False),
    ("set", ["C-1", "S-1"], 5, False),
])
def test_scorer_normalisation(answer_type, key, given, ok):
    question = {"id": "X", "category": "c", "answer_type": answer_type, "key": key}
    assert score_mod.is_correct(question, given) is ok


def test_scorer_ignores_bad_lines_and_takes_the_last_repeat(tmp_path):
    qs = questions()
    path = tmp_path / "answers.jsonl"
    path.write_text('not json\n\n{"id": "Q10", "answer": "yes"}\n[1]\n{"id": "Q10", "answer": "no"}\n{"id": "Q99"}\n',
                    encoding="utf-8")
    result = score_mod.score(qs, score_mod.load_answers(path))
    assert result["correct"] == 1
    assert next(r for r in result["results"] if r["id"] == "Q10")["correct"] is True


# --- the eval repository is not collected, the hash is frozen ---------------------

def test_pytest_collects_nothing_under_eval():
    assert (EVAL / "conftest.py").is_file()
    stray = [p for p in EVAL.rglob("*.py") if p.name.startswith("test_") or p.name.endswith("_test.py")]
    assert stray == []
    done = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "eval"],
                          cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 5, done.stdout + done.stderr  # exit code 5: no tests collected


def test_readme_states_the_frozen_hash_of_the_questions():
    data = QUESTIONS.read_bytes().replace(b"\r\n", b"\n")
    digest = hashlib.sha256(data).hexdigest()
    readme = (EVAL / "README.md").read_text(encoding="utf-8")
    stated = re.findall(r"SHA-256[^\n]*?\b([0-9a-f]{64})\b", readme)
    assert stated == [digest]
