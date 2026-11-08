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

from server.rootlock import RootLock  # noqa: E402
from server.status import status  # noqa: E402

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

    server = MCPServer("sdlc", instructions="Read-only view of the project's sdlc records and scope guard state.")

    @server.tool(name="status", description="Guard state, active task, Files in and Files out, and the record file names of this project.")
    def status_tool() -> dict[str, Any]:
        return status(lock.root, root_source)

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
