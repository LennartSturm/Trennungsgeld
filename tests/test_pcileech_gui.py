"""Tests für Importverhalten der PCILeech-GUI."""
from __future__ import annotations

import importlib
import sys


def test_pcileech_gui_module_does_not_import_tkinter_by_default() -> None:
    sys.modules.pop("trennungsgeld.pcileech_gui", None)
    sys.modules.pop("tkinter", None)
    module = importlib.import_module("trennungsgeld.pcileech_gui")
    assert "tkinter" not in sys.modules
    assert hasattr(module, "launch_gui")
