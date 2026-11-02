from __future__ import annotations

from datetime import date

from tools.metrics.metrics_text import compute
from tools.metrics.profile import load_profile
from tools.metrics.records import assign_periods, period_of, strip_parentheses

from conftest import ROOT, fixture_text

KIT_PROFILE = ROOT / "tools" / "metrics" / "profiles" / "kit.json"


def run(profile, changelog: str | None = None, log: str | None = None):
    texts = {"changelog": changelog, "log": log}
    return compute(profile, texts)


def log_with(lines: list[str], day: str = "2026-11-02") -> str:
    return "\n".join(["# Log", "", f"## {day} (1) - task", *lines, ""])


# --- M1, M2 against a fixture with a known answer -------------------------

def test_m1_known_answer(test_profile) -> None:
    metrics, warnings = run(test_profile, changelog=fixture_text("changelog-test.md"))
    assert metrics["M1"] == {
        "status": "ok",
        "v1": {"n": 3, "count": 0, "items": 1},
        "v2": {"n": 4, "count": 1, "items": 1},
        "undated": {"n": 2, "count": 1, "items": 0},
    }
    assert warnings["m1_undated_heading"] == 2


def test_m2_known_answer(test_profile) -> None:
    metrics, warnings = run(test_profile, changelog=fixture_text("changelog-test.md"))
    assert metrics["M2"] == {
        "status": "ok",
        "v1": {"n": 3, "count": 1, "no_change": 0},
        "v2": {"n": 4, "count": 2, "no_change": 2},
        "undated": {"n": 2, "count": 1, "no_change": 0},
    }
    assert warnings["m2_undated_heading"] == 2


def test_revert_word_in_scope_or_outside_a_version_section_never_counts(test_profile) -> None:
    dash = chr(0x2014)
    text = (
        "# Changelog\n"
        f"## 1.0.0 {dash} 2026-11-01 (a reverted feature) {dash} to be tested\n"
        "1. Plain item mentioning reverted.\n"
        "## Notes\n"
        "1. ~~Struck~~: reverted.\n"
    )
    metrics, _ = run(test_profile, changelog=text)
    assert metrics["M1"]["v2"] == {"n": 1, "count": 0, "items": 0}


def test_version_heading_with_unparseable_date_is_undated(test_profile) -> None:
    dash = chr(0x2014)
    text = f"## 1.0.0 {dash} 2026-13-45 (bad month) {dash} to be tested\n"
    metrics, warnings = run(test_profile, changelog=text)
    assert metrics["M2"]["undated"] == {"n": 1, "count": 1, "no_change": 0}
    assert warnings["m2_undated_heading"] == 1


# --- M5, M6 against a fixture with a known answer --------------------------

def test_m5_known_answer(test_profile) -> None:
    metrics, warnings = run(test_profile, log=fixture_text("log-test.md"))
    assert metrics["M5"] == {
        "status": "ok",
        "v1": {"n": 4, "distribution": {"0": 1, "1": 0, "2": 1, "3+": 2}},
        "v2": {"n": 1, "distribution": {"0": 0, "1": 1, "2": 0, "3+": 0}},
        "undated": {"n": 1, "distribution": {"0": 0, "1": 1, "2": 0, "3+": 0}},
    }
    assert {k: v for k, v in warnings.items() if k.startswith("m5_")} == {
        "m5_session_line": 1,
        "m5_line_without_number": 1,
        "m5_undated_line": 1,
    }


def test_m6_known_answer(test_profile) -> None:
    metrics, warnings = run(test_profile, log=fixture_text("log-test.md"))
    assert metrics["M6"] == {
        "status": "ok",
        "v1": {"questions_back": {"n": 3, "count": 2}, "out_of_scope": {"n": 3, "count": 2}},
        "v2": {"questions_back": {"n": 1, "count": 0}, "out_of_scope": {"n": 1, "count": 0}},
        "undated": {"questions_back": {"n": 1, "count": 1}, "out_of_scope": {"n": 1, "count": 1}},
    }
    assert {k: v for k, v in warnings.items() if k.startswith("m6_")} == {
        "m6_session_line": 1,
        "m6_line_without_number": 1,
        "m6_missing_out_of_scope": 1,
        "m6_missing_questions_back": 1,
        "m6_undated_line": 1,
    }


# --- one test per metric-line phrasing -------------------------------------

def one_line(profile, line: str):
    metrics, warnings = run(profile, log=log_with([line]))
    return metrics, warnings


def test_phrasing_all_three_fields_with_final_period(test_profile) -> None:
    metrics, warnings = one_line(
        test_profile, "- measures: review rounds 1, questions back 0, out-of-scope files 0."
    )
    assert metrics["M5"]["v2"]["distribution"]["1"] == 1
    assert metrics["M6"]["v2"] == {
        "questions_back": {"n": 1, "count": 0},
        "out_of_scope": {"n": 1, "count": 0},
    }
    assert not warnings


def test_phrasing_parenthesis_after_the_number(test_profile) -> None:
    metrics, warnings = one_line(
        test_profile, "- measures: review rounds 1 (2 fixes), questions back 2 (a, b), out-of-scope files 0."
    )
    assert metrics["M5"]["v2"] == {"n": 1, "distribution": {"0": 0, "1": 1, "2": 0, "3+": 0}}
    assert metrics["M6"]["v2"]["questions_back"] == {"n": 1, "count": 1}
    assert not warnings


def test_phrasing_extra_word_inside_the_field_label(test_profile) -> None:
    metrics, warnings = one_line(
        test_profile, "- measures: review rounds 0, questions back 0, out-of-scope small files 1 (x)."
    )
    assert metrics["M6"]["v2"]["out_of_scope"] == {"n": 1, "count": 1}
    assert not warnings


def test_phrasing_missing_field_is_reported_not_guessed(test_profile) -> None:
    metrics, warnings = one_line(test_profile, "- measures: review rounds 2, questions back 1.")
    assert metrics["M6"]["v2"]["out_of_scope"] == {"n": 0}
    assert metrics["M6"]["v2"]["questions_back"] == {"n": 1, "count": 1}
    assert dict(warnings) == {"m6_missing_out_of_scope": 1}


def test_phrasing_session_line_with_several_versions_is_not_counted(test_profile) -> None:
    metrics, warnings = one_line(
        test_profile,
        "- session measures: 2 versions (2.2.0, 2.3.0), 2 developer tasks, review rounds 1/0.",
    )
    assert metrics["M5"] == {"status": "no data"}
    assert metrics["M6"] == {"status": "no data"}
    assert dict(warnings) == {"m5_session_line": 1, "m6_session_line": 1}


def test_phrasing_other_label_family_is_excluded(test_profile) -> None:
    metrics, warnings = one_line(test_profile, "- measurements: review rounds 9, questions back 9.")
    assert metrics["M5"] == {"status": "no data"}
    assert not warnings


def test_phrasing_line_without_a_number(test_profile) -> None:
    metrics, warnings = one_line(
        test_profile, "- measures: review rounds none, questions back many."
    )
    assert metrics["M5"] == {"status": "no data"}
    assert dict(warnings) == {"m5_line_without_number": 1, "m6_line_without_number": 1}


def test_phrasing_rounds_in_free_text_is_not_parsed(test_profile) -> None:
    metrics, _ = one_line(test_profile, "Review: review rounds 5 were needed for this task.")
    assert metrics["M5"] == {"status": "no data"}


def test_phrasing_markers_match_in_any_case(test_profile) -> None:
    metrics, _ = one_line(test_profile, "- MEASURES: Review Rounds 3, QUESTIONS BACK 1, Out-Of-Scope Files 0.")
    assert metrics["M5"]["v2"]["distribution"]["3+"] == 1


def test_kit_phrasing_with_models_and_commas_inside_parentheses() -> None:
    profile = load_profile(KIT_PROFILE)
    line = (
        '- Metrics (T-15): review rounds 2, questions back 3 (more "user" rows, "proposes" in '
        "Appendix C, length of the core sentence), out-of-scope files 0, models Sonnet "
        "(tech-writer), Haiku (scribe)."
    )
    metrics, warnings = run(profile, log=log_with([line]))
    assert metrics["M5"]["v2"]["distribution"]["2"] == 1
    assert metrics["M6"]["v2"] == {
        "questions_back": {"n": 1, "count": 1},
        "out_of_scope": {"n": 1, "count": 0},
    }
    assert not warnings


def test_kit_phrasing_with_a_customer_result_field_after_the_models() -> None:
    profile = load_profile(KIT_PROFILE)
    line = "- Metrics (T-20): review rounds 0, questions back 0, out-of-scope files 0, models Sonnet (developer), customer result accepted."
    metrics, _ = run(profile, log=log_with([line]))
    assert metrics["M5"]["v2"]["distribution"]["0"] == 1


# --- no data ---------------------------------------------------------------

def test_empty_profile_entries_show_no_data_for_all_four() -> None:
    from tools.metrics.profile import parse_profile

    empty = parse_profile(
        b'{"schema": 1, "files": {"changelog": "C.md", "log": "L.md"},'
        b' "metrics": {"M1": {}, "M2": {}, "M5": {}, "M6": {}}}'
    )
    metrics, warnings = run(empty, changelog="## 1.0.0\n", log=log_with(["- measures: review rounds 1."]))
    assert metrics == {m: {"status": "no data"} for m in ("M1", "M2", "M5", "M6")}
    assert not warnings


def test_missing_file_shows_no_data_not_zero(test_profile) -> None:
    metrics, _ = run(test_profile, changelog=None, log=None)
    assert all(metrics[m] == {"status": "no data"} for m in metrics)


def test_file_without_records_shows_no_data_not_zero(test_profile) -> None:
    metrics, _ = run(test_profile, changelog="# Changelog\n\nNothing yet.\n", log="# Log\n")
    assert all(metrics[m] == {"status": "no data"} for m in metrics)


def test_period_with_no_items_has_n_zero_and_no_rate(test_profile) -> None:
    dash = chr(0x2014)
    text = f"## 1.0.0 {dash} 2026-11-01 (a) {dash} to be tested\n"
    metrics, _ = run(test_profile, changelog=text)
    assert metrics["M2"]["v1"] == {"n": 0}
    assert metrics["M2"]["undated"] == {"n": 0}


# --- periods ---------------------------------------------------------------

def test_cutoff_day_is_v2_and_the_day_before_is_v1() -> None:
    assert period_of(date(2026, 10, 24)) == "v1"
    assert period_of(date(2026, 10, 25)) == "v2"


def test_undated_takes_the_period_of_agreeing_neighbours_only() -> None:
    v1, v2 = date(2026, 1, 1), date(2026, 12, 1)
    assert assign_periods([v1, None, v1]) == ["v1", "v1", "v1"]
    assert assign_periods([v2, None, None, v2]) == ["v2", "v2", "v2", "v2"]
    assert assign_periods([v2, None, v1]) == ["v2", "undated", "v1"]
    assert assign_periods([None, v1]) == ["undated", "v1"]
    assert assign_periods([v1, None]) == ["v1", "undated"]
    assert assign_periods([None]) == ["undated"]


def test_strip_parentheses_handles_nesting() -> None:
    assert strip_parentheses("a 1 (x (y, z), w), b 2") == "a 1 , b 2"
