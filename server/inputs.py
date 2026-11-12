"""Checks on the files that the scope guard and git read for the server's tools (T-44).

The guard functions in `tools/scope_guard.py` read `.sdlc/project.md` and `.sdlc/active-contract.md`
with no size limit and follow links. `control_problem` looks at both files first (link, kind, size). `git_problem` looks at the repository config before
`git status` runs. `scrub` removes the root and the home folder from a text. A problem text names no path.
This module defines no path or glob rule of its own.
"""
from __future__ import annotations

import os
from pathlib import Path

from tools.records import UnsafeFile, read_inside
from tools.scope_guard import CONTRACT_FILE, PROJECT_FILE

CONTROL_FILES = (PROJECT_FILE, CONTRACT_FILE)
CONTROL_LIMIT = 256_000  # bytes; the real files are under 2,000
CONFIG_LIMIT = 1_000_000
GIT_DIR = ".git"
GIT_HEAD = "HEAD"
GIT_FOLDER_PARTS = ("objects", "refs", "commondir")  # with HEAD, git takes a folder as a repository folder itself
GIT_RUNS_CONFIG = ("[filter", "[include")  # a filter driver runs on `git status`; an include can hide one
MAX_PATTERNS = 500  # Files in, Files out or always-allowed entries in one answer
MAX_RECORD_NAMES = 40
MAX_RECORD_VALUE = 200


def bounded(items: list[str]) -> tuple[list[str], bool]:
    """At most MAX_PATTERNS entries, and whether any were left out."""
    return list(items[:MAX_PATTERNS]), len(items) > MAX_PATTERNS


def bounded_records(records: dict[str, str]) -> dict[str, str]:
    """At most MAX_RECORD_NAMES entries of the record map, each value cut to MAX_RECORD_VALUE characters."""
    return {key[:60]: value[:MAX_RECORD_VALUE] for key, value in list(records.items())[:MAX_RECORD_NAMES]}


def scrub(text: str, root: Path) -> str:
    """The text without the root's absolute path or the home folder (an OS or git message can carry them)."""
    places = [(root, "<root>")]
    try:
        places.append((Path.home(), "<home>"))
    except (RuntimeError, OSError):
        pass
    forms: set[tuple[str, str]] = set()
    for place, mark in places:
        # the plain form, the slash form, and the form inside an OSError text (backslashes doubled)
        for form in (str(place), place.as_posix(), repr(str(place))[1:-1]):
            forms.add((form, mark))
    for form, mark in sorted(forms, key=lambda pair: len(pair[0]), reverse=True):
        if len(form) > 3:
            text = mark.join(text.split(form))
    return text


def control_problem(root: Path) -> str:
    """"" when the project file and the contract can be handed to the guard; else one sentence why not."""
    base = Path(root).resolve()
    for rel in CONTROL_FILES:
        try:
            read_inside(base, rel, CONTROL_LIMIT)
        except FileNotFoundError:
            continue
        except UnsafeFile as exc:
            return f"{rel} {exc}"
        except OSError:
            return f"{rel} could not be read"
    return ""


def git_problem(root: Path) -> str:
    """"" when `git status` can run in `root`; else one sentence why not.

    Git runs a clean filter from the repository config when it compares a file whose time changed
    (measured on git 2.35). The config of a plain repository is read here; a linked worktree or a
    submodule keeps its config elsewhere and is refused. A folder laid out as a git folder with no `.git`
    entry is refused too: git takes it as the repository and reads its `config` (T-45a). Git looks for
    the `.git` entry first and for the folder itself second, one folder at a time, going up; so does this.
    """
    base = Path(root).resolve()
    for folder in (base, *base.parents):
        dot = folder / GIT_DIR
        if not os.path.lexists(dot):
            if os.path.lexists(folder / GIT_HEAD) and any(os.path.lexists(folder / name) for name in GIT_FOLDER_PARTS):
                return "the folder is laid out as a git folder (HEAD with objects or refs); its config is not checked"
            continue
        if dot.is_symlink():
            return "the .git entry is a link"
        if dot.is_file():
            return "the .git entry is a file (a linked worktree or a submodule); its config is not checked"
        try:
            data = read_inside(folder, f"{GIT_DIR}/config", CONFIG_LIMIT)
        except FileNotFoundError:
            return ""
        except UnsafeFile as exc:
            return f"the repository config {exc}"
        except OSError:
            return "the repository config could not be read"
        for line in data.decode("utf-8-sig", errors="replace").splitlines():
            if "".join(line.split()).lower().startswith(GIT_RUNS_CONFIG):
                return "the repository config defines a filter or an include, which git may run when it reads status"
        return ""
    return ""
