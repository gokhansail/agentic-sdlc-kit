"""Tests for the build bench files of T-64a and T-64c (bench/build/): frozen texts, spec map, engine tests
of steps 1 to 7 and of the handoff, reference guitar, architecture check. No model is called and nothing
is downloaded; the engine tests need Node (`node --test`) and are skipped when `node` is not on PATH.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
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
ENGINE_DIR = BUILD / "hidden" / "engine"
HANDOFF_DIR = BUILD / "hidden" / "handoff"
# Test file of each step; the key is the step as spec-map.json writes it and as the test IDs prefix it.
STEP_FILES: dict[int | str, Path] = {n: ENGINE_DIR / f"step{n}.test.mjs" for n in range(1, 8)}
STEP_FILES["handoff"] = HANDOFF_DIR / "song.test.mjs"
# Known-answer tests of the helpers (pitch estimator, decay measure); they need no project folder.
ESTIMATOR_FILES = [ENGINE_DIR / "pitch.test.mjs", ENGINE_DIR / "decay.test.mjs"]
ENGINE_TESTS = [*STEP_FILES.values(), *ESTIMATOR_FILES]
ESTIMATOR_TEST_COUNT = 8
SPECTRUM_RETIRED_AT = 6
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
    cases.append(("prompts/handoff.txt", "handoff", block_after("- Prompt:")))
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
    # the handoff prompt is run headless and typed by nobody, so it is not a human-turn text
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
    assert len(results) == len(spec_map()) + ESTIMATOR_TEST_COUNT
    assert sum(name.startswith("estimator.") for name in results) == ESTIMATOR_TEST_COUNT


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
def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def frozen_text(name: str) -> str:
    return squash((BUILD / name).read_text(encoding="utf-8"))


def step_of(test_id: str) -> int | str:
    prefix = test_id.split(".")[0]
    return "handoff" if prefix == "handoff" else int(prefix[1:])


def sentence_sources(test_id: str, step: int | str) -> list[str]:
    """Texts a test's sentence may come from: SPEC.md and the prompt of its own step. The tempo clamp tests of
    step 7 and the handoff belong to their step but quote the step 5 prompt, where the decision was said."""
    own = "prompts/handoff.txt" if step == "handoff" else f"prompts/step-{step}.txt"
    sources = ["SPEC.md", own]
    if ".clamp-" in test_id or test_id.endswith(".clamp"):
        sources.append("prompts/step-5.txt")
    return [frozen_text(name) for name in sources]


def test_spec_map_entries_have_a_step_a_retire_step_and_a_verbatim_sentence() -> None:
    mapped = spec_map()
    assert mapped
    for test_id, entry in mapped.items():
        assert set(entry) == {"step", "sentence", "retired_at"}, test_id
        assert entry["step"] == step_of(test_id), f"{test_id}: step {entry['step']!r} does not match the ID"
        spectrum = ".spectrum-" in test_id
        assert entry["retired_at"] == (SPECTRUM_RETIRED_AT if spectrum else None), f"{test_id}: retired_at {entry['retired_at']!r}"
        sentence = squash(entry["sentence"])
        assert sentence == entry["sentence"], f"{test_id}: write the sentence with single spaces"
        assert any(sentence in source for source in sentence_sources(test_id, entry["step"])), (
            f"{test_id}: sentence is not in SPEC.md or the prompt of step {entry['step']}: {sentence!r}"
        )


def test_every_step_has_mapped_tests_and_the_spectrum_ones_retire_at_6() -> None:
    mapped = spec_map()
    steps = {entry["step"] for entry in mapped.values()}
    assert steps == {1, 2, 3, 4, 5, 6, 7, "handoff"}, "step 8 has no engine test"
    assert sorted(test_id for test_id, entry in mapped.items() if entry["retired_at"] is not None) == [
        "s3.engine.spectrum-peak", "s3.engine.spectrum-shape",
    ]
    for entry in mapped.values():
        assert entry["retired_at"] is None or (isinstance(entry["step"], int) and entry["retired_at"] > entry["step"])


def test_spec_map_ids_belong_to_the_file_of_their_step() -> None:
    declared = re.compile(r"""\btest\(\s*[`"']((?:s\d|handoff))\.""")
    for step, path in STEP_FILES.items():
        prefixes = set(declared.findall(path.read_text(encoding="utf-8")))
        assert prefixes == {"handoff" if step == "handoff" else f"s{step}"}, f"{path.name} holds tests of {prefixes}"
    on_disk = {p for p in [*ENGINE_DIR.glob("*.test.mjs"), *HANDOFF_DIR.glob("*.test.mjs")]}
    assert on_disk == set(ENGINE_TESTS), "a test file is not run by this suite or is missing"


# ------------------------------------------------------------------------------- the name rule per step
CAMEL_CASE = re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9]*\b")
KEY_CODE_NAME = re.compile(r"\bKey[A-Z]\b")
CALL_NAME = re.compile(r"\b([a-z][A-Za-z0-9]*)\(")
DESTRUCTURED = re.compile(r"const\s*\{([^}]*)\}\s*=\s*await\s+loadEngine\(\)")
ENGINE_MEMBER = re.compile(r"(?<![\w.])engine\.([A-Za-z_]\w*)")


def names_in(text: str) -> set[str]:
    return set(CAMEL_CASE.findall(text)) | set(KEY_CODE_NAME.findall(text)) | set(CALL_NAME.findall(text))


def allowed_names(step: int | str) -> set[str]:
    """Names SPEC.md and the prompts 1 to N give. A handoff test may use every name of every prompt."""
    names = names_in(frozen_text("SPEC.md"))
    last = 8 if step == "handoff" else int(step)
    for n in range(1, last + 1):
        names |= names_in(frozen_text(f"prompts/step-{n}.txt"))
    if step == "handoff":
        names |= names_in(frozen_text("prompts/handoff.txt"))
    return names


def name_violations(source: str, step: int | str) -> list[str]:
    """Names a test of step N uses that its texts do not give: a name that a later prompt introduces, or an
    engine export (taken from `await loadEngine()` or `engine.x`) that no text up to step N names."""
    allowed = allowed_names(step)
    every = allowed_names("handoff")
    used = names_in(source)
    exports: set[str] = set(ENGINE_MEMBER.findall(source))
    for group in DESTRUCTURED.findall(source):
        exports |= {part.split(":")[0].strip() for part in group.split(",") if part.strip()}
    return sorted(((used & every) - allowed) | (exports - allowed))


@pytest.mark.parametrize("step", list(STEP_FILES), ids=[str(step) for step in STEP_FILES])
def test_a_step_test_uses_only_names_given_up_to_its_step(step: int | str) -> None:
    source = STEP_FILES[step].read_text(encoding="utf-8")
    assert name_violations(source, step) == [], f"{STEP_FILES[step].name} uses names from later prompts"


def test_the_name_rule_catches_a_name_of_a_later_step() -> None:
    later = "const { strumSchedule } = await loadEngine();\nconst a = keyToAction('KeyY');\nspectrum(x, 44100);\n"
    assert name_violations(later, 1) == ["KeyY", "spectrum", "strumSchedule"]
    assert name_violations(later, 3) == ["KeyY"]
    assert name_violations(later, 6) == []
    assert name_violations("engine.madeUpName()", 7) == ["madeUpName"]
    assert name_violations("const { parseSong, songSchedule } = await loadEngine();", 7) == ["parseSong", "songSchedule"]
    assert name_violations("const { parseSong, songSchedule } = await loadEngine();", "handoff") == []
    assert name_violations("noteFrequency(6, 0, 'dropD'); renderPluck({ decaySeconds: 1 });", 3) == ["decaySeconds", "dropD"]


def test_allowed_names_grow_with_the_steps() -> None:
    assert {"noteFrequency", "renderPluck", "chordShape", "keyToAction"} <= allowed_names(1)
    assert "strumSchedule" not in allowed_names(1) and "strumSchedule" in allowed_names(2)
    assert {"spectrum", "detectPitch", "noteName"} <= allowed_names(3) and "detectPitch" not in allowed_names(2)
    assert "decaySeconds" in allowed_names(5) and "decaySeconds" not in allowed_names(4)
    assert "KeyY" in allowed_names(6) and "metronomeClicks" in allowed_names(7) and "metronomeClicks" not in allowed_names(6)
    assert "parseSong" not in allowed_names(7) and {"parseSong", "songSchedule"} <= allowed_names("handoff")


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
class PageParser(HTMLParser):
    """Elements of the reference page by data-testid: tag, attributes, and the option values of a select."""

    def __init__(self) -> None:
        super().__init__()
        self.elements: dict[str, tuple[str, dict[str, str | None]]] = {}
        self.options: dict[str, list[str]] = {}
        self._select: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        testid = attributes.get("data-testid")
        if testid:
            self.elements[testid] = (tag, attributes)
        if tag == "select":
            self._select = testid
            self.options[testid or ""] = []
        elif tag == "option" and self._select is not None:
            self.options[self._select].append(attributes.get("value") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "select":
            self._select = None


def reference_page() -> PageParser:
    parser = PageParser()
    parser.feed((REFERENCE / "index.html").read_text(encoding="utf-8"))
    return parser


def test_reference_page_has_every_test_id_of_the_prompts() -> None:
    page = reference_page()
    ids = (
        ["start-audio", "fretboard", "chord-name", "strum-spread", "capo", "tuning", "sustain", "strings", "pitch-readout"]
        + ["metronome", "tempo", "share", "share-code", "song-input", "song-play"]
        + [f"string-{n}" for n in range(1, 8)] + [f"dot-{n}" for n in range(1, 8)]
    )
    for test_id in ids:
        assert test_id in page.elements, test_id
    assert "spectrum" not in page.elements, "the spectrum view is removed at step 6"
    html = (REFERENCE / "index.html").read_text(encoding="utf-8")
    assert 'src="src/app.js"' in html and 'type="module"' in html and "<canvas" not in html


def test_reference_controls_have_the_values_the_prompts_name() -> None:
    page = reference_page()
    assert page.options["capo"] == [str(n) for n in range(8)]
    assert page.options["tuning"] == ["standard", "dropD", "openG"]
    assert page.options["sustain"] == ["short", "normal", "long"]
    assert page.options["strings"] == ["6", "7"]
    tag, slider = page.elements["strum-spread"]
    assert (tag, slider["type"], slider["min"], slider["max"], slider["value"]) == ("input", "range", "0", "100", "30")
    assert page.elements["tempo"][1]["type"] == "number" and page.elements["tempo"][1]["value"] == "100"
    assert page.elements["metronome"][1]["type"] == "checkbox" and page.elements["pitch-readout"][0] == "div"
    assert page.elements["dot-7"][1]["data-fret"] == "x" and "hidden" in page.elements["string-7"][1]
    assert page.elements["song-input"][1]["type"] == "text"


def test_reference_fires_the_events_and_calls_the_engine_names_of_the_prompts() -> None:
    app = (REFERENCE / "src" / "app.js").read_text(encoding="utf-8")
    for event in ["guitar:note", "guitar:mute", "guitar:stop", "guitar:click"]:
        assert f'"{event}"' in app, event
    engine = (REFERENCE / "src" / "engine.js").read_text(encoding="utf-8")
    for name in ["noteFrequency", "renderPluck", "chordShape", "keyToAction", "strumSchedule", "spectrum", "detectPitch",
                 "noteName", "metronomeClicks", "parseSong", "songSchedule"]:
        assert re.search(rf"\b{name}\b", engine), name
        assert name in allowed_names("handoff"), name


def test_reference_share_posts_the_settings_with_the_header_and_the_placeholder_key() -> None:
    share = (REFERENCE / "src" / "share.js").read_text(encoding="utf-8")
    assert '"https://share.example.invalid/v1/presets"' in share and 'method: "POST"' in share
    assert "Authorization: `Bearer ${SHARE_KEY}`" in share and 'SHARE_KEY = "{FAKE_KEY}"' in share
    app = (REFERENCE / "src" / "app.js").read_text(encoding="utf-8")
    assert re.search(r"tuning: .*\n\s*capo: .*\n\s*sustain: .*\n\s*strings: .*\n\s*tempo: ", app)


def test_reference_has_no_packages_and_no_build() -> None:
    assert not (REFERENCE / "node_modules").exists()
    assert not (REFERENCE / "package.json").exists()
    for path in REFERENCE.rglob("*.js"):
        text = path.read_text(encoding="utf-8")
        assert "require(" not in text and "http://" not in text, path.name
        # the one address in the reference is the share service of step 8, which never resolves
        urls = re.findall(r"https://[^\s\"'`]+", text)
        assert urls == ([] if path.name != "share.js" else ["https://share.example.invalid/v1/presets"]), path.name


@needs_node
def test_reference_keeps_the_architecture_rule_in_its_own_files() -> None:
    result = arch_check.check(REFERENCE)
    assert result["c_files"] == [] and result["a_files"] == {}
    for name in ["app.js", "audio.js", "share.js"]:
        assert name not in " ".join(result["engine_files"]), f"{name} must stay outside the engine graph"
    keys = (REFERENCE / "src" / "keys.js").read_text(encoding="utf-8")
    assert "KeyY: 7" in keys
