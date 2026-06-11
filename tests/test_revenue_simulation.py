import pytest

from src.revenue_simulation import (
    build_candidate_prices,
    simulate_revenue_maximizing_price,
)


def test_elastic_weak_demand_recommends_lower_band_edge():
    """Elastic demand (-2.0) with ample capacity: revenue falls with price, so the
    optimum pins to the lower edge of the allowed change band."""
    result = simulate_revenue_maximizing_price(
        current_price=100.0,
        sellable_rooms=100.0,
        known_sold_rooms=10.0,
        known_room_revenue=1000.0,
        occupancy=0.10,
        baseline_occupancy=0.60,
        pickup_14d=0.0,
        days_to_arrival=10,
        is_weekend=False,
        max_change_pct=0.15,
        rounding_strategy="nearest_1",
    )
    assert result.demand_elasticity == pytest.approx(-2.0)
    assert result.recommended_price == pytest.approx(85.0)
    assert not result.price_floor_applied
    assert not result.price_ceiling_applied


def test_price_floor_caps_elastic_decrease():
    """Same elastic scenario but with a floor inside the band: the floor wins."""
    result = simulate_revenue_maximizing_price(
        current_price=100.0,
        sellable_rooms=100.0,
        known_sold_rooms=10.0,
        known_room_revenue=1000.0,
        occupancy=0.10,
        baseline_occupancy=0.60,
        pickup_14d=0.0,
        days_to_arrival=10,
        is_weekend=False,
        max_change_pct=0.15,
        rounding_strategy="nearest_1",
        price_floor=90.0,
    )
    assert result.recommended_price == pytest.approx(90.0)
    assert result.price_floor_applied


def test_capacity_constraint_yields_interior_solution():
    """Elastic demand close to remaining capacity: below the clearing price demand
    is capped, so the revenue peak sits strictly inside the band."""
    result = simulate_revenue_maximizing_price(
        current_price=100.0,
        sellable_rooms=100.0,
        known_sold_rooms=40.0,
        known_room_revenue=4000.0,
        occupancy=0.40,
        baseline_occupancy=0.45,
        pickup_14d=82.0,
        days_to_arrival=10,
        is_weekend=False,
        max_change_pct=0.15,
        rounding_strategy="nearest_1",
    )
    assert result.demand_elasticity == pytest.approx(-1.45)
    assert 85.0 < result.recommended_price < 115.0
    assert 90.0 <= result.recommended_price <= 96.0
    assert result.expected_sold_rooms <= 100.0


def test_inelastic_high_demand_recommends_upper_band_edge():
    """Inelastic demand (clipped to -0.6) with strong pickup: revenue rises with
    price, so the optimum pins to the upper edge of the band."""
    result = simulate_revenue_maximizing_price(
        current_price=100.0,
        sellable_rooms=100.0,
        known_sold_rooms=80.0,
        known_room_revenue=8000.0,
        occupancy=0.80,
        baseline_occupancy=0.55,
        pickup_14d=44.0,
        days_to_arrival=7,
        is_weekend=True,
        max_change_pct=0.15,
        rounding_strategy="nearest_1",
    )
    assert result.demand_elasticity == pytest.approx(-0.6)
    assert result.recommended_price == pytest.approx(115.0)


def test_candidate_prices_respect_floor_ceiling_and_include_current():
    candidates = build_candidate_prices(
        current_price=100.0,
        max_change_pct=0.15,
        rounding_strategy="nearest_1",
        price_floor=90.0,
        price_ceiling=110.0,
    )
    assert candidates, "candidate list must not be empty"
    assert min(candidates) >= 90.0 - 0.01
    assert max(candidates) <= 110.0 + 0.01
    assert 100.0 in candidates
