"""Interactive quickstart interface for the separation allowance calculator."""
from __future__ import annotations

from typing import Callable, Optional, TypeVar

from .calculator import (
    AllowanceInput,
    TrennungsgeldCalculator,
    TravelCostInput,
    format_breakdown,
)

T = TypeVar("T")


def _prompt(
    message: str,
    caster: Callable[[str], T],
    *,
    default: Optional[T] = None,
) -> Optional[T]:
    """Prompt the user for input and cast to the requested type."""

    suffix = "leer" if default is None else default
    prompt = f"{message} [{suffix}]: "
    while True:
        raw = input(prompt).strip()
        if not raw:
            return default
        try:
            return caster(raw)
        except ValueError:
            print("Bitte eine gültige Eingabe machen.")


def _prompt_int(message: str, default: int = 0) -> int:
    return _prompt(message, int, default=default) or 0


def _prompt_float(message: str, default: float = 0.0) -> float:
    def cast(value: str) -> float:
        return float(value.replace(",", "."))

    return _prompt(message, cast, default=default) or 0.0


def _prompt_optional_float(message: str) -> Optional[float]:
    def cast(value: str) -> float:
        return float(value.replace(",", "."))

    return _prompt(message, cast, default=None)


def _prompt_vehicle(default: str = "car") -> str:
    choices = {"car", "motorcycle", "bike"}
    prompt = f"Fortbewegungsmittel {choices} [{default}]: "
    while True:
        raw = input(prompt).strip().lower()
        if not raw:
            return default
        if raw in choices:
            return raw
        print("Bitte 'car', 'motorcycle' oder 'bike' eingeben.")


def run_simple_cli() -> None:
    """Run the interactive quickstart workflow."""

    print("Trennungsgeld Schnelleinstieg")
    print("(Eingabe mit Enter übernimmt den Standardwert)")

    allowance = AllowanceInput(
        full_days=_prompt_int("Anzahl voller Abwesenheitstage"),
        arrival_departure_days=_prompt_int("Anzahl An-/Abreisetage"),
        partial_days=_prompt_int("Anzahl weiterer Tage mit >8h Abwesenheit"),
        overnight_stays_with_receipts=_prompt_int("Übernachtungen mit Beleg"),
        overnight_costs_total=_prompt_float("Summe belegter Übernachtungskosten (EUR)"),
        overnight_stays_without_receipts=_prompt_int("Übernachtungen ohne Beleg"),
    )

    travel = TravelCostInput(
        vehicle=_prompt_vehicle(),
        initial_trip_distance_km=_prompt_float("Kilometer Anreise"),
        initial_trip_actual_cost=_prompt_optional_float("Tatsächliche Kosten Anreise (EUR)"),
        return_trip_distance_km=_prompt_float("Kilometer Rückreise"),
        return_trip_actual_cost=_prompt_optional_float("Tatsächliche Kosten Rückreise (EUR)"),
        weekly_home_trips=_prompt_int("Anzahl Heimfahrten"),
        home_trip_distance_km=_prompt_float("Entfernung einer Heimfahrt (km)"),
        home_trip_actual_cost=_prompt_optional_float("Tatsächliche Kosten einer Heimfahrt (EUR)"),
        commuting_days=_prompt_int("Anzahl Pendeltage"),
        commuting_distance_km=_prompt_float("Pendeldistanz (km)"),
        commuting_actual_cost_per_day=_prompt_optional_float(
            "Tatsächliche Pendelkosten pro Tag (EUR)"
        ),
        additional_costs=_prompt_float("Weitere erstattungsfähige Kosten (EUR)"),
    )

    calculator = TrennungsgeldCalculator()
    result = calculator.calculate(allowance, travel)

    print()
    for line in format_breakdown(result):
        print(line)


__all__ = ["run_simple_cli"]
