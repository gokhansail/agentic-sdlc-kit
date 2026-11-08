"""Tests for the MCP server skeleton (T-40): status, root lock, start check, no network, stdio.

Projects live in pytest temp dirs and are built from tests/fixtures/server/. Tests that need
the `mcp` package skip when it is missing, so a clone without it still runs green.
"""
from __future__ import annotations

import ast
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import main as server_main  # noqa: E402
from server.rootlock import RootLock, RootLockError  # noqa: E402
from server.status import status  # noqa: E402
from tools import scope_guard  # noqa: E402
from tools.records import read_records  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "server"
SERVER_DIR = ROOT / "server"
ENTRY = SERVER_DIR / "main.py"
TOOL_ARGS: dict[str, dict[str, Any]] = {"status": {}}  # a tool with arguments adds its entry here


def make_project(base: Path, project: str | None, contract: str | None) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    if project is not None:
        (base / ".sdlc").mkdir(exist_ok=True)
        (base / ".sdlc" / "project.md").write_bytes((FIXTURES / project).read_bytes())
    if contract is not None:
        (base / ".sdlc").mkdir(exist_ok=True)
        (base / ".sdlc" / "active-contract.md").write_bytes((FIXTURES / contract).read_bytes())
    return base


# --- status on fixture repositories --------------------------------------------------

def test_status_not_opted_in(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, None, None))
    assert got["opted_in"] is False
    assert got["guard_state"] == "not-opted-in"
    assert got["task_id"] is None and got["files_in"] == [] and got["files_out"] == []
    assert got["records"] == read_records(tmp_path)  # template defaults
    assert got["records"]["status"] == "STATUS.md"


def test_status_opted_in_without_contract(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, "project.md", None))
    assert got["opted_in"] is True
    assert got["guard_state"] == scope_guard.NO_CONTRACT
    assert got["task_id"] is None and got["files_in"] == [] and got["files_out"] == []
    assert got["broken_reason"] == ""


def test_status_with_an_active_contract(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, "project-custom.md", "contract.md"), "CLAUDE_PROJECT_DIR")
    assert got["opted_in"] is True
    assert got["guard_state"] == scope_guard.ACTIVE
    assert got["task_id"] == "T-77"
    assert got["files_in"] == ["src/a.py", "src/pkg/", "tests/a.py", "tests/b.py"]  # braces expanded as the guard does
    assert got["files_out"] == ["src/secret.py"]
    assert got["records"]["status"] == "docs/state.md"
    assert got["records"]["developer_rules"] == "rules/DEV.md"
    assert got["root_source"] == "CLAUDE_PROJECT_DIR"


def test_status_with_a_broken_contract(tmp_path: Path) -> None:
    got = status(make_project(tmp_path, "project.md", "contract-broken.md"))
    assert got["guard_state"] == scope_guard.BROKEN
    assert got["task_id"] is None and got["files_in"] == []
    assert "active-contract.md" in got["broken_reason"]


def test_status_equals_the_guard_state_and_the_record_map(tmp_path: Path) -> None:
    root = make_project(tmp_path, "project-custom.md", "contract.md")
    state, contract, _always, _reason = scope_guard.load_state(root)
    got = status(root)
    assert contract is not None
    assert (got["guard_state"], got["task_id"]) == (state, contract.task_id)
    assert got["files_in"] == list(contract.files_in) and got["files_out"] == list(contract.files_out)
    assert got["records"] == read_records(root)


def test_status_is_json_serialisable_and_names_no_path(tmp_path: Path) -> None:
    text = json.dumps(status(make_project(tmp_path, "project.md", "contract.md")))
    assert str(tmp_path) not in text and tmp_path.name not in text


# --- root lock ---------------------------------------------------------------------

@pytest.fixture()
def lock(tmp_path: Path) -> RootLock:
    root = tmp_path / "project"
    (root / "src").mkdir(parents=True)
    (root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "outside").mkdir()
    (tmp_path / "outside" / "secret.txt").write_text("s\n", encoding="utf-8")
    return RootLock(root)


def test_root_lock_allows_paths_inside(lock: RootLock) -> None:
    expect = (lock.root / "src" / "a.py").resolve()
    assert lock.resolve("src/a.py") == expect
    assert lock.resolve("src\\a.py") == expect
    assert lock.resolve("./src/../src/a.py") == expect
    assert lock.resolve(str(lock.root / "src" / "a.py")) == expect
    assert lock.resolve("src/missing.py") == (lock.root / "src" / "missing.py").resolve()


@pytest.mark.parametrize("raw", [
    "..", "../outside/secret.txt", "src/../../outside/secret.txt", "src\\..\\..\\outside\\secret.txt",
    "src/..\\..//outside/secret.txt", "../project2/x", "/etc/passwd", "C:\\Windows\\win.ini", "C:/Windows/win.ini",
    "//server/share/x", "", "\0", "src/a.py\0.txt",
])
def test_root_lock_denies(lock: RootLock, raw: str) -> None:
    with pytest.raises(RootLockError):
        lock.resolve(raw)


def test_root_lock_denies_an_absolute_path_outside(lock: RootLock, tmp_path: Path) -> None:
    for outside in (tmp_path / "outside" / "secret.txt", lock.root.parent / "project2" / "a.py", lock.root.parent):
        with pytest.raises(RootLockError):
            lock.resolve(str(outside))


def test_root_lock_denies_the_root_itself_and_non_strings(lock: RootLock) -> None:
    for raw in (".", str(lock.root), None, 5, b"src/a.py"):
        with pytest.raises(RootLockError):
            lock.resolve(raw)


def test_root_lock_error_does_not_repeat_the_path(lock: RootLock) -> None:
    with pytest.raises(RootLockError) as err:
        lock.resolve("../outside/secret.txt")
    assert "secret" not in str(err.value) and "outside/" not in str(err.value)


def test_root_lock_case_follows_the_flag(lock: RootLock) -> None:
    upper = str(lock.root).upper() + "/src/a.py"
    assert RootLock(lock.root, casefold=True).resolve(upper).name == "a.py"
    with pytest.raises(RootLockError):
        RootLock(lock.root, casefold=False).resolve(upper)
    assert lock.casefold is (os.name == "nt")


def _make_link(link: Path, target: Path) -> bool:
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":  # a junction needs no privilege
        res = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        return res.returncode == 0 and link.exists()
    return False


def test_root_lock_denies_a_link_pointing_outside(lock: RootLock, tmp_path: Path) -> None:
    link = lock.root / "link"
    if not _make_link(link, tmp_path / "outside"):
        pytest.skip("cannot create a symlink or junction here")
    for raw in ("link", "link/secret.txt", "link/new.txt"):
        with pytest.raises(RootLockError):
            lock.resolve(raw)


def test_root_lock_allows_a_link_pointing_inside(lock: RootLock) -> None:
    link = lock.root / "inner"
    if not _make_link(link, lock.root / "src"):
        pytest.skip("cannot create a symlink or junction here")
    assert lock.resolve("inner/a.py") == (lock.root / "src" / "a.py").resolve()


# --- start check -------------------------------------------------------------------

@pytest.mark.parametrize("version,ok", [
    ("2.3.0", True), ("2.3", True), ("2.9.12", True), ("2.3.0rc1", True), ("2.10.0", True),
    ("2.2.9", False), ("1.30.0", False), ("3.0.0", False), ("3.0.0a1", False), ("", False), ("dev", False),
])
def test_sdk_range(monkeypatch: pytest.MonkeyPatch, version: str, ok: bool) -> None:
    monkeypatch.setattr(server_main.metadata, "version", lambda name: version)
    assert (server_main.sdk_problem() is None) is ok
    if not ok:
        assert server_main.sdk_problem() == server_main.INSTALL_HINT


def test_sdk_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    def gone(name: str) -> str:
        raise server_main.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(server_main.metadata, "version", gone)
    assert server_main.sdk_problem() == server_main.INSTALL_HINT
    assert 'pip install "mcp>=2.3,<3"' in server_main.INSTALL_HINT and "\n" not in server_main.INSTALL_HINT


def _run_entry_with_version(version_code: str) -> subprocess.CompletedProcess:
    driver = (
        "import importlib.metadata as m, runpy\n"
        f"m.version = {version_code}\n"
        f"runpy.run_path({str(ENTRY)!r}, run_name='__main__')\n"
    )
    return subprocess.run([sys.executable, "-I", "-c", driver], capture_output=True, text=True, timeout=60,
                          stdin=subprocess.DEVNULL)


def test_entry_without_mcp_exits_1_with_one_line() -> None:
    res = _run_entry_with_version("lambda name: (_ for _ in ()).throw(m.PackageNotFoundError(name))")
    assert res.returncode == 1
    assert res.stdout == ""
    assert res.stderr.strip() == server_main.INSTALL_HINT and len(res.stderr.strip().splitlines()) == 1


def test_entry_with_mcp_out_of_range_exits_1() -> None:
    for version in ("1.30.0", "3.0.0"):
        res = _run_entry_with_version(f"lambda name: {version!r}")
        assert res.returncode == 1 and res.stderr.strip() == server_main.INSTALL_HINT


def test_entry_with_a_bad_root_exits_1(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    res = subprocess.run([sys.executable, "-I", str(ENTRY)], capture_output=True, text=True, timeout=60,
                         env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path / "missing")},
                         stdin=subprocess.DEVNULL)
    assert res.returncode == 1 and "not a folder" in res.stderr


def test_resolve_root_prefers_the_variable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert server_main.resolve_root() == (tmp_path, "CLAUDE_PROJECT_DIR")
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    root, source = server_main.resolve_root()
    assert source == "start folder" and root == Path.cwd()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    assert server_main.resolve_root()[1] == "start folder"


# --- no network, read only, one rule in one place --------------------------------------

def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


NETWORK = {"socket", "ssl", "http", "urllib", "urllib3", "ftplib", "smtplib", "poplib", "imaplib", "telnetlib",
           "socketserver", "xmlrpc", "requests", "httpx", "httpx2", "aiohttp", "websockets", "uvicorn", "starlette",
           "sse_starlette", "selectors", "asyncio"}


def test_server_modules_import_no_network_module() -> None:
    files = sorted(SERVER_DIR.glob("*.py"))
    assert len(files) >= 4
    for path in files:
        assert not (_imports(path) & NETWORK), path.name


def test_server_runs_stdio_only() -> None:
    for path in SERVER_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for word in ("streamable", "run_sse", "sse_app", "http_app", "uvicorn", " port=", "host="):
            assert word not in text, (path.name, word)
    assert 'transport="stdio"' in ENTRY.read_text(encoding="utf-8")


WRITE_NAMES = {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "replace", "touch", "remove",
               "makedirs", "rmtree", "copy", "copyfile", "copytree", "move", "symlink_to", "chmod"}


def test_server_has_no_write_call() -> None:
    for path in SERVER_DIR.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Attribute):
                assert node.attr not in WRITE_NAMES, (path.name, node.attr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                mode = node.args[1] if len(node.args) > 1 else None
                assert mode is None or (isinstance(mode, ast.Constant) and set(str(mode.value)) <= set("rbt")), path.name


def test_server_defines_no_glob_or_path_matching_rule() -> None:
    banned_imports = {"fnmatch", "glob", "re"}
    banned_attrs = {"glob", "rglob", "match", "fullmatch", "fnmatch", "is_relative_to"}
    for path in SERVER_DIR.glob("*.py"):
        assert not (_imports(path) & banned_imports), path.name
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Attribute):
                assert node.attr not in banned_attrs, (path.name, node.attr)


def test_root_lock_uses_the_guard_function() -> None:
    assert "relative_to_root" in (SERVER_DIR / "rootlock.py").read_text(encoding="utf-8")


def test_tools_import_neither_server_nor_mcp() -> None:
    for path in sorted((ROOT / "tools").rglob("*.py")):
        assert not (_imports(path) & {"server", "mcp"}), path.relative_to(ROOT)


def test_the_entry_imports_mcp_only_inside_a_function() -> None:
    # A clone without the SDK must reach the install hint, so no top-level mcp import.
    tree = ast.parse(ENTRY.read_text(encoding="utf-8"))
    top = {a.name.split(".")[0] for n in tree.body if isinstance(n, ast.Import) for a in n.names}
    top |= {n.module.split(".")[0] for n in tree.body if isinstance(n, ast.ImportFrom) and n.module}
    assert "mcp" not in top
    assert "mcp" in _imports(ENTRY)


# --- plugin config -------------------------------------------------------------------

def test_plugin_manifest_registers_the_stdio_server() -> None:
    data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    ((name, entry),) = data["mcpServers"].items()
    assert name == "sdlc"
    assert entry["command"] == "python"
    assert entry["args"] == ["${CLAUDE_PLUGIN_ROOT}/server/main.py"]
    assert "url" not in entry and "type" not in entry
    assert ENTRY.is_file()
    assert not (ROOT / ".mcp.json").exists()  # this folder's own sessions would read it as project config


def test_json_files_use_lf() -> None:
    lines = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "*.json text eol=lf" in lines
    assert b"\r" not in (ROOT / ".claude-plugin" / "plugin.json").read_bytes()


# --- the SDK: registered tools and one stdio round trip ---------------------------------

def _block_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: object, **kwargs: object) -> None:
        raise OSError("network blocked in this test")

    monkeypatch.setattr(socket.socket, "__init__", blocked)
    for name in ("socketpair", "create_connection", "getaddrinfo", "gethostbyname", "create_server"):
        monkeypatch.setattr(socket, name, blocked)


def test_every_tool_runs_with_socket_creation_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    root = make_project(tmp_path, "project.md", "contract.md")
    server = server_main.build_server(RootLock(root), "CLAUDE_PROJECT_DIR")

    async def run() -> dict[str, Any]:
        seen: dict[str, Any] = {}
        _block_sockets(monkeypatch)  # after the event loop exists; the loop's own sockets are already open
        try:
            with pytest.raises(OSError):
                socket.socket()  # the block works
            for tool in await server.list_tools():
                result = await server.call_tool(tool.name, TOOL_ARGS[tool.name])
                assert not result.is_error, tool.name
                seen[tool.name] = result.structured_content
        finally:
            monkeypatch.undo()
        return seen

    seen = asyncio.run(run())
    assert set(seen) == set(TOOL_ARGS)
    assert seen["status"] == status(root, "CLAUDE_PROJECT_DIR")


async def _round_trip(env: dict[str, str] | None, cwd: Path | None) -> tuple[list[str], Any]:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(command=sys.executable, args=["-I", str(ENTRY)], env=env, cwd=cwd)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = [t.name for t in (await session.list_tools()).tools]
            result = await session.call_tool("status", {})
            assert not result.is_error
            return names, result.structured_content


def test_stdio_round_trip_with_the_project_variable(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    project = make_project(tmp_path / "p", "project-custom.md", "contract.md")
    names, got = asyncio.run(asyncio.wait_for(
        _round_trip({"CLAUDE_PROJECT_DIR": str(project)}, tmp_path), 90))
    assert names == ["status"]
    assert got == status(project, "CLAUDE_PROJECT_DIR")
    assert got["task_id"] == "T-77" and got["records"]["tasks"] == "plan/TASKS.md"


def test_stdio_round_trip_from_the_start_folder(tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    project = make_project(tmp_path / "p", None, None)
    names, got = asyncio.run(asyncio.wait_for(_round_trip(None, project), 90))
    assert names == ["status"]
    assert got == status(project, "start folder")
    assert got["guard_state"] == "not-opted-in"


@pytest.mark.skipif(shutil.which("git") is None, reason="no git on PATH")
def test_server_files_are_not_ignored_by_git() -> None:
    res = subprocess.run(["git", "check-ignore", "server/main.py", "server/status.py", "server/rootlock.py"],
                         cwd=ROOT, capture_output=True, timeout=60)
    assert res.returncode == 1 and res.stdout == b""  # 1 = none of the paths is ignored
