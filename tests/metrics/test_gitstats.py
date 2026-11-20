"""M3 and M12 against a repository built in a temp dir with fixed dates."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from tools.metrics import gitstats
from tools.metrics.fold import folded_lines
from tools.metrics.profile import load_profile

from conftest import EM_DASH, FIXTURES, git_commit, git_init, git_run

PROFILE = FIXTURES / "profile-records.json"
HASH = "a" * 40


def probes(n: int) -> str:
    """n test attributes, plus lines that must not count."""
    body = "".join(f"    [Probe]\n    public void T{i}() {{}}\n" for i in range(n))
    return body + "    // [Probe] in a comment\n    [ProbeCase(1)]\n"


def build_repo(path: Path) -> Path:
    repo = git_init(path)
    # c0: author day far before its committer day (out of the committer span)
    git_commit(repo, {"tests/a.cs": probes(0), "src/b.cs": probes(9)},
               "2026-01-05T10:00:00+00:00", "2026-10-12T09:00:00+00:00")
    git_commit(repo, {"tests/a.cs": probes(2)}, "2026-10-12T10:00:00+00:00")
    git_commit(repo, {"tests/a.cs": probes(3)}, "2026-10-14T10:00:00+00:00")
    git_commit(repo, {"tests/a.cs": probes(5)}, "2026-10-26T09:00:00+00:00")
    git_commit(repo, {"tests/a.cs": probes(6)}, "2026-10-28T09:00:00+00:00")
    git_commit(repo, {"tests/a.cs": probes(4)}, "2026-11-02T09:00:00+00:00")
    return repo


CHANGELOG = "\n".join(
    [
        "# Changelog",
        f"## 1.2.0 {EM_DASH} 2026-11-16 (later)",
        f"## 1.1.0 {EM_DASH} 2026-10-27 (mid)",
        f"## 1.0.0 {EM_DASH} 2026-10-13 (first)",
        "## 0.9.0 (no date in this heading)",
        "",
    ]
)


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> Path:
    return build_repo(tmp_path_factory.mktemp("gitrepo") / "src")


@pytest.fixture(scope="module")
def extracts(repo: Path) -> dict[str, str]:
    profile = load_profile(PROFILE)
    head = git_run(repo, "rev-parse", "HEAD")
    return {
        "git_log": gitstats.collect_log(repo, head),
        "git_tests": gitstats.collect_tests(repo, head, profile.metrics["M3"]),
    }


def test_log_extract_has_hash_author_and_committer_dates(extracts) -> None:
    commits = gitstats.parse_log(extracts["git_log"])
    assert len(commits) == 6
    oldest = commits[-1]
    assert oldest.author_day == date(2026, 1, 5) and oldest.committer_day == date(2026, 10, 12)


def test_parse_log_reads_a_z_suffix_like_a_zero_offset() -> None:
    # newer git prints UTC as Z; Python 3.10 fromisoformat rejects it on its own
    z = gitstats.parse_log(f"{HASH} 2026-11-02T23:30:00Z 2026-11-03T08:00:00Z\n")
    plus = gitstats.parse_log(f"{HASH} 2026-11-02T23:30:00+00:00 2026-11-03T08:00:00+00:00\n")
    assert len(z) == 1 and z == plus
    assert z[0].hash == HASH and z[0].author_day == date(2026, 11, 2) and z[0].committer_day == date(2026, 11, 3)
    assert z[0].author.utcoffset().total_seconds() == 0
    assert gitstats.parse_log(f"{HASH} 2026-11-02T23:30:00Zx 2026-11-03T08:00:00Z\n") == []  # other bad lines still skipped


def test_m3_counts_attributes_at_the_last_commit_of_each_week(extracts) -> None:
    result = gitstats.m3(extracts["git_tests"])
    assert result == {
        "status": "ok",
        # the week of the first commit holds no attribute: counted as 0, not dropped
        "v1": {"n": 2, "count": 3, "weeks": {"2026-W02": 0, "2026-W42": 3}},
        "v2": {"n": 2, "count": 4, "weeks": {"2026-W44": 6, "2026-W45": 4}},
    }


def test_m3_ignores_files_outside_the_glob_and_non_attribute_lines(repo: Path, extracts) -> None:
    # src/b.cs holds 9 attributes, the comment and the ProbeCase line also look similar
    assert "2026-W02" in extracts["git_tests"] and extracts["git_tests"].count(" 9\n") == 0


def test_m3_with_no_extract_is_no_data() -> None:
    assert gitstats.m3(None) == {"status": "no data"}
    assert gitstats.m3("") == {"status": "no data"}


def test_m12_commits_and_versions_per_period(extracts) -> None:
    profile = load_profile(PROFILE)
    result, warnings = gitstats.m12(profile.metrics["M12"], extracts["git_log"], CHANGELOG)
    assert result == {
        "status": "ok",
        # 3 commits (one out of span) + 1 version; the span is W42 only
        "v1": {"n": 4, "count": 3, "versions": 1, "weeks": 1},
        # 3 commits + 2 versions; W44 to W47, the empty weeks W46 included
        "v2": {"n": 5, "count": 3, "versions": 2, "weeks": 4},
    }
    assert warnings["m12_author_date_outside_span"] == 1
    assert warnings["m12_undated_version"] == 1


def test_m12_commits_only_has_no_versions_key(extracts) -> None:
    result, _ = gitstats.m12({"commits": True}, extracts["git_log"], None)
    assert "versions" not in result["v2"] and result["v2"]["count"] == 3


def test_m12_versions_only_has_no_count_key() -> None:
    profile = load_profile(PROFILE)
    result, _ = gitstats.m12(profile.metrics["M12"] | {"commits": False}, None, CHANGELOG)
    assert result["v2"] == {"n": 2, "versions": 2, "weeks": 4}


def test_m12_without_any_input_is_no_data() -> None:
    result, _ = gitstats.m12({"commits": True}, None, None)
    assert result == {"status": "no data"}


def test_compute_gives_no_data_for_metrics_the_profile_lacks() -> None:
    profile = load_profile(FIXTURES / "profile-test.json")
    results, warnings = gitstats.compute(profile, {}, {})
    assert results == {"M3": {"status": "no data"}, "M12": {"status": "no data"}} and not warnings


# --- weeks and dates --------------------------------------------------------

def test_iso_week_label_uses_the_iso_year() -> None:
    assert gitstats.iso_week(date(2027, 1, 1)) == "2026-W53"
    assert gitstats.iso_week(date(2025, 12, 29)) == "2026-W01"
    assert gitstats.iso_week(date(2026, 10, 25)) == "2026-W43"  # the cutoff is a Sunday


def test_last_commit_of_a_week_is_the_latest_instant_not_the_latest_clock_time() -> None:
    text = (
        f"{'1' * 40} 2026-10-14T23:30:00-05:00 2026-10-15T00:00:00+00:00\n"  # 04:30 UTC on the 15th
        f"{'2' * 40} 2026-10-15T02:00:00+00:00 2026-10-15T02:00:00+00:00\n"
    )
    best = gitstats.last_commit_per_week(gitstats.parse_log(text))
    assert best["2026-W42"].hash == "1" * 40


def test_dates_are_read_in_the_recorded_offset() -> None:
    (commit,) = gitstats.parse_log(f"{HASH} 2026-10-14T23:30:00-05:00 2026-10-14T23:30:00-05:00\n")
    assert commit.author_day == date(2026, 10, 14)


def test_a_line_that_is_not_a_log_line_is_ignored() -> None:
    assert gitstats.parse_log("not a log line\n") == []


def test_changelog_text_is_folded_before_versions_are_read() -> None:
    profile = load_profile(PROFILE)
    folded = folded_lines(CHANGELOG)
    assert any(line.startswith("## 1.0.0") for line in folded) and profile.metrics["M12"]["file"] == "changelog"
