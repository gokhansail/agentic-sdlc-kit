"""The writer allowlist for the T-21 keys: one pass test, and refuse tests for each new shape."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.metrics.output import OutputError, validate_manifest, validate_result, write_json

SHA = "c" * 64
HEAD = "d" * 40


def good_result() -> dict:
    return {
        "schema": 1,
        "label": "kit",
        "cutoff": "2026-10-25",
        "kit_commit": HEAD,
        "input": {
            "head": HEAD,
            "dirty": False,
            "files": {"changelog": SHA, "git_log": SHA, "git_tests": SHA},
            "folders": {"audits": {"files": 3, "untracked": 1, "sha256": SHA}},
            "profile_sha256": SHA,
        },
        "metrics": {
            "M3": {
                "status": "ok",
                "v1": {"n": 1, "count": 3, "weeks": {"2026-W42": 3}},
                "v2": {"n": 0},
            },
            "M8": {
                "status": "ok",
                "v1": {
                    "n": 5,
                    "severity": {"critical": 1, "high": 1, "medium": 1, "low": 1, "unrated": 1},
                    "latest": {"closed": 1, "partial": 1, "open": 1, "deferred": 1, "none": 1},
                    "days_to_closed": {"0": 1, "1-3": 0, "4-7": 0, "8+": 0},
                },
                "v2": {"n": 0},
            },
            "M9": {"status": "ok", "v1": {"n": 2, "count": 1}, "v2": {"n": 0}, "undated": {"n": 0}},
            "M12": {
                "status": "ok",
                "v1": {"n": 6, "count": 5, "versions": 1, "weeks": 3},
                "v2": {"n": 0},
            },
            "M13": {
                "status": "ok",
                "v1": {"n": 4, "distribution": {"E": 2, "M": 1, "H": 1}, "done": 3},
                "v2": {"n": 0},
                "undated": {"n": 0},
            },
        },
        "warnings": {
            "m8_unrated_finding": 1,
            "m9_undated_entry": 1,
            "m12_author_date_outside_span": 2,
            "m13_untagged_heading": 1,
            "record_folder_missing": 1,
        },
    }


def good_manifest() -> dict:
    return {
        "schema": 1, "label": "kit", "kit_commit": None, "head": HEAD, "dirty": False,
        "profile_sha256": SHA, "files": {"git_log": SHA},
        "folders": {"audits": {"2026-11-02_gate1.md": {"sha256": SHA, "tracked": False}}},
        "warnings": {},
    }


def test_writer_passes_the_new_keys(tmp_path: Path) -> None:
    target = tmp_path / "out.json"
    write_json(target, good_result(), "result")
    assert json.loads(target.read_bytes()) == good_result()


def test_writer_passes_a_manifest_with_folders(tmp_path: Path) -> None:
    write_json(tmp_path / "m.json", good_manifest(), "manifest")
    validate_manifest(good_manifest())


def put(path: list, value):
    def apply(obj):
        node = obj
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        return obj
    return apply


FREE = "Some record text, with spaces"


@pytest.mark.parametrize(
    "mutate",
    [
        put(["metrics", "M3", "v1", "weeks", FREE], 1),
        put(["metrics", "M3", "v1", "weeks", "2026-W42"], FREE),
        put(["metrics", "M3", "v1", "weeks", "week 42"], 1),
        put(["metrics", "M8", "v1", "severity", "serious"], 1),
        put(["metrics", "M8", "v1", "severity", "high"], FREE),
        put(["metrics", "M8", "v1", "latest", "finished"], 1),
        put(["metrics", "M8", "v1", "days_to_closed", "9"], 1),
        put(["metrics", "M13", "v1", "distribution", "Z"], 1),
        put(["metrics", "M13", "v1", "distribution", "0"], 1),  # buckets of M5 do not belong to M13
        put(["metrics", "M13", "v1", "done"], FREE),
        put(["metrics", "M12", "v1", "weeks"], FREE),
        put(["metrics", "M12", "v1", "versions"], -1),
        put(["metrics", "M12", "v1", "title"], 1),
        put(["input", "folders", "audits", "sha256"], FREE),
        put(["input", "folders", "audits", "files"], FREE),
        put(["input", "folders", "audits", "names"], 1),
        put(["input", "folders", "Bad Role"], {"files": 1, "untracked": 0, "sha256": SHA}),
        put(["warnings", "m8_the_record_said_so"], 1),
    ],
)
def test_writer_refuses_free_text_in_the_new_shapes(mutate, tmp_path: Path) -> None:
    bad = mutate(copy.deepcopy(good_result()))
    target = tmp_path / "out.json"
    with pytest.raises(OutputError) as err:
        write_json(target, bad, "result")
    assert not target.exists() and FREE not in str(err.value)


@pytest.mark.parametrize(
    "mutate",
    [
        put(["folders", "audits", "has space.md"], {"sha256": SHA, "tracked": True}),
        put(["folders", "audits", "..", ], {"sha256": SHA, "tracked": True}),
        put(["folders", "audits", "a.md", "tracked"], "no"),
        put(["folders", "audits", "a.md"], {"sha256": FREE, "tracked": False}),
        put(["folders", "audits", "a.md"], {"sha256": SHA, "tracked": False, "extra": 1}),
        put(["folders", "Bad Role"], {}),
    ],
)
def test_writer_refuses_unsafe_folder_listings(mutate, tmp_path: Path) -> None:
    manifest = good_manifest()
    manifest["folders"]["audits"]["a.md"] = {"sha256": SHA, "tracked": True}
    bad = mutate(manifest)
    target = tmp_path / "m.json"
    with pytest.raises(OutputError):
        write_json(target, bad, "manifest")
    assert not target.exists()


def test_result_without_folders_is_still_valid() -> None:
    result = good_result()
    del result["input"]["folders"]
    validate_result(result)
