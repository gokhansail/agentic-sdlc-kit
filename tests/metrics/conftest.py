"""Shared helpers for the metrics tests.

Fixtures are ASCII. The em dash of the source record format is written as {EM}
in the fixture files and replaced here with a code point built at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "tests" / "fixtures" / "metrics"
EM_DASH = chr(0x2014)


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="ascii").replace("{EM}", EM_DASH)


@pytest.fixture
def test_profile():
    from tools.metrics.profile import load_profile

    return load_profile(FIXTURES / "profile-test.json")
