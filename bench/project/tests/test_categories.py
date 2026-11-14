import pytest

from budgetbook.categories import is_within, normalize_category, parent_of, top_level
from budgetbook.errors import CategoryError


def test_normalize_lowers_and_trims():
    assert normalize_category("  Food ") == "food"


def test_normalize_collapses_inner_spaces_but_keeps_one():
    assert normalize_category("Eating   Out") == "eating out"


def test_normalize_keeps_path_separator():
    assert normalize_category("Food/Groceries") == "food/groceries"


@pytest.mark.parametrize("name", ["", "   ", "food//x", "/food", "food/"])
def test_normalize_rejects_empty_names_and_parts(name):
    with pytest.raises(CategoryError):
        normalize_category(name)


def test_parent_and_top_level():
    assert parent_of("food/groceries/organic") == "food/groceries"
    assert parent_of("food") is None
    assert top_level("food/groceries") == "food"


def test_is_within_matches_whole_parts_only():
    assert is_within("food/groceries", "food")
    assert is_within("food", "food")
    assert not is_within("foodcourt", "food")
    assert not is_within("food", "food/groceries")
