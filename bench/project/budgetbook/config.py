"""Settings. They come from ``BUDGETBOOK_*`` environment variables and from a ``.env`` file
in the current folder. A variable in the environment wins over the same name in ``.env``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

ENV_PREFIX = "BUDGETBOOK_"
DEFAULT_DATA_FILE = "budgetbook.json"


@dataclass(frozen=True)
class Settings:
    """The effective settings of one run.

    ``data_file`` is the path of the ledger file the commands read and write.
    """

    data_file: str = DEFAULT_DATA_FILE


def parse_dotenv(text: str) -> dict[str, str]:
    """Parse ``NAME=value`` lines. Blank lines and lines starting with ``#`` are skipped.

    A value may be wrapped in one pair of single or double quotes, and a line may start
    with ``export``.
    """
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        name, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[name.strip()] = value
    return values


def read_dotenv(path: Path) -> dict[str, str]:
    """Read a ``.env`` file; a missing file gives no values."""
    if not path.is_file():
        return {}
    return parse_dotenv(path.read_text(encoding="utf-8"))


def load_settings(
    environ: Mapping[str, str] | None = None, cwd: str | os.PathLike | None = None
) -> Settings:
    """Settings from ``.env`` in ``cwd`` (default: the current folder) and the environment."""
    environ = os.environ if environ is None else environ
    folder = Path(cwd) if cwd is not None else Path.cwd()
    values = dict(read_dotenv(folder / ".env"))
    values.update({name: value for name, value in environ.items() if name.startswith(ENV_PREFIX)})
    return Settings(data_file=values.get(ENV_PREFIX + "DATA_FILE", DEFAULT_DATA_FILE))
