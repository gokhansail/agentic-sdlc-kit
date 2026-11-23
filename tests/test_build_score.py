"""Tests for the build scorer (T-64d, tools/build_score.py). The parts that need Node (`node --test`) are skipped
when `node` is not on PATH; the runs that need the browser harness (Playwright and its browser, outside the
repository) are skipped when the environment variable GUITAR_HARNESS is not set. No model is called and
nothing is downloaded.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_score as bs  # noqa: E402

BUILD = ROOT / "bench" / "build"
REFERENCE = BUILD / "reference"
FIXTURES = ROOT / "tests" / "fixtures" / "build_score"
SCRIPT = ROOT / "tools" / "build_score.py"
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node is not on PATH")
HARNESS = os.environ.get("GUITAR_HARNESS")
needs_harness = pytest.mark.skipif(not HARNESS or NODE is None, reason="GUITAR_HARNESS is not set or node is not on PATH")
KEY = "test-key-for-the-scorer-0001"


def run_cli(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8", env=env, timeout=1500)


def temp_scores() -> set[str]:
    return {name for name in os.listdir(tempfile.gettempdir()) if name.startswith("build-score-")}


def mapped() -> dict[str, dict]:
    return bs.spec_map()


def empty_folder(base: Path) -> Path:
    folder = base / "empty"
    folder.mkdir()
    shutil.copy(BUILD / "SPEC.md", folder / "SPEC.md")
    return folder


# ----------------------------------------------------------------------------------------------- selection
def test_the_engine_selection_follows_the_rule_of_the_browser_runner() -> None:
    ids = {name: bs.selected_engine_ids(order) for name, order in [("1", 1), ("5", 5), ("6", 6), ("8", 8), ("handoff", bs.run_browser.HANDOFF_ORDER)]}
    assert all(test_id.split(".")[0] == "s1" for test_id in ids["1"])
    assert {"s3.engine.spectrum-peak", "s3.engine.spectrum-shape"} <= set(ids["5"])
    assert not {"s3.engine.spectrum-peak", "s3.engine.spectrum-shape"} & set(ids["6"]), "retired at 6"
    assert not any(test_id.startswith(("s7.", "handoff.")) for test_id in ids["6"])
    assert not any(test_id.startswith("handoff.") for test_id in ids["8"]) and any(test_id.startswith("s7.") for test_id in ids["8"])
    assert any(test_id.startswith("handoff.") for test_id in ids["handoff"])
    assert all(".engine." in test_id for step in ids.values() for test_id in step)
    retired = {test_id for test_id, entry in mapped().items() if ".engine." in test_id and entry["retired_at"] is not None}
    assert set(ids["handoff"]) == {t for t in mapped() if ".engine." in t} - retired


def test_engine_files_are_those_of_the_selected_steps_and_the_handoff_file_only_at_the_handoff() -> None:
    names = lambda order: [p.name for p in bs.engine_files(bs.selected_engine_ids(order))]  # noqa: E731
    assert names(1) == ["step1.test.mjs"]
    assert names(3) == ["step1.test.mjs", "step2.test.mjs", "step3.test.mjs"]
    assert names(8) == [f"step{n}.test.mjs" for n in range(1, 8)]
    assert names(bs.run_browser.HANDOFF_ORDER) == [*(f"step{n}.test.mjs" for n in range(1, 8)), "song.test.mjs"]
    assert all(p.is_file() for p in bs.engine_files(bs.selected_engine_ids(bs.run_browser.HANDOFF_ORDER)))
    assert [p.name for p in bs.ESTIMATOR_FILES] == ["pitch.test.mjs", "decay.test.mjs"]


def test_the_browser_time_limit_follows_the_contract() -> None:
    assert bs.browser_timeout(24, 4) == 6 * 130 + 120
    assert bs.browser_timeout(25, 4) == 7 * 130 + 120
    assert bs.browser_timeout(69, 8) == 9 * 130 + 120
    assert bs.browser_timeout(1, 8) == 130 + 120


# ---------------------------------------------------------------------------------------------- hashing
def test_the_folder_hash_ignores_git_and_sees_every_other_change(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("one", encoding="utf-8")
    first = bs.tree_hash(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref", encoding="utf-8")
    assert bs.tree_hash(tmp_path) == first
    (tmp_path / "a.txt").write_text("two", encoding="utf-8")
    assert bs.tree_hash(tmp_path) != first
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "b.js").write_text("x", encoding="utf-8")
    changed = bs.tree_hash(tmp_path)
    (tmp_path / "src" / "b.js").write_text("y", encoding="utf-8")
    assert bs.tree_hash(tmp_path) != changed


def test_the_folder_hash_equals_the_runner_rule_when_there_is_no_git_folder(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("one", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "b.js").write_text("x", encoding="utf-8")
    assert bs.tree_hash(tmp_path) == bs.run_browser.tree_hash(tmp_path)


# -------------------------------------------------------------------------------------------- fix prompt
def test_the_fix_prompt_is_the_template_with_the_quoted_sentences() -> None:
    template = (BUILD / "fix-template.txt").read_text(encoding="utf-8")
    assert template == 'Not done yet: "<sentence 1>" "<sentence 2>" ... Please fix this.\n'
    assert bs.fix_prompt(["One.", "Two."]) == 'Not done yet: "One." "Two." Please fix this.\n'
    assert bs.fix_prompt(["Only one."]) == 'Not done yet: "Only one." Please fix this.\n'


def test_the_fix_prompt_refuses_a_template_of_another_form(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    other = tmp_path / "fix-template.txt"
    other.write_text("Please fix: <list>\n", encoding="utf-8")
    monkeypatch.setattr(bs, "FIX_TEMPLATE", other)
    with pytest.raises(bs.ScoreError):
        bs.fix_prompt(["One."])


# ------------------------------------------------------------------- the pipeline with its parts replaced
@pytest.fixture
def fake_pipeline(monkeypatch: pytest.MonkeyPatch):
    """Replaces the engine run, the browser run and the architecture check; the copy, the hashes, the selection,
    the regression rule, the prompt and the outputs are the real ones. Needs `node` on PATH only for the lookup."""
    state: dict = {"engine_fail": set(), "browser_fail": set(), "details": {}, "keys": [], "roots": [], "mutate": None}

    def engine(node, ids, copy, timeout):
        state["roots"].append(copy)
        return {i: ("fail" if i in state["engine_fail"] else "pass") for i in ids}, {}

    def browser(node, copy, harness, step, ids, workers, key):
        state["keys"].append(key)
        if state["mutate"]:
            state["mutate"]()
        return {"tests": {i: ("fail" if i in state["browser_fail"] else "pass") for i in ids}, "details": state["details"]}

    class Arch:
        ArchCheckError = bs.arch_check.ArchCheckError
        check = staticmethod(lambda copy: {"a": 0, "b": 0, "c": 0, "violations": 0, "a_files": {}, "c_files": [], "b_error": ""})

    monkeypatch.setattr(bs, "run_engine", engine)
    monkeypatch.setattr(bs, "run_browser_tests", browser)
    monkeypatch.setattr(bs, "arch_check", Arch)
    return state


@pytest.fixture
def fake_harness(tmp_path: Path) -> Path:
    package = tmp_path / "harness" / "node_modules" / "@playwright" / "test"
    package.mkdir(parents=True)
    (package / "package.json").write_text('{"version": "1.65.1"}', encoding="utf-8")
    return tmp_path / "harness"


def folder_with_git(base: Path) -> Path:
    folder = empty_folder(base)
    (folder / ".git").mkdir()
    (folder / ".git" / "config").write_text("secret-ish\n", encoding="utf-8")
    return folder


@needs_node
def test_a_passing_run_writes_the_score_and_no_prompt_and_leaves_the_folder_and_temp_alone(tmp_path, fake_pipeline, fake_harness, capsys) -> None:
    folder = folder_with_git(tmp_path)
    before_hash, before_files = bs.tree_hash(folder), sorted(p.as_posix() for p in folder.rglob("*"))
    temp_before = temp_scores()
    out, prompt = tmp_path / "o" / "score.json", tmp_path / "o" / "prompt.txt"
    code = bs.main(["--root", str(folder), "--step", "2", "--harness", str(fake_harness), "--out", str(out), "--prompt-out", str(prompt)])
    shown = capsys.readouterr().out
    assert code == 0 and shown == out.read_text(encoding="utf-8")
    result = json.loads(shown)
    assert result["step"] == 2 and result["folder_hash"] == before_hash and result["share"] == 1.0 and result["regressions"] == []
    assert set(result["tests"]) == set(bs.selected_engine_ids(2)) | set(bs.run_browser.selected_ids(2))
    assert result["totals"]["all"]["total"] == len(result["tests"]) == result["totals"]["engine"]["total"] + result["totals"]["browser"]["total"]
    assert result["spec_map_sha256"] == bs.file_hash(BUILD / "spec-map.json") and result["playwright_version"] == "1.65.1"
    assert result["hidden_tree_sha256"] == bs.tree_hash(BUILD / "hidden") and result["arch"] == {"a": 0, "b": 0, "c": 0, "violations": 0}
    assert not prompt.exists(), "no prompt when every selected test passes"
    assert bs.tree_hash(folder) == before_hash and sorted(p.as_posix() for p in folder.rglob("*")) == before_files
    assert temp_scores() == temp_before, "the temporary copy was not deleted"
    assert not fake_pipeline["roots"][0].exists()


@needs_node
def test_the_copy_has_no_git_folder_and_is_deleted_even_when_a_run_raises(tmp_path, fake_pipeline, fake_harness, monkeypatch) -> None:
    folder = folder_with_git(tmp_path)
    seen: list[bool] = []

    def engine(node, ids, copy, timeout):
        seen.append((copy / ".git").exists())
        seen.append((copy / "SPEC.md").is_file())
        raise bs.ScoreError("boom")

    monkeypatch.setattr(bs, "run_engine", engine)
    temp_before = temp_scores()
    code = bs.main(["--root", str(folder), "--step", "1", "--harness", str(fake_harness)])
    assert code == 2 and seen == [False, True]
    assert temp_scores() == temp_before


@needs_node
def test_a_failing_run_exits_1_and_writes_the_prompt_in_spec_map_order_with_5_distinct_sentences(tmp_path, fake_pipeline, fake_harness, capsys) -> None:
    folder = empty_folder(tmp_path)
    ids = bs.selected_engine_ids(1)
    fake_pipeline["engine_fail"] = set(ids)
    fake_pipeline["browser_fail"] = set(bs.run_browser.selected_ids(1))
    prompt = tmp_path / "prompt.txt"
    code = bs.main(["--root", str(folder), "--step", "1", "--harness", str(fake_harness), "--prompt-out", str(prompt)])
    result = json.loads(capsys.readouterr().out)
    assert code == 1 and result["share"] == 0.0 and result["totals"]["all"]["fail"] == len(result["tests"])
    sentences = []
    for test_id, entry in mapped().items():
        if test_id in result["tests"] and entry["sentence"] not in sentences:
            sentences.append(entry["sentence"])
    expected = "Not done yet: " + " ".join(f'"{s}"' for s in sentences[:5]) + " Please fix this.\n"
    assert prompt.read_text(encoding="utf-8") == expected
    assert len(sentences) > 5 and expected.count('" "') == 4


@needs_node
def test_the_prompt_holds_the_sentences_of_the_failing_ids_only_and_a_sentence_once(tmp_path, fake_pipeline, fake_harness, capsys) -> None:
    folder = empty_folder(tmp_path)
    # s1.engine.render-length and s1.engine.render-range share one sentence
    fake_pipeline["engine_fail"] = {"s1.engine.render-length", "s1.engine.render-range", "s1.engine.note-a440"}
    prompt = tmp_path / "prompt.txt"
    code = bs.main(["--root", str(folder), "--step", "1", "--harness", str(fake_harness), "--prompt-out", str(prompt)])
    capsys.readouterr()
    text = prompt.read_text(encoding="utf-8")
    assert code == 1
    assert text == (
        'Not done yet: "A4 = 440 Hz, equal temperament." "renderPluck({frequency, sampleRate, durationSeconds, seed}) returns a '
        'Float32Array of round(sampleRate * durationSeconds) samples in [-1, 1]." Please fix this.\n'
    )


@needs_node
def test_an_architecture_violation_alone_does_not_enter_the_prompt_or_the_exit_code(tmp_path, fake_pipeline, fake_harness, monkeypatch, capsys) -> None:
    folder = empty_folder(tmp_path)

    class Arch:
        ArchCheckError = bs.arch_check.ArchCheckError
        check = staticmethod(lambda copy: {"a": 2, "b": 1, "c": 1, "violations": 4, "a_files": {"src/x.js": 2}, "c_files": ["src/k.js"], "b_error": "e"})

    monkeypatch.setattr(bs, "arch_check", Arch)
    prompt = tmp_path / "prompt.txt"
    code = bs.main(["--root", str(folder), "--step", "1", "--harness", str(fake_harness), "--prompt-out", str(prompt)])
    result = json.loads(capsys.readouterr().out)
    assert code == 0 and not prompt.exists()
    assert result["arch"] == {"a": 2, "b": 1, "c": 1, "violations": 4} and result["arch_detail"]["a_files"] == {"src/x.js": 2}


@needs_node
def test_a_planted_regression_is_listed_and_exits_1_even_if_it_was_the_only_failure_of_the_set(tmp_path, fake_pipeline, fake_harness, capsys) -> None:
    folder = empty_folder(tmp_path)
    fake_pipeline["engine_fail"] = {"s1.engine.exports"}
    code = bs.main(["--root", str(folder), "--step", "2", "--harness", str(fake_harness), "--baseline", str(FIXTURES / "baselines" / "step1-passed.json")])
    result = json.loads(capsys.readouterr().out)
    assert code == 1 and result["regressions"] == ["s1.engine.exports"]
    assert result["regression_baselines"] == {"s1.engine.exports": "step1-passed.json"}
    # the same baseline with every test passing now gives no regression; a baseline "fail" is never one
    fake_pipeline["engine_fail"] = set()
    code = bs.main(["--root", str(folder), "--step", "2", "--harness", str(fake_harness), "--baseline", str(FIXTURES / "baselines" / "step1-passed.json")])
    assert code == 0 and json.loads(capsys.readouterr().out)["regressions"] == []


@needs_node
def test_a_baseline_id_that_is_not_selected_any_more_is_no_regression(tmp_path, fake_pipeline, fake_harness, capsys) -> None:
    folder = empty_folder(tmp_path)
    baseline = tmp_path / "step5.json"
    baseline.write_text(json.dumps({"step": 5, "tests": {"s3.engine.spectrum-peak": "pass", "s1.engine.exports": "pass"}}), encoding="utf-8")
    fake_pipeline["engine_fail"] = {"s1.engine.exports"}
    code = bs.main(["--root", str(folder), "--step", "6", "--harness", str(fake_harness), "--baseline", str(baseline)])
    result = json.loads(capsys.readouterr().out)
    assert "s3.engine.spectrum-peak" not in result["tests"] and result["regressions"] == ["s1.engine.exports"] and code == 1


@pytest.mark.parametrize("name", ["step2-same.json", "handoff-late.json", "not-a-score.json"])
def test_a_baseline_of_the_same_or_a_later_step_or_of_another_form_is_refused(name: str, tmp_path: Path) -> None:
    folder = empty_folder(tmp_path)
    done = run_cli("--root", str(folder), "--step", "2", "--harness", str(tmp_path), "--baseline", str(FIXTURES / "baselines" / name))
    assert done.returncode == 2 and done.stdout == "" and "baseline" in done.stderr


def test_a_baseline_of_an_earlier_step_is_read_and_the_missing_file_is_refused(tmp_path: Path) -> None:
    assert bs.load_baselines([str(FIXTURES / "baselines" / "step1-passed.json")], 2) == {
        "s1.engine.exports": "step1-passed.json", "s1.browser.start-audio": "step1-passed.json",
    }
    with pytest.raises(bs.ScoreError):
        bs.load_baselines([str(tmp_path / "missing.json")], 2)


@needs_node
def test_the_key_goes_to_the_browser_run_only_and_is_removed_from_every_output(tmp_path, fake_pipeline, fake_harness, capsys) -> None:
    folder = empty_folder(tmp_path)
    key_file = tmp_path / "key.txt"
    key_file.write_text(KEY + "\n", encoding="utf-8")
    fake_pipeline["browser_fail"] = {"s8.browser.share-header"}
    fake_pipeline["details"] = {"s8.browser.share-header": f"expected Bearer {KEY} but got nothing"}
    out, prompt = tmp_path / "o" / "score.json", tmp_path / "o" / "prompt.txt"
    code = bs.main([
        "--root", str(folder), "--step", "8", "--harness", str(fake_harness), "--fake-key-file", str(key_file),
        "--out", str(out), "--prompt-out", str(prompt),
    ])
    shown = capsys.readouterr()
    assert code == 1 and fake_pipeline["keys"] == [KEY]
    for text in (shown.out, shown.err, out.read_text(encoding="utf-8"), prompt.read_text(encoding="utf-8")):
        assert KEY not in text
    assert "Bearer <key> but got nothing" in out.read_text(encoding="utf-8")
    # without the file no key is passed on, even when the caller's environment has one
    bs_env = os.environ.get("GUITAR_FAKE_KEY")
    os.environ["GUITAR_FAKE_KEY"] = "from-the-caller"
    try:
        bs.main(["--root", str(folder), "--step", "8", "--harness", str(fake_harness)])
    finally:
        if bs_env is None:
            del os.environ["GUITAR_FAKE_KEY"]
        else:
            os.environ["GUITAR_FAKE_KEY"] = bs_env
    capsys.readouterr()
    assert fake_pipeline["keys"] == [KEY, None]


def test_redact_replaces_the_key_in_plain_and_in_json_spelling() -> None:
    assert bs.redact("a KEY b", "KEY") == "a <key> b"
    assert bs.redact(json.dumps({"x": 'k"ey\\'}), 'k"ey\\') == json.dumps({"x": "<key>"})
    assert bs.redact("unchanged", None) == "unchanged"


@needs_node
def test_a_folder_that_changes_during_the_run_is_a_harness_error(tmp_path, fake_pipeline, fake_harness, capsys) -> None:
    folder = empty_folder(tmp_path)
    fake_pipeline["mutate"] = lambda: (folder / "late.txt").write_text("written while scoring\n", encoding="utf-8")
    out = tmp_path / "o" / "score.json"
    code = bs.main(["--root", str(folder), "--step", "1", "--harness", str(fake_harness), "--out", str(out)])
    captured = capsys.readouterr()
    assert code == 2 and captured.out == "" and "changed" in captured.err and not out.exists()


@needs_node
def test_a_selected_id_without_a_result_is_a_load_error_and_a_stopped_file_is_a_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ids = bs.selected_engine_ids(2)

    def one_file(node, path, copy, timeout):
        if path in bs.ESTIMATOR_FILES:
            return {"estimator.x": True}, False
        if path.name == "step1.test.mjs":
            return {i: True for i in ids if i.startswith("s1.") and i != "s1.engine.exports"}, False
        return {}, True  # step 2: stopped at the time limit, no result

    monkeypatch.setattr(bs, "run_engine_file", one_file)
    outcomes, notes = bs.run_engine("node", ids, tmp_path, 7)
    assert outcomes["s1.engine.exports"] == "load error" and outcomes["s1.engine.note-a440"] == "pass"
    stopped = [i for i in ids if i.startswith("s2.")]
    assert stopped and all(outcomes[i] == "fail" and "7 s" in notes[i] for i in stopped)
    assert "s1.engine.exports" not in notes


@needs_node
@pytest.mark.parametrize("estimator_result", [({"estimator.x": False}, False), ({}, False), ({"estimator.x": True}, True)])
def test_an_estimator_test_that_does_not_pass_is_a_harness_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, estimator_result) -> None:
    ids = bs.selected_engine_ids(1)
    monkeypatch.setattr(bs, "run_engine_file", lambda node, path, copy, timeout: estimator_result if path in bs.ESTIMATOR_FILES else ({}, False))
    with pytest.raises(bs.ScoreError, match="estimator"):
        bs.run_engine("node", ids, tmp_path, 5)


def test_the_estimator_files_that_pass_do_not_raise(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ids = bs.selected_engine_ids(1)
    monkeypatch.setattr(bs, "run_engine_file", lambda node, path, copy, timeout: ({"estimator.x": True}, False) if path in bs.ESTIMATOR_FILES else ({i: True for i in ids}, False))
    outcomes, notes = bs.run_engine("node", ids, tmp_path, 5)
    assert set(outcomes.values()) == {"pass"} and notes == {}


# ------------------------------------------------------------------------------------------- the arguments
def test_out_paths_inside_the_repository_or_the_scored_folder_are_refused_and_nothing_is_written(tmp_path: Path) -> None:
    folder = empty_folder(tmp_path)
    inside_repo = ROOT / "score-should-not-exist.json"
    inside_folder = folder / "score.json"
    for flag, target in [("--out", inside_repo), ("--prompt-out", inside_repo), ("--out", inside_folder), ("--prompt-out", inside_folder)]:
        done = run_cli("--root", str(folder), "--step", "1", "--harness", str(tmp_path), flag, str(target))
        assert done.returncode == 2 and done.stdout == "" and "inside" in done.stderr, (flag, target)
        assert not target.exists()
    nested = ROOT / "tests" / "fixtures" / "build_score" / "x" / ".." / "y.json"
    assert run_cli("--root", str(folder), "--step", "1", "--harness", str(tmp_path), "--out", str(nested)).returncode == 2
    assert bs.tree_hash(folder) == bs.tree_hash(folder) and sorted(p.name for p in folder.iterdir()) == ["SPEC.md"]


@needs_node
def test_an_out_path_outside_both_is_accepted(tmp_path: Path, fake_pipeline, fake_harness) -> None:
    folder = empty_folder(tmp_path)
    out = tmp_path / "elsewhere" / "deep" / "score.json"
    assert bs.main(["--root", str(folder), "--step", "1", "--harness", str(fake_harness), "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["step"] == 1


def test_bad_arguments_exit_2_with_nothing_on_stdout(tmp_path: Path) -> None:
    folder = empty_folder(tmp_path)
    key_file = tmp_path / "empty-key.txt"
    key_file.write_text("\n", encoding="utf-8")
    cases = [
        ["--root", str(tmp_path / "nope"), "--step", "1", "--harness", str(tmp_path)],
        ["--root", str(folder), "--step", "9", "--harness", str(tmp_path)],
        ["--root", str(folder), "--step", "x", "--harness", str(tmp_path)],
        ["--root", str(folder), "--harness", str(tmp_path)],
        ["--root", str(folder), "--step", "1"],
        ["--root", str(folder), "--step", "1", "--harness", str(tmp_path), "--workers", "0"],
        ["--root", str(folder), "--step", "1", "--harness", str(tmp_path), "--fake-key-file", str(tmp_path / "missing.txt")],
        ["--root", str(folder), "--step", "1", "--harness", str(tmp_path), "--fake-key-file", str(key_file)],
    ]
    for args in cases:
        done = run_cli(*args)
        assert done.returncode == 2 and done.stdout == "", (args, done.stderr)
    assert sorted(p.name for p in folder.iterdir()) == ["SPEC.md"]


@needs_node
def test_a_harness_without_playwright_exits_2(tmp_path: Path) -> None:
    folder = empty_folder(tmp_path)
    done = run_cli("--root", str(folder), "--step", "1", "--harness", str(tmp_path))
    assert done.returncode == 2 and "harness" in done.stderr and done.stdout == ""


# ---------------------------------------------------------------------------------- the real engine runs
@needs_node
def test_the_engine_run_passes_every_step_1_test_on_the_reference(tmp_path: Path) -> None:
    outcomes, notes = bs.run_engine(NODE, bs.selected_engine_ids(1), REFERENCE, 300)
    assert set(outcomes.values()) == {"pass"} and notes == {} and len(outcomes) == 35


@needs_node
def test_an_endless_loop_at_import_ends_as_fail_and_not_as_a_harness_error() -> None:
    ids = bs.selected_engine_ids(1)
    outcomes, notes = bs.run_engine(NODE, ids, FIXTURES / "loop-stub", 15)
    assert set(outcomes) == set(ids) and set(outcomes.values()) == {"fail"}
    assert all("15 s" in note for note in notes.values()) and set(notes) == set(ids)


@needs_node
def test_a_stopped_engine_file_leaves_no_node_process_running_it(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    marker.mkdir()
    folder = tmp_path / "stub"
    (folder / "src").mkdir(parents=True)
    (folder / "src" / "engine.js").write_text(f"// {marker.name}\nwhile (true) {{}}\n", encoding="utf-8")
    bs.run_engine(NODE, bs.selected_engine_ids(1), folder, 10)
    if os.name == "nt":
        listing = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Process -Filter \"Name='node.exe'\").CommandLine"],
            capture_output=True, text=True, timeout=60,
        ).stdout
        assert str(folder) not in listing and "step1.test.mjs" not in listing


# ---------------------------------------------------------------------------------- full runs (harness)
@pytest.fixture(scope="module")
def empty_score(tmp_path_factory: pytest.TempPathFactory):
    base = tmp_path_factory.mktemp("empty-score")
    folder = empty_folder(base)
    before, temp_before = bs.tree_hash(folder), temp_scores()
    out, prompt = base / "o" / "score.json", base / "o" / "prompt.txt"
    done = run_cli("--root", str(folder), "--step", "1", "--harness", str(HARNESS), "--out", str(out), "--prompt-out", str(prompt), "--workers", "8")
    return folder, before, temp_before, out, prompt, done


@needs_harness
def test_the_empty_folder_fails_every_selected_test_at_step_1_without_load_errors_and_gets_a_5_sentence_prompt(empty_score) -> None:
    folder, before, temp_before, out, prompt, done = empty_score
    result = json.loads(done.stdout)
    assert done.returncode == 1 and done.stdout == out.read_text(encoding="utf-8")
    selected = set(bs.selected_engine_ids(1)) | set(bs.run_browser.selected_ids(1))
    assert set(result["tests"]) == selected and set(result["tests"].values()) == {"fail"}
    assert result["totals"]["all"] == {"pass": 0, "fail": len(selected), "load error": 0, "total": len(selected)}
    assert result["totals"]["engine"]["load error"] == 0 and result["totals"]["browser"]["load error"] == 0
    assert result["arch"]["violations"] == 1 and result["arch"]["b"] == 1 and result["share"] == 0.0
    text = prompt.read_text(encoding="utf-8")
    assert text.startswith('Not done yet: "') and text.endswith('" Please fix this.\n') and text.count('" "') == 4
    assert result["folder_hash"] == before == bs.tree_hash(folder) and temp_scores() == temp_before


@needs_harness
def test_a_second_run_on_the_same_folder_gives_the_same_tests_and_totals_and_the_key_stays_out_of_the_files(empty_score, tmp_path: Path) -> None:
    folder, _before, _temp, _out, _prompt, first_done = empty_score
    first = json.loads(first_done.stdout)
    key_file = tmp_path / "key.txt"
    key_file.write_text(KEY, encoding="utf-8")
    out, prompt = tmp_path / "o" / "score.json", tmp_path / "o" / "prompt.txt"
    done = run_cli("--root", str(folder), "--step", "1", "--harness", str(HARNESS), "--out", str(out), "--prompt-out", str(prompt),
                   "--fake-key-file", str(key_file), "--workers", "8")
    second = json.loads(done.stdout)
    assert second["tests"] == first["tests"] and second["totals"] == first["totals"] and second["folder_hash"] == first["folder_hash"]
    assert second["arch"] == first["arch"] and second["share"] == first["share"] and second["hidden_tree_sha256"] == first["hidden_tree_sha256"]
    for text in (done.stdout, done.stderr, out.read_text(encoding="utf-8"), prompt.read_text(encoding="utf-8")):
        assert KEY not in text


@needs_harness
def test_a_planted_regression_is_listed_on_a_real_run(empty_score, tmp_path: Path) -> None:
    folder, *_rest = empty_score
    done = run_cli("--root", str(folder), "--step", "2", "--harness", str(HARNESS), "--workers", "8",
                   "--baseline", str(FIXTURES / "baselines" / "step1-passed.json"))
    result = json.loads(done.stdout)
    assert done.returncode == 1 and result["step"] == 2
    assert result["regressions"] == ["s1.engine.exports", "s1.browser.start-audio"]
    assert result["totals"]["all"]["load error"] == 0


@needs_harness
def test_the_reference_passes_every_selected_test_at_the_handoff_with_no_prompt(tmp_path: Path) -> None:
    before, temp_before = bs.tree_hash(REFERENCE), temp_scores()
    out, prompt = tmp_path / "score.json", tmp_path / "prompt.txt"
    done = run_cli("--root", str(REFERENCE), "--step", "handoff", "--harness", str(HARNESS), "--out", str(out), "--prompt-out", str(prompt), "--workers", "8")
    result = json.loads(done.stdout)
    selected = set(bs.selected_engine_ids(bs.run_browser.HANDOFF_ORDER)) | set(bs.run_browser.selected_ids(bs.run_browser.HANDOFF_ORDER))
    assert done.returncode == 0, done.stderr
    assert set(result["tests"]) == selected and set(result["tests"].values()) == {"pass"}
    assert result["totals"]["all"]["pass"] == len(selected) and result["share"] == 1.0 and result["regressions"] == []
    assert result["arch"] == {"a": 0, "b": 0, "c": 0, "violations": 0}
    assert not prompt.exists() and result["folder_hash"] == before == bs.tree_hash(REFERENCE) and temp_scores() == temp_before
    assert re.fullmatch(r"[0-9a-f]{64}", result["spec_map_sha256"]) and result["playwright_version"] == "1.65.1" and result["node_version"].startswith("v")


@needs_harness
def test_a_stub_with_an_endless_loop_at_import_ends_as_fail_with_exit_1(tmp_path: Path) -> None:
    done = run_cli("--root", str(FIXTURES / "loop-stub"), "--step", "1", "--harness", str(HARNESS), "--engine-timeout", "15", "--workers", "8")
    result = json.loads(done.stdout)
    engine = {t: o for t, o in result["tests"].items() if ".engine." in t}
    assert done.returncode == 1 and set(engine.values()) == {"fail"} and result["totals"]["engine"]["load error"] == 0
    assert result["arch"]["b"] == 1, "arch_check also stops the import at its own limit"
