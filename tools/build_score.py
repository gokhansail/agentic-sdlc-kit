"""Scores a guitar app folder against the hidden tests of the build bench at a step (plan 5.1, 5.3, D13).

    python tools/build_score.py --root <folder> --step N|handoff --harness <dir>
        [--baseline <score.json> ...] [--fake-key-file <file>] [--out <file>] [--prompt-out <file>]
        [--workers N] [--engine-timeout SECONDS]

What it does:
 1. hashes the folder (without `.git`) and copies it, without `.git`, to a temporary folder in the system
    temp folder; the scored folder is never written to;
 2. runs the engine test files of the steps up to N (and the handoff file at `handoff`) with
    `node --test --test-reporter=tap --test-timeout=60000`, GUITAR_ROOT at the copy, one process per file;
    the estimator tests (pitch.test.mjs, decay.test.mjs) run too and must pass, else exit 2;
 3. runs bench/build/run_browser.py on the copy at the same step, with a time limit of
    ceil(browser tests / workers) x 130 s + 120 s;
 4. runs bench/build/arch_check.py on the copy; deletes the copy; hashes the folder again (changed: exit 2).
A selected ID with no result is "load error", except in an engine file that was stopped at the time limit
(an endless loop): its IDs without a result are "fail". Results are filtered to the selected IDs (the rule of
run_browser.selected_ids: step up to N, not retired at N).

--baseline files are earlier step-end scores. An ID that passed in any of them and does not pass now is a
regression. A baseline of the same or a later step is refused (exit 2).
--fake-key-file: its content is GUITAR_FAKE_KEY in the browser run only. The key is removed from everything
this script prints or writes.
The fix prompt is bench/build/fix-template.txt filled with the distinct sentences of the failing selected IDs,
in spec-map order, at most 5; it goes to --prompt-out only, and only when a selected test fails.
--out and --prompt-out inside the repository, or inside the scored folder, are refused (exit 2).

stdout (and --out) is one JSON object. Exit codes: 0 every selected test passes and no regression; 1 a test
failed or did not load, or a regression; 2 harness error (bad argument, estimator test failed, no node, no
harness, folder changed, browser run failed to run).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence

KIT_ROOT = Path(__file__).resolve().parent.parent
BUILD = KIT_ROOT / "bench" / "build"
HIDDEN = BUILD / "hidden"
ENGINE_DIR = HIDDEN / "engine"
HANDOFF_FILE = HIDDEN / "handoff" / "song.test.mjs"
ESTIMATOR_FILES = [ENGINE_DIR / "pitch.test.mjs", ENGINE_DIR / "decay.test.mjs"]
SPEC_MAP = BUILD / "spec-map.json"
FIX_TEMPLATE = BUILD / "fix-template.txt"
ENGINE_TEST_TIMEOUT_MS = 60000
ENGINE_TOTAL_SECONDS = 600
BROWSER_SECONDS_PER_TEST = 130
BROWSER_SECONDS_EXTRA = 120
MAX_SENTENCES = 5
KINDS = ("engine", "browser")
OUTCOMES = ("pass", "fail", "load error")
TAP_LINE = re.compile(r"^(not )?ok \d+ - (\S+)")

_spec = importlib.util.spec_from_file_location("run_browser", BUILD / "run_browser.py")
run_browser = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["run_browser"] = run_browser
_spec.loader.exec_module(run_browser)  # type: ignore[union-attr]
_arch_spec = importlib.util.spec_from_file_location("arch_check", BUILD / "arch_check.py")
arch_check = importlib.util.module_from_spec(_arch_spec)  # type: ignore[arg-type]
sys.modules["arch_check"] = arch_check
_arch_spec.loader.exec_module(arch_check)  # type: ignore[union-attr]


class ScoreError(Exception):
    """The run could not be made or the harness is broken (exit 2)."""


# --------------------------------------------------------------------------------------------- hashing
def tree_hash(root: Path) -> str:
    """The run_browser.tree_hash rule, without any `.git` folder or file."""
    digest = hashlib.sha256()
    files = [p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts]
    for path in sorted(files):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ------------------------------------------------------------------------------------------- selection
def spec_map() -> dict[str, dict]:
    return json.loads(SPEC_MAP.read_text(encoding="utf-8"))


def selected_engine_ids(order: int) -> list[str]:
    """The run_browser.selected_ids rule for the engine IDs, in map order."""
    chosen = []
    for test_id, entry in spec_map().items():
        if ".engine." not in test_id or run_browser.step_order(entry["step"]) > order:
            continue
        if entry["retired_at"] is not None and entry["retired_at"] <= order:
            continue
        chosen.append(test_id)
    return chosen


def engine_file_of(prefix: str) -> Path:
    return HANDOFF_FILE if prefix == "handoff" else ENGINE_DIR / f"step{prefix[1:]}.test.mjs"


def engine_files(ids: list[str]) -> list[Path]:
    return [engine_file_of(prefix) for prefix in sorted({test_id.split(".")[0] for test_id in ids}, key=lambda prefix: run_browser.step_order("handoff" if prefix == "handoff" else prefix[1:]))]


def browser_timeout(count: int, workers: int) -> int:
    return math.ceil(count / workers) * BROWSER_SECONDS_PER_TEST + BROWSER_SECONDS_EXTRA


# ----------------------------------------------------------------------------------------- processes
def kill_tree(process: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)
    else:
        try:
            os.killpg(process.pid, 9)
        except OSError:
            process.kill()


def run_limited(command: list[str], env: dict[str, str], cwd: Path, timeout: float) -> tuple[bool, str, str, int | None]:
    """(timed_out, stdout, stderr, returncode). On a timeout the whole process tree is killed: a node test
    runner starts one child per file, and a child in an endless loop outlives its parent."""
    process = subprocess.Popen(
        command, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", start_new_session=(os.name != "nt"),
    )
    try:
        out, err = process.communicate(timeout=timeout)
        return False, out or "", err or "", process.returncode
    except subprocess.TimeoutExpired:
        kill_tree(process)
        try:
            out, err = process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            out, err = "", ""
        return True, out or "", err or "", None


def parse_tap(stdout: str) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for line in stdout.split("\n"):
        match = TAP_LINE.match(line)
        if match:
            results[match.group(2)] = match.group(1) is None
    return results


def run_engine_file(node: str, path: Path, copy: Path, timeout: int) -> tuple[dict[str, bool], bool]:
    env = dict(os.environ, GUITAR_ROOT=str(copy))
    env.pop("GUITAR_FAKE_KEY", None)
    command = [node, "--test", "--test-reporter=tap", f"--test-timeout={ENGINE_TEST_TIMEOUT_MS}", str(path)]
    timed_out, out, _err, _code = run_limited(command, env, copy, timeout)
    return parse_tap(out), timed_out


def run_engine(node: str, ids: list[str], copy: Path, timeout: int) -> tuple[dict[str, str], dict[str, str]]:
    """Outcome per selected engine ID and a note per ID that did not pass (a stopped file)."""
    files = engine_files(ids)
    jobs = [*files, *ESTIMATOR_FILES]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        done = list(pool.map(lambda path: run_engine_file(node, path, copy, timeout), jobs))
    by_file = dict(zip(jobs, done))
    for path in ESTIMATOR_FILES:
        results, timed_out = by_file[path]
        if timed_out or not results or not all(results.values()):
            raise ScoreError(f"estimator test file {path.name} did not pass: this is a harness error")
    outcomes: dict[str, str] = {}
    notes: dict[str, str] = {}
    for test_id in ids:
        path = engine_file_of(test_id.split(".")[0])
        results, timed_out = by_file[path]
        if test_id in results:
            outcomes[test_id] = "pass" if results[test_id] else "fail"
        elif timed_out:
            outcomes[test_id] = "fail"
            notes[test_id] = f"the test file did not finish in {timeout} s"
        else:
            outcomes[test_id] = "load error"
    return outcomes, notes


def run_browser_tests(node: str, copy: Path, harness: Path, step: str, ids: list[str], workers: int, key: str | None) -> dict:
    timeout = browser_timeout(len(ids), workers)
    env = dict(os.environ)
    env.pop("GUITAR_FAKE_KEY", None)
    if key is not None:
        env["GUITAR_FAKE_KEY"] = key
    command = [
        sys.executable, str(BUILD / "run_browser.py"), "--root", str(copy), "--harness", str(harness),
        "--step", step, "--workers", str(workers), "--timeout", str(timeout),
    ]
    timed_out, out, err, code = run_limited(command, env, KIT_ROOT, timeout + 60)
    if timed_out:
        raise ScoreError(f"the browser run did not end in {timeout + 60} s")
    if code == 2 or not out.strip():
        raise ScoreError(f"the browser run failed to run: {err.strip()[-300:]}")
    try:
        return json.loads(out)
    except ValueError as error:
        raise ScoreError("the browser run gave no JSON") from error


# ----------------------------------------------------------------------------------- results and prompt
def totals_of(outcomes: dict[str, str]) -> dict[str, int]:
    totals = {name: 0 for name in OUTCOMES}
    for outcome in outcomes.values():
        totals[outcome] += 1
    totals["total"] = len(outcomes)
    return totals


def load_baselines(paths: Sequence[str], order: int) -> dict[str, str]:
    """ID -> baseline file name for every ID that passed in a baseline of an earlier step."""
    passed: dict[str, str] = {}
    for text in paths:
        path = Path(text)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            base_order = run_browser.step_order(data["step"])
            tests = data["tests"]
            if not isinstance(tests, dict):
                raise TypeError
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ScoreError(f"--baseline is not a score file: {path.name}") from error
        if base_order >= order:
            raise ScoreError(f"--baseline {path.name} is of step {data['step']}, not earlier than this step")
        for test_id, outcome in tests.items():
            if outcome == "pass":
                passed.setdefault(test_id, path.name)
    return passed


def fix_prompt(sentences: list[str]) -> str:
    """The template with its `"<sentence 1>" "<sentence 2>" ...` part replaced by the quoted sentences."""
    template = FIX_TEMPLATE.read_text(encoding="utf-8")
    match = re.fullmatch(r'(.*?)"<sentence 1>"\s+"<sentence 2>"\s+\.\.\.\s+(.*)', template, re.DOTALL)
    if match is None:
        raise ScoreError("fix-template.txt does not have the form with <sentence 1> <sentence 2> ...")
    return match.group(1) + " ".join(f'"{sentence}"' for sentence in sentences) + " " + match.group(2)


def check_out_path(value: str | None, flag: str, root: Path) -> Path | None:
    if value is None:
        return None
    resolved = Path(value).resolve()
    for name, base in (("the repository", KIT_ROOT), ("the scored folder", root)):
        base = base.resolve()
        if resolved == base or base in resolved.parents:
            raise ScoreError(f"{flag} is inside {name}: write it outside")
    if resolved.is_dir():
        raise ScoreError(f"{flag} is a folder")
    return resolved


def node_version(node: str) -> str:
    done = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=30)
    return done.stdout.strip()


def playwright_version(harness: Path) -> str:
    package = harness / "node_modules" / "@playwright" / "test" / "package.json"
    try:
        return str(json.loads(package.read_text(encoding="utf-8"))["version"])
    except (OSError, ValueError, KeyError) as error:
        raise ScoreError("--harness has no node_modules/@playwright/test") from error


def score(args: argparse.Namespace) -> tuple[dict, str | None]:
    root = Path(args.root)
    harness = Path(args.harness)
    if not root.is_dir():
        raise ScoreError(f"--root is not a folder: {root}")
    if args.workers < 1 or args.engine_timeout < 1:
        raise ScoreError("--workers and --engine-timeout must be positive")
    try:
        order = run_browser.parse_step(args.step)
    except run_browser.RunnerError as error:
        raise ScoreError(str(error)) from error
    root = root.resolve()
    out_path = check_out_path(args.out, "--out", root)
    prompt_path = check_out_path(args.prompt_out, "--prompt-out", root)
    baseline = load_baselines(args.baseline, order)
    key = None
    if args.fake_key_file:
        try:
            key = Path(args.fake_key_file).read_text(encoding="utf-8").strip()
        except OSError as error:
            raise ScoreError("--fake-key-file cannot be read") from error
        if not key:
            raise ScoreError("--fake-key-file is empty")
    node = shutil.which("node")
    if node is None:
        raise ScoreError("node is not on PATH")
    version = playwright_version(harness)

    engine_ids = selected_engine_ids(order)
    browser_ids = run_browser.selected_ids(order)
    step = "handoff" if order == run_browser.HANDOFF_ORDER else str(order)

    before = tree_hash(root)
    temp = Path(tempfile.mkdtemp(prefix="build-score-"))
    try:
        copy = temp / "project"
        shutil.copytree(root, copy, ignore=shutil.ignore_patterns(".git"))
        engine, notes = run_engine(node, engine_ids, copy, args.engine_timeout)
        browser = run_browser_tests(node, copy, harness, step, browser_ids, args.workers, key)
        arch = arch_check.check(copy)
    except arch_check.ArchCheckError as error:
        raise ScoreError(f"arch_check: {error}") from error
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    after = tree_hash(root)
    if after != before:
        raise ScoreError("the scored folder changed during the run")

    browser_tests = {test_id: browser.get("tests", {}).get(test_id, "load error") for test_id in browser_ids}
    tests = {test_id: {**engine, **browser_tests}[test_id] for test_id in spec_map() if test_id in engine or test_id in browser_tests}
    details = {**notes, **{k: v for k, v in browser.get("details", {}).items() if k in browser_tests}}
    regressions = [test_id for test_id in tests if test_id in baseline and tests[test_id] != "pass"]
    kinds = {
        "engine": totals_of({k: v for k, v in tests.items() if ".engine." in k}),
        "browser": totals_of({k: v for k, v in tests.items() if ".browser." in k}),
    }
    overall = totals_of(tests)
    failing = [test_id for test_id, outcome in tests.items() if outcome != "pass"]
    mapped = spec_map()
    sentences: list[str] = []
    for test_id in failing:
        sentence = mapped[test_id]["sentence"]
        if sentence not in sentences:
            sentences.append(sentence)
    prompt = fix_prompt(sentences[:MAX_SENTENCES]) if failing else None

    result = {
        "step": "handoff" if order == run_browser.HANDOFF_ORDER else order,
        "folder_hash": before,
        "tests": tests,
        "details": dict(sorted(details.items())),
        "totals": {**kinds, "all": overall},
        "share": round(overall["pass"] / overall["total"], 4) if overall["total"] else 0.0,
        "regressions": regressions,
        "regression_baselines": {test_id: baseline[test_id] for test_id in regressions},
        "arch": {name: arch[name] for name in ("a", "b", "c", "violations")},
        "arch_detail": {"a_files": arch["a_files"], "c_files": arch["c_files"], "b_error": arch["b_error"]},
        "spec_map_sha256": file_hash(SPEC_MAP),
        "hidden_tree_sha256": tree_hash(HIDDEN),
        "node_version": node_version(node),
        "playwright_version": version,
    }
    text = redact(json.dumps(result, indent=2, sort_keys=False), key) + "\n"
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8", newline="\n")
    if prompt is not None and prompt_path is not None:
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(redact(prompt, key), encoding="utf-8", newline="\n")
    result["_text"] = text  # type: ignore[assignment]
    return result, prompt


def redact(text: str, key: str | None) -> str:
    """The key never reaches an output. JSON writes a key with escapes, so both spellings are replaced."""
    if not key:
        return text
    return text.replace(key, "<key>").replace(json.dumps(key)[1:-1], "<key>")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_score.py", description="Score a guitar app folder at a step of the build bench.")
    parser.add_argument("--root", required=True, help="the arm folder or a stored snapshot")
    parser.add_argument("--step", required=True, help="1 to 8 or handoff")
    parser.add_argument("--harness", required=True, help="harness folder with node_modules/@playwright/test")
    parser.add_argument("--baseline", action="append", default=[], help="score JSON of an earlier step end (repeatable)")
    parser.add_argument("--fake-key-file", default=None, help="file with the key of the share tests (GUITAR_FAKE_KEY)")
    parser.add_argument("--out", default=None, help="score JSON file, outside the repository")
    parser.add_argument("--prompt-out", default=None, help="fix prompt file, outside the repository")
    parser.add_argument("--workers", type=int, default=4, help="browser workers")
    parser.add_argument("--engine-timeout", type=int, default=ENGINE_TOTAL_SECONDS, help="seconds for each engine test file")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        result, _prompt = score(args)
    except ScoreError as error:
        print(f"build_score: {error}", file=sys.stderr)
        return 2
    text = result.pop("_text")  # type: ignore[misc]
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.flush()
    totals = result["totals"]["all"]
    print(
        f"score (step {result['step']}): {totals['pass']} pass, {totals['fail']} fail, {totals['load error']} load error, "
        f"of {totals['total']}; {len(result['regressions'])} regressions; arch {result['arch']['violations']}",
        file=sys.stderr,
    )
    return 0 if totals["pass"] == totals["total"] and not result["regressions"] else 1


if __name__ == "__main__":
    sys.exit(main())
