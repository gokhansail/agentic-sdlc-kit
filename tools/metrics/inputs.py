"""Input pinning: snapshot the record files, write a manifest, read only the copy.

`--snapshot` copies the files the profile names from the source root into
`<root>/evidence/raw/<label>/` (ignored by git) and writes `manifest.json` there:
SHA-256 per file, the source HEAD, the dirty flag, the profile hash. Every run
parses the copy, after checking its hash against the manifest.

Path safety: record paths from the profile must be relative and resolve inside
the source root; the snapshot and the output file must resolve inside the
project root. Anything else is refused before a file is copied or written.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

from . import gitstats, output
from .fold import fold
from .profile import Profile

LABEL_RE = re.compile(r"[a-z0-9-]+")
RAW_DIR = ("evidence", "raw")
MANIFEST_NAME = "manifest.json"
GIT_HASH_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")
GIT_LOG_NAME = "git-log.txt"
GIT_TESTS_NAME = "git-tests.txt"
GIT_EXTRACTS = (("git_log", GIT_LOG_NAME), ("git_tests", GIT_TESTS_NAME))


class InputError(ValueError):
    pass


def check_label(label: str) -> str:
    if not LABEL_RE.fullmatch(label or ""):
        raise InputError("label must match [a-z0-9-]+")
    return label


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_inside(base: Path, candidate: str | Path, what: str, *, allow_absolute: bool) -> Path:
    """Resolve candidate against base and require the result to stay inside base."""
    text = str(candidate)
    absolute = bool(PurePosixPath(text).anchor or PureWindowsPath(text).anchor)
    if absolute and not allow_absolute:
        raise InputError(f"{what}: an absolute path is not allowed")
    base_real = base.resolve()
    full = (base_real / text).resolve() if not absolute else Path(text).resolve()
    try:
        full.relative_to(base_real)
    except ValueError:
        raise InputError(f"{what}: path resolves outside the allowed root")
    return full


def raw_dir(root: Path, label: str) -> Path:
    check_label(label)
    return resolve_inside(root, Path(*RAW_DIR, label), "snapshot directory", allow_absolute=False)


# --- git ---------------------------------------------------------------

def _git(cwd: Path, *args: str) -> str | None:
    try:
        res = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError:
        return None
    return res.stdout.strip() if res.returncode == 0 else None


def git_state(path: Path) -> tuple[str | None, bool | None]:
    """HEAD and dirty flag of the repository whose top level is exactly `path`.

    Returns (None, None) when `path` is not a repository root, so a folder that
    sits inside another repository is not mistaken for one. Dirty means a tracked
    file differs from HEAD; untracked files do not count.
    """
    top = _git(path, "rev-parse", "--show-toplevel")
    if not top:
        return None, None
    try:
        if not os.path.samefile(top, path):
            return None, None
    except OSError:
        return None, None
    head = _git(path, "rev-parse", "HEAD")
    if not head or not GIT_HASH_RE.fullmatch(head):
        return None, None
    status = _git(path, "status", "--porcelain", "--untracked-files=no")
    return head, (None if status is None else bool(status))


# --- snapshot and manifest ----------------------------------------------

def record_paths(source: Path, files: Mapping[str, str]) -> dict[str, tuple[str, Path]]:
    """role -> (relative posix path, absolute path in the source). Raises on any escape."""
    out: dict[str, tuple[str, Path]] = {}
    for role, rel in files.items():
        full = resolve_inside(source, rel, f"record file '{role}'", allow_absolute=False)
        out[role] = (full.relative_to(source.resolve()).as_posix(), full)
    return out


def _tracked_names(source: Path, rel_dir: str, is_repo: bool) -> set[str]:
    """Paths (relative to the source root) that git tracks under rel_dir."""
    if not is_repo:
        return set()
    listing = _git(source, "-c", "core.quotepath=off", "ls-files", "--", rel_dir)
    return set(listing.splitlines()) if listing else set()


def _copy_folder(
    source: Path, dest: Path, role: str, spec: Mapping[str, Any], is_repo: bool, warnings: dict[str, int]
) -> dict[str, dict[str, Any]]:
    """Copy the files of one folder entry; return {name: {"sha256", "tracked"}}."""
    folder = resolve_inside(source, spec["dir"], f"folder '{role}'", allow_absolute=False)
    if not folder.is_dir():
        warnings["record_folder_missing"] = warnings.get("record_folder_missing", 0) + 1
        return {}
    rel_dir = folder.relative_to(source.resolve()).as_posix()
    tracked = _tracked_names(source, rel_dir, is_repo)
    found: dict[str, dict[str, Any]] = {}
    for child in sorted(folder.iterdir(), key=lambda p: p.name):
        folded = fold(child.name)
        if not spec["name"].search(folded) or (spec["skip"] and spec["skip"].search(folded)):
            continue
        if not NAME_RE.fullmatch(child.name):
            warnings["folder_file_skipped"] = warnings.get("folder_file_skipped", 0) + 1
            continue
        rel = f"{rel_dir}/{child.name}"
        src = resolve_inside(source, rel, f"folder '{role}' file", allow_absolute=False)
        if not src.is_file():
            continue
        data = src.read_bytes()
        target = resolve_inside(dest, rel, f"snapshot of '{role}'", allow_absolute=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        found[child.name] = {"sha256": sha256_bytes(data), "tracked": rel in tracked}
    return found


def _write_git_extracts(source: Path, dest: Path, head: str | None, profile: Profile) -> dict[str, str]:
    """Write git-log.txt and git-tests.txt when the profile needs them; return their hashes."""
    wanted = {
        "git_log": bool(profile.metrics.get("M12", {}).get("commits")),
        "git_tests": "M3" in profile.metrics,
    }
    produced: dict[str, str] = {}
    for role, name in GIT_EXTRACTS:
        target = dest / name
        if not (wanted[role] and head):
            target.unlink(missing_ok=True)
            continue
        if role == "git_log":
            text = gitstats.collect_log(source, head)
        else:
            text = gitstats.collect_tests(source, head, profile.metrics["M3"])
        data = text.encode("ascii")
        dest.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        produced[role] = sha256_bytes(data)
    return produced


def snapshot(root: Path, source: Path, profile: Profile, label: str, *, replace: bool = False) -> dict[str, Any]:
    if not source.is_dir():
        raise InputError("--source is not a directory")
    paths = record_paths(source, profile.files)  # validates every path before any copy
    for role, spec in profile.folders.items():  # same check for the folder entries
        resolve_inside(source, spec["dir"], f"folder '{role}'", allow_absolute=False)
    dest = raw_dir(root, label)
    if (dest / MANIFEST_NAME).exists() and not replace:  # refused before anything is written
        raise InputError(
            f"a snapshot for label '{label}' already exists; "
            "pass --replace-snapshot to replace it"
        )
    head, dirty = git_state(source)
    warnings: dict[str, int] = {}
    if head is None:
        warnings["source_not_git"] = 1
    hashes: dict[str, str | None] = {}
    missing = 0
    for role, (rel, src) in sorted(paths.items()):
        if not src.is_file():
            hashes[role] = None
            missing += 1
            continue
        data = src.read_bytes()
        target = resolve_inside(dest, rel, f"snapshot of '{role}'", allow_absolute=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[role] = sha256_bytes(data)
    if missing:
        warnings["record_file_missing"] = missing
    folders = {
        role: _copy_folder(source, dest, role, spec, head is not None, warnings)
        for role, spec in sorted(profile.folders.items())
    }
    hashes.update(_write_git_extracts(source, dest, head, profile))
    manifest: dict[str, Any] = {
        "schema": output.SCHEMA,
        "label": label,
        "kit_commit": git_state(root)[0],
        "head": head,
        "dirty": dirty,
        "profile_sha256": profile.sha256,
        "files": hashes,
        "warnings": warnings,
    }
    if profile.folders:
        manifest["folders"] = folders
    output.write_json(dest / MANIFEST_NAME, manifest, "manifest")
    return manifest


def read_manifest(root: Path, label: str) -> dict[str, Any]:
    path = raw_dir(root, label) / MANIFEST_NAME
    try:
        manifest = json.loads(path.read_text(encoding="ascii"))
    except (OSError, ValueError):
        raise InputError("no readable snapshot for this label; run once with --snapshot")
    try:
        output.validate_manifest(manifest)
    except output.OutputError:
        raise InputError("the snapshot manifest is not valid")
    return manifest


def load_copies(root: Path, label: str, profile: Profile, manifest: Mapping[str, Any]) -> dict[str, str | None]:
    """Read the snapshot copies the profile names, checking each hash against the manifest."""
    dest = raw_dir(root, label)
    texts: dict[str, str | None] = {}
    for role, rel in sorted(profile.files.items()):
        if role not in manifest["files"]:
            raise InputError(f"role '{role}' is not in the snapshot manifest")
        expected = manifest["files"][role]
        if expected is None:
            texts[role] = None
            continue
        path = resolve_inside(dest, rel, f"snapshot of '{role}'", allow_absolute=False)
        try:
            data = path.read_bytes()
        except OSError:
            raise InputError(f"snapshot copy of '{role}' is missing")
        if sha256_bytes(data) != expected:
            raise InputError(f"snapshot copy of '{role}' does not match the manifest hash")
        texts[role] = data.decode("utf-8-sig", errors="replace")
    return texts


def load_folders(
    root: Path, label: str, profile: Profile, manifest: Mapping[str, Any]
) -> dict[str, dict[str, str]]:
    """Read the folder copies the manifest lists, checking each hash."""
    dest = raw_dir(root, label)
    out: dict[str, dict[str, str]] = {}
    for role, spec in sorted(profile.folders.items()):
        listed = manifest.get("folders", {}).get(role)
        if listed is None:
            raise InputError(f"folder '{role}' is not in the snapshot manifest")
        texts: dict[str, str] = {}
        for name, info in sorted(listed.items()):
            path = resolve_inside(dest, f"{spec['dir']}/{name}", f"snapshot of '{role}'", allow_absolute=False)
            try:
                data = path.read_bytes()
            except OSError:
                raise InputError(f"snapshot copy of a '{role}' file is missing")
            if sha256_bytes(data) != info["sha256"]:
                raise InputError(f"snapshot copy of a '{role}' file does not match the manifest hash")
            texts[name] = data.decode("utf-8-sig", errors="replace")
        out[role] = texts
    return out


def load_git(root: Path, label: str, manifest: Mapping[str, Any]) -> dict[str, str | None]:
    """git-log.txt and git-tests.txt by role; None when the snapshot has no such extract."""
    dest = raw_dir(root, label)
    out: dict[str, str | None] = {}
    for role, name in GIT_EXTRACTS:
        expected = manifest["files"].get(role)
        if expected is None:
            out[role] = None
            continue
        try:
            data = (dest / name).read_bytes()
        except OSError:
            raise InputError(f"snapshot copy of '{role}' is missing")
        if sha256_bytes(data) != expected:
            raise InputError(f"snapshot copy of '{role}' does not match the manifest hash")
        out[role] = data.decode("ascii", errors="replace")
    return out


def folder_summary(folders: Mapping[str, Mapping[str, Mapping[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Per folder: file count, untracked count and one digest over names and hashes.

    The committed result carries this summary instead of file names.
    """
    out: dict[str, dict[str, Any]] = {}
    for role, listed in sorted(folders.items()):
        lines = "".join(f"{name} {info['sha256']}\n" for name, info in sorted(listed.items()))
        out[role] = {
            "files": len(listed),
            "untracked": sum(1 for info in listed.values() if not info["tracked"]),
            "sha256": sha256_bytes(lines.encode("ascii")),
        }
    return out
