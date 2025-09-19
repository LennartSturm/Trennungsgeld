import pytest

from trennungsgeld.calculator import (
    AllowanceInput,
    AllowanceRates,
    CalculationResult,
    TrennungsgeldCalculator,
    TravelCostInput,
    TravelRates,
    format_breakdown,
)


def test_meal_allowance_basic():
    calculator = TrennungsgeldCalculator()
    data = AllowanceInput(
        full_days=5,
        arrival_departure_days=2,
        partial_days=3,
        overnight_stays_with_receipts=4,
        overnight_costs_total=320.0,
        overnight_stays_without_receipts=2,
    )

    components = calculator.calculate_meal_allowance(data)

    expected_total = (
        5 * calculator.allowance_rates.full_day
        + 2 * calculator.allowance_rates.arrival_departure
        + 3 * calculator.allowance_rates.partial_day
        + 320.0
        + 2 * calculator.allowance_rates.overnight_flat
    )

    assert components["total_meal_allowance"] == expected_total


def test_travel_costs_with_mixed_inputs():
    rates = TravelRates(car_per_km=0.2)
    calculator = TrennungsgeldCalculator(travel_rates=rates)
    data = TravelCostInput(
        initial_trip_distance_km=500,
        return_trip_actual_cost=120.0,
        weekly_home_trips=4,
        home_trip_distance_km=400,
        commuting_days=10,
        commuting_distance_km=15,
        additional_costs=50.0,
    )

    components = calculator.calculate_travel_costs(data)

    expected_initial = 500 * rates.car_per_km
    expected_home = 4 * 400 * rates.car_per_km
    expected_commuting = 10 * 15 * rates.car_per_km
    expected_total = (
        expected_initial
        + 120.0
        + expected_home
        + expected_commuting
        + 50.0
    )

    assert components["total_travel_costs"] == expected_total


def test_calculate_combined():
    calculator = TrennungsgeldCalculator(
        allowance_rates=AllowanceRates(full_day=28, arrival_departure=14, partial_day=14),
        travel_rates=TravelRates(car_per_km=0.2),
    )

    allowance_input = AllowanceInput(full_days=2, arrival_departure_days=1, partial_days=0)
    travel_input = TravelCostInput(initial_trip_distance_km=100)

    result = calculator.calculate(allowance_input, travel_input)

    assert isinstance(result, CalculationResult)
    assert result.meal_allowance == 2 * 28 + 1 * 14
    assert result.travel_costs == 100 * 0.2
    assert result.total_allowance == result.meal_allowance + result.travel_costs
    assert "meal_full_days" in result.breakdown
    assert "travel_initial_trip" in result.breakdown


def test_meal_allowance_validations():
    calculator = TrennungsgeldCalculator()
    with pytest.raises(ValueError):
        calculator.calculate_meal_allowance(
            AllowanceInput(
                full_days=-1,
                arrival_departure_days=0,
                partial_days=0,
            )
        )

    with pytest.raises(ValueError):
        calculator.calculate_meal_allowance(
            AllowanceInput(
                full_days=0,
                arrival_departure_days=0,
                partial_days=0,
                overnight_stays_with_receipts=-2,
                overnight_costs_total=0.0,
            )
        )

    with pytest.raises(ValueError):
        calculator.calculate_meal_allowance(
            AllowanceInput(
                full_days=0,
                arrival_departure_days=0,
                partial_days=0,
                overnight_stays_without_receipts=-3,
            )
        )


@pytest.mark.parametrize(
    "vehicle,expected",
    [
        ("car", 0.20),
        ("motorcycle", 0.13),
        ("bike", 0.05),
        ("bicycle", 0.05),
    ],
)
def test_vehicle_rate_selection(vehicle, expected):
    travel_rates = TravelRates(
        car_per_km=0.20, motorcycle_per_km=0.13, bicycle_per_km=0.05
    )
    calculator = TrennungsgeldCalculator(travel_rates=travel_rates)
    data = TravelCostInput(initial_trip_distance_km=100, vehicle=vehicle)

    components = calculator.calculate_travel_costs(data)

    assert components["initial_trip"] == pytest.approx(100 * expected)


def test_invalid_vehicle_raises_value_error():
    calculator = TrennungsgeldCalculator()
    with pytest.raises(ValueError):
        calculator.calculate_travel_costs(
            TravelCostInput(initial_trip_distance_km=10, vehicle="plane")
        )


def test_actual_cost_overrides_distance_and_validates_negatives():
    calculator = TrennungsgeldCalculator()

    data = TravelCostInput(
        initial_trip_distance_km=1000,
        initial_trip_actual_cost=50.0,
        return_trip_distance_km=1000,
        return_trip_actual_cost=None,
        weekly_home_trips=1,
        home_trip_distance_km=100,
        home_trip_actual_cost=40.0,
    )

    components = calculator.calculate_travel_costs(data)

    assert components["initial_trip"] == 50.0
    assert components["home_trips"] == 40.0

    with pytest.raises(ValueError):
        calculator.calculate_travel_costs(
            TravelCostInput(initial_trip_actual_cost=-1.0)
        )


def test_commuting_actual_costs_take_precedence():
    calculator = TrennungsgeldCalculator()
    data = TravelCostInput(
        commuting_days=5,
        commuting_distance_km=20,
        commuting_actual_cost_per_day=12.5,
    )

    components = calculator.calculate_travel_costs(data)

    assert components["commuting"] == 5 * 12.5


def test_commuting_and_home_trip_negative_values_rejected():
    calculator = TrennungsgeldCalculator()

    with pytest.raises(ValueError, match="home trips must be non-negative"):
        calculator.calculate_travel_costs(
            TravelCostInput(weekly_home_trips=-1, home_trip_distance_km=10)
        )

    with pytest.raises(ValueError, match="commuting days must be non-negative"):
        calculator.calculate_travel_costs(
            TravelCostInput(
                commuting_days=-2,
                commuting_actual_cost_per_day=5.0,
            )
        )


def test_format_breakdown_outputs_sorted_keys():
    calculator = TrennungsgeldCalculator()
    result = calculator.calculate(
        AllowanceInput(full_days=1, arrival_departure_days=1, partial_days=1),
        TravelCostInput(initial_trip_distance_km=10, weekly_home_trips=1, home_trip_distance_km=10),
    )

    lines = format_breakdown(result)

    assert lines[0] == "Berechnungsübersicht:"
    assert "Gesamtsumme" in lines[1]
    assert lines[4] == "  Detailposten:"
    detail_lines = lines[5:]
    assert any(line.strip().startswith("meal_") for line in detail_lines)
    assert detail_lines == sorted(detail_lines)
