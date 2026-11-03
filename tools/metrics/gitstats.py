"""Git metrics M3 and M12, from two text extracts taken at a pinned HEAD.

The snapshot writes two files next to the record copies:

  git-log.txt    one line per commit reachable from HEAD:
                 <hash> <author date> <committer date>   (strict ISO 8601)
  git-tests.txt  one line per ISO week that has a commit, by author date:
                 <week> <hash of the week's last commit> <its author day> <count>
                 where count is the number of attribute lines `git grep`
                 finds in that commit under the profile path glob.

A run parses these copies only; git is called at snapshot time and nowhere
else. Dates are read in the author's or committer's own offset, as recorded,
so the result does not depend on the machine's time zone.

M3   test attributes at the last commit of each ISO week; a period cell holds
     the count of its last week and all weeks of the period.
M12  commits per ISO week by author date, versions per ISO week by changelog
     heading date. A period cell holds the totals and the number of ISO weeks
     from the first to the last item, empty weeks included. Commits whose
     author day lies outside the committer-day span are counted and reported;
     they do not stretch the week span.
"""
from __future__ import annotations

import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from .fold import folded_lines
from .profile import Profile
from .records import period_of, scan_versions, to_date

NO_DATA = {"status": "no data"}
PERIODS = ("v1", "v2")
HASH = r"(?:[0-9a-f]{40}|[0-9a-f]{64})"
LOG_LINE = re.compile(rf"({HASH}) (\S+) (\S+)")
TESTS_LINE = re.compile(rf"(\d{{4}}-W\d{{2}}) ({HASH}) (\d{{4}}-\d{{2}}-\d{{2}}) (\d+)")


class GitError(ValueError):
    pass


def _run(cwd: Path, *args: str) -> tuple[int, str]:
    try:
        res = subprocess.run(
            ["git", "-c", "core.quotepath=off", *args], cwd=cwd, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        raise GitError("git could not be run")
    return res.returncode, res.stdout


def iso_week(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


@dataclass(frozen=True)
class Commit:
    hash: str
    author: datetime
    author_day: date
    committer_day: date


def parse_log(text: str) -> list[Commit]:
    commits: list[Commit] = []
    for line in text.splitlines():
        hit = LOG_LINE.fullmatch(line)
        if not hit:
            continue
        try:
            author = datetime.fromisoformat(hit.group(2))
            committer = datetime.fromisoformat(hit.group(3))
        except ValueError:
            continue
        commits.append(Commit(hit.group(1), author, author.date(), committer.date()))
    return commits


def collect_log(source: Path, head: str) -> str:
    code, out = _run(source, "log", "--format=%H %aI %cI", head)
    if code != 0:
        raise GitError("git log failed")
    return out if out.endswith("\n") or not out else out + "\n"


def last_commit_per_week(commits: list[Commit]) -> dict[str, Commit]:
    """The commit with the latest author date in each ISO week of the author day."""
    best: dict[str, Commit] = {}
    for commit in commits:
        week = iso_week(commit.author_day)
        current = best.get(week)
        if current is None or (commit.author, commit.hash) > (current.author, current.hash):
            best[week] = commit
    return best


def count_attributes(source: Path, commit: str, spec: Mapping[str, Any]) -> int:
    code, out = _run(
        source, "grep", "-c", "-I", "-E", "-e", spec["attribute"], commit, "--",
        f":(glob){spec['path_glob']}",
    )
    if code not in (0, 1):  # 1 means no match
        raise GitError("git grep failed")
    total = 0
    for line in out.splitlines():
        tail = line.rsplit(":", 1)[-1]
        if tail.isdigit():
            total += int(tail)
    return total


def collect_tests(source: Path, head: str, spec: Mapping[str, Any]) -> str:
    commits = parse_log(collect_log(source, head))
    lines = []
    for week, commit in sorted(last_commit_per_week(commits).items()):
        count = count_attributes(source, commit.hash, spec)
        lines.append(f"{week} {commit.hash} {commit.author_day.isoformat()} {count}\n")
    return "".join(lines)


# --- M3 -------------------------------------------------------------------

def m3(tests_text: str | None) -> dict[str, Any]:
    if not tests_text:
        return dict(NO_DATA)
    rows: dict[str, list[tuple[str, int]]] = {p: [] for p in PERIODS}
    for line in tests_text.splitlines():
        hit = TESTS_LINE.fullmatch(line)
        day = to_date(hit.group(3)) if hit else None
        if hit is None or day is None:
            continue
        rows[period_of(day)].append((hit.group(1), int(hit.group(4))))
    if not any(rows.values()):
        return dict(NO_DATA)
    out: dict[str, Any] = {"status": "ok"}
    for period in PERIODS:
        weeks = dict(sorted(rows[period]))
        if not weeks:
            out[period] = {"n": 0}
            continue
        last = weeks[max(weeks)]
        out[period] = {"n": len(weeks), "count": last, "weeks": weeks}
    return out


# --- M12 ------------------------------------------------------------------

def _monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _span_weeks(days: list[date]) -> int:
    if not days:
        return 0
    return (_monday(max(days)) - _monday(min(days))).days // 7 + 1


def m12(
    cfg: Mapping[str, Any], log_text: str | None, changelog_text: str | None
) -> tuple[dict[str, Any], Counter]:
    warnings: Counter = Counter()
    commits = parse_log(log_text) if (cfg["commits"] and log_text) else None
    version_days: list[date] | None = None
    if "file" in cfg and changelog_text is not None:
        version_days = []
        for version in scan_versions(folded_lines(changelog_text), cfg):
            if version.day is None:
                warnings["m12_undated_version"] += 1
            else:
                version_days.append(version.day)
    if not commits and not version_days:
        return dict(NO_DATA), warnings

    items: dict[str, list[date]] = {p: [] for p in PERIODS}  # days that set the week span
    commit_count = {p: 0 for p in PERIODS}
    version_count = {p: 0 for p in PERIODS}
    if commits:
        first = min(c.committer_day for c in commits)
        last = max(c.committer_day for c in commits)
        for commit in commits:
            period = period_of(commit.author_day)
            commit_count[period] += 1
            if first <= commit.author_day <= last:
                items[period].append(commit.author_day)
            else:
                warnings["m12_author_date_outside_span"] += 1
    for day in version_days or []:
        period = period_of(day)
        version_count[period] += 1
        items[period].append(day)

    out: dict[str, Any] = {"status": "ok"}
    for period in PERIODS:
        n = commit_count[period] + version_count[period]
        if n == 0:
            out[period] = {"n": 0}
            continue
        cell: dict[str, Any] = {"n": n, "weeks": _span_weeks(items[period])}
        if commits is not None:
            cell["count"] = commit_count[period]
        if version_days is not None:
            cell["versions"] = version_count[period]
        out[period] = cell
    return out, warnings


def compute(
    profile: Profile, texts: Mapping[str, str | None], git: Mapping[str, str | None]
) -> tuple[dict[str, Any], Counter]:
    """Return ({"M3": ..., "M12": ...}, warnings). Missing input is "no data"."""
    results: dict[str, Any] = {}
    warnings: Counter = Counter()
    results["M3"] = m3(git.get("git_tests")) if "M3" in profile.metrics else dict(NO_DATA)
    cfg = profile.metrics.get("M12")
    if cfg is None:
        results["M12"] = dict(NO_DATA)
    else:
        changelog = texts.get(cfg["file"]) if "file" in cfg else None
        results["M12"], found = m12(cfg, git.get("git_log"), changelog)
        warnings.update(found)
    return results, warnings
