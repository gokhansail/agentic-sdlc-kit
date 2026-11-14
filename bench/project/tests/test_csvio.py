import datetime as dt

import pytest

from budgetbook.csvio import export_csv, import_csv
from budgetbook.errors import CsvImportError
from budgetbook.ledger import Ledger


def test_export_has_header_and_formatted_amounts(march_ledger):
    lines = export_csv(march_ledger.in_month(2024, 3)).splitlines()
    assert lines[0] == "id,date,amount,category,description,account"
    assert lines[1] == "1,2024-03-01,2500.00,salary,March salary,main"
    assert lines[2] == "2,2024-03-05,-42.80,food/groceries,weekly shop,main"


def test_export_quotes_commas_in_descriptions():
    ledger = Ledger()
    ledger.add(dt.date(2024, 3, 5), -100, "food", "bread, milk")
    assert '"bread, milk"' in export_csv(ledger.all())


def test_import_adds_rows_and_ignores_the_id_column():
    ledger = Ledger()
    text = "id,date,amount,category,description\n99,2024-03-05,-42.80,Food,shop\n98,2024-03-06,10,salary,\n"
    assert import_csv(ledger, text) == 2
    assert [tx.id for tx in ledger.all()] == [1, 2]
    assert ledger.get(1).category == "food"
    assert ledger.get(2).account == "main"


def test_import_normalizes_categories():
    ledger = Ledger()
    import_csv(ledger, "date,amount,category\n2024-03-05,-5,Eating  Out\n")
    assert ledger.get(1).category == "eating out"


def test_import_error_names_the_line_and_adds_nothing():
    ledger = Ledger()
    text = "date,amount,category\n2024-03-05,-5,food\n2024-03-06,abc,food\n"
    with pytest.raises(CsvImportError) as info:
        import_csv(ledger, text)
    assert info.value.line == 3
    assert len(ledger) == 0


def test_import_needs_the_required_columns():
    with pytest.raises(CsvImportError) as info:
        import_csv(Ledger(), "date,amount\n2024-03-05,-5\n")
    assert "category" in str(info.value)


def test_export_then_import_round_trips(march_ledger):
    copy = Ledger()
    import_csv(copy, export_csv(march_ledger.all()))
    assert [(t.date, t.amount, t.category) for t in copy.all()] == [
        (t.date, t.amount, t.category) for t in march_ledger.all()
    ]
