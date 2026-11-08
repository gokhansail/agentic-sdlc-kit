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

    server = MCPServer("sdlc", instructions="Read-only view of the project's sdlc records and scope guard state.")

    @server.tool(name="status", description="Guard state, active task, Files in and Files out, and the record file names of this project.")
    def status_tool() -> dict[str, Any]:
        return status(lock.root, root_source)

    @server.tool(
        name="scope_check",
        description="Tells whether the scope guard would allow or deny a write to each of up to 50 paths, "
        "as a sub-agent or as the main session, with the reason, the guard state and the task.",
    )
    def scope_check_tool(paths: list[str], actor: str) -> dict[str, Any]:
        try:
            return scope_check(lock.root, paths, actor, lock.casefold)
        except ValueError as exc:  # a refused argument: the model reads the text and corrects the call
            raise ToolError(str(exc)) from None

    @server.tool(
        name="contract",
        description="Reads the active contract of this project: whether it parses, its task ID, Files in, "
        "Files out, the always-allowed list and the developer rules path.",
    )
    def contract_tool() -> dict[str, Any]:
        return contract(lock.root)

    @server.tool(
        name="changed_outside",
        description="Lists the paths git shows as changed that the active contract does not cover, "
        "counting files changed before the task started too.",
    )
    def changed_outside_tool() -> dict[str, Any]:
        return changed_outside(lock.root, lock.casefold)

    @server.tool(
        name="guard_events",
        description="Counts the scope guard's allow and deny events in .sdlc/metrics.jsonl per task, tool and agent, "
        "for all tasks or one task, and counts the lines it cannot read.",
    )
    def guard_events_tool(task: str | None = None) -> dict[str, Any]:
        try:
            return guard_events(lock.root, task)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="decisions",
        description="Reads decisions: one entry by ID with all its fields, or a list (ID, title, date, whether the "
        "outcome is filled, later decisions that name it) filtered by the words of a query.",
    )
    def decisions_tool(id: str | None = None, query: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.decisions(lock.root, id, query, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="lessons",
        description="Lists the entries of the lessons log with title, date and fields, filtered by the words of a query.",
    )
    def lessons_tool(query: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.lessons(lock.root, query, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="findings",
        description="Lists audit findings per report with severity, re-verify rows, the latest status of each finding "
        "(OPEN, CLOSED, PARTIAL or none) and the verdict line, filtered by status or by report name.",
    )
    def findings_tool(status: str | None = None, report: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.findings(lock.root, status, report, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(
        name="tasks",
        description="Reads the task list: ID, size tag, done or open, title and result line of one task by ID or of "
        "all tasks, plus the NOW NEXT text.",
    )
    def tasks_tool(id: str | None = None) -> dict[str, Any]:
        try:
            return lookup_tools.tasks(lock.root, id, lock.casefold)
        except ValueError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(name="log", description="Reads the newest 1 to 20 entries of the project log, newest first.")
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
