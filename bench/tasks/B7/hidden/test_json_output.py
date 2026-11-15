"""`--format json` of the eight table commands: the document, the key order, the value types."""
import datetime as dt
import json

from budgetbook.ledger import Ledger

LIST_KEYS = ["id", "date", "amount", "account", "category", "description"]


def load(out):
    document = json.loads(out)
    assert isinstance(document, dict)
    return document


def rows(document, name, keys):
    """The rows under ``name``, each checked for its keys in order, as tuples of values."""
    records = document[name]
    assert all(list(record) == keys for record in records), records
    return [tuple(record.values()) for record in records]


def test_list_json_has_the_rows_total_and_count(run, rich):
    code, out, err = run("list", "--format", "json")
    assert (code, err) == (0, "")
    document = load(out)
    assert list(document) == ["transactions", "total", "count"]
    assert rows(document, "transactions", LIST_KEYS) == [
        (6, "2024-02-10", "-800.00", "main", "housing", "rent"),
        (7, "2024-02-14", "-50.00", "cash", "food/groceries", "February shop"),
        (1, "2024-03-01", "2500.00", "main", "salary", "March salary"),
        (2, "2024-03-05", "-42.80", "main", "food/groceries", "weekly shop"),
        (3, "2024-03-12", "-15.50", "main", "food/eating out", "lunch"),
        (4, "2024-03-15", "-900.00", "main", "housing", "rent"),
        (8, "2024-03-20", "300.00", "cash", "gifts", "Birthday money, from grandma"),
        (9, "2024-03-22", "-64.25", "cash", "transport", 'Monthly pass "city zone" extended to next month'),
        (10, "2024-03-28", "-20.00", "savings", "savings", ""),
        (5, "2024-04-02", "-9.99", "main", "food/groceries", "milk"),
    ]
    assert document["total"] == "897.46"
    assert document["count"] == 10 and type(document["count"]) is int
    assert all(type(record["id"]) is int for record in document["transactions"])
    document = load(run("list", "--account", "cash", "--format", "json")[1])
    assert [record["id"] for record in document["transactions"]] == [7, 8, 9]
    assert (document["total"], document["count"]) == ("185.75", 3)


def test_list_json_does_not_cut_long_descriptions(run, lengths):
    document = load(run("list", "--format", "json")[1])
    assert [record["description"] for record in document["transactions"]] == [
        "abcdefghijklmnopqrstuvwxyz0123",
        "abcdefghijklmnopqrstuvwxyz01234",
        "x" * 60,
    ]


def test_list_json_when_nothing_is_listed(run, data_file):
    code, out, _ = run("list", "--format", "json")
    assert code == 0
    document = load(out)
    assert list(document) == ["transactions", "total", "count"]
    assert document == {"transactions": [], "total": "0.00", "count": 0}


def test_top_json(run, rich):
    document = load(run("top", "2024-03", "--count", "2", "--format", "json")[1])
    assert list(document) == ["categories"]
    assert rows(document, "categories", ["category", "expenses"]) == [("housing", "900.00"), ("transport", "64.25")]
    assert load(run("top", "2024-05", "--format", "json")[1]) == {"categories": []}


def test_report_json_has_the_month_figures_and_the_categories(run, rich):
    code, out, _ = run("report", "2024-03", "--format", "json")
    assert code == 0
    document = load(out)
    assert list(document) == ["month", "income", "expenses", "net", "categories"]
    assert (document["month"], document["income"], document["expenses"], document["net"]) == (
        "2024-03",
        "2800.00",
        "1042.55",
        "1757.45",
    )
    assert rows(document, "categories", ["category", "total"]) == [
        ("food/eating out", "-15.50"),
        ("food/groceries", "-42.80"),
        ("gifts", "300.00"),
        ("housing", "-900.00"),
        ("salary", "2500.00"),
        ("savings", "-20.00"),
        ("transport", "-64.25"),
    ]
    document = load(run("report", "2024-05", "--format", "json")[1])
    assert list(document) == ["month", "income", "expenses", "net", "categories"]
    assert document == {
        "month": "2024-05",
        "income": "0.00",
        "expenses": "0.00",
        "net": "0.00",
        "categories": [],
    }


def test_summary_json_has_twelve_months_and_a_total(run, rich):
    code, out, _ = run("summary", "2024", "--format", "json")
    assert code == 0
    document = load(out)
    assert list(document) == ["year", "months", "total"]
    assert document["year"] == 2024 and type(document["year"]) is int
    months = rows(document, "months", ["month", "income", "expenses", "net"])
    assert [row[0] for row in months] == [f"2024-{number:02d}" for number in range(1, 13)]
    assert months[0] == ("2024-01", "0.00", "0.00", "0.00")
    assert months[1] == ("2024-02", "0.00", "850.00", "-850.00")
    assert months[2] == ("2024-03", "2800.00", "1042.55", "1757.45")
    assert months[3] == ("2024-04", "0.00", "9.99", "-9.99")
    assert list(document["total"]) == ["income", "expenses", "net"]
    assert document["total"] == {"income": "2800.00", "expenses": "1902.54", "net": "897.46"}
    document = load(run("summary", "2023", "--format", "json")[1])
    assert len(document["months"]) == 12
    assert all(record["income"] == record["expenses"] == record["net"] == "0.00" for record in document["months"])
    assert document["total"] == {"income": "0.00", "expenses": "0.00", "net": "0.00"}


def test_accounts_json(run, rich, data_file):
    document = load(run("accounts", "--format", "json")[1])
    assert list(document) == ["accounts", "total"]
    assert rows(document, "accounts", ["account", "balance"]) == [
        ("cash", "185.75"),
        ("main", "731.71"),
        ("savings", "-20.00"),
    ]
    assert document["total"] == "897.46"
    assert load(run("accounts", "--as-of", "2024-03-10", "--format", "json")[1])["total"] == "1607.20"
    assert load(run("accounts", "--as-of", "2020-01-01", "--format", "json")[1]) == {"accounts": [], "total": "0.00"}


def test_compare_json_is_one_flat_object(run, rich):
    code, out, _ = run("compare", "2024-03", "--format", "json")
    assert code == 0
    document = load(out)
    assert list(document) == ["month", "expenses", "previous_expenses", "change", "change_percent"]
    assert document == {
        "month": "2024-03",
        "expenses": "1042.55",
        "previous_expenses": "850.00",
        "change": "192.55",
        "change_percent": "22.7",
    }
    assert load(run("compare", "2024-04", "--format", "json")[1])["change_percent"] == "-99.0"


def test_compare_json_percent_null_and_rounding(run, rich, data_file):
    document = load(run("compare", "2024-02", "--format", "json")[1])
    assert document["previous_expenses"] == "0.00" and document["change"] == "850.00"
    assert document["change_percent"] is None
    ledger = Ledger()
    ledger.add(dt.date(2024, 2, 10), -16, "food", "x")
    ledger.add(dt.date(2024, 3, 10), -17, "food", "x")
    ledger.save(data_file)
    assert load(run("compare", "2024-03", "--format", "json")[1])["change_percent"] == "6.3"


def test_forecast_json(run, rich):
    document = load(run("forecast", "2024-02", "--format", "json")[1])
    assert list(document) == ["month", "entries", "net"]
    assert document["month"] == "2024-02" and document["net"] == "1000.00"
    assert rows(document, "entries", ["date", "name", "amount", "category", "account"]) == [
        ("2024-02-01", "salary", "2500.00", "salary", "bank"),
        ("2024-02-02", "gym", "-30.00", "health", "cash"),
        ("2024-02-09", "gym", "-30.00", "health", "cash"),
        ("2024-02-15", "insurance", "-480.00", "insurance", "main"),
        ("2024-02-16", "gym", "-30.00", "health", "cash"),
        ("2024-02-23", "gym", "-30.00", "health", "cash"),
        ("2024-02-29", "rent", "-900.00", "housing", "main"),
    ]
    assert load(run("forecast", "2023-05", "--format", "json")[1]) == {"month": "2023-05", "entries": [], "net": "0.00"}


def test_budget_list_json(run, rich, data_file):
    document = load(run("budget", "list", "--format", "json")[1])
    assert list(document) == ["budgets"]
    assert rows(document, "budgets", ["category", "limit"]) == [
        ("eating out", "100.00"),
        ("food", "400.00"),
        ("housing", "1000.00"),
    ]
    data_file.unlink()
    assert load(run("budget", "list", "--format", "json")[1]) == {"budgets": []}


def test_json_output_is_one_document_and_nothing_else(run, rich):
    for command in (("list",), ("report", "2024-03"), ("summary", "2024"), ("budget", "list")):
        code, out, err = run(*command, "--format", "json")
        assert code == 0 and err == ""
        assert out.endswith("}\n") and not out.endswith("\n\n")
        assert out.startswith("{")
        json.loads(out)
