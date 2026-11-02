"""Text folding applied to every input line before a marker is matched.

Steps: NFKD, drop combining marks, map the dotless i to i, casefold. The sources
write one marker in upper case, lower case and with or without diacritics;
folding makes them one string.
"""
from __future__ import annotations

import unicodedata

_DOTLESS_I = chr(0x131)  # dotless i


def fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    kept = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return kept.replace(_DOTLESS_I, "i").casefold().replace(_DOTLESS_I, "i")


def folded_lines(raw: str) -> list[str]:
    """Split on line ends only (not on other separators) and fold each line."""
    unified = raw.replace("\r\n", "\n").replace("\r", "\n")
    return [fold(line) for line in unified.split("\n")]
