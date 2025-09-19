"""Utilities to estimate federal German separation allowance (Trennungsgeld).

The module intentionally focuses on transparency rather than covering every
special case covered by the Bundesreisekostengesetz (BRKG).  The implemented
rules follow the BRKG rates as of 2024 for meal allowances and kilometre-based
travel reimbursements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AllowanceRates:
    """Allowance rates in Euro according to the BRKG.

    The defaults reflect the 2024 federal rates:

    * 28 EUR for full 24-hour absences
    * 14 EUR for arrival or departure days
    * 14 EUR for partial days with more than 8 hours of absence
    * 20 EUR flat overnight allowance when no receipts are provided
    """

    full_day: float = 28.0
    arrival_departure: float = 14.0
    partial_day: float = 14.0
    overnight_flat: float = 20.0


@dataclass(frozen=True)
class TravelRates:
    """Mileage reimbursement rates in Euro per kilometre.

    The standard BRKG kilometre allowance for cars is 0.20 EUR per kilometre.
    Lower rates are used for motorcycles and bicycles.
    """

    car_per_km: float = 0.20
    motorcycle_per_km: float = 0.13
    bicycle_per_km: float = 0.05


@dataclass(frozen=True)
class AllowanceInput:
    """Inputs for the meal allowance component of the calculation."""

    full_days: int
    arrival_departure_days: int
    partial_days: int
    overnight_stays_with_receipts: int = 0
    overnight_costs_total: float = 0.0
    overnight_stays_without_receipts: int = 0


@dataclass(frozen=True)
class TravelCostInput:
    """Inputs required to estimate reimbursable travel costs."""

    initial_trip_distance_km: float = 0.0
    initial_trip_actual_cost: Optional[float] = None
    return_trip_distance_km: float = 0.0
    return_trip_actual_cost: Optional[float] = None
    weekly_home_trips: int = 0
    home_trip_distance_km: float = 0.0
    home_trip_actual_cost: Optional[float] = None
    commuting_days: int = 0
    commuting_distance_km: float = 0.0
    commuting_actual_cost_per_day: Optional[float] = None
    additional_costs: float = 0.0
    vehicle: str = "car"


@dataclass
class CalculationResult:
    """Structured result of the calculator."""

    total_allowance: float
    meal_allowance: float
    travel_costs: float
    breakdown: Dict[str, float] = field(default_factory=dict)


class TrennungsgeldCalculator:
    """Central service to calculate the estimated separation allowance."""

    def __init__(
        self,
        allowance_rates: AllowanceRates | None = None,
        travel_rates: TravelRates | None = None,
    ) -> None:
        self.allowance_rates = allowance_rates or AllowanceRates()
        self.travel_rates = travel_rates or TravelRates()

    def calculate_meal_allowance(self, data: AllowanceInput) -> Dict[str, float]:
        """Calculate the meal (Verpflegung) and overnight allowances."""

        if min(data.full_days, data.arrival_departure_days, data.partial_days) < 0:
            raise ValueError("Day counts must be non-negative")

        components: Dict[str, float] = {}

        full_day_amount = data.full_days * self.allowance_rates.full_day
        components["full_days"] = full_day_amount

        arrival_amount = (
            data.arrival_departure_days * self.allowance_rates.arrival_departure
        )
        components["arrival_departure_days"] = arrival_amount

        partial_amount = data.partial_days * self.allowance_rates.partial_day
        components["partial_days"] = partial_amount

        if data.overnight_stays_with_receipts < 0 or data.overnight_costs_total < 0:
            raise ValueError("Overnight stays and costs must be non-negative")

        components["overnight_with_receipts"] = data.overnight_costs_total

        if data.overnight_stays_without_receipts < 0:
            raise ValueError("Number of overnight stays without receipts must be non-negative")

        overnight_flat_amount = (
            data.overnight_stays_without_receipts
            * self.allowance_rates.overnight_flat
        )
        components["overnight_without_receipts"] = overnight_flat_amount

        components["total_meal_allowance"] = sum(components.values())
        return components

    def _rate_for_vehicle(self, vehicle: str) -> float:
        rate_lookup = {
            "car": self.travel_rates.car_per_km,
            "motorcycle": self.travel_rates.motorcycle_per_km,
            "bike": self.travel_rates.bicycle_per_km,
            "bicycle": self.travel_rates.bicycle_per_km,
        }
        try:
            return rate_lookup[vehicle]
        except KeyError as exc:  # pragma: no cover - defensive coding
            raise ValueError(
                f"Unsupported vehicle '{vehicle}'. Choose from {', '.join(rate_lookup)}."
            ) from exc

    def calculate_travel_costs(self, data: TravelCostInput) -> Dict[str, float]:
        """Calculate reimbursable travel costs."""

        components: Dict[str, float] = {}
        rate = self._rate_for_vehicle(data.vehicle)

        def km_or_cost(distance_km: float, actual_cost: Optional[float]) -> float:
            if actual_cost is not None:
                if actual_cost < 0:
                    raise ValueError("Actual costs must not be negative")
                return actual_cost
            if distance_km < 0:
                raise ValueError("Distances must not be negative")
            return distance_km * rate

        components["initial_trip"] = km_or_cost(
            data.initial_trip_distance_km, data.initial_trip_actual_cost
        )
        components["return_trip"] = km_or_cost(
            data.return_trip_distance_km, data.return_trip_actual_cost
        )

        home_trip_amount = km_or_cost(
            data.home_trip_distance_km, data.home_trip_actual_cost
        ) * data.weekly_home_trips
        components["home_trips"] = home_trip_amount

        commuting_amount = 0.0
        if data.commuting_actual_cost_per_day is not None:
            if data.commuting_actual_cost_per_day < 0:
                raise ValueError("Commuting cost per day must be non-negative")
            commuting_amount = data.commuting_actual_cost_per_day * data.commuting_days
        else:
            if data.commuting_distance_km < 0 or data.commuting_days < 0:
                raise ValueError("Commuting distance and days must be non-negative")
            commuting_amount = (
                data.commuting_distance_km * data.commuting_days * rate
            )
        components["commuting"] = commuting_amount

        if data.additional_costs < 0:
            raise ValueError("Additional costs must be non-negative")
        components["additional_costs"] = data.additional_costs

        components["total_travel_costs"] = sum(components.values())
        return components

    def calculate(
        self,
        allowance_input: AllowanceInput,
        travel_input: TravelCostInput,
    ) -> CalculationResult:
        meal_components = self.calculate_meal_allowance(allowance_input)
        travel_components = self.calculate_travel_costs(travel_input)

        meal_total = meal_components.pop("total_meal_allowance")
        travel_total = travel_components.pop("total_travel_costs")

        total = meal_total + travel_total
        breakdown: Dict[str, float] = {}
        breakdown.update({f"meal_{k}": v for k, v in meal_components.items()})
        breakdown.update({f"travel_{k}": v for k, v in travel_components.items()})

        return CalculationResult(
            total_allowance=total,
            meal_allowance=meal_total,
            travel_costs=travel_total,
            breakdown=breakdown,
        )


def format_breakdown(result: CalculationResult) -> List[str]:
    """Generate a human readable breakdown list."""

    lines = [
        "Berechnungsübersicht:",
        f"  Gesamtsumme: {result.total_allowance:.2f} EUR",
        f"  Verpflegung und Übernachtung: {result.meal_allowance:.2f} EUR",
        f"  Reisekosten: {result.travel_costs:.2f} EUR",
        "  Detailposten:",
    ]
    for key, value in sorted(result.breakdown.items()):
        lines.append(f"    {key}: {value:.2f} EUR")
    return lines


__all__ = [
    "AllowanceRates",
    "TravelRates",
    "AllowanceInput",
    "TravelCostInput",
    "CalculationResult",
    "TrennungsgeldCalculator",
    "format_breakdown",
]
