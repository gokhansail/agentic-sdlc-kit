"""Runs the hidden browser tests of the build bench against a project folder.

    python bench/build/run_browser.py --root <project> --harness <dir> [--step N|handoff] [--workers N]

<project> is a folder with the guitar app (index.html at its root). <dir> is the harness folder: it holds
node_modules with @playwright/test (see harness/package.json) and a browsers folder. The harness is not
part of the repository; its path comes only from this argument.

What it does:
 1. hashes the project folder;
 2. copies the specs of the chosen steps, their helper and the Playwright config from hidden/browser/ into
    a temporary folder under the harness (the specs import @playwright/test, which resolves from there);
 3. serves the project folder read-only on a free 127.0.0.1 port, with .js and .mjs sent as text/javascript
    (a Windows registry may map .js to another type, which breaks module loading);
 4. runs the Playwright CLI from the harness (PLAYWRIGHT_BROWSERS_PATH set to <dir>/browsers) and reads its
    JSON report;
 5. deletes the temporary folder and hashes the project folder again.
The project folder is never written to. GUITAR_FAKE_KEY, when set in the environment, is the key the share
tests expect in the Authorization header; the default is the literal {FAKE_KEY}.

--step N (1 to 8) or handoff (default) selects the tests of that step and every earlier step that the step
does not retire (spec-map.json, retired_at): the set a scorer runs at the end of step N. At the default
(handoff) the retired tests are left out.

stdout is one JSON object: step, project_hash, tests (ID -> "pass" | "fail" | "load error"), details (ID ->
first error line of a failure, harness path replaced by <run>) and totals. stderr gets one summary line.
Exit codes: 0 every selected test passed; 1 at least one test failed or did not load; 2 the run could not be
made (bad argument, no node, no Playwright in the harness, no report, or the project folder changed).
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

BUILD = Path(__file__).resolve().parent
BROWSER_DIR = BUILD / "hidden" / "browser"
SPEC_MAP = BUILD / "spec-map.json"
HANDOFF_ORDER = 9
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class RunnerError(Exception):
    """The run could not be made (exit 2)."""


def step_order(step: int | str) -> int:
    return HANDOFF_ORDER if step == "handoff" else int(step)


def parse_step(text: str) -> int:
    if text == "handoff":
        return HANDOFF_ORDER
    if text.isdigit() and 1 <= int(text) <= 8:
        return int(text)
    raise RunnerError(f"--step must be 1 to 8 or handoff, got {text!r}")


def selected_ids(order: int) -> list[str]:
    """Browser test IDs of the steps up to `order` that the step does not retire, in map order."""
    mapped = json.loads(SPEC_MAP.read_text(encoding="utf-8"))
    chosen = []
    for test_id, entry in mapped.items():
        if ".browser." not in test_id or step_order(entry["step"]) > order:
            continue
        if entry["retired_at"] is not None and entry["retired_at"] <= order:
            continue
        chosen.append(test_id)
    return chosen


def spec_names(ids: list[str]) -> list[str]:
    """Spec files that hold the IDs: s3.browser.x is in step3.spec.mjs, handoff.browser.x in handoff.spec.mjs."""
    prefixes = sorted({test_id.split(".")[0] for test_id in ids})
    return [f"{'handoff' if p == 'handoff' else 'step' + p[1:]}.spec.mjs" for p in prefixes]


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


class StaticHandler(http.server.SimpleHTTPRequestHandler):
    """Serves files only: a folder without index.html is a 404, not a listing."""

    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript", ".mjs": "text/javascript"}

    def log_message(self, *args: object) -> None:
        pass

    def list_directory(self, path: object):  # type: ignore[override]
        self.send_error(404, "No listing")
        return None

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class StaticServer(http.server.ThreadingHTTPServer):
    # The default backlog of 5 drops connections when several browsers load a module graph at once, and a
    # dropped module request breaks the whole page without any message.
    request_queue_size = 256


def serve(root: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    handler = functools.partial(StaticHandler, directory=str(root))
    server = StaticServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def first_error_line(error: dict, run_dir: Path) -> str:
    message = ANSI.sub("", str(error.get("message") or error.get("value") or "")).replace(str(run_dir), "<run>")
    lines = [line.strip() for line in message.split("\n") if line.strip()]
    return " | ".join(lines[:2])[:300]


def collect(suite: dict, found: dict[str, tuple[str, str]], run_dir: Path) -> None:
    for spec in suite.get("specs", []):
        tests = spec.get("tests", [])
        passed = bool(spec.get("ok")) and bool(tests) and all(t.get("status") != "skipped" for t in tests)
        detail = ""
        if not passed:
            for test in tests:
                for result in test.get("results", []):
                    if result.get("error"):
                        detail = first_error_line(result["error"], run_dir)
        found[spec["title"]] = ("pass" if passed else "fail", detail)
    for child in suite.get("suites", []):
        collect(child, found, run_dir)


def run(root: Path, harness: Path, order: int, workers: int, timeout: int) -> dict:
    if not root.is_dir():
        raise RunnerError(f"--root is not a folder: {root}")
    cli = harness / "node_modules" / "@playwright" / "test" / "cli.js"
    if not cli.is_file():
        raise RunnerError("--harness has no node_modules/@playwright/test (see harness/package.json)")
    node = shutil.which("node")
    if node is None:
        raise RunnerError("node is not on PATH")
    ids = selected_ids(order)
    if not ids:
        raise RunnerError("no browser test is selected")

    before = tree_hash(root)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=str(harness)))
    server = None
    try:
        for name in [*spec_names(ids), "helpers.mjs", "playwright.config.mjs"]:
            shutil.copy(BROWSER_DIR / name, run_dir / name)
        server, port = serve(root)
        env = dict(os.environ)
        env.update(GUITAR_URL=f"http://127.0.0.1:{port}", GUITAR_REPORT=str(run_dir / "report.json"), GUITAR_WORKERS=str(workers), NO_COLOR="1")
        if (harness / "browsers").is_dir():
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(harness / "browsers")
        try:
            done = subprocess.run(
                [node, str(cli), "test", "--config", str(run_dir / "playwright.config.mjs")],
                cwd=str(run_dir), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise RunnerError(f"Playwright did not finish in {timeout} s") from exc
        report_file = run_dir / "report.json"
        if not report_file.is_file():
            tail = ANSI.sub("", (done.stderr or done.stdout)[-600:]).replace(str(run_dir), "<run>")
            raise RunnerError(f"Playwright wrote no report (exit {done.returncode}): {tail}")
        report = json.loads(report_file.read_text(encoding="utf-8"))
        found: dict[str, tuple[str, str]] = {}
        for suite in report.get("suites", []):
            collect(suite, found, run_dir)
        load_note = " | ".join(first_error_line(e, run_dir) for e in report.get("errors", []))[:300]
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        shutil.rmtree(run_dir, ignore_errors=True)

    after = tree_hash(root)
    if after != before:
        raise RunnerError("the project folder changed during the run")
    tests = {test_id: found[test_id][0] if test_id in found else "load error" for test_id in ids}
    details = {test_id: (found[test_id][1] if test_id in found else load_note) for test_id in ids if tests[test_id] != "pass"}
    totals = {"pass": 0, "fail": 0, "load error": 0}
    for outcome in tests.values():
        totals[outcome] += 1
    totals["total"] = len(tests)
    return {"step": "handoff" if order == HANDOFF_ORDER else order, "project_hash": after, "tests": tests, "details": {k: v for k, v in details.items() if v}, "totals": totals}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the hidden browser tests of the build bench against a project folder.")
    parser.add_argument("--root", required=True, help="project folder with index.html at its root")
    parser.add_argument("--harness", required=True, help="harness folder with node_modules/@playwright/test")
    parser.add_argument("--step", default="handoff", help="1 to 8 or handoff (default): tests of that step and earlier, not retired")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=900, help="seconds for the whole Playwright run")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        result = run(Path(args.root), Path(args.harness), parse_step(args.step), args.workers, args.timeout)
    except RunnerError as error:
        print(f"run_browser: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    totals = result["totals"]
    print(f"browser tests (step {result['step']}): {totals['pass']} pass, {totals['fail']} fail, {totals['load error']} load error, of {totals['total']}", file=sys.stderr)
    return 0 if totals["pass"] == totals["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
