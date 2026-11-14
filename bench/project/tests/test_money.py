import pytest

from budgetbook.errors import AmountError
from budgetbook.money import format_amount, parse_amount, round_half_up_div, split_evenly


@pytest.mark.parametrize(
    "text, cents",
    [("12", 1200), ("12.5", 1250), ("12.50", 1250), ("-0.05", -5), ("+3", 300), ("1,234.56", 123456), (" 7.00 ", 700)],
)
def test_parse_amount(text, cents):
    assert parse_amount(text) == cents


@pytest.mark.parametrize("text", ["", "abc", "1.234", "12,5", "1,23,456", "--3", "1e3"])
def test_parse_amount_rejects(text):
    with pytest.raises(AmountError):
        parse_amount(text)


def test_format_amount_keeps_sign_for_small_negatives():
    assert format_amount(-5) == "-0.05"
    assert format_amount(123456) == "1234.56"
    assert format_amount(0) == "0.00"


def test_round_half_up_div_rounds_halves_up():
    assert round_half_up_div(1, 2) == 1
    assert round_half_up_div(5, 10) == 1
    assert round_half_up_div(1, 3) == 0
    assert round_half_up_div(2, 3) == 1
    assert round_half_up_div(25, 10) == 3


def test_round_half_up_div_needs_positive_denominator():
    with pytest.raises(ValueError):
        round_half_up_div(1, 0)


def test_split_evenly_adds_up():
    assert split_evenly(10000, 3) == [3334, 3333, 3333]
    assert sum(split_evenly(1001, 7)) == 1001
