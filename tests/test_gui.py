"""Tests für Hilfsfunktionen der grafischen Oberfläche."""
from __future__ import annotations

import importlib
import sys

import pytest


def test_gui_module_does_not_import_tkinter_by_default() -> None:
    sys.modules.pop("trennungsgeld.gui", None)
    sys.modules.pop("tkinter", None)
    module = importlib.import_module("trennungsgeld.gui")
    assert "tkinter" not in sys.modules
    assert hasattr(module, "launch_gui")


def test_parse_helpers() -> None:
    from trennungsgeld.gui import parse_float, parse_int, parse_optional_float

    assert parse_int("5", "Test") == 5
    assert parse_int("   ", "Test") == 0
    assert parse_float("3.5", "Test") == pytest.approx(3.5)
    assert parse_float("", "Test") == pytest.approx(0.0)
    assert parse_optional_float("", "Test") is None
    assert parse_optional_float("42", "Test") == pytest.approx(42)

    with pytest.raises(ValueError):
        parse_int("abc", "Feld")
    with pytest.raises(ValueError):
        parse_float("abc", "Feld")
    with pytest.raises(ValueError):
        parse_optional_float("abc", "Feld")
