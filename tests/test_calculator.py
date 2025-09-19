from trennungsgeld.calculator import (
    AllowanceInput,
    AllowanceRates,
    CalculationResult,
    TrennungsgeldCalculator,
    TravelCostInput,
    TravelRates,
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
