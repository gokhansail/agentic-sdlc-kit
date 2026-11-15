"""`--format csv` of the eight table commands: header, rows, quoting and line ends."""
import csv
import datetime as dt
import io

from budgetbook.ledger import Ledger


def text(*lines):
    return "".join(line + "\n" for line in lines)


def parse(out):
    return list(csv.reader(io.StringIO(out, newline="")))


def test_list_csv_is_the_exact_text_with_no_total_line(run, rich):
    code, out, err = run("list", "--format", "csv")
    assert (code, err) == (0, "")
    assert out == text(
        "id,date,amount,account,category,description",
        "6,2024-02-10,-800.00,main,housing,rent",
        "7,2024-02-14,-50.00,cash,food/groceries,February shop",
        "1,2024-03-01,2500.00,main,salary,March salary",
        "2,2024-03-05,-42.80,main,food/groceries,weekly shop",
        "3,2024-03-12,-15.50,main,food/eating out,lunch",
        "4,2024-03-15,-900.00,main,housing,rent",
        '8,2024-03-20,300.00,cash,gifts,"Birthday money, from grandma"',
        '9,2024-03-22,-64.25,cash,transport,"Monthly pass ""city zone"" extended to next month"',
        "10,2024-03-28,-20.00,savings,savings,",
        "5,2024-04-02,-9.99,main,food/groceries,milk",
    )
    out = run("list", "--category", "food", "--format", "csv")[1]
    assert out == text(
        "id,date,amount,account,category,description",
        "7,2024-02-14,-50.00,cash,food/groceries,February shop",
        "2,2024-03-05,-42.80,main,food/groceries,weekly shop",
        "3,2024-03-12,-15.50,main,food/eating out,lunch",
        "5,2024-04-02,-9.99,main,food/groceries,milk",
    )


def test_list_csv_does_not_cut_long_descriptions(run, lengths):
    out = run("list", "--format", "csv")[1]
    assert out == text(
        "id,date,amount,account,category,description",
        "1,2024-06-01,-1.00,main,food,abcdefghijklmnopqrstuvwxyz0123",
        "2,2024-06-02,-2.00,main,food,abcdefghijklmnopqrstuvwxyz01234",
        "3,2024-06-03,-3.00,main,food," + "x" * 60,
    )


def test_csv_quotes_a_field_with_a_line_break(run, data_file):
    ledger = Ledger()
    ledger.add(dt.date(2024, 7, 1), -500, "food", "line one\nline two")
    ledger.add(dt.date(2024, 7, 2), -600, "food", "plain")
    ledger.save(data_file)
    out = run("list", "--format", "csv")[1]
    assert out == (
        "id,date,amount,account,category,description\n"
        '1,2024-07-01,-5.00,main,food,"line one\nline two"\n'
        "2,2024-07-02,-6.00,main,food,plain\n"
    )
    assert [row[5] for row in parse(out)[1:]] == ["line one\nline two", "plain"]


def test_csv_line_ends_and_an_empty_list(run, rich, data_file):
    for command in (("list",), ("report", "2024-03"), ("summary", "2024"), ("forecast", "2024-03")):
        code, out, err = run(*command, "--format", "csv")
        assert code == 0 and err == ""
        assert out.endswith("\n") and not out.endswith("\n\n")
        assert "\r" not in out
    data_file.unlink()
    code, out, _ = run("list", "--format", "csv")
    assert code == 0
    assert out == "id,date,amount,account,category,description\n"


def test_top_csv(run, rich):
    assert run("top", "2024-03", "--count", "2", "--format", "csv")[1] == text(
        "category,expenses",
        "housing,900.00",
        "transport,64.25",
    )
    assert run("top", "2024-05", "--format", "csv")[1] == "category,expenses\n"


def test_report_csv_is_the_category_table_only(run, rich):
    assert run("report", "2024-03", "--format", "csv")[1] == text(
        "category,total",
        "food/eating out,-15.50",
        "food/groceries,-42.80",
        "gifts,300.00",
        "housing,-900.00",
        "salary,2500.00",
        "savings,-20.00",
        "transport,-64.25",
    )
    assert run("report", "2024-05", "--format", "csv")[1] == "category,total\n"


def test_summary_csv_has_the_twelve_months_and_no_year_row(run, rich):
    out = run("summary", "2024", "--format", "csv")[1]
    table = parse(out)
    assert table[0] == ["month", "income", "expenses", "net"]
    assert len(table) == 13
    assert [row[0] for row in table[1:]] == [f"2024-{number:02d}" for number in range(1, 13)]
    assert table[2] == ["2024-02", "0.00", "850.00", "-850.00"]
    assert table[3] == ["2024-03", "2800.00", "1042.55", "1757.45"]
    assert "Year" not in out and "1902.54" not in out
    zero = parse(run("summary", "2023", "--format", "csv")[1])
    assert len(zero) == 13 and all(row[1:] == ["0.00", "0.00", "0.00"] for row in zero[1:])


def test_accounts_csv_has_no_total_line(run, rich):
    assert run("accounts", "--format", "csv")[1] == text(
        "account,balance",
        "cash,185.75",
        "main,731.71",
        "savings,-20.00",
    )
    assert run("accounts", "--as-of", "2020-01-01", "--format", "csv")[1] == "account,balance\n"


def test_compare_csv_is_one_row(run, rich):
    header = "month,expenses,previous_expenses,change,change_percent"
    assert run("compare", "2024-03", "--format", "csv")[1] == text(header, "2024-03,1042.55,850.00,192.55,22.7")
    assert run("compare", "2024-04", "--format", "csv")[1] == text(header, "2024-04,9.99,1042.55,-1032.56,-99.0")
    assert run("compare", "2024-02", "--format", "csv")[1] == text(header, "2024-02,850.00,0.00,850.00,")


def test_forecast_csv_has_no_title_and_no_net_line(run, rich):
    assert run("forecast", "2024-02", "--format", "csv")[1] == text(
        "date,name,amount,category,account",
        "2024-02-01,salary,2500.00,salary,bank",
        "2024-02-02,gym,-30.00,health,cash",
        "2024-02-09,gym,-30.00,health,cash",
        "2024-02-15,insurance,-480.00,insurance,main",
        "2024-02-16,gym,-30.00,health,cash",
        "2024-02-23,gym,-30.00,health,cash",
        "2024-02-29,rent,-900.00,housing,main",
    )
    assert run("forecast", "2023-05", "--format", "csv")[1] == "date,name,amount,category,account\n"


def test_budget_list_csv(run, rich, data_file):
    assert run("budget", "list", "--format", "csv")[1] == text(
        "category,limit",
        "eating out,100.00",
        "food,400.00",
        "housing,1000.00",
    )
    data_file.unlink()
    assert run("budget", "list", "--format", "csv")[1] == "category,limit\n"
