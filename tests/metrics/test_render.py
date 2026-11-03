"""The table render: block content, marker handling, idempotence, refusals."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.metrics import render
from tools.metrics.render import BEGIN, END, RenderError, render_block, rewrite

from conftest import ROOT

SHA = "e" * 64
HEAD = "f" * 40


def result(label: str, metrics: dict, warnings: dict | None = None) -> dict:
    return {
        "schema": 1,
        "label": label,
        "cutoff": "2026-10-25",
        "kit_commit": None,
        "input": {"head": HEAD, "dirty": False, "files": {"log": SHA}, "profile_sha256": SHA},
        "metrics": metrics,
        "warnings": warnings or {},
    }


M1_OK = {"status": "ok", "v1": {"n": 10, "count": 3, "items": 1}, "v2": {"n": 4, "count": 1, "items": 0}}
NO_DATA = {"status": "no data"}


def doc(body: str = "old block\n") -> str:
    return f"# Evidence\n\nIntro text.\n\n{BEGIN}\n{body}{END}\n\nClosing text.\n"


# --- block content ----------------------------------------------------------------

def test_one_table_per_metric_with_source_rows_and_period_columns() -> None:
    block = render_block([result("project-a", {"M1": M1_OK}), result("kit", {"M1": NO_DATA})])
    assert block == "\n".join(
        [
            "M1: Reverted versions",
            "",
            "| Source | v1 | v2 |",
            "|---|---|---|",
            "| project-a | 3 of 10 (30%); item reverts 1 | 1 of 4; item reverts 0 |",
            "| kit | no data | no data |",
        ]
    )


def test_a_cell_under_five_items_shows_the_count_and_no_rate() -> None:
    four = {"status": "ok", "v1": {"n": 4, "count": 2, "items": 0}, "v2": {"n": 5, "count": 2, "items": 0}}
    block = render_block([result("a", {"M1": four})])
    assert "| 2 of 4; item reverts 0 |" in block and "2 of 5 (40%)" in block
    assert "%" not in block.split("2 of 5")[0]


def test_percent_rounds_halves_up_with_integer_arithmetic() -> None:
    assert render.percent(1, 8) == "13%" and render.percent(1, 3) == "33%" and render.percent(2, 3) == "67%"
    assert render.per_week(5, 4) == "1.25" and render.per_week(1, 3) == "0.33"


def test_no_data_stays_no_data_and_an_empty_period_is_marked() -> None:
    block = render_block([result("a", {"M9": {"status": "ok", "v1": {"n": 0}, "v2": {"n": 6, "count": 3}}})])
    assert "| a | no items | 3 of 6 (50%) |" in block
    assert "no data" not in render_block([result("a", {"M9": {"status": "ok", "v1": {"n": 5, "count": 5}, "v2": {"n": 0}}})])


def test_undated_column_appears_only_when_it_holds_items() -> None:
    with_undated = {"status": "ok", "v1": {"n": 0}, "v2": {"n": 0}, "undated": {"n": 6, "count": 1}}
    assert "| Source | v1 | v2 | undated |" in render_block([result("a", {"M9": with_undated})])
    empty_undated = dict(with_undated, undated={"n": 0})
    assert "undated" not in render_block([result("a", {"M9": empty_undated})])


def test_every_metric_layout_renders() -> None:
    cells = {
        "M2": {"status": "ok", "v1": {"n": 6, "count": 2, "no_change": 1}, "v2": {"n": 0}},
        "M3": {"status": "ok", "v1": {"n": 2, "count": 3, "weeks": {"2026-W41": 1, "2026-W42": 3}}, "v2": {"n": 0}},
        "M5": {"status": "ok", "v1": {"n": 5, "distribution": {"0": 1, "1": 2, "2": 2, "3+": 0}}, "v2": {"n": 2, "distribution": {"0": 1, "1": 1, "2": 0, "3+": 0}}},
        "M6": {"status": "ok", "v1": {"questions_back": {"n": 5, "count": 2}, "out_of_scope": {"n": 0}}, "v2": {"questions_back": {"n": 0}, "out_of_scope": {"n": 0}}},
        "M8": {"status": "ok", "v1": {"n": 2, "severity": {"high": 1, "low": 1}, "latest": {"closed": 1, "none": 1}, "days_to_closed": {"0": 1}}, "v2": {"n": 0}},
        "M12": {"status": "ok", "v1": {"n": 12, "count": 10, "versions": 2, "weeks": 4}, "v2": {"n": 3, "count": 3, "weeks": 2}},
        "M13": {"status": "ok", "v1": {"n": 6, "distribution": {"E": 3, "M": 1, "H": 2}, "done": 5}, "v2": {"n": 0}},
    }
    block = render_block([result("a", cells)])
    for mid in cells:
        assert f"\n{mid}: " in "\n" + block
    assert "| a | 3 in 2026-W42; 2 weeks | no items |" in block
    assert "commits 10 (2.50 per week); versions 2; 4 weeks" in block  # versions under 5: no rate
    assert "commits 3; 2 weeks" in block  # a cell under 5 items: no rate
    assert "hard 2 of 6 (33%); E 3, M 1, H 2; done 5" in block
    assert "0: 1 (20%); 1: 2 (40%); 2: 2 (40%); 3+: 0 (0%); n 5" in block
    assert "0: 1; 1: 1; 2: 0; 3+: 0; n 2" in block
    assert "questions back 2 of 5 (40%); out of scope n 0" in block


def test_metric_tables_come_in_numeric_order() -> None:
    m2 = {"status": "ok", "v1": {"n": 1, "count": 1, "no_change": 0}, "v2": {"n": 0}}
    m12 = {"status": "ok", "v1": {"n": 1, "count": 1, "weeks": 1}, "v2": {"n": 0}}
    block = render_block([result("a", {"M2": m2, "M12": m12, "M1": M1_OK})])
    order = [line.split(":")[0] for line in block.splitlines() if line[:1] == "M"]
    assert order == ["M1", "M2", "M12"]


def test_two_results_with_one_label_are_refused() -> None:
    with pytest.raises(RenderError):
        render_block([result("a", {"M1": M1_OK}), result("a", {"M1": M1_OK})])


# --- markers ----------------------------------------------------------------------

def test_only_the_text_between_the_markers_changes() -> None:
    original = doc("old block\nmore old\n")
    new = rewrite(original, "NEW")
    assert new == doc("NEW\n")
    assert new.startswith("# Evidence\n\nIntro text.\n\n") and new.endswith("\n\nClosing text.\n")


def test_rewriting_twice_gives_no_diff() -> None:
    block = render_block([result("a", {"M1": M1_OK})])
    once = rewrite(doc(), block)
    assert rewrite(once, block) == once


def test_missing_doubled_or_reversed_markers_are_refused() -> None:
    with pytest.raises(RenderError):
        rewrite("no markers\n", "x")
    with pytest.raises(RenderError):
        rewrite(f"{BEGIN}\n", "x")
    with pytest.raises(RenderError):
        rewrite(f"{END}\n", "x")
    with pytest.raises(RenderError):
        rewrite(doc() + f"{BEGIN}\n{END}\n", "x")
    with pytest.raises(RenderError):
        rewrite(f"{END}\nx\n{BEGIN}\n", "x")


def test_a_document_with_crlf_line_ends_keeps_them() -> None:
    crlf = doc().replace("\n", "\r\n")
    new = rewrite(crlf, "line one\nline two")
    assert "\r\n" in new and "\n" not in new.replace("\r\n", "")
    assert f"{BEGIN}\r\nline one\r\nline two\r\n{END}" in new


# --- command line -----------------------------------------------------------------

@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "kit"
    root.mkdir()
    return root


def write_result(root: Path, name: str, data: dict) -> Path:
    path = root / name
    path.write_text(json.dumps(data), encoding="ascii")
    return path


def run(root: Path, *args: str) -> int:
    return render.main(list(args), root=root)


def test_cli_rewrites_the_block_and_a_second_run_changes_nothing(project: Path) -> None:
    a = write_result(project, "a.json", result("project-a", {"M1": M1_OK}))
    k = write_result(project, "k.json", result("kit", {"M1": NO_DATA}))
    target = project / "EVIDENCE.md"
    target.write_text(doc(), encoding="utf-8", newline="\n")
    assert run(project, "--doc", str(target), str(a), str(k)) == 0
    first = target.read_bytes()
    assert b"| project-a | 3 of 10 (30%)" in first and first.startswith(b"# Evidence\n\nIntro text.")
    assert run(project, "--doc", str(target), str(a), str(k)) == 0
    assert target.read_bytes() == first


def test_cli_refuses_a_result_with_free_text_and_leaves_the_document(project: Path, capsys) -> None:
    bad = result("project-a", {"M1": M1_OK})
    bad["label"] = "Some record text, with spaces"
    path = write_result(project, "bad.json", bad)
    target = project / "EVIDENCE.md"
    target.write_text(doc(), encoding="utf-8", newline="\n")
    assert run(project, "--doc", str(target), str(path)) == 2
    assert target.read_text(encoding="utf-8") == doc()
    assert "Some record text" not in capsys.readouterr().err


def test_cli_refuses_a_document_without_markers_and_leaves_it(project: Path) -> None:
    path = write_result(project, "a.json", result("a", {"M1": M1_OK}))
    target = project / "EVIDENCE.md"
    target.write_text("# No markers here\n", encoding="utf-8", newline="\n")
    assert run(project, "--doc", str(target), str(path)) == 2
    assert target.read_text(encoding="utf-8") == "# No markers here\n"


def test_cli_refuses_a_file_that_is_not_json(project: Path) -> None:
    path = project / "a.json"
    path.write_text("{nope", encoding="ascii")
    target = project / "EVIDENCE.md"
    target.write_text(doc(), encoding="utf-8", newline="\n")
    assert run(project, "--doc", str(target), str(path)) == 2


def test_cli_refuses_paths_outside_the_project_root(project: Path, tmp_path: Path) -> None:
    outside_doc = tmp_path / "outside.md"
    outside_doc.write_text(doc(), encoding="utf-8", newline="\n")
    inside = write_result(project, "a.json", result("a", {"M1": M1_OK}))
    assert run(project, "--doc", str(outside_doc), str(inside)) == 2
    assert outside_doc.read_text(encoding="utf-8") == doc()
    target = project / "EVIDENCE.md"
    target.write_text(doc(), encoding="utf-8", newline="\n")
    outside_json = tmp_path / "b.json"
    outside_json.write_text(json.dumps(result("b", {"M1": M1_OK})), encoding="ascii")
    assert run(project, "--doc", str(target), str(outside_json)) == 2
    dotdot = project / "sub" / ".." / ".." / "b.json"
    assert run(project, "--doc", str(target), str(dotdot)) == 2
    assert target.read_text(encoding="utf-8") == doc()


def test_cli_module_entry_point_runs() -> None:
    import subprocess
    import sys

    res = subprocess.run([sys.executable, "-m", "tools.metrics.render", "--help"], cwd=ROOT, capture_output=True, text=True)
    assert res.returncode == 0 and "--doc" in res.stdout
