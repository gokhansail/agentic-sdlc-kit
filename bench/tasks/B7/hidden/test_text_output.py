"""The text output of the eight table commands is what it was before the rebuild, byte for byte.

The expected text was taken from the project as shipped, before any change. The last tests copy
the output checks of the project's own suite, because a rebuild may edit that suite.
"""
import datetime as dt

from budgetbook.ledger import Ledger


def text(*lines):
    return "".join(line + "\n" for line in lines)


# -- list ---------------------------------------------------------------------


def test_list_text_is_unchanged(run, rich):
    code, out, err = run("list")
    assert (code, err) == (0, "")
    assert out == text(
        "ID  Date         Amount  Account  Category         Description",
        " 6  2024-02-10  -800.00  main     housing          rent",
        " 7  2024-02-14   -50.00  cash     food/groceries   February shop",
        " 1  2024-03-01  2500.00  main     salary           March salary",
        " 2  2024-03-05   -42.80  main     food/groceries   weekly shop",
        " 3  2024-03-12   -15.50  main     food/eating out  lunch",
        " 4  2024-03-15  -900.00  main     housing          rent",
        " 8  2024-03-20   300.00  cash     gifts            Birthday money, from grandma",
        ' 9  2024-03-22   -64.25  cash     transport        Monthly pass "city zone" exten...',
        "10  2024-03-28   -20.00  savings  savings",
        " 5  2024-04-02    -9.99  main     food/groceries   milk",
        "Total: 897.46 (10 transactions)",
    )
    assert run("list", "--category", "food")[1] == text(
        "ID  Date        Amount  Account  Category         Description",
        " 7  2024-02-14  -50.00  cash     food/groceries   February shop",
        " 2  2024-03-05  -42.80  main     food/groceries   weekly shop",
        " 3  2024-03-12  -15.50  main     food/eating out  lunch",
        " 5  2024-04-02   -9.99  main     food/groceries   milk",
        "Total: -118.29 (4 transactions)",
    )
    assert run("list", "--search", "pass")[1] == text(
        "ID  Date        Amount  Account  Category   Description",
        ' 9  2024-03-22  -64.25  cash     transport  Monthly pass "city zone" exten...',
        "Total: -64.25 (1 transaction)",
    )


def test_list_text_cuts_a_long_description_after_30_characters(run, lengths):
    assert run("list")[1] == text(
        "ID  Date        Amount  Account  Category  Description",
        " 1  2024-06-01   -1.00  main     food      abcdefghijklmnopqrstuvwxyz0123",
        " 2  2024-06-02   -2.00  main     food      abcdefghijklmnopqrstuvwxyz0123...",
        " 3  2024-06-03   -3.00  main     food      xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...",
        "Total: -6.00 (3 transactions)",
    )


# -- the other table commands ---------------------------------------------------


def test_report_text_is_unchanged(run, rich):
    assert run("report", "2024-03")[1] == text(
        "Report 2024-03",
        "Income: 2800.00",
        "Expenses: 1042.55",
        "Net: 1757.45",
        "By category:",
        "  food/eating out: -15.50",
        "  food/groceries: -42.80",
        "  gifts: 300.00",
        "  housing: -900.00",
        "  salary: 2500.00",
        "  savings: -20.00",
        "  transport: -64.25",
    )


def test_top_text_is_unchanged(run, rich):
    assert run("top", "2024-03")[1] == text(
        "Category   Expenses",
        "housing      900.00",
        "transport     64.25",
        "food          58.30",
        "savings       20.00",
    )
    assert run("top", "2024-03", "--count", "2")[1] == text(
        "Category   Expenses",
        "housing      900.00",
        "transport     64.25",
    )


def test_summary_text_is_unchanged(run, rich):
    assert run("summary", "2024")[1] == text(
        "Summary 2024",
        "Month   Income  Expenses      Net",
        "Jan       0.00      0.00     0.00",
        "Feb       0.00    850.00  -850.00",
        "Mar    2800.00   1042.55  1757.45",
        "Apr       0.00      9.99    -9.99",
        "May       0.00      0.00     0.00",
        "Jun       0.00      0.00     0.00",
        "Jul       0.00      0.00     0.00",
        "Aug       0.00      0.00     0.00",
        "Sep       0.00      0.00     0.00",
        "Oct       0.00      0.00     0.00",
        "Nov       0.00      0.00     0.00",
        "Dec       0.00      0.00     0.00",
        "Year   2800.00   1902.54   897.46",
    )


def test_accounts_text_is_unchanged(run, rich):
    assert run("accounts")[1] == text(
        "Account  Balance",
        "cash      185.75",
        "main      731.71",
        "savings   -20.00",
        "Total: 897.46",
    )
    assert run("accounts", "--as-of", "2024-03-10")[1] == text(
        "Account  Balance",
        "cash      -50.00",
        "main     1657.20",
        "Total: 1607.20",
    )


def test_compare_text_is_unchanged(run, rich, data_file):
    assert run("compare", "2024-03")[1] == text(
        "Expenses 2024-03: 1042.55",
        "Expenses before: 850.00",
        "Change: 192.55",
        "Change in percent: 22.7%",
    )
    assert run("compare", "2024-04")[1] == text(
        "Expenses 2024-04: 9.99",
        "Expenses before: 1042.55",
        "Change: -1032.56",
        "Change in percent: -99.0%",
    )
    assert run("compare", "2024-02")[1] == text(
        "Expenses 2024-02: 850.00",
        "Expenses before: 0.00",
        "Change: 850.00",
        "Change in percent: not available",
    )
    ledger = Ledger()
    ledger.add(dt.date(2024, 2, 10), -16, "food", "x")
    ledger.add(dt.date(2024, 3, 10), -17, "food", "x")
    ledger.save(data_file)
    assert run("compare", "2024-03")[1].splitlines()[-1] == "Change in percent: 6.3%"


def test_forecast_text_is_unchanged(run, rich):
    assert run("forecast", "2024-02")[1] == text(
        "Forecast 2024-02",
        "Date        Name        Amount  Category   Account",
        "2024-02-01  salary     2500.00  salary     bank",
        "2024-02-02  gym         -30.00  health     cash",
        "2024-02-09  gym         -30.00  health     cash",
        "2024-02-15  insurance  -480.00  insurance  main",
        "2024-02-16  gym         -30.00  health     cash",
        "2024-02-23  gym         -30.00  health     cash",
        "2024-02-29  rent       -900.00  housing    main",
        "Net: 1000.00",
    )


def test_budget_list_text_is_unchanged(run, rich):
    assert run("budget", "list")[1] == text(
        "Category    Monthly limit",
        "eating out         100.00",
        "food               400.00",
        "housing           1000.00",
    )


# -- empty results ------------------------------------------------------------


def test_empty_results_text_is_unchanged(run, rich, data_file):
    """Months and years without bookings first, then a ledger file that does not exist."""
    assert run("report", "2024-05")[1] == text("Report 2024-05", "Income: 0.00", "Expenses: 0.00", "Net: 0.00")
    assert run("top", "2024-05")[1] == "No expenses.\n"
    assert run("accounts", "--as-of", "2020-01-01")[1] == "No accounts.\n"
    assert run("forecast", "2023-05")[1] == "Nothing expected in 2023-05.\n"
    assert run("summary", "2023")[1].splitlines()[-1] == "Year     0.00      0.00  0.00"
    assert len(run("summary", "2023")[1].splitlines()) == 15
    data_file.unlink()
    assert run("list")[1] == "No transactions.\n"
    assert run("top", "2024-03")[1] == "No expenses.\n"
    assert run("accounts")[1] == "No accounts.\n"
    assert run("forecast", "2024-03")[1] == "Nothing expected in 2024-03.\n"
    assert run("budget", "list")[1] == "No budgets set.\n"
    assert run("compare", "2024-03")[1] == text(
        "Expenses 2024-03: 0.00",
        "Expenses before: 0.00",
        "Change: 0.00",
        "Change in percent: not available",
    )
    assert run("report", "2024-03")[1] == text("Report 2024-03", "Income: 0.00", "Expenses: 0.00", "Net: 0.00")


# -- the format option names the default --------------------------------------


def test_format_text_gives_the_same_bytes_as_no_option(run, rich):
    commands = [
        ("list",),
        ("report", "2024-03"),
        ("top", "2024-03"),
        ("summary", "2024"),
        ("compare", "2024-03"),
        ("accounts",),
        ("forecast", "2024-03"),
        ("budget", "list"),
    ]
    for command in commands:
        default = run(*command)
        named = run(*command, "--format", "text")
        assert default[0] == 0 and named == default, command


# -- copies of the output checks of the project's own suite -------------------------


def test_copy_of_visible_checks_list_report_summary_accounts(run, data_file, march):
    code, out, _ = run("list")
    assert code == 0
    assert out.splitlines()[0].split() == ["ID", "Date", "Amount", "Account", "Category", "Description"]
    assert out.splitlines()[-1] == "Total: 1531.71 (5 transactions)"
    _, out, _ = run("list", "--category", "food", "--from", "2024-03-01", "--to", "2024-03-31")
    assert out.splitlines()[-1] == "Total: -58.30 (2 transactions)"
    _, out, _ = run("list", "--search", "rent")
    assert out.splitlines()[-1] == "Total: -900.00 (1 transaction)"
    _, out, _ = run("report", "2024-03")
    assert out.splitlines() == [
        "Report 2024-03",
        "Income: 2500.00",
        "Expenses: 958.30",
        "Net: 1541.70",
        "By category:",
        "  food/eating out: -15.50",
        "  food/groceries: -42.80",
        "  housing: -900.00",
        "  salary: 2500.00",
    ]
    _, out, _ = run("summary", "2024")
    assert out.splitlines()[0] == "Summary 2024"
    assert out.splitlines()[-1].split() == ["Year", "2500.00", "968.29", "1531.71"]
    _, out, _ = run("accounts", "--as-of", "2024-03-31")
    assert out.splitlines()[-1] == "Total: 1541.70"


def test_copy_of_visible_checks_top_compare_forecast_budgets_and_add(run, march):
    _, out, _ = run("top", "2024-03", "--count", "1")
    assert out.splitlines()[1].split() == ["housing", "900.00"]
    _, out, _ = run("compare", "2024-04")
    assert out.splitlines()[-1] == "Change in percent: -99.0%"
    _, out, _ = run("compare", "2024-03")
    assert out.splitlines()[-1] == "Change in percent: not available"
    run("recurring", "add", "rent", "-900", "housing", "monthly", "2024-01-31")
    _, out, _ = run("forecast", "2024-02")
    assert "2024-02-29" in out
    assert out.splitlines()[-1] == "Net: -900.00"
    run("budget", "set", "Eating Out", "200")
    _, out, _ = run("budget", "list")
    assert out.splitlines()[1].split() == ["eating", "out", "200.00"]
    assert run("budget", "remove", "eating out")[0] == 0
    assert run("budget", "list")[1] == "No budgets set.\n"
    march.unlink()
    assert run("list")[1] == "No transactions.\n"
    assert run("add", "2024-03-05", "-42.80", "Food/Groceries", "weekly shop")[0] == 0
    code, out, _ = run("list")
    assert code == 0
    assert "food/groceries" in out and "-42.80" in out
    assert out.splitlines()[-1] == "Total: -42.80 (1 transaction)"
