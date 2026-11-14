import os

import pytest


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    """Empty working folder, no BUDGETBOOK_* variables."""
    monkeypatch.chdir(tmp_path)
    for name in list(os.environ):
        if name.startswith("BUDGETBOOK_"):
            monkeypatch.delenv(name)


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "ledger.json"


@pytest.fixture
def run(capsys, data_file):
    """Run the CLI against the data file; returns (exit code, stdout, stderr)."""
    from budgetbook.cli import main

    def _run(*args):
        try:
            code = main(["--data", str(data_file), *args])
        except SystemExit as exit_info:
            code = exit_info.code
        captured = capsys.readouterr()
        return code, captured.out, captured.err

    return _run
