"""Command line interface for the Trennungsgeld calculator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .calculator import (
    AllowanceInput,
    TrennungsgeldCalculator,
    TravelCostInput,
    format_breakdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Berechnet eine Prognose für den Trennungsgeldanspruch auf "
            "Bundesebene inklusive Reisekosten."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Optionaler Pfad zu einer JSON-Datei mit den Eingabedaten. "
            "Im JSON können sowohl meal_allowance als auch travel_costs "
            "Objekte definiert werden."
        ),
    )

    meal = parser.add_argument_group("Verpflegungs- und Übernachtungskosten")
    meal.add_argument("--full-days", type=int, default=0, help="Anzahl voller Abwesenheitstage")
    meal.add_argument(
        "--arrival-days",
        type=int,
        default=0,
        help="Anzahl von An- oder Abreisetagen",
    )
    meal.add_argument(
        "--partial-days",
        type=int,
        default=0,
        help="Anzahl weiterer Tage mit mehr als 8 Stunden Abwesenheit",
    )
    meal.add_argument(
        "--overnight-receipts",
        type=int,
        default=0,
        help="Übernachtungen mit Belegen",
    )
    meal.add_argument(
        "--overnight-costs",
        type=float,
        default=0.0,
        help="Summe der belegten Übernachtungskosten",
    )
    meal.add_argument(
        "--overnight-flat",
        type=int,
        default=0,
        help="Übernachtungen ohne Beleg (20 EUR Pauschale)",
    )

    travel = parser.add_argument_group("Reisekosten")
    travel.add_argument(
        "--vehicle",
        choices=["car", "motorcycle", "bike"],
        default="car",
        help="Fortbewegungsmittel für Kilometerpauschalen",
    )
    travel.add_argument(
        "--initial-trip-km",
        type=float,
        default=0.0,
        help="Kilometer bei der Anreise zur neuen Dienststelle",
    )
    travel.add_argument(
        "--initial-trip-cost",
        type=float,
        help="Tatsächliche Kosten der Anreise (überschreibt Kilometerangabe)",
    )
    travel.add_argument(
        "--return-trip-km",
        type=float,
        default=0.0,
        help="Kilometer bei der endgültigen Rückreise",
    )
    travel.add_argument(
        "--return-trip-cost",
        type=float,
        help="Tatsächliche Kosten der Rückreise",
    )
    travel.add_argument(
        "--home-trips",
        type=int,
        default=0,
        help="Anzahl genehmigter Heimfahrten",
    )
    travel.add_argument(
        "--home-trip-km",
        type=float,
        default=0.0,
        help="Entfernung einer Heimfahrt (einfache Strecke)",
    )
    travel.add_argument(
        "--home-trip-cost",
        type=float,
        help="Tatsächliche Kosten einer Heimfahrt",
    )
    travel.add_argument(
        "--commuting-days",
        type=int,
        default=0,
        help="Anzahl täglicher Fahrten zwischen Unterkunft und Dienststelle",
    )
    travel.add_argument(
        "--commuting-distance",
        type=float,
        default=0.0,
        help="Entfernung einer einfachen Pendelstrecke",
    )
    travel.add_argument(
        "--commuting-cost",
        type=float,
        help="Tatsächliche Kosten pro Pendeltag",
    )
    travel.add_argument(
        "--additional-costs",
        type=float,
        default=0.0,
        help="Weitere erstattungsfähige Kosten (z.B. Gepäck, Parken)",
    )

    return parser.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Die JSON-Datei muss ein Objekt enthalten")
    return data


def _build_inputs(args: argparse.Namespace) -> tuple[AllowanceInput, TravelCostInput]:
    allowance_kwargs = dict(
        full_days=args.full_days,
        arrival_departure_days=args.arrival_days,
        partial_days=args.partial_days,
        overnight_stays_with_receipts=args.overnight_receipts,
        overnight_costs_total=args.overnight_costs,
        overnight_stays_without_receipts=args.overnight_flat,
    )

    travel_kwargs = dict(
        vehicle=args.vehicle,
        initial_trip_distance_km=args.initial_trip_km,
        initial_trip_actual_cost=args.initial_trip_cost,
        return_trip_distance_km=args.return_trip_km,
        return_trip_actual_cost=args.return_trip_cost,
        weekly_home_trips=args.home_trips,
        home_trip_distance_km=args.home_trip_km,
        home_trip_actual_cost=args.home_trip_cost,
        commuting_days=args.commuting_days,
        commuting_distance_km=args.commuting_distance,
        commuting_actual_cost_per_day=args.commuting_cost,
        additional_costs=args.additional_costs,
    )

    if args.input:
        file_data = _load_json(args.input)
        allowance_kwargs.update(file_data.get("meal_allowance", {}))
        travel_kwargs.update(file_data.get("travel_costs", {}))

    return AllowanceInput(**allowance_kwargs), TravelCostInput(**travel_kwargs)


def main() -> None:
    args = parse_args()
    allowance_input, travel_input = _build_inputs(args)

    calculator = TrennungsgeldCalculator()
    result = calculator.calculate(allowance_input, travel_input)

    for line in format_breakdown(result):
        print(line)


if __name__ == "__main__":
    main()
