import datetime as dt

import pytest

from budgetbook.dates import add_months, month_bounds, parse_date, parse_month
from budgetbook.errors import DateError


def test_parse_date():
    assert parse_date("2024-02-29") == dt.date(2024, 2, 29)
    with pytest.raises(DateError):
        parse_date("2023-02-29")
    with pytest.raises(DateError):
        parse_date("29.02.2024")


def test_parse_month():
    assert parse_month("2024-03") == (2024, 3)
    for bad in ("2024-13", "2024-3", "March"):
        with pytest.raises(DateError):
            parse_month(bad)


def test_month_bounds_handles_leap_february():
    assert month_bounds(2024, 2) == (dt.date(2024, 2, 1), dt.date(2024, 2, 29))
    assert month_bounds(2023, 2)[1] == dt.date(2023, 2, 28)


def test_add_months_clamps_to_the_end_of_the_month():
    assert add_months(dt.date(2024, 1, 31), 1) == dt.date(2024, 2, 29)
    assert add_months(dt.date(2023, 1, 31), 1) == dt.date(2023, 2, 28)
    assert add_months(dt.date(2024, 1, 31), 2) == dt.date(2024, 3, 31)


def test_add_months_crosses_years_both_ways():
    assert add_months(dt.date(2023, 11, 15), 3) == dt.date(2024, 2, 15)
    assert add_months(dt.date(2024, 1, 15), -2) == dt.date(2023, 11, 15)
