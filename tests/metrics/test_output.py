from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.metrics import output
from tools.metrics.output import OutputError, dumps, validate_manifest, validate_result, write_json

SHA = "a" * 64
HEAD = "b" * 40


def good_result() -> dict:
    return {
        "schema": 1,
        "label": "project-a",
        "cutoff": "2026-10-25",
        "kit_commit": HEAD,
        "input": {"head": HEAD, "dirty": True, "files": {"changelog": SHA, "log": None}, "profile_sha256": SHA},
        "metrics": {
            "M1": {
                "status": "ok",
                "v1": {"n": 3, "count": 1, "items": 0},
                "v2": {"n": 0},
                "undated": {"n": 2, "count": 0, "items": 0},
            },
            "M5": {
                "status": "ok",
                "v1": {"n": 2, "distribution": {"0": 1, "1": 0, "2": 1, "3+": 0}},
                "v2": {"n": 0},
                "undated": {"n": 0},
            },
            "M6": {
                "status": "ok",
                "v1": {"questions_back": {"n": 2, "count": 1}, "out_of_scope": {"n": 0}},
                "v2": {"questions_back": {"n": 0}, "out_of_scope": {"n": 0}},
                "undated": {"questions_back": {"n": 0}, "out_of_scope": {"n": 0}},
            },
            "M2": {"status": "no data"},
        },
        "warnings": {"m1_undated_heading": 2, "source_not_git": 1},
    }


def test_writer_passes_a_result_with_only_fixed_forms(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "out.json"
    write_json(target, good_result(), "result")
    data = target.read_bytes()
    assert data.endswith(b"\n") and b"\r" not in data
    assert json.loads(data) == good_result()


def test_writer_passes_a_manifest(tmp_path: Path) -> None:
    manifest = {
        "schema": 1, "label": "kit", "kit_commit": None, "head": None, "dirty": None,
        "profile_sha256": SHA, "files": {"changelog": SHA}, "warnings": {"source_not_git": 1},
    }
    write_json(tmp_path / "manifest.json", manifest, "manifest")
    validate_manifest(manifest)


FREE_TEXT = "Some record text, with spaces"


def put(path: list, value):
    def apply(obj):
        node = obj
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        return obj
    return apply


@pytest.mark.parametrize(
    "mutate",
    [
        put(["label"], FREE_TEXT),
        put(["label"], "Upper_Case"),
        put(["cutoff"], FREE_TEXT),
        put(["cutoff"], "2026-10-25 and a note"),
        put(["kit_commit"], "main"),
        put(["input", "head"], FREE_TEXT),
        put(["input", "profile_sha256"], "xyz"),
        put(["input", "files", "log"], FREE_TEXT),
        put(["input", "files", "Bad Role"], SHA),
        put(["input", "dirty"], "yes"),
        put(["metrics", "M1", "status"], FREE_TEXT),
        put(["metrics", "M1", "v1", "note"], 1),
        put(["metrics", "M1", "v1", "count"], FREE_TEXT),
        put(["metrics", "M1", "v1", "count"], 0.5),
        put(["metrics", "M1", "v1", "count"], True),
        put(["metrics", "M1", "v1", "count"], -1),
        put(["metrics", "free text key"], {"status": "ok"}),
        put(["metrics", "M5", "v1", "distribution", "4"], 1),
        put(["warnings", "a record line said so"], 1),
        put(["warnings", "m1_undated_heading"], FREE_TEXT),
        put(["extra"], 1),
    ],
)
def test_writer_refuses_free_text_and_unknown_shapes(mutate, tmp_path: Path) -> None:
    bad = mutate(copy.deepcopy(good_result()))
    target = tmp_path / "out.json"
    with pytest.raises(OutputError) as err:
        write_json(target, bad, "result")
    assert not target.exists()
    assert FREE_TEXT not in str(err.value)


def test_refusal_message_does_not_echo_the_value(tmp_path: Path) -> None:
    secret = "private record text"
    bad = good_result()
    bad["label"] = secret
    with pytest.raises(OutputError) as err:
        validate_result(bad)
    assert secret not in str(err.value)


def test_output_is_sorted_ascii_and_has_no_timestamp() -> None:
    text = dumps(good_result()).decode("ascii")
    keys = list(json.loads(text))
    assert keys == sorted(keys)
    assert "T00:" not in text and "time" not in text
    assert dumps(good_result()) == dumps(copy.deepcopy(good_result()))


def test_every_warning_name_is_lowercase_with_underscores() -> None:
    assert all(name.replace("_", "").isalnum() and name.islower() for name in output.WARNING_NAMES)
