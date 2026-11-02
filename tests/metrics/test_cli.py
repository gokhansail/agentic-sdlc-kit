"""End-to-end tests of `python -m tools.metrics` with a temporary project root.

The project root is injected, so evidence/ is created in a temp folder, never in
this repository. Source folders are temp folders as well.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.metrics.__main__ import main
from conftest import FIXTURES, ROOT, fixture_text

PROFILE = FIXTURES / "profile-test.json"


def make_source(path: Path, git: bool = False) -> Path:
    path.mkdir(parents=True)
    (path / "CHANGELOG.md").write_text(fixture_text("changelog-test.md"), encoding="utf-8", newline="\n")
    (path / "LOG.md").write_text(fixture_text("log-test.md"), encoding="utf-8", newline="\n")
    if git:
        for args in (
            ["init", "-q", "-b", "main"],
            ["config", "user.name", "Test"],
            ["config", "user.email", "test@users.noreply.github.com"],
            ["config", "core.autocrlf", "false"],
            ["add", "-A"],
            ["commit", "-q", "-m", "Records"],
        ):
            subprocess.run(["git", *args], cwd=path, check=True, capture_output=True)
    return path


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "kit"
    root.mkdir()
    return root


def cli(root: Path, source, out: Path, *extra: str, profile: Path = PROFILE, label: str = "demo") -> int:
    argv = ["--profile", str(profile), "--label", label, "--out", str(out), *extra]
    if source is not None:
        argv = ["--source", str(source), *argv]
    return main(argv, root=root)


def test_snapshot_run_writes_copy_manifest_and_result(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    out = project / "evidence" / "demo.json"
    assert cli(project, source, out, "--snapshot") == 0

    raw = project / "evidence" / "raw" / "demo"
    assert (raw / "CHANGELOG.md").read_bytes() == (source / "CHANGELOG.md").read_bytes()
    manifest = json.loads((raw / "manifest.json").read_text(encoding="ascii"))
    assert manifest["files"]["log"] == hashlib.sha256((source / "LOG.md").read_bytes()).hexdigest()
    assert manifest["profile_sha256"] == hashlib.sha256(PROFILE.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert manifest["head"] is None and manifest["dirty"] is None
    assert manifest["warnings"] == {"source_not_git": 1}

    result = json.loads(out.read_text(encoding="ascii"))
    assert result["schema"] == 1 and result["label"] == "demo" and result["cutoff"] == "2026-10-25"
    assert result["input"]["files"] == manifest["files"]
    assert result["metrics"]["M2"]["v2"] == {"n": 4, "count": 2, "no_change": 2}
    assert result["warnings"]["source_not_git"] == 1
    assert result["warnings"]["m1_undated_heading"] == 2


def test_two_runs_give_byte_identical_json(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    first, second, third = (project / f"{n}.json" for n in ("a", "b", "c"))
    assert cli(project, source, first, "--snapshot") == 0
    assert cli(project, source, second, "--snapshot") == 0
    assert cli(project, None, third) == 0  # rerun on the copy, no source needed
    assert first.read_bytes() == second.read_bytes() == third.read_bytes()


def test_run_parses_the_copy_not_the_source(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    before, after = project / "before.json", project / "after.json"
    assert cli(project, source, before, "--snapshot") == 0
    (source / "LOG.md").write_text("# Log\n", encoding="utf-8")  # source changes after the snapshot
    assert cli(project, source, after) == 0
    assert before.read_bytes() == after.read_bytes()


def test_tampered_copy_is_refused(project: Path, tmp_path: Path, capsys) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot") == 0
    copy = project / "evidence" / "raw" / "demo" / "LOG.md"
    copy.write_text(copy.read_text(encoding="utf-8") + "\nextra\n", encoding="utf-8")
    assert cli(project, None, project / "o2.json") == 2
    assert "manifest" in capsys.readouterr().err
    assert not (project / "o2.json").exists()


def test_rerun_without_a_snapshot_is_refused(project: Path) -> None:
    assert cli(project, None, project / "o.json") == 2


def test_git_source_records_head_and_dirty_flag(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src", git=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True, check=True
    ).stdout.strip()
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    result = json.loads(out.read_text(encoding="ascii"))
    assert result["input"]["head"] == head and result["input"]["dirty"] is False
    assert "source_not_git" not in result["warnings"]

    (source / "LOG.md").write_text("# Log\n\nchanged\n", encoding="utf-8")
    assert cli(project, source, out, "--snapshot") == 0
    result = json.loads(out.read_text(encoding="ascii"))
    assert result["input"]["head"] == head and result["input"]["dirty"] is True


def test_folder_inside_another_repository_is_not_taken_for_one(project: Path, tmp_path: Path) -> None:
    outer = make_source(tmp_path / "outer", git=True)
    inner = make_source(outer / "inner")
    out = project / "o.json"
    assert cli(project, inner, out, "--snapshot") == 0
    result = json.loads(out.read_text(encoding="ascii"))
    assert result["input"]["head"] is None and result["warnings"]["source_not_git"] == 1


def test_missing_record_file_shows_no_data_and_a_warning(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    (source / "LOG.md").unlink()
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    result = json.loads(out.read_text(encoding="ascii"))
    assert result["input"]["files"]["log"] is None
    assert result["metrics"]["M5"] == {"status": "no data"}
    assert result["metrics"]["M1"]["status"] == "ok"
    assert result["warnings"]["record_file_missing"] == 1


def test_project_b_style_profile_gives_no_data_for_all_four(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    out = project / "o.json"
    profile = ROOT / "tools" / "metrics" / "profiles" / "project-b.json"
    assert cli(project, source, out, "--snapshot", profile=profile) == 0
    metrics = json.loads(out.read_text(encoding="ascii"))["metrics"]
    assert metrics == {m: {"status": "no data"} for m in ("M1", "M2", "M5", "M6")}


# --- path safety (DEV_RULES 10) --------------------------------------------

def profile_with_path(tmp_path: Path, rel: str) -> Path:
    data = json.loads(PROFILE.read_text(encoding="ascii"))
    data["files"]["changelog"] = rel
    path = tmp_path / "profile-paths.json"
    path.write_text(json.dumps(data), encoding="ascii")
    return path


def test_profile_path_with_dotdot_escape_is_refused_and_nothing_is_copied(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    (tmp_path / "secret.md").write_text("outside the source root\n", encoding="utf-8")
    profile = profile_with_path(tmp_path, "../secret.md")
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 2
    assert not (project / "evidence").exists()
    assert not (project / "o.json").exists()


def test_profile_absolute_path_outside_the_root_is_refused(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    outside = tmp_path / "secret.md"
    outside.write_text("outside the source root\n", encoding="utf-8")
    profile = profile_with_path(tmp_path, str(outside))
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 2
    assert not (project / "evidence").exists()


def test_profile_absolute_path_inside_the_root_is_also_refused(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    profile = profile_with_path(tmp_path, str(source / "CHANGELOG.md"))
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 2


def test_profile_path_with_dotdot_that_stays_inside_the_root_passes(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    (source / "docs").mkdir()
    profile = profile_with_path(tmp_path, "docs/../CHANGELOG.md")
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 0
    assert (project / "evidence" / "raw" / "demo" / "CHANGELOG.md").is_file()


def test_out_path_outside_the_project_root_is_refused(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    outside = tmp_path / "elsewhere" / "o.json"
    assert cli(project, source, outside, "--snapshot") == 2
    assert not outside.exists() and not (project / "evidence").exists()
    escape = project / "sub" / ".." / ".." / "escaped.json"
    assert cli(project, source, escape, "--snapshot") == 2
    assert not (tmp_path / "escaped.json").exists()


def test_out_path_inside_the_project_root_passes(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "evidence" / "demo.json", "--snapshot") == 0
    assert (project / "evidence" / "demo.json").is_file()


@pytest.mark.parametrize("label", ["", "Upper", "a_b", "a/b", "..", "a b", "x.json"])
def test_bad_labels_are_refused(project: Path, tmp_path: Path, label: str) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot", label=label) == 2
    assert not (project / "evidence").exists()


def test_good_label_passes(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot", label="project-a-2") == 0


def test_snapshot_without_source_is_refused(project: Path) -> None:
    assert cli(project, None, project / "o.json", "--snapshot") == 2


# --- module entry point ------------------------------------------------------

def test_module_entry_point_runs_from_the_command_line(tmp_path: Path) -> None:
    res = subprocess.run(
        [sys.executable, "-m", "tools.metrics", "--help"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert res.returncode == 0 and "--snapshot" in res.stdout


def test_new_files_are_ascii_only() -> None:
    roots = [ROOT / "tools" / "metrics", ROOT / "tests" / "metrics", ROOT / "tests" / "fixtures" / "metrics"]
    for base in roots:
        for path in base.rglob("*"):
            if path.is_file() and path.suffix != ".pyc":
                path.read_bytes().decode("ascii")
