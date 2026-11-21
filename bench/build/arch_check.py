"""Architecture check of the build bench (plan section 5.4).

The step 1 rule: the sound engine is pure. `src/engine.js` and every file it imports use no browser
API, and key codes appear only in the engine's key map. Counts for one project folder:

  a  occurrences of the listed browser names in `src/engine.js` and every file it imports
     (static relative imports followed), comments stripped;
  b  1 when `src/engine.js` does not import in Node without error, else 0;
  c  files outside the engine import graph that contain a key-code string literal, comments stripped.

violations = a + b + c. Usage: python arch_check.py <project folder>   (prints JSON, exit 0; exit 2 on
a missing folder or a missing node). Python 3.10, standard library only; the folder is only read.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

BROWSER_NAMES = (
    "window", "document", "navigator", "AudioContext", "OfflineAudioContext",
    "requestAnimationFrame", "localStorage",
)
KEY_CODE = r"(?:Key[A-Z]|Space|Period|Semicolon|Quote)"
KEY_LITERAL = re.compile(r"""(["'`])""" + KEY_CODE + r"\1")
KEY_AS_OBJECT_KEY = re.compile(r"\b" + KEY_CODE + r"\s*:")
BROWSER_NAME = re.compile(r"\b(" + "|".join(BROWSER_NAMES) + r")\b")
STATIC_IMPORT = re.compile(r"""\bimport\b\s*(?:[^'";()]*?\bfrom\s*)?(["'])([^"']+)\1""")
STATIC_REEXPORT = re.compile(r"""\bexport\b\s*(?:\*(?:\s+as\s+\w+)?|\{[^}]*\})\s*from\s*(["'])([^"']+)\1""")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
SCRIPT_BODY = re.compile(r"(<script\b[^>]*>)(.*?)(</script>)", re.DOTALL | re.IGNORECASE)
CODE_SUFFIXES = {".js", ".mjs", ".cjs"}
PAGE_SUFFIXES = {".html", ".htm"}
SKIP_DIRS = {"node_modules", ".git"}
TEST_DIRS = {"test", "tests", "__tests__"}
TEST_NAME = re.compile(r"\.(test|spec)\.[cm]?js$")
NODE_TIMEOUT_SECONDS = 30


class ArchCheckError(Exception):
    pass


def strip_js_comments(source: str) -> str:
    """Remove // and /* */ comments; string and template literals are kept as they are."""
    out: list[str] = []
    i, n = 0, len(source)
    quote = ""
    while i < n:
        ch = source[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(source[i + 1])
                i += 2
                continue
            if ch == quote or (ch == "\n" and quote != "`"):
                quote = ""
            i += 1
            continue
        pair = source[i:i + 2]
        if pair == "//":
            while i < n and source[i] != "\n":
                i += 1
        elif pair == "/*":
            end = source.find("*/", i + 2)
            i = n if end < 0 else end + 2
            out.append(" ")
        else:
            if ch in "\"'`":
                quote = ch
            out.append(ch)
            i += 1
    return "".join(out)


def _shown(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _relative_imports(path: Path, code: str) -> list[Path]:
    found: list[Path] = []
    for pattern in (STATIC_IMPORT, STATIC_REEXPORT):
        for match in pattern.finditer(code):
            spec = match.group(2)
            if spec.startswith("./") or spec.startswith("../"):
                target = (path.parent / spec).resolve()
                if target.is_file():
                    found.append(target)
    return found


def engine_graph(root: Path) -> dict[Path, str]:
    """The engine entry and everything it imports statically and relatively, with comment-free code."""
    entry = (root / "src" / "engine.js").resolve()
    graph: dict[Path, str] = {}
    pending = [entry] if entry.is_file() else []
    while pending:
        path = pending.pop()
        if path in graph:
            continue
        code = strip_js_comments(_read(path))
        graph[path] = code
        pending.extend(_relative_imports(path, code))
    return graph


def count_browser_names(code: str) -> int:
    return len(BROWSER_NAME.findall(code))


def engine_imports_in_node(root: Path) -> tuple[bool, str]:
    entry = root / "src" / "engine.js"
    if not entry.is_file():
        return False, "src/engine.js is missing"
    node = shutil.which("node")
    if node is None:
        raise ArchCheckError("node was not found on PATH")
    try:
        done = subprocess.run(
            [node, "--input-type=module", "-e", "await import(process.argv[1])", entry.resolve().as_uri()],
            capture_output=True, text=True, timeout=NODE_TIMEOUT_SECONDS, cwd=str(root),
        )
    except subprocess.TimeoutExpired:
        return False, "import timed out"
    if done.returncode == 0:
        return True, ""
    lines = [line for line in done.stderr.splitlines() if line.strip()]
    error = next((line for line in lines if re.match(r"\s*\w*Error\b", line)), lines[0] if lines else "node failed")
    return False, error.strip()[:300]


def _is_test_file(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return bool(TEST_NAME.search(path.name)) or any(part in TEST_DIRS for part in parts[:-1])


def has_key_code_literal(path: Path) -> bool:
    text = _read(path)
    if path.suffix.lower() in PAGE_SUFFIXES:
        text = HTML_COMMENT.sub("", text)
        scripts = [strip_js_comments(m.group(2)) for m in SCRIPT_BODY.finditer(text)]
        text = SCRIPT_BODY.sub(lambda m: m.group(1) + m.group(3), text)
        return bool(KEY_LITERAL.search(text)) or any(KEY_LITERAL.search(s) or KEY_AS_OBJECT_KEY.search(s) for s in scripts)
    code = strip_js_comments(text)
    return bool(KEY_LITERAL.search(code) or KEY_AS_OBJECT_KEY.search(code))


def key_code_files(root: Path, graph: dict[Path, str]) -> list[str]:
    hits: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in CODE_SUFFIXES | PAGE_SUFFIXES:
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or path.resolve() in graph or _is_test_file(path, root):
            continue
        if has_key_code_literal(path):
            hits.append(rel.as_posix())
    return hits


def check(root: Path) -> dict:
    root = Path(root).resolve()
    if not root.is_dir():
        raise ArchCheckError(f"not a folder: {root}")
    graph = engine_graph(root)
    a_files = {}
    for path, code in graph.items():
        count = count_browser_names(code)
        if count:
            a_files[_shown(path, root)] = count
    a = sum(a_files.values())
    imported, error = engine_imports_in_node(root)
    b = 0 if imported else 1
    c_files = key_code_files(root, graph)
    return {
        "a": a, "b": b, "c": len(c_files), "violations": a + b + len(c_files),
        "a_files": dict(sorted(a_files.items())), "c_files": c_files, "b_error": error,
        "engine_files": sorted(_shown(p, root) for p in graph),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python arch_check.py <project folder>", file=sys.stderr)
        return 2
    try:
        result = check(Path(argv[1]))
    except ArchCheckError as error:
        print(f"arch_check: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
