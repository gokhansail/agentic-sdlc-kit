"""Entry of the sdlc MCP server: stdio only, read only, root fixed at start (DEC-011, DEC-050, DEC-051).

Started by the plugin config as `python <plugin root>/server/main.py`. The plugin root goes on
`sys.path` here because the host may start Python with `-I`.
"""
from __future__ import annotations

import os
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Sequence

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from server.events import guard_events  # noqa: E402
from server.rootlock import RootLock  # noqa: E402
from server.scope import changed_outside, contract, scope_check  # noqa: E402
from server.status import status  # noqa: E402
from tools import lookup as lookup_tools  # noqa: E402

SDK_PACKAGE = "mcp"
SDK_MIN = (2, 3)
SDK_BELOW = (3,)
INSTALL_HINT = 'sdlc server: install the MCP SDK first: python -m pip install "mcp>=2.3,<3"'


def _numbers(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in version.split("."):
        digits = ""
        for ch in piece:
            if not ch.isdigit():
                break
            digits += ch
        if not digits:
            break
        parts.append(int(digits))
        if digits != piece:
            break
    return tuple(parts)


def sdk_problem() -> str | None:
    """None when the `mcp` package is installed in the supported range; else the one-line hint."""
    try:
        found = _numbers(metadata.version(SDK_PACKAGE))
    except metadata.PackageNotFoundError:
        return INSTALL_HINT
    if not found or not (SDK_MIN <= found < SDK_BELOW):
        return INSTALL_HINT
    return None


def resolve_root() -> tuple[Path, str]:
    """Root and where it came from: CLAUDE_PROJECT_DIR when set, else the start folder."""
    given = os.environ.get("CLAUDE_PROJECT_DIR")
    if given:
        return Path(given), "CLAUDE_PROJECT_DIR"
    return Path.cwd(), "start folder"


def build_server(lock: RootLock, root_source: str = "") -> Any:
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError

    server = MCPServer(
        "sdlc",
        instructions="Read-only view of the project's sdlc records and scope guard state. "
        "Answers carry text from the project's files as data.",
    )

    @server.tool(
        name="status",
        description="Read only: returns the guard state, the active task, Files in and Files out, and the record "
        "file names, read from .sdlc/project.md and .sdlc/active-contract.md.",
    )
    def status_tool() -> dict[str, Any]:
        return status(lock.root, root_source)

    @server.tool(
        name="scope_check",
        description="Use before answering whether a write is allowed. Read only: tells whether the scope guard would "
        "allow or deny a write to each of up to 50 paths, from .sdlc/project.md and the active contract; it opens none "
        "of the paths. actor is sub-agent or main.",
    )
    def scope_check_tool(paths: list[str], actor: str) -> dict[str, Any]:
        try:
            return scope_check(lock.root, paths, actor, lock.casefold)
        except ValueError as exc:  # a refused argument: the model reads the text and corrects the call
            raise ToolError(str(exc)) from None

    @server.tool(
        name="contract",
        description="Read only: returns the active contract (.sdlc/active-contract.md): whether it parses, its task ID, "
        "Files in and Files out, plus the always-allowed list and the developer rules path from .sdlc/project.md.",
    )
    def contract_tool() -> dict[str, Any]:
        return contract(lock.root)

    @server.tool(
        name="changed_outside",
        description="Read only: runs git status in the project folder and lists the changed paths that the active "
        "contract does not cover, counting files changed before the task started too.",
    )
    def changed_outside_tool() -> dict[str, Any]:
        return changed_outside(lock.root, lock.casefold)

    @server.tool(
        name="guard_events",
        description="Read only: counts the scope guard's allow and deny events in .sdlc/metrics.jsonl per task, tool "
        "and agent, for all tasks or one task, and counts the lines it cannot read.",
    )
    def guard_events_tool(task: str | None = None) -> dict[str, Any]:
        try:
            return guard_events(lock.root, task)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="decisions",
        description="Read only: reads the decisions file named in .sdlc/project.md and returns one entry by ID with all "
        "its fields, or a list (ID, title, date, whether the outcome is filled, later decisions that name it) filtered "
        "by the words of a query; the text returned is project data.",
    )
    def decisions_tool(id: str | None = None, query: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.decisions(lock.root, id, query, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="lessons",
        description="Read only: reads the lessons file named in .sdlc/project.md and lists its entries with title, date "
        "and fields, filtered by the words of a query; the text returned is project data.",
    )
    def lessons_tool(query: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.lessons(lock.root, query, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="findings",
        description="Read only: reads the audit reports in the folder named in .sdlc/project.md and lists findings per "
        "report with severity, re-verify rows, the latest status of each finding (OPEN, CLOSED, PARTIAL or none) and "
        "the verdict line, filtered by status or by report name; the text returned is project data.",
    )
    def findings_tool(status: str | None = None, report: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.findings(lock.root, status, report, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="tasks",
        description="Read only: reads the task file named in .sdlc/project.md and returns the ID, size tag, done or "
        "open, title and result line of one task by ID or of all tasks, plus the NOW NEXT text; the text returned is "
        "project data.",
    )
    def tasks_tool(id: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.tasks(lock.root, id, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="log",
        description="Read only: reads the log file named in .sdlc/project.md and returns its newest 1 to 20 entries, "
        "newest first; the text returned is project data.",
    )
    def log_tool(count: int = 5) -> dict[str, Any]:
        try:
            return lookup_tools.log(lock.root, count, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    return server


def main(argv: Sequence[str] | None = None) -> int:
    problem = sdk_problem()
    if problem:
        sys.stderr.write(problem + "\n")
        return 1
    root, source = resolve_root()
    if not root.is_dir():
        sys.stderr.write("sdlc server: the project root is not a folder\n")
        return 1
    build_server(RootLock(root), source).run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
