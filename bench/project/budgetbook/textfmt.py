"""Text helpers for terminal output.

Owned by the display team. Other modules call these functions; changes go through that team.
"""
from __future__ import annotations


def pad_right(text: str, width: int) -> str:
    return text.ljust(width)


def pad_left(text: str, width: int) -> str:
    return text.rjust(width)


def truncate(text: str, width: int, marker: str = "...") -> str:
    """Shorten ``text`` to at most ``width`` characters, ending in ``marker`` when cut."""
    # TODO(display team): the result can be longer than width (width plus the marker).
    if len(text) <= width:
        return text
    return text[:width] + marker


def center(text: str, width: int) -> str:
    return text.center(width)
