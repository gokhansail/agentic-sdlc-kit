"""Tests for the build bench files of T-64a (bench/build/): frozen texts, spec map, step 1 engine tests,
reference guitar, architecture check. No model is called and nothing is downloaded; the engine tests
need Node (`node --test`) and are skipped when `node` is not on PATH.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import transcript_meter as tm  # noqa: E402

BUILD = ROOT / "bench" / "build"
PLAN = ROOT / "cto" / "2026-11-21_build-bench-plan.md"
REFERENCE = BUILD / "reference"
FIXTURES = ROOT / "tests" / "fixtures" / "arch_check"
ENGINE_TESTS = [BUILD / "hidden" / "engine" / "step1.test.mjs", BUILD / "hidden" / "engine" / "pitch.test.mjs"]
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node is not on PATH")

_spec = importlib.util.spec_from_file_location("arch_check", BUILD / "arch_check.py")
arch_check = importlib.util.module_from_spec(_spec)
sys.modules["arch_check"] = arch_check
_spec.loader.exec_module(arch_check)  # type: ignore[union-attr]


# ------------------------------------------------------------------------------------------ plan blocks
def plan_lines() -> list[str]:
    return PLAN.read_text(encoding="utf-8").split("\n")


def block_after(marker: str) -> str:
    """Content of the first fenced block after the first line that starts with `marker`."""
    lines = plan_lines()
    start = next(i for i, line in enumerate(lines) if line.startswith(marker))
    opening = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("```"))
    closing = next(i for i in range(opening + 1, len(lines)) if lines[i].startswith("```"))
    return "\n".join(lines[opening + 1:closing])


def answer_table() -> str:
    lines = plan_lines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| ID | When the arm..."))
    end = start
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    return "\n".join(lines[start:end])


def frozen_cases() -> list[tuple[str, str, str]]:
    cases = [("SPEC.md", "SPEC.md", block_after("`SPEC.md` (frozen text"))]
    for n in range(1, 9):
        cases.append((f"prompts/step-{n}.txt", f"step {n}", block_after(f"Step {n}")))
    cases.append(("fix-template.txt", "fix template", block_after("Fix prompt template")))
    cases.append(("answers.md", "answer table", answer_table()))
    return cases


@pytest.mark.parametrize("name,label,block", frozen_cases(), ids=[c[1] for c in frozen_cases()])
def test_frozen_text_is_byte_equal_to_the_plan_block(name: str, label: str, block: str) -> None:
    data = (BUILD / name).read_bytes()
    assert data == (block + "\n").encode("utf-8"), f"{name} differs from the plan block ({label})"


def test_plan_blocks_were_found_not_empty() -> None:
    for _name, label, block in frozen_cases():
        assert len(block) > 20, label


def test_frozen_files_are_ascii_with_lf_and_the_key_placeholder_only() -> None:
    for name, _label, _block in frozen_cases():
        data = (BUILD / name).read_bytes()
        assert data.isascii(), f"{name} has a non-ASCII byte"
        assert b"\r" not in data, f"{name} has a CR"
    assert b"{FAKE_KEY}" in (BUILD / "prompts" / "step-8.txt").read_bytes()
    real_key = re.compile(rb"sk-[A-Za-z0-9]{20,}")
    turkish_codepoints = (0xE7, 0x11F, 0x131, 0xF6, 0x15F, 0xFC, 0xC7, 0x11E, 0x130, 0xD6, 0x15E, 0xDC)
    turkish = re.compile("[" + "".join(chr(code) for code in turkish_codepoints) + "]")
    for path in BUILD.rglob("*"):
        if path.is_file() and path.suffix in {".txt", ".md", ".json", ".js", ".mjs", ".py", ".html"}:
            assert not real_key.search(path.read_bytes()), f"{path.name} holds a key-shaped string"
            assert not turkish.search(path.read_text(encoding="utf-8")), f"{path.name} holds a Turkish letter"


# --------------------------------------------------------------------------------------------- texts.json
def test_texts_json_equals_prompt_and_answer_files() -> None:
    texts = json.loads((BUILD / "texts.json").read_text(encoding="utf-8"))
    expected: dict[str, dict[str, str]] = {}
    for n in range(1, 9):
        body = (BUILD / "prompts" / f"step-{n}.txt").read_text(encoding="utf-8")
        assert body.endswith("\n")
        expected[f"S{n}"] = {"type": "step", "text": body[:-1]}
    types = {"A1": "approval", "A9": "resume"}
    for line in (BUILD / "answers.md").read_text(encoding="utf-8").split("\n")[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[2].startswith("`") and cells[2].endswith("`"):
            expected[cells[0]] = {"type": types.get(cells[0], "answer"), "text": cells[2][1:-1]}
    assert texts == expected
    assert sorted(texts) == ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A8", "A9", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
    assert not any("Not done yet" in item["text"] for item in texts.values())


def test_texts_json_loads_in_the_transcript_meter() -> None:
    loaded = tm.load_texts(BUILD / "texts.json")
    assert loaded.types["S8"] == "step" and loaded.types["A1"] == "approval" and loaded.types["A9"] == "resume"
    assert len(loaded.types) == 17


# -------------------------------------------------------------------------------------- node engine tests
def run_node_tests(guitar_root: Path) -> tuple[int, dict[str, bool], str]:
    env = dict(os.environ, GUITAR_ROOT=str(guitar_root))
    done = subprocess.run(
        [NODE, "--test", "--test-reporter=tap", *[str(p) for p in ENGINE_TESTS]],
        capture_output=True, text=True, env=env, timeout=300, encoding="utf-8",
    )
    results: dict[str, bool] = {}
    for line in done.stdout.split("\n"):
        match = re.match(r"^(not )?ok \d+ - (\S+)", line)
        if match:
            results[match.group(2)] = match.group(1) is None
    return done.returncode, results, done.stdout


@pytest.fixture(scope="module")
def reference_run() -> tuple[int, dict[str, bool], str]:
    return run_node_tests(REFERENCE)


@pytest.fixture(scope="module")
def empty_run(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, dict[str, bool], str]:
    folder = tmp_path_factory.mktemp("empty-project")
    shutil.copy(BUILD / "SPEC.md", folder / "SPEC.md")
    return run_node_tests(folder)


def spec_map() -> dict[str, dict]:
    return json.loads((BUILD / "spec-map.json").read_text(encoding="utf-8"))


@needs_node
def test_every_engine_test_passes_on_the_reference(reference_run) -> None:
    code, results, out = reference_run
    failed = sorted(name for name, ok in results.items() if not ok)
    assert code == 0 and not failed, f"failed on the reference: {failed}\n{out[-2000:]}"
    assert len(results) == len(spec_map()) + 5


@needs_node
def test_every_engine_test_fails_on_an_empty_project_without_load_errors(empty_run) -> None:
    code, results, out = empty_run
    estimator = {name for name in results if name.startswith("estimator.")}
    mapped = {name for name in results if name not in estimator}
    # a file-level load error would show as a missing test name or as a name that is no test ID
    assert mapped == set(spec_map()), "a test file did not load or tests are not mapped"
    assert code != 0
    assert all(not results[name] for name in mapped), "a project test passed on an empty project"
    assert all(results[name] for name in estimator), "the estimator tests need no project and must pass"


@needs_node
def test_a_broken_engine_fails_the_test_and_not_the_file(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "engine.js").write_text("export const noteFrequency = 1;\nthrow new Error('boom');\n", encoding="utf-8")
    code, results, _out = run_node_tests(tmp_path)
    assert {n for n in results if not n.startswith("estimator.")} == set(spec_map())
    assert not any(ok for name, ok in results.items() if not name.startswith("estimator."))


# ------------------------------------------------------------------------------------------- the spec map
def test_spec_map_entries_have_a_step_and_a_sentence_that_is_in_the_spec() -> None:
    spec = re.sub(r"\s+", " ", (BUILD / "SPEC.md").read_text(encoding="utf-8"))
    mapped = spec_map()
    assert mapped
    for test_id, entry in mapped.items():
        assert set(entry) == {"step", "sentence", "retired_at"}, test_id
        assert entry["step"] == 1 and entry["retired_at"] is None, test_id
        sentence = re.sub(r"\s+", " ", entry["sentence"])
        assert sentence in spec, f"{test_id}: sentence is not in SPEC.md: {sentence!r}"
        assert sentence == entry["sentence"], f"{test_id}: write the sentence with single spaces"


@needs_node
def test_spec_map_ids_are_the_ids_of_the_engine_tests(reference_run) -> None:
    _code, results, _out = reference_run
    assert {n for n in results if not n.startswith("estimator.")} == set(spec_map())


def test_estimator_tests_are_not_in_the_spec_map() -> None:
    assert not any(test_id.startswith("estimator.") for test_id in spec_map())


# ---------------------------------------------------------------------------------- the architecture check
def counts(folder: Path) -> tuple[int, int, int, int]:
    result = arch_check.check(folder)
    return result["a"], result["b"], result["c"], result["violations"]


@needs_node
def test_arch_check_gives_zero_on_the_clean_fixture() -> None:
    assert counts(FIXTURES / "clean") == (0, 0, 0, 0)


@needs_node
@pytest.mark.parametrize(
    "name,expected",
    [
        ("planted-browser-name", (1, 0, 0, 1)),
        ("planted-import-fails", (0, 1, 0, 1)),
        ("planted-key-code", (0, 0, 1, 1)),
        ("planted-key-code-html", (0, 0, 1, 1)),
    ],
)
def test_arch_check_gives_one_per_planted_kind(name: str, expected: tuple[int, int, int, int]) -> None:
    assert counts(FIXTURES / name) == expected


@needs_node
def test_arch_check_follows_imports_and_names_the_deep_file() -> None:
    result = arch_check.check(FIXTURES / "planted-browser-name")
    assert result["a_files"] == {"src/deep.js": 1}
    assert result["engine_files"] == ["src/deep.js", "src/engine.js", "src/mid.js"]


@needs_node
def test_arch_check_skips_comments_and_the_arms_own_test_files() -> None:
    result = arch_check.check(FIXTURES / "clean")
    assert result["c_files"] == [] and "tests/own.test.mjs" not in result["engine_files"]
    assert arch_check.count_browser_names(arch_check.strip_js_comments("// window\n/* document */ const x = 1;")) == 0
    assert arch_check.count_browser_names("const s = 'a // window'; document.x") == 2


@needs_node
def test_arch_check_counts_a_project_without_an_engine_as_one_violation(tmp_path: Path) -> None:
    assert counts(tmp_path) == (0, 1, 0, 1)


def test_arch_check_cli_exit_codes(tmp_path: Path) -> None:
    script = str(BUILD / "arch_check.py")
    missing = subprocess.run([sys.executable, script, str(tmp_path / "nope")], capture_output=True, text=True)
    assert missing.returncode == 2 and "not a folder" in missing.stderr
    usage = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert usage.returncode == 2
    if NODE:
        ok = subprocess.run([sys.executable, script, str(FIXTURES / "clean")], capture_output=True, text=True)
        assert ok.returncode == 0 and json.loads(ok.stdout)["violations"] == 0


@needs_node
def test_arch_check_gives_zero_on_the_reference() -> None:
    result = arch_check.check(REFERENCE)
    assert result["violations"] == 0, result
    assert "src/keys.js" in result["engine_files"] and "src/audio.js" not in result["engine_files"]


# ------------------------------------------------------------------------------------------- the reference
def test_reference_page_has_every_step_1_test_id_and_event() -> None:
    page = (REFERENCE / "index.html").read_text(encoding="utf-8")
    ids = ["start-audio", "fretboard", "chord-name"] + [f"string-{n}" for n in range(1, 7)] + [f"dot-{n}" for n in range(1, 7)]
    for test_id in ids:
        assert f'data-testid="{test_id}"' in page, test_id
    assert 'src="src/app.js"' in page and 'type="module"' in page
    app = (REFERENCE / "src" / "app.js").read_text(encoding="utf-8")
    assert '"guitar:note"' in app and '"guitar:mute"' in app and "data-testid" in app


def test_reference_has_no_packages_and_no_build() -> None:
    assert not (REFERENCE / "node_modules").exists()
    assert not (REFERENCE / "package.json").exists()
    for path in REFERENCE.rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert "require(" not in text and "http://" not in text and "https://" not in text, path.name
