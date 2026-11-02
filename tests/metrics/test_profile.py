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
    assert set(profile.files) == {"changelog", "log"}
    assert len(profile.sha256) == 64


def test_project_b_has_no_text_metrics_and_kit_has_only_log_metrics() -> None:
    assert load_profile(PROFILES / "project-b.json").metrics == {}
    assert set(load_profile(PROFILES / "kit.json").metrics) == {"M5", "M6"}
    assert set(load_profile(PROFILES / "project-a.json").metrics) == {"M1", "M2", "M5", "M6"}


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
