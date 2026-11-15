"""The `--format` option itself: which values it takes, where it is accepted, what stays as it was."""
import json

TABLE_COMMANDS = [
    ("list",),
    ("report", "2024-03"),
    ("top", "2024-03"),
    ("summary", "2024"),
    ("compare", "2024-03"),
    ("accounts",),
    ("forecast", "2024-03"),
    ("budget", "list"),
]


def test_an_unknown_format_is_wrong_usage(run, rich):
    before = rich.read_bytes()
    for command in TABLE_COMMANDS:
        code, out, err = run(*command, "--format", "xml")
        assert code == 2, command
        assert out == "", command
        assert "xml" in err, command
    assert rich.read_bytes() == before


def test_the_format_name_must_be_written_exactly(run, rich):
    for value in ("JSON", "Csv", "TEXT", "", "json "):
        code, out, err = run("list", "--format", value)
        assert code == 2 and out == "", repr(value)
        assert err != ""


def test_the_format_may_come_before_the_positional_argument(run, rich):
    _, before, _ = run("report", "--format", "json", "2024-03")
    _, after, _ = run("report", "2024-03", "--format", "json")
    assert json.loads(before)["month"] == "2024-03"
    assert before == after
    top = run("top", "--format", "json", "2024-03", "--count", "1")
    assert json.loads(top[1])["categories"] == [{"category": "housing", "expenses": "900.00"}]


def test_other_commands_do_not_take_the_option(run, rich):
    before = rich.read_bytes()
    for command in (
        ("add", "2024-03-05", "5", "x"),
        ("edit", "1", "--amount", "5"),
        ("remove", "1"),
        ("installments", "100", "3", "2024-05-31", "furniture"),
        ("export", "-"),
        ("import", "bank.csv"),
        ("recurring", "add", "rent", "-900", "housing", "monthly", "2024-01-31"),
        ("recurring", "list"),
        ("budget", "set", "food", "10"),
        ("budget", "remove", "food"),
    ):
        code, out, err = run(*command, "--format", "json")
        assert code == 2, command
        assert out == "", command
    assert rich.read_bytes() == before


def test_other_commands_print_what_they_printed_before(run, data_file):
    assert run("add", "2024-03-05", "-42.80", "Food/Groceries", "weekly shop")[1] == "Added 1: 2024-03-05 -42.80 food/groceries\n"
    assert run("add", "2024-03-06", "10", "gifts", "--account", "cash")[1] == "Added 2: 2024-03-06 10.00 gifts\n"
    assert run("edit", "2", "--amount", "-50", "--category", "Eating  Out")[1] == "Updated 2: 2024-03-06 -50.00 eating out\n"
    assert run("remove", "1")[1] == "Removed 1: 2024-03-05 food/groceries\n"
    assert run("installments", "100", "3", "2024-05-31", "furniture", "sofa")[1] == "Booked 3 installments, ids 3 to 5.\n"
    assert run("recurring", "add", "rent", "-900", "housing", "monthly", "2024-01-31")[1] == "Added recurring item rent.\n"
    assert run("recurring", "list")[1] == "rent: -900.00 monthly from 2024-01-31\n"
    assert run("budget", "set", "Eating Out", "200")[1] == "Budget for eating out set.\n"
    assert run("budget", "remove", "eating out")[1] == "Budget for eating out removed.\n"


def test_import_prints_what_it_printed_before(run, data_file, tmp_path):
    source = tmp_path / "bank.csv"
    source.write_text("date,amount,category\n2024-03-05,-5,food\n", encoding="utf-8")
    assert run("import", str(source))[1] == "Imported 1 transaction.\n"
    assert run("import", str(source), "--skip-duplicates")[1] == "Imported 0 transactions.\n"


def test_a_failing_edit_keeps_its_error_line(run, rich):
    code, out, err = run("remove", "99")
    assert code == 1 and out == ""
    assert err.startswith("error: no transaction with id 99")
    code, out, err = run("edit", "1")
    assert code == 1 and out == ""
    assert err.startswith("error: nothing to change")


def test_export_keeps_its_own_columns(run, data_file):
    run("add", "2024-03-06", "10", "gifts", "gift card", "--account", "cash")
    code, out, _ = run("export", "-")
    assert code == 0
    assert out == (
        "id,date,amount,category,description,account\n"
        "1,2024-03-06,10.00,gifts,gift card,cash\n"
    )


def test_errors_while_running_are_the_same_in_every_format(run, data_file):
    data_file.write_text("not json", encoding="utf-8")
    for fmt in ("text", "json", "csv"):
        code, out, err = run("list", "--format", fmt)
        assert code == 1, fmt
        assert out == "", fmt
        assert err.startswith("error: "), fmt


def test_a_bad_argument_is_still_wrong_usage_in_every_format(run, rich):
    for fmt in ("text", "json", "csv"):
        for command in (("report", "2024-13"), ("report", "March"), ("compare", "x"), ("top", "2024-3")):
            code, out, err = run(*command, "--format", fmt)
            assert code == 2 and out == "" and err != "", (fmt, command)


def test_reading_commands_leave_the_ledger_file_alone(run, rich):
    before = rich.read_bytes()
    for fmt in ("text", "json", "csv"):
        for command in TABLE_COMMANDS:
            assert run(*command, "--format", fmt)[0] == 0
    assert rich.read_bytes() == before
