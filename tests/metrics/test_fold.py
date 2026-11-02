from __future__ import annotations

from tools.metrics.fold import fold, folded_lines


def test_fold_maps_diacritics_dotless_i_and_case_to_ascii() -> None:
    # Letters are built from code points so this file stays ASCII.
    dotted_capital_i = chr(0x130)
    dotless_i = chr(0x131)
    g_breve = chr(0x11F)
    s_cedilla = chr(0x15F)
    c_cedilla = chr(0xE7)
    o_umlaut = chr(0xF6)
    u_umlaut = chr(0xFC)
    e_acute = chr(0xE9)

    upper = dotted_capital_i + "I" + "ST" + "ANBUL"
    assert fold(upper) == "iistanbul"
    assert fold("a" + dotless_i + "r") == "air"
    word = "ca" + g_breve + "r" + s_cedilla + c_cedilla + o_umlaut + u_umlaut + e_acute
    assert fold(word) == "cagrscoue"
    assert fold(word.upper()) == "cagrscoue"
    # The same marker in three spellings folds to one string.
    spellings = ["Caf" + e_acute, "CAFE" + chr(0x301), "caf" + "e"]
    assert {fold(s) for s in spellings} == {"cafe"}


def test_fold_keeps_structure_characters() -> None:
    assert fold("## 1.0.0 " + chr(0x2014) + " Done") == "## 1.0.0 " + chr(0x2014) + " done"


def test_folded_lines_splits_on_line_ends_only() -> None:
    text = "A\r\nB\rC\nD" + chr(0x2028) + "E"
    assert folded_lines(text) == ["a", "b", "c", "d" + chr(0x2028) + "e"]
