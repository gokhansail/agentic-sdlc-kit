"""End-to-end runs for the T-21 inputs: folder snapshots, git extracts, determinism."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.metrics.__main__ import main

from conftest import EM_DASH, FIXTURES, git_commit, git_init, git_run

PROFILE = FIXTURES / "profile-records.json"

CHANGELOG = f"# Changelog\n## 1.0.0 {EM_DASH} 2026-10-13 (first)\n## 1.1.0 {EM_DASH} 2026-10-27 (mid)\n"
DECISIONS = f"**D-1 First** {EM_DASH} 2026-10-01 {EM_DASH} in force\n- Outcome: kept\n"
TASKS = "### [x] T-1 [S] Small (2026-10-01, ab12cd3)\n### [ ] T-2 [L] Large\n"
AUDIT = f"### P-1 {EM_DASH} high {EM_DASH} first\n"
REVERIFY = "| Finding | Claim | Evidence | Status |\n|---|---|---|---|\n| P-1 | c | e | CLOSED |\n"
LATE = f"### P-2 {EM_DASH} low {EM_DASH} late report, never committed\n"


def probes(n: int) -> str:
    return "".join(f"    [Probe]\n    public void T{i}() {{}}\n" for i in range(n))


def make_source(path: Path) -> Path:
    repo = git_init(path)
    git_commit(
        repo,
        {
            "CHANGELOG.md": CHANGELOG, "DECISIONS.md": DECISIONS, "TASKS.md": TASKS,
            "reports/2026-10-20_audit.md": AUDIT, "reports/2026-10-22_reverify.md": REVERIFY,
            "reports/skipme_2026-10-20.md": AUDIT, "reports/README.md": "readme\n",
            "tests/a.cs": probes(1),
        },
        "2026-10-12T10:00:00+00:00",
    )
    git_commit(repo, {"tests/a.cs": probes(3)}, "2026-10-26T10:00:00+00:00")
    # not committed: the untracked report (DEC-029) and a file name that is not safe to record
    (repo / "reports" / "2026-10-29_late.md").write_text(LATE, encoding="utf-8", newline="\n")
    (repo / "reports" / "2026-10-21_spaced name.md").write_text(AUDIT, encoding="utf-8", newline="\n")
    return repo


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


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="ascii"))


def test_snapshot_copies_folder_files_and_marks_untracked_ones(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot") == 0
    raw = project / "evidence" / "raw" / "demo"
    manifest = read(raw / "manifest.json")
    listed = manifest["folders"]["audits"]
    assert {name: info["tracked"] for name, info in listed.items()} == {
        "2026-10-20_audit.md": True,
        "2026-10-22_reverify.md": True,
        "2026-10-29_late.md": False,  # untracked: copied, flagged
    }
    for name in listed:
        assert (raw / "reports" / name).is_file()
    assert not (raw / "reports" / "README.md").exists()  # name regex does not match
    assert not (raw / "reports" / "skipme_2026-10-20.md").exists()  # skip regex
    assert not list((raw / "reports").glob("*spaced*"))  # unsafe name, reported
    assert manifest["warnings"]["folder_file_skipped"] == 1


def test_result_carries_a_folder_summary_and_no_file_names(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    result = read(out)
    summary = result["input"]["folders"]["audits"]
    assert summary["files"] == 3 and summary["untracked"] == 1 and len(summary["sha256"]) == 64
    text = out.read_text(encoding="ascii")
    assert "2026-10-20_audit" not in text and "reports" not in text


def test_all_new_metrics_match_the_known_answers(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    metrics = read(out)["metrics"]
    # the untracked report counts (DEC-029): P-1 in v1, P-2 in v2
    assert metrics["M8"]["v1"]["latest"]["closed"] == 1 and metrics["M8"]["v1"]["n"] == 1
    assert metrics["M8"]["v2"]["n"] == 1 and metrics["M8"]["v2"]["severity"]["low"] == 1
    assert metrics["M9"]["v1"] == {"n": 1, "count": 1}
    assert metrics["M13"]["v1"] == {"n": 1, "distribution": {"E": 1, "M": 0, "H": 0}, "done": 1}
    assert metrics["M13"]["undated"]["distribution"]["H"] == 1
    assert metrics["M3"]["v1"] == {"n": 1, "count": 1, "weeks": {"2026-W42": 1}}
    assert metrics["M3"]["v2"] == {"n": 1, "count": 3, "weeks": {"2026-W44": 3}}
    assert metrics["M12"]["v1"] == {"n": 2, "count": 1, "versions": 1, "weeks": 1}
    assert metrics["M12"]["v2"] == {"n": 2, "count": 1, "versions": 1, "weeks": 1}


def test_git_extracts_are_hashed_in_the_manifest(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot") == 0
    raw = project / "evidence" / "raw" / "demo"
    manifest = read(raw / "manifest.json")
    import hashlib

    for role, name in (("git_log", "git-log.txt"), ("git_tests", "git-tests.txt")):
        assert manifest["files"][role] == hashlib.sha256((raw / name).read_bytes()).hexdigest()
    head = git_run(source, "rev-parse", "HEAD")
    first = (raw / "git-log.txt").read_text(encoding="ascii").splitlines()[0].split()
    assert first[0] == head and first[1].startswith("2026-10-26T10:00:00")  # hash, author date, committer date
    assert (raw / "git-tests.txt").read_text(encoding="ascii").splitlines()[0].startswith("2026-W42 ")


def test_git_metrics_stop_at_the_recorded_head(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    before = out.read_bytes()
    git_commit(source, {"tests/a.cs": probes(9)}, "2026-11-02T10:00:00+00:00")  # after the snapshot
    second = project / "second.json"
    assert cli(project, source, second) == 0  # no --snapshot: reads the copy
    assert second.read_bytes() == before


def test_two_snapshot_runs_and_a_rerun_are_byte_identical(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    a, b, c = (project / f"{n}.json" for n in "abc")
    assert cli(project, source, a, "--snapshot") == 0
    assert cli(project, source, b, "--snapshot") == 0
    assert cli(project, None, c) == 0
    assert a.read_bytes() == b.read_bytes() == c.read_bytes()


def test_tampered_folder_copy_is_refused(project: Path, tmp_path: Path, capsys) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot") == 0
    copy = project / "evidence" / "raw" / "demo" / "reports" / "2026-10-20_audit.md"
    copy.write_text(copy.read_text(encoding="utf-8") + "\nextra\n", encoding="utf-8")
    assert cli(project, None, project / "o2.json") == 2
    assert "manifest" in capsys.readouterr().err and not (project / "o2.json").exists()


def test_tampered_git_extract_is_refused(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot") == 0
    extract = project / "evidence" / "raw" / "demo" / "git-log.txt"
    extract.write_text(extract.read_text(encoding="ascii") + "x\n", encoding="ascii")
    assert cli(project, None, project / "o2.json") == 2


def test_source_that_is_not_git_gives_no_git_metrics_and_no_extracts(project: Path, tmp_path: Path) -> None:
    source = tmp_path / "plain"
    (source / "reports").mkdir(parents=True)
    (source / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    (source / "reports" / "2026-10-20_audit.md").write_text(AUDIT, encoding="utf-8")
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    result = read(out)
    assert result["metrics"]["M3"] == {"status": "no data"}
    assert "versions" in result["metrics"]["M12"]["v1"] and "count" not in result["metrics"]["M12"]["v1"]
    assert "git_log" not in result["input"]["files"] and result["warnings"]["source_not_git"] == 1
    raw = project / "evidence" / "raw" / "demo"
    assert not (raw / "git-log.txt").exists() and not (raw / "git-tests.txt").exists()
    # not a repository: nothing is tracked
    assert read(raw / "manifest.json")["folders"]["audits"]["2026-10-20_audit.md"]["tracked"] is False


def test_stale_git_extract_is_removed_when_a_later_snapshot_cannot_make_one(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    assert cli(project, source, project / "o.json", "--snapshot") == 0
    plain = tmp_path / "plain"
    plain.mkdir()
    for name in ("CHANGELOG.md", "DECISIONS.md", "TASKS.md"):
        (plain / name).write_text("# x\n", encoding="utf-8")
    assert cli(project, plain, project / "o2.json", "--snapshot") == 0
    assert not (project / "evidence" / "raw" / "demo" / "git-log.txt").exists()


def test_missing_folder_is_reported_and_gives_no_data(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    for child in (source / "reports").iterdir():
        child.unlink()
    (source / "reports").rmdir()
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    result = read(out)
    assert result["metrics"]["M8"] == {"status": "no data"}
    assert result["warnings"]["record_folder_missing"] == 1


# --- path safety (DEV_RULES 10) -----------------------------------------------

def profile_with(tmp_path: Path, **folder_changes) -> Path:
    data = json.loads(PROFILE.read_text(encoding="ascii"))
    data["folders"]["audits"].update(folder_changes)
    path = tmp_path / "profile-folder.json"
    path.write_text(json.dumps(data), encoding="ascii")
    return path


@pytest.mark.parametrize("bad", ["../secret", "/etc", "C:/Windows", "reports/../../secret"])
def test_folder_dir_that_escapes_the_source_is_refused_before_any_copy(project: Path, tmp_path: Path, bad: str) -> None:
    source = make_source(tmp_path / "src")
    (tmp_path / "secret").mkdir()
    (tmp_path / "secret" / "2026-10-20_x.md").write_text("outside\n", encoding="utf-8")
    profile = profile_with(tmp_path, dir=bad)
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 2
    assert not (project / "evidence").exists()


def test_folder_dir_with_dotdot_is_refused_even_when_it_stays_inside(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    profile = profile_with(tmp_path, dir="tests/../reports")
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 2
    assert not (project / "evidence").exists()


def test_folder_dir_inside_a_subfolder_passes(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    (source / "docs" / "audits").mkdir(parents=True)
    (source / "docs" / "audits" / "2026-10-20_audit.md").write_text(AUDIT, encoding="utf-8")
    profile = profile_with(tmp_path, dir="docs/audits")
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 0
    assert (project / "evidence" / "raw" / "demo" / "docs" / "audits" / "2026-10-20_audit.md").is_file()


def test_git_pathspec_from_the_profile_cannot_leave_the_source(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    data = json.loads(PROFILE.read_text(encoding="ascii"))
    data["metrics"]["M3"]["path_glob"] = "../outside/*.cs"
    path = tmp_path / "profile-glob.json"
    path.write_text(json.dumps(data), encoding="ascii")
    assert cli(project, source, project / "o.json", "--snapshot", profile=path) == 2
    assert not (project / "evidence").exists()


def test_a_folder_symlink_that_leaves_the_source_is_refused(project: Path, tmp_path: Path) -> None:
    source = make_source(tmp_path / "src")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "2026-10-20_x.md").write_text("outside\n", encoding="utf-8")
    link = source / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available here")
    profile = profile_with(tmp_path, dir="linked")
    assert cli(project, source, project / "o.json", "--snapshot", profile=profile) == 2


def test_a_real_result_renders_into_a_marked_block_without_change_on_rerun(project: Path, tmp_path: Path) -> None:
    from tools.metrics import render

    source = make_source(tmp_path / "src")
    out = project / "o.json"
    assert cli(project, source, out, "--snapshot") == 0
    doc = project / "EVIDENCE.md"
    doc.write_text(f"Before\n{render.BEGIN}\n{render.END}\nAfter\n", encoding="utf-8", newline="\n")
    assert render.main(["--doc", str(doc), str(out)], root=project) == 0
    first = doc.read_bytes()
    text = first.decode("utf-8")
    for mid in ("M3", "M8", "M9", "M12", "M13"):
        assert f"\n{mid}: " in text
    assert text.startswith("Before\n") and text.endswith("After\n")
    assert render.main(["--doc", str(doc), str(out)], root=project) == 0
    assert doc.read_bytes() == first
