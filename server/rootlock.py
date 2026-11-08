"""Root lock: the project root is fixed once at start; every path argument is checked against it.

The text rule is `tools.scope_guard.relative_to_root` (`..`, both separators, drive letters,
case on Windows). A path that passes it is then resolved on disk and must still sit inside the
root, which catches a link or junction pointing outside. This module has no glob or path
matching rule of its own.
"""
from __future__ import annotations

import os
from pathlib import Path

from tools.scope_guard import relative_to_root


class RootLockError(ValueError):
    """A path argument is not allowed. The message does not repeat the path."""


class RootLock:
    def __init__(self, root: Path | str, casefold: bool | None = None) -> None:
        self.root = Path(root).resolve()
        self.casefold = (os.name == "nt") if casefold is None else casefold

    def resolve(self, raw: object) -> Path:
        """The absolute path for `raw` (relative to the root, or absolute inside it); else RootLockError."""
        if not isinstance(raw, str) or not raw or "\0" in raw:
            raise RootLockError("path: not a usable path")
        rel = relative_to_root(str(self.root), raw, self.casefold)
        if rel is None:
            raise RootLockError("path: outside the project root")
        try:
            full = (self.root / rel).resolve()
            full.relative_to(self.root)
        except (OSError, ValueError):
            raise RootLockError("path: resolves outside the project root") from None
        return full
