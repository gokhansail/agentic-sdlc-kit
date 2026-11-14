import pytest

from budgetbook.cli import main
from budgetbook.ledger import Ledger


def run(capsys, data_file, *args):
    code = main(["--data", str(data_file), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_add_then_list(capsys, data_file):
    assert run(capsys, data_file, "add", "2024-03-05", "-42.80", "Food/Groceries", "weekly shop")[0] == 0
    code, out, _ = run(capsys, data_file, "list")
    assert code == 0
    assert "food/groceries" in out and "-42.80" in out
    assert out.splitlines()[-1] == "Total: -42.80 (1 transaction)"


def test_list_filters(capsys, data_file, march_ledger):
    march_ledger.save(data_file)
    _, out, _ = run(capsys, data_file, "list", "--category", "food", "--from", "2024-03-01", "--to", "2024-03-31")
    assert out.splitlines()[-1] == "Total: -58.30 (2 transactions)"
    _, out, _ = run(capsys, data_file, "list", "--search", "rent")
    assert out.splitlines()[-1] == "Total: -900.00 (1 transaction)"


def test_list_on_an_empty_ledger(capsys, data_file):
    assert run(capsys, data_file, "list")[1] == "No transactions.\n"


def test_remove(capsys, data_file, march_ledger):
    march_ledger.save(data_file)
    assert run(capsys, data_file, "remove", "4")[0] == 0
    assert len(Ledger.load(data_file)) == 4
    code, _, err = run(capsys, data_file, "remove", "4")
    assert code == 1
    assert err.startswith("error: no transaction with id 4")


def test_report(capsys, data_file, march_ledger):
    march_ledger.save(data_file)
    _, out, _ = run(capsys, data_file, "report", "2024-03")
    assert out.splitlines()[:4] == ["Report 2024-03", "Income: 2500.00", "Expenses: 958.30", "Net: 1541.70"]


def test_summary_and_accounts(capsys, data_file, march_ledger):
    march_ledger.save(data_file)
    _, out, _ = run(capsys, data_file, "summary", "2024")
    lines = out.splitlines()
    assert lines[0] == "Summary 2024"
    assert lines[-1].split() == ["Year", "2500.00", "968.29", "1531.71"]
    _, out, _ = run(capsys, data_file, "accounts", "--as-of", "2024-03-31")
    assert out.splitlines()[-1] == "Total: 1541.70"


def test_export_and_import_round_trip(capsys, tmp_path, data_file, march_ledger):
    march_ledger.save(data_file)
    csv_file = tmp_path / "out.csv"
    assert run(capsys, data_file, "export", str(csv_file), "--from", "2024-03-01", "--to", "2024-03-31")[0] == 0
    other = tmp_path / "other.json"
    _, out, _ = run(capsys, other, "import", str(csv_file))
    assert out == "Imported 4 transactions.\n"
    assert len(Ledger.load(other)) == 4


def test_export_to_stdout(capsys, data_file, march_ledger):
    march_ledger.save(data_file)
    _, out, _ = run(capsys, data_file, "export", "-")
    assert out.startswith("id,date,amount,category,description,account\n")


def test_import_errors_are_reported_with_the_line(capsys, tmp_path, data_file):
    bad = tmp_path / "bad.csv"
    bad.write_text("date,amount,category\n2024-03-05,x,food\n", encoding="utf-8")
    code, _, err = run(capsys, data_file, "import", str(bad))
    assert code == 1
    assert err.startswith("error: line 2:")


def test_recurring_and_forecast(capsys, data_file):
    run(capsys, data_file, "recurring", "add", "rent", "-900", "housing", "monthly", "2024-01-31")
    _, out, _ = run(capsys, data_file, "recurring", "list")
    assert out.strip() == "rent: -900.00 monthly from 2024-01-31"
    _, out, _ = run(capsys, data_file, "forecast", "2024-02")
    assert "2024-02-29" in out
    assert out.splitlines()[-1] == "Net: -900.00"


def test_budget_commands(capsys, data_file):
    run(capsys, data_file, "budget", "set", "Eating Out", "200")
    _, out, _ = run(capsys, data_file, "budget", "list")
    assert out.splitlines()[1].split() == ["eating", "out", "200.00"]
    assert run(capsys, data_file, "budget", "remove", "eating out")[0] == 0
    assert run(capsys, data_file, "budget", "list")[1] == "No budgets set.\n"


def test_wrong_usage_exits_with_2(capsys, data_file):
    for args in (["add", "2024-13-01", "5", "x"], ["report", "March"], ["add", "2024-03-05", "abc", "x"]):
        with pytest.raises(SystemExit) as info:
            main(["--data", str(data_file), *args])
        assert info.value.code == 2
    capsys.readouterr()


def test_edit_changes_only_the_given_fields(capsys, data_file, march_ledger):
    march_ledger.save(data_file)
    code, out, _ = run(capsys, data_file, "edit", "2", "--amount", "-50", "--category", "Eating  Out")
    assert code == 0
    assert out == "Updated 2: 2024-03-05 -50.00 eating out\n"
    changed = Ledger.load(data_file).get(2)
    assert changed.description == "weekly shop"
    code, _, err = run(capsys, data_file, "edit", "2")
    assert code == 1 and err.startswith("error: nothing to change")


def test_top_and_compare(capsys, data_file, march_ledger):
    march_ledger.save(data_file)
    _, out, _ = run(capsys, data_file, "top", "2024-03", "--count", "1")
    assert out.splitlines()[1].split() == ["housing", "900.00"]
    _, out, _ = run(capsys, data_file, "compare", "2024-04")
    assert out.splitlines()[-1] == "Change in percent: -99.0%"
    _, out, _ = run(capsys, data_file, "compare", "2024-03")
    assert out.splitlines()[-1] == "Change in percent: not available"


def test_installments_command(capsys, data_file):
    code, out, _ = run(capsys, data_file, "installments", "100", "3", "2024-05-31", "furniture", "sofa")
    assert code == 0
    assert out == "Booked 3 installments, ids 1 to 3.\n"
    dates = [tx.date.isoformat() for tx in Ledger.load(data_file).all()]
    assert dates == ["2024-05-31", "2024-06-30", "2024-07-31"]


def test_import_skip_duplicates(capsys, tmp_path, data_file):
    source = tmp_path / "bank.csv"
    source.write_text("date,amount,category\n2024-03-05,-5,food\n", encoding="utf-8")
    run(capsys, data_file, "import", str(source))
    _, out, _ = run(capsys, data_file, "import", str(source), "--skip-duplicates")
    assert out == "Imported 0 transactions.\n"
    assert len(Ledger.load(data_file)) == 1


def test_data_file_comes_from_the_environment(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGETBOOK_DATA_FILE", str(tmp_path / "env.json"))
    assert main(["add", "2024-03-05", "-5", "food"]) == 0
    capsys.readouterr()
    assert (tmp_path / "env.json").is_file()
