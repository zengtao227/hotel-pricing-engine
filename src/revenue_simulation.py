from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional

from .price_rounding import round_to_price_ending


DEFAULT_ELASTICITY: float = -1.25
MIN_ELASTICITY: float = -2.20
MAX_ELASTICITY: float = -0.60
MIN_REVENUE_UPLIFT_PCT: float = 0.005


@dataclass(frozen=True)
class RevenueSimulationResult:
    recommended_price: float
    current_expected_revenue: float
    recommended_expected_revenue: float
    expected_revenue_delta: float
    current_expected_sold_rooms: float
    expected_sold_rooms: float
    expected_new_sold_rooms: float
    demand_forecast_at_current_price: float
    demand_elasticity: float
    candidate_price_count: int
    price_floor_applied: bool
    price_ceiling_applied: bool


def _finite_number(value: object, default: float = 0.0) -> float:
    try:
        number: float = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _positive_bound(value: Optional[float]) -> Optional[float]:
    number: float = _finite_number(value, 0.0)
    return number if number > 0 else None


def _clip(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _pace_weight(days_to_arrival: int) -> float:
    if days_to_arrival <= 7:
        return 0.75
    if days_to_arrival <= 14:
        return 0.65
    if days_to_arrival <= 30:
        return 0.50
    return 0.35


def _pickup_projection_factor(days_to_arrival: int) -> float:
    if days_to_arrival <= 3:
        return 0.30
    if days_to_arrival <= 7:
        return 0.65
    if days_to_arrival <= 14:
        return 1.00
    if days_to_arrival <= 30:
        return 1.45
    return 2.00


def forecast_final_demand_at_current_price(
    known_sold_rooms: float,
    sellable_rooms: float,
    baseline_occupancy: float,
    pickup_14d: float,
    days_to_arrival: int,
) -> float:
    """Forecast final sold room-nights at the current price before price response."""
    known_sold: float = max(_finite_number(known_sold_rooms), 0.0)
    sellable: float = max(_finite_number(sellable_rooms), 0.0)
    baseline_occ: float = _clip(_finite_number(baseline_occupancy, 0.0), 0.0, 1.20)
    pickup: float = max(_finite_number(pickup_14d), 0.0)

    if sellable <= 0:
        return known_sold

    historical_demand: float = baseline_occ * sellable
    pace_projection: float = known_sold + pickup * _pickup_projection_factor(days_to_arrival)
    weight: float = _pace_weight(days_to_arrival)
    blended_demand: float = weight * pace_projection + (1.0 - weight) * historical_demand
    capped_demand: float = min(max(blended_demand, known_sold), sellable)
    return float(capped_demand)


def estimate_price_elasticity(
    occupancy: float,
    baseline_occupancy: float,
    remaining_inventory_ratio: float,
    pickup_14d: float,
    days_to_arrival: int,
    is_weekend: bool,
) -> float:
    """Estimate a transparent constant price elasticity from demand and inventory signals."""
    elasticity: float = DEFAULT_ELASTICITY
    current_occ: float = _finite_number(occupancy, 0.0)
    baseline_occ: float = _finite_number(baseline_occupancy, current_occ)
    remaining_ratio: float = _finite_number(remaining_inventory_ratio, 1.0)
    pickup: float = _finite_number(pickup_14d, 0.0)

    if is_weekend:
        elasticity += 0.15
    if current_occ > baseline_occ + 0.12:
        elasticity += 0.20
    if current_occ >= 0.75:
        elasticity += 0.20
    if remaining_ratio < 0.25:
        elasticity += 0.25
    if days_to_arrival <= 14 and pickup >= 4:
        elasticity += 0.15

    if current_occ < max(0.20, baseline_occ - 0.12):
        elasticity -= 0.25
    if days_to_arrival <= 14 and remaining_ratio > 0.55:
        elasticity -= 0.35
    if days_to_arrival <= 14 and pickup <= 1:
        elasticity -= 0.15
    if days_to_arrival > 30:
        elasticity -= 0.10

    return float(_clip(elasticity, MIN_ELASTICITY, MAX_ELASTICITY))


def _price_range(
    current_price: float,
    max_change_pct: float,
    price_floor: Optional[float],
    price_ceiling: Optional[float],
) -> tuple[float, float]:
    change_pct: float = max(_finite_number(max_change_pct), 0.0)
    lower: float = current_price * (1.0 - change_pct)
    upper: float = current_price * (1.0 + change_pct)
    floor: Optional[float] = _positive_bound(price_floor)
    ceiling: Optional[float] = _positive_bound(price_ceiling)

    if floor is not None:
        lower = max(lower, floor)
    if ceiling is not None:
        upper = min(upper, ceiling)
    if lower <= upper:
        return lower, upper

    bounded_current: float = current_price
    if floor is not None:
        bounded_current = max(bounded_current, floor)
    if ceiling is not None:
        bounded_current = min(bounded_current, ceiling)
    return bounded_current, bounded_current


def _is_price_allowed(price: float, lower: float, upper: float) -> bool:
    return lower - 0.01 <= price <= upper + 0.01


def build_candidate_prices(
    current_price: float,
    max_change_pct: float,
    rounding_strategy: str,
    price_floor: Optional[float] = None,
    price_ceiling: Optional[float] = None,
) -> list[float]:
    lower, upper = _price_range(current_price, max_change_pct, price_floor, price_ceiling)
    if lower <= 0 or upper <= 0:
        return [max(current_price, 0.0)]
    if math.isclose(lower, upper, abs_tol=0.01):
        return [round(lower, 2)]

    grid_size: int = 31
    step: float = (upper - lower) / float(grid_size - 1)
    raw_grid: list[float] = [lower + step * index for index in range(grid_size)]
    anchor_changes: list[float] = [-max_change_pct, -0.12, -0.07, -0.03, 0.0, 0.03, 0.07, 0.12, max_change_pct]
    raw_grid.extend(current_price * (1.0 + change) for change in anchor_changes)

    rounded_prices: set[float] = set()
    for raw_price in raw_grid:
        rounded_price: float = round_to_price_ending(raw_price, strategy=rounding_strategy)
        bounded_price: float = _clip(rounded_price, lower, upper)
        rounded_prices.add(round(bounded_price, 2))

    if _is_price_allowed(current_price, lower, upper):
        rounded_prices.add(round(current_price, 2))

    return sorted(rounded_prices)


def _expected_revenue(
    candidate_price: float,
    current_price: float,
    known_revenue: float,
    price_neutral_new_demand: float,
    remaining_capacity: float,
    elasticity: float,
) -> tuple[float, float]:
    if current_price <= 0:
        return known_revenue, 0.0

    relative_price: float = max(candidate_price / current_price, 0.01)
    demand_multiplier: float = relative_price**elasticity
    expected_new_sold: float = min(remaining_capacity, price_neutral_new_demand * demand_multiplier)
    expected_revenue: float = known_revenue + candidate_price * expected_new_sold
    return float(expected_revenue), float(expected_new_sold)


def simulate_candidate_revenue_curve(
    *,
    current_price: float,
    sellable_rooms: float,
    known_sold_rooms: float,
    known_room_revenue: float,
    demand_forecast_at_current_price: float,
    demand_elasticity: float,
    max_change_pct: float,
    rounding_strategy: str,
    price_floor: Optional[float] = None,
    price_ceiling: Optional[float] = None,
) -> list[dict[str, float]]:
    """Return expected revenue for every feasible candidate price."""
    price: float = max(_finite_number(current_price), 0.0)
    sellable: float = max(_finite_number(sellable_rooms), 0.0)
    known_sold: float = max(_finite_number(known_sold_rooms), 0.0)
    known_revenue: float = _finite_number(known_room_revenue, 0.0)
    demand_forecast: float = max(_finite_number(demand_forecast_at_current_price), known_sold)
    elasticity: float = _clip(_finite_number(demand_elasticity, DEFAULT_ELASTICITY), MIN_ELASTICITY, MAX_ELASTICITY)

    if price <= 0 or sellable <= 0:
        return []

    remaining_capacity: float = max(sellable - known_sold, 0.0)
    price_neutral_new_demand: float = max(demand_forecast - known_sold, 0.0)
    candidates: list[float] = build_candidate_prices(
        current_price=price,
        max_change_pct=max_change_pct,
        rounding_strategy=rounding_strategy,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )

    rows: list[dict[str, float]] = []
    for candidate_price in candidates:
        expected_revenue, expected_new_sold = _expected_revenue(
            candidate_price=candidate_price,
            current_price=price,
            known_revenue=known_revenue,
            price_neutral_new_demand=price_neutral_new_demand,
            remaining_capacity=remaining_capacity,
            elasticity=elasticity,
        )
        rows.append(
            {
                "candidate_price": round(candidate_price, 2),
                "expected_revenue": round(expected_revenue, 2),
                "expected_new_sold_rooms": round(expected_new_sold, 3),
                "expected_sold_rooms": round(known_sold + expected_new_sold, 3),
            }
        )
    return rows


def simulate_revenue_maximizing_price(
    *,
    current_price: float,
    sellable_rooms: float,
    known_sold_rooms: float,
    known_room_revenue: float,
    occupancy: float,
    baseline_occupancy: float,
    pickup_14d: float,
    days_to_arrival: int,
    is_weekend: bool,
    max_change_pct: float,
    rounding_strategy: str,
    price_floor: Optional[float] = None,
    price_ceiling: Optional[float] = None,
) -> RevenueSimulationResult:
    price: float = max(_finite_number(current_price), 0.0)
    sellable: float = max(_finite_number(sellable_rooms), 0.0)
    known_sold: float = max(_finite_number(known_sold_rooms), 0.0)
    remaining_capacity: float = max(sellable - known_sold, 0.0)
    known_revenue: float = _finite_number(known_room_revenue, 0.0)

    demand_forecast: float = forecast_final_demand_at_current_price(
        known_sold_rooms=known_sold,
        sellable_rooms=sellable,
        baseline_occupancy=baseline_occupancy,
        pickup_14d=pickup_14d,
        days_to_arrival=days_to_arrival,
    )
    price_neutral_new_demand: float = max(demand_forecast - known_sold, 0.0)
    remaining_inventory_ratio: float = remaining_capacity / sellable if sellable else 1.0
    elasticity: float = estimate_price_elasticity(
        occupancy=occupancy,
        baseline_occupancy=baseline_occupancy,
        remaining_inventory_ratio=remaining_inventory_ratio,
        pickup_14d=pickup_14d,
        days_to_arrival=days_to_arrival,
        is_weekend=is_weekend,
    )

    current_expected_revenue, current_expected_new_sold = _expected_revenue(
        candidate_price=price,
        current_price=price,
        known_revenue=known_revenue,
        price_neutral_new_demand=price_neutral_new_demand,
        remaining_capacity=remaining_capacity,
        elasticity=elasticity,
    )

    if price <= 0:
        return RevenueSimulationResult(
            recommended_price=price,
            current_expected_revenue=current_expected_revenue,
            recommended_expected_revenue=current_expected_revenue,
            expected_revenue_delta=0.0,
            current_expected_sold_rooms=known_sold + current_expected_new_sold,
            expected_sold_rooms=known_sold + current_expected_new_sold,
            expected_new_sold_rooms=current_expected_new_sold,
            demand_forecast_at_current_price=demand_forecast,
            demand_elasticity=elasticity,
            candidate_price_count=1,
            price_floor_applied=False,
            price_ceiling_applied=False,
        )

    candidates: list[float] = build_candidate_prices(
        current_price=price,
        max_change_pct=max_change_pct,
        rounding_strategy=rounding_strategy,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )

    best_price: float = price
    best_revenue: float = current_expected_revenue
    best_new_sold: float = current_expected_new_sold
    for candidate_price in candidates:
        candidate_revenue, candidate_new_sold = _expected_revenue(
            candidate_price=candidate_price,
            current_price=price,
            known_revenue=known_revenue,
            price_neutral_new_demand=price_neutral_new_demand,
            remaining_capacity=remaining_capacity,
            elasticity=elasticity,
        )
        better_revenue: bool = candidate_revenue > best_revenue + 0.01
        same_revenue_closer: bool = math.isclose(candidate_revenue, best_revenue, abs_tol=0.01) and abs(candidate_price - price) < abs(best_price - price)
        if better_revenue or same_revenue_closer:
            best_price = candidate_price
            best_revenue = candidate_revenue
            best_new_sold = candidate_new_sold

    lower, upper = _price_range(price, max_change_pct, price_floor, price_ceiling)
    minimum_uplift: float = max(abs(current_expected_revenue) * MIN_REVENUE_UPLIFT_PCT, 0.01)
    current_price_allowed: bool = _is_price_allowed(price, lower, upper)
    if current_price_allowed and best_revenue - current_expected_revenue < minimum_uplift:
        best_price = price
        best_revenue = current_expected_revenue
        best_new_sold = current_expected_new_sold

    floor: Optional[float] = _positive_bound(price_floor)
    ceiling: Optional[float] = _positive_bound(price_ceiling)
    floor_applied: bool = floor is not None and math.isclose(best_price, floor, abs_tol=0.01)
    ceiling_applied: bool = ceiling is not None and math.isclose(best_price, ceiling, abs_tol=0.01)

    return RevenueSimulationResult(
        recommended_price=round(best_price, 2),
        current_expected_revenue=round(current_expected_revenue, 2),
        recommended_expected_revenue=round(best_revenue, 2),
        expected_revenue_delta=round(best_revenue - current_expected_revenue, 2),
        current_expected_sold_rooms=round(known_sold + current_expected_new_sold, 3),
        expected_sold_rooms=round(known_sold + best_new_sold, 3),
        expected_new_sold_rooms=round(best_new_sold, 3),
        demand_forecast_at_current_price=round(demand_forecast, 3),
        demand_elasticity=round(elasticity, 3),
        candidate_price_count=len(candidates),
        price_floor_applied=floor_applied,
        price_ceiling_applied=ceiling_applied,
    )
