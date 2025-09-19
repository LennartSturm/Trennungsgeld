from __future__ import annotations

from typing import Iterator

import pytest

from trennungsgeld.simple_cli import run_simple_cli


def _make_input(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    iterator: Iterator[str] = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(iterator))


def test_simple_cli_all_defaults(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _make_input(monkeypatch, [""] * 18)
    run_simple_cli()
    out = capsys.readouterr().out
    assert "Gesamtsumme: 0.00 EUR" in out
    assert "Detailposten" in out


def test_simple_cli_with_values(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    answers = [
        "abc",  # invalid full days -> triggers retry
        "3",  # full days
        "1",  # arrival days
        "1",  # partial days
        "0",  # overnight with receipts
        "0",  # overnight cost total
        "0",  # overnight without receipts
        "",  # vehicle defaults to car
        "500",  # initial trip km
        "",  # actual cost initial
        "500",  # return trip km
        "",  # actual cost return
        "2",  # home trips
        "200",  # home trip distance
        "",  # home trip actual cost
        "5",  # commuting days
        "10",  # commuting distance
        "",  # commuting actual cost per day
        "30",  # additional costs
    ]
    _make_input(monkeypatch, answers)
    run_simple_cli()
    out = capsys.readouterr().out
    assert "Bitte eine gültige Eingabe machen." in out
    assert "Gesamtsumme: 432.00 EUR" in out
    assert "travel_initial_trip: 100.00 EUR" in out
    assert "meal_full_days: 84.00 EUR" in out
