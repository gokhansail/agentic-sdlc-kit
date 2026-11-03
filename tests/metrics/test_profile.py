from __future__ import annotations

import json

import pytest

from tools.metrics.profile import ProfileError, load_profile, parse_profile
from conftest import ROOT

PROFILES = ROOT / "tools" / "metrics" / "profiles"


def doc(**changes) -> bytes:
    base = {
        "schema": 1,
        "files": {"log": "LOG.md"},
        "metrics": {
            "M5": {
                "file": "log",
                "entry_heading": "^## (?P<date>[0-9-]+)",
                "task_line": "^- measures:",
                "fields": {"review_rounds": "rounds (?P<n>[0-9]+)"},
            }
        },
    }
    base.update(changes)
    return json.dumps(base).encode("ascii")


@pytest.mark.parametrize("name", ["project-a", "project-b", "kit"])
def test_shipped_profiles_load(name: str) -> None:
    profile = load_profile(PROFILES / f"{name}.json")
    assert {"changelog", "log"} <= set(profile.files)
    assert len(profile.sha256) == 64


def test_shipped_profiles_name_the_metrics_each_source_has() -> None:
    assert set(load_profile(PROFILES / "project-b.json").metrics) == {"M3", "M8", "M12"}
    assert set(load_profile(PROFILES / "kit.json").metrics) == {"M5", "M6", "M8", "M9", "M12", "M13"}
    assert set(load_profile(PROFILES / "project-a.json").metrics) == {
        "M1", "M2", "M3", "M5", "M6", "M8", "M9", "M12", "M13"
    }


def test_profile_hash_ignores_line_end_style() -> None:
    lf = doc().replace(b", ", b",\n")
    crlf = lf.replace(b"\n", b"\r\n")
    assert parse_profile(lf).sha256 == parse_profile(crlf).sha256


def test_valid_profile_parses() -> None:
    assert "M5" in parse_profile(doc()).metrics


def test_non_ascii_profile_is_refused() -> None:
    raw = doc().replace(b"measures", ("m" + chr(0xE9) + "sures").encode("utf-8"))
    with pytest.raises(ProfileError, match="ASCII"):
        parse_profile(raw)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("files"),
        lambda d: d.update(schema=2),
        lambda d: d["metrics"].update(M99={"file": "log"}),
        lambda d: d["metrics"]["M5"].pop("task_line"),
        lambda d: d["metrics"]["M5"].update(task_line="(unclosed"),
        lambda d: d["metrics"]["M5"].update(extra="x"),
        lambda d: d["metrics"]["M5"]["fields"].update(review_rounds="rounds [0-9]+"),
        lambda d: d["metrics"]["M5"]["fields"].update(other="x (?P<n>1)"),
        lambda d: d["metrics"]["M5"].update(file="elsewhere"),
        lambda d: d["metrics"]["M5"].update(entry_heading="^## no group"),
    ],
)
def test_malformed_profiles_are_refused(mutate) -> None:
    data = json.loads(doc())
    mutate(data)
    with pytest.raises(ProfileError):
        parse_profile(json.dumps(data).encode("ascii"))


def test_not_json_is_refused() -> None:
    with pytest.raises(ProfileError):
        parse_profile(b"{nope")


# --- T-21 entries: folders, M3, M8, M9, M12, M13 ---------------------------------

from conftest import FIXTURES  # noqa: E402


def records_doc() -> dict:
    return json.loads((FIXTURES / "profile-records.json").read_text(encoding="ascii"))


def test_records_profile_parses_all_new_metrics() -> None:
    profile = parse_profile(json.dumps(records_doc()).encode("ascii"))
    assert set(profile.metrics) == {"M3", "M8", "M9", "M12", "M13"}
    assert set(profile.folders) == {"audits"}
    assert profile.metrics["M12"]["commits"] is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["folders"]["audits"].update(dir="../elsewhere"),
        lambda d: d["folders"]["audits"].update(dir="/abs/path"),
        lambda d: d["folders"]["audits"].update(name="no date group"),
        lambda d: d["folders"]["audits"].update(extra="x"),
        lambda d: d["folders"].update(changelog={"dir": "x", "name": "(?P<date>1)"}),  # role of a file
        lambda d: d["folders"].update(git_log={"dir": "x", "name": "(?P<date>1)"}),  # reserved role
        lambda d: d["files"].update(git_tests="x.txt"),  # reserved role
        lambda d: d["metrics"]["M3"].update(path_glob="../outside/*.cs"),
        lambda d: d["metrics"]["M3"].update(path_glob="/abs/*.cs"),
        lambda d: d["metrics"]["M3"].update(path_glob="has space/*.cs"),
        lambda d: d["metrics"]["M3"].update(attribute="-e injected"),
        lambda d: d["metrics"]["M3"].pop("attribute"),
        lambda d: d["metrics"]["M8"].update(folder="nowhere"),
        lambda d: d["metrics"]["M8"].update(finding_heading="^### no group"),
        lambda d: d["metrics"]["M8"].update(table_row=r"^\|\s*(?P<id>x)"),  # needs a status group too
        lambda d: d["metrics"]["M9"].update(file="nowhere"),
        lambda d: d["metrics"]["M9"].update(outcome="no value group"),
        lambda d: d["metrics"]["M9"].pop("empty"),
        lambda d: d["metrics"]["M12"].update(commits="yes"),
        lambda d: d["metrics"]["M12"].pop("date"),
        lambda d: d["metrics"]["M13"].update(tags={"X": "a"}),
        lambda d: d["metrics"]["M13"].update(tags={}),
        lambda d: d["metrics"]["M13"].update(tags={"E": "s", "M": "s"}),
        lambda d: d["metrics"]["M13"].update(tag="no group"),
    ],
)
def test_malformed_record_profiles_are_refused(mutate) -> None:
    data = records_doc()
    mutate(data)
    with pytest.raises(ProfileError):
        parse_profile(json.dumps(data).encode("ascii"))


def test_m12_with_commits_alone_is_valid_and_empty_is_not() -> None:
    data = records_doc()
    data["metrics"]["M12"] = {"commits": True}
    assert parse_profile(json.dumps(data).encode("ascii")).metrics["M12"] == {"commits": True}
    data["metrics"]["M12"] = {"commits": False}
    with pytest.raises(ProfileError):
        parse_profile(json.dumps(data).encode("ascii"))
