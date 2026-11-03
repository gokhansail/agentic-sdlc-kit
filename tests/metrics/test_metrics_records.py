"""M8, M9 and M13 against invented records with known answers, one test per layout."""
from __future__ import annotations

import json

import pytest

from tools.metrics.metrics_records import compute
from tools.metrics.profile import ProfileError, load_profile, parse_profile

from conftest import EM_DASH, FIXTURES, ROOT

KIT_PROFILE = ROOT / "tools" / "metrics" / "profiles" / "kit.json"
RAW = json.loads((FIXTURES / "profile-records.json").read_text(encoding="ascii"))


def profile_with(**metric_changes):
    data = json.loads(json.dumps(RAW))
    for mid, change in metric_changes.items():
        data["metrics"][mid] = change
    return parse_profile(json.dumps(data).encode("ascii"))


def em(text: str) -> str:
    return text.replace("{EM}", EM_DASH)


def m8(reports: dict[str, str], profile=None):
    profile = profile or load_profile(FIXTURES / "profile-records.json")
    results, warnings = compute(profile, {}, {"audits": {k: em(v) for k, v in reports.items()}})
    return results["M8"], warnings


# --- M8: finding heading with severity in the heading ----------------------

HEADING_REPORT = """# Audit
### P-1 {EM} High {EM} first
### P-2 {EM} low {EM} second
### P-3 {EM} MEDIUM {EM} third
### P-4 {EM} Low {EM} fourth
### P-5 {EM} critical {EM} fifth
## Not a finding
### 5.1 numbered section
"""
REVERIFY_TABLE = """| Finding | Claim | Evidence | Status |
|---|---|---|---|
{rows}
"""


def table(*rows: str) -> str:
    return REVERIFY_TABLE.format(rows="\n".join(rows))


def test_m8_heading_layout_and_reverify_table_known_answer() -> None:
    reports = {
        "2026-10-20_audit.md": HEADING_REPORT,
        "2026-10-20_reverify.md": table("| P-1 | saved | test | CLOSED (by test) |"),  # 0 days
        "2026-10-22_reverify.md": table(
            "| P-2 | typo | none | partial (doc-only) |",
            "| P-3 | x | y | OPEN |",
            "| P-4 | x | y | closed |",  # 2 days
        ),
        "2026-10-27_reverify.md": table(
            "| p-3 | x | y | Closed by test substitute |",  # 7 days, status = first word
            "| P-2 | typo | none | CLOSED |",  # latest status of P-2; 7 days
        ),
        "2026-10-28_reverify.md": table("| P-5 | x | y | DEFERRED |"),
    }
    result, warnings = m8(reports)
    assert result["v1"] == {
        "n": 5,
        "severity": {"critical": 1, "high": 1, "medium": 1, "low": 2, "unrated": 0},
        "latest": {"closed": 4, "partial": 0, "open": 0, "deferred": 1, "none": 0},
        "days_to_closed": {"0": 1, "1-3": 1, "4-7": 2, "8+": 0},
    }
    assert result["v2"] == {"n": 0} and result["status"] == "ok"
    assert not warnings


def test_m8_days_to_closed_8_or_more_and_never_reverified() -> None:
    reports = {
        "2026-10-20_audit.md": HEADING_REPORT,
        "2026-10-28_reverify.md": table("| P-1 | x | y | OPEN |", "| P-1 | x | y | CLOSED |"),
        "2026-10-29_reverify.md": table("| P-1 | x | y | OPEN |"),  # latest status wins, closed day stays
    }
    result, _ = m8(reports)
    assert result["v1"]["days_to_closed"] == {"0": 0, "1-3": 0, "4-7": 0, "8+": 1}
    assert result["v1"]["latest"] == {"closed": 0, "partial": 0, "open": 1, "deferred": 0, "none": 4}


def test_m8_period_is_set_by_report_date_and_ids_restart_per_report() -> None:
    reports = {
        "2026-10-20_audit.md": f"### P-1 {EM_DASH} high {EM_DASH} old\n",
        "2026-10-30_audit.md": f"### P-1 {EM_DASH} low {EM_DASH} new, same ID\n",
        "2026-10-25_reverify.md": table("| P-1 | x | y | CLOSED |"),  # links to the 10-20 report
        "2026-11-02_reverify.md": table("| P-1 | x | y | OPEN |"),  # links to the 10-30 report
    }
    result, warnings = m8(reports)
    assert result["v1"]["n"] == 1 and result["v1"]["latest"]["closed"] == 1
    assert result["v1"]["days_to_closed"]["4-7"] == 1
    assert result["v2"]["n"] == 1 and result["v2"]["latest"]["open"] == 1
    assert result["v2"]["severity"]["low"] == 1
    assert not warnings


def test_m8_same_id_twice_on_one_date_counts_once_with_a_warning() -> None:
    reports = {
        "2026-10-20_a.md": f"### P-1 {EM_DASH} high {EM_DASH} one\n",
        "2026-10-20_b.md": f"### P-1 {EM_DASH} low {EM_DASH} two\n",
    }
    result, warnings = m8(reports)
    assert result["v1"]["n"] == 1 and warnings["m8_duplicate_finding"] == 1


def test_m8_rows_that_cannot_be_used_are_reported_not_guessed() -> None:
    reports = {
        "2026-10-20_audit.md": f"### P-1 {EM_DASH} high {EM_DASH} one\n",
        "2026-10-21_reverify.md": table("| X-9 | no such finding | y | CLOSED |", "| P-1 | z | y | yes |"),
        "2026-10-19_reverify.md": table("| P-1 | before the report | y | CLOSED |"),
    }
    result, warnings = m8(reports)
    assert result["v1"]["latest"]["none"] == 1  # the row dated before the report is not linked
    assert warnings["m8_unlinked_row"] == 2  # X-9 and the early P-1 row; "yes" is not a status row


def test_m8_file_without_a_date_is_reported() -> None:
    result, warnings = m8({"notes.md": f"### P-1 {EM_DASH} high {EM_DASH} one\n"})
    assert result == {"status": "no data"} and warnings["m8_file_without_date"] == 1


def test_m8_unrated_finding_is_counted_and_reported() -> None:
    reports = {"2026-10-20_audit.md": f"### P-1 {EM_DASH} odd {EM_DASH} one\n"}
    result, warnings = m8(reports)
    assert result["v1"]["severity"]["unrated"] == 1 and warnings["m8_unrated_finding"] == 1


def test_m8_without_a_folder_or_files_is_no_data() -> None:
    profile = load_profile(FIXTURES / "profile-test.json")
    assert compute(profile, {}, {})[0]["M8"] == {"status": "no data"}
    result, _ = m8({})
    assert result == {"status": "no data"}


# --- M8: severity on its own line (the kit layout) ---------------------------

def severity_line_profile():
    return profile_with(
        M8={
            "folder": "audits",
            "finding_heading": r"^###\s+(?P<id>[a-z]+-\d+)\b",
            "severity_line": r"^\s*-\s+severity:\s*(?P<severity>[a-z]+)",
            "table_row": RAW["metrics"]["M8"]["table_row"],
        }
    )


def test_m8_severity_line_layout() -> None:
    report = "\n".join(
        [
            "### P-1 First finding",
            "- Severity: High",
            "- Evidence: text",
            "### P-2 Second finding",
            "- Evidence: no severity line before the next heading",
            "### P-3 Third finding",
            "- Severity: Low",
            "- Severity: High",  # only the first severity line counts
            "",
        ]
    )
    result, warnings = m8({"2026-11-02_gate.md": report}, severity_line_profile())
    assert result["v2"]["severity"] == {"critical": 0, "high": 1, "medium": 0, "low": 1, "unrated": 1}
    assert warnings["m8_unrated_finding"] == 1


def test_m8_severity_line_does_not_leak_into_the_next_finding() -> None:
    report = "### P-1 First\n### P-2 Second\n- Severity: Medium\n"
    result, _ = m8({"2026-11-02_gate.md": report}, severity_line_profile())
    assert result["v2"]["severity"]["medium"] == 1 and result["v2"]["severity"]["unrated"] == 1


def test_m8_kit_profile_reads_the_kit_layout() -> None:
    profile = load_profile(KIT_PROFILE)
    reports = {
        "2026-11-02_gate.md": "### P-1 Title\n- Severity: High\n",
        "2026-11-03_reverify.md": "| Finding | Claim | Evidence | Status |\n|---|---|---|---|\n| P-1 | c | e | CLOSED |\n",
    }
    results, _ = compute(profile, {}, {"audits": reports})
    assert results["M8"]["v2"]["severity"]["high"] == 1
    assert results["M8"]["v2"]["days_to_closed"]["1-3"] == 1


# --- M9: decision entries and outcome layouts ---------------------------------

DECISIONS = """# Decisions
**Outcome:** described once in the intro, not an entry.

**D-1 Crates stack** {EM} 2026-10-01 {EM} in force
- Outcome: {EM}
**D-2 Lamp** {EM} 2026-10-26 {EM} to try
- **Outcome:** turned out right, players noticed.
**D-3 Menu** {EM} 2026-10-27 {EM} in force
Outcome (2026-10-30 check): kept.
**D-4 No outcome field** {EM} 2026-10-28 {EM} in force
- Why: nothing else
**D-5 Undated** {EM} in force
- Outcome: filled but undated
**D-6 Blank outcome** {EM} 2026-10-01 {EM} in force
- Outcome:
"""


def m9(text: str, profile=None):
    profile = profile or load_profile(FIXTURES / "profile-records.json")
    results, warnings = compute(profile, {"decisions": em(text)}, {})
    return results["M9"], warnings


def test_m9_known_answer_over_the_three_outcome_layouts() -> None:
    result, warnings = m9(DECISIONS)
    assert result == {
        "status": "ok",
        "v1": {"n": 2, "count": 0},  # a dash alone and a blank value are not filled
        "v2": {"n": 2, "count": 2},  # bold label, and a label with a parenthesis
        "undated": {"n": 1, "count": 1},
    }
    assert warnings["m9_entry_without_outcome"] == 1 and warnings["m9_undated_entry"] == 1


def test_m9_text_before_the_first_entry_is_skipped() -> None:
    result, _ = m9("**Outcome:** intro line\n")
    assert result == {"status": "no data"}


def test_m9_kit_layout_takes_the_date_from_its_own_line() -> None:
    text = "\n".join(
        [
            "# Decisions",
            "Entry format: date, question, outcome.",
            "## DEC-001 Name",
            "- Date: 2026-10-20 - Question: D-1",
            "- Outcome:",
            "## DEC-002 Other",
            "- Date: 2026-11-02 - Question: D-2",
            "- Outcome: 2026-11-03, judged against the result.",
            "## DEC-003 Third",
            "- Date: 2026-11-03",
            "- Outcome: text",
            "",
        ]
    )
    results, warnings = compute(load_profile(KIT_PROFILE), {"decisions": text}, {})
    assert results["M9"] == {
        "status": "ok",
        "v1": {"n": 1, "count": 0},
        "v2": {"n": 2, "count": 2},
        "undated": {"n": 0},
    }
    assert not warnings


def test_m9_another_heading_ends_the_entry() -> None:
    text = "## DEC-001 A\n- Date: 2026-11-02\n## Notes\n- Outcome: belongs to no entry\n"
    results, warnings = compute(load_profile(KIT_PROFILE), {"decisions": text}, {})
    assert results["M9"] == {"status": "no data"} and warnings["m9_entry_without_outcome"] == 1


def test_m9_missing_file_or_entry_is_no_data() -> None:
    profile = load_profile(FIXTURES / "profile-records.json")
    assert compute(profile, {"decisions": None}, {})[0]["M9"] == {"status": "no data"}
    assert compute(load_profile(FIXTURES / "profile-test.json"), {}, {})[0]["M9"] == {"status": "no data"}


# --- M13: tasks by size tag, two tag sets -----------------------------------

TASKS_SML = """# Tasks
### [x] T-1 [S] Small done {EM} v1 {EM} Once: none (2026-10-01, ab12cd3)
### [x] T-2 [L] Large done {EM} v2 (2026-10-27, ab12cd3)
### [ ] T-3 [M] Medium open {EM} v3
### [x] T-4 Untagged done (2026-10-28, ab12cd3)
### [x] T-5 [Q] Unknown tag (2026-10-28, ab12cd3)
- [ ] T-6 [L] a bullet copy, not a heading
### [~] T-7 [S] partial
"""


def m13(text: str, profile=None):
    profile = profile or load_profile(FIXTURES / "profile-records.json")
    results, warnings = compute(profile, {"tasks": em(text)}, {})
    return results["M13"], warnings


def test_m13_small_medium_large_tags_known_answer() -> None:
    result, warnings = m13(TASKS_SML)
    assert result == {
        "status": "ok",
        "v1": {"n": 1, "distribution": {"E": 1, "M": 0, "H": 0}, "done": 1},
        "v2": {"n": 1, "distribution": {"E": 0, "M": 0, "H": 1}, "done": 1},
        "undated": {"n": 2, "distribution": {"E": 1, "M": 1, "H": 0}, "done": 0},
    }
    assert warnings["m13_untagged_heading"] == 1 and warnings["m13_unknown_tag"] == 1


def test_m13_kit_tag_set_takes_the_done_date_from_the_result_line() -> None:
    text = "\n".join(
        [
            "## Phase",
            "### [x] T-1 [E] First",
            "- Result: done 2026-11-01.",
            "### [x] T-2 [H] Second",
            "- Goal: no date here",
            "### [x] T-3 Gate",
            "- Result: 2026-11-02",
            "### [ ] T-4 [M] Open",
            "- Result: not a done date, task is open 2026-11-03",
            "",
        ]
    )
    results, warnings = compute(load_profile(KIT_PROFILE), {"tasks": text}, {})
    assert results["M13"] == {
        "status": "ok",
        "v1": {"n": 0},
        "v2": {"n": 1, "distribution": {"E": 1, "M": 0, "H": 0}, "done": 1},
        "undated": {"n": 2, "distribution": {"E": 0, "M": 1, "H": 1}, "done": 1},
    }
    assert warnings["m13_untagged_heading"] == 1


def test_m13_a_tag_set_must_not_share_letters() -> None:
    data = json.loads(json.dumps(RAW))
    data["metrics"]["M13"]["tags"] = {"E": "s", "M": "s"}
    with pytest.raises(ProfileError):
        parse_profile(json.dumps(data).encode("ascii"))


def test_m13_no_headings_is_no_data() -> None:
    assert m13("# nothing here\n")[0] == {"status": "no data"}
