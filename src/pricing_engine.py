from __future__ import annotations

import pandas as pd

from .metrics import calculate_pickup
from .revenue_simulation import RevenueSimulationResult, simulate_revenue_maximizing_price


RECOMMENDATION_COLUMNS = [
    "stay_date",
    "hotel_id",
    "room_type",
    "current_price",
    "recommended_price",
    "price_floor",
    "price_ceiling",
    "action",
    "expected_revenue_delta",
    "current_expected_revenue",
    "recommended_expected_revenue",
    "demand_forecast_at_current_price",
    "current_expected_sold_rooms",
    "expected_sold_rooms",
    "expected_new_sold_rooms",
    "demand_elasticity",
    "candidate_price_count",
    "confidence",
    "occupancy",
    "remaining_inventory_ratio",
    "pickup_14d",
    "main_reasons",
    "risk_flags",
]


def _action(current_price: float, recommended_price: float) -> str:
    change = (recommended_price - current_price) / current_price if current_price else 0
    if change > 0.03:
        return "increase"
    if change < -0.03:
        return "decrease"
    return "hold"


def _apply_price_bounds(price: float, room_type: str, room_price_bounds: dict | None) -> tuple[float, float | None, float | None]:
    if not room_price_bounds or room_type not in room_price_bounds:
        return float(price), None, None
    bounds = room_price_bounds[room_type]
    min_price = float(bounds.get("min_price") or 0)
    max_price = float(bounds.get("max_price") or 0)
    bounded = float(price)
    if min_price > 0:
        bounded = max(bounded, min_price)
    if max_price > 0:
        bounded = min(bounded, max_price)
    return bounded, min_price or None, max_price or None


def _confidence_from_simulation(
    score: int,
    action: str,
    expected_revenue_delta: float,
    current_expected_revenue: float,
) -> str:
    if action == "hold":
        return "medium" if abs(score) >= 2 else "low"

    uplift_ratio: float = expected_revenue_delta / current_expected_revenue if current_expected_revenue > 0 else 0.0
    if abs(score) >= 4 and uplift_ratio >= 0.03:
        return "high"
    if abs(score) >= 2 or uplift_ratio >= 0.015:
        return "medium"
    return "low"


def generate_recommendations(
    metrics: pd.DataFrame,
    bookings: pd.DataFrame,
    current_prices: pd.DataFrame,
    observation_date=None,
    horizon_days: int = 30,
    max_change_pct: float = 0.15,
    price_rounding_strategy: str = "chinese_lucky",
    room_price_bounds: dict | None = None,
) -> pd.DataFrame:
    """Generate explainable revenue-maximizing price recommendations."""
    prices = current_prices.copy()
    prices["stay_date"] = pd.to_datetime(prices["stay_date"]).dt.normalize()

    if observation_date is None:
        observation_date = prices["stay_date"].min()
    observation_date = pd.to_datetime(observation_date).normalize()
    end_date = observation_date + pd.Timedelta(days=horizon_days)

    future_prices = prices[(prices["stay_date"] >= observation_date) & (prices["stay_date"] <= end_date)].copy()

    m = metrics.copy()
    m["stay_date"] = pd.to_datetime(m["stay_date"]).dt.normalize()
    pickup = calculate_pickup(bookings, observation_date=observation_date)

    future = future_prices.merge(
        m[["hotel_id", "room_type", "stay_date", "sellable_rooms", "sold_rooms", "room_revenue", "occupancy", "adr", "revpar", "is_weekend"]],
        how="left",
        on=["hotel_id", "room_type", "stay_date"],
    ).merge(pickup, how="left", on=["hotel_id", "room_type", "stay_date"])

    future["sellable_rooms"] = pd.to_numeric(future["sellable_rooms"], errors="coerce")
    future = future[future["sellable_rooms"].fillna(0) > 0].copy()
    if future.empty:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)

    future[["sold_rooms", "room_revenue", "pickup_7d", "pickup_14d"]] = future[["sold_rooms", "room_revenue", "pickup_7d", "pickup_14d"]].fillna(0)
    future["occupancy"] = future["occupancy"].fillna(0)

    historical = m[m["stay_date"] < observation_date].copy()

    baselines = (
        historical.groupby(["room_type", "is_weekend"], as_index=False)
        .agg(
            baseline_occupancy=("occupancy", "median"),
            baseline_adr=("adr", "median"),
            baseline_revpar=("revpar", "median"),
        )
    )

    recs = future.merge(baselines, how="left", on=["room_type", "is_weekend"])
    recs["baseline_occupancy"] = recs["baseline_occupancy"].fillna(historical["occupancy"].median())
    recs["baseline_adr"] = recs["baseline_adr"].fillna(historical["adr"].median())
    recs["baseline_revpar"] = recs["baseline_revpar"].fillna(historical["revpar"].median())

    recommendations = []
    for row in recs.itertuples(index=False):
        current_price = float(row.current_price)
        occupancy = float(row.occupancy or 0)
        baseline_occupancy = float(row.baseline_occupancy or 0)
        pickup_14d = float(getattr(row, "pickup_14d", 0) or 0)
        sellable_rooms = float(getattr(row, "sellable_rooms", 0) or 0)
        sold_rooms = float(getattr(row, "sold_rooms", 0) or 0)
        remaining_ratio = (sellable_rooms - sold_rooms) / sellable_rooms if sellable_rooms else 1
        days_to_arrival = int((row.stay_date - observation_date).days)

        score = 0
        reasons = []
        risk_flags = []

        if row.is_weekend:
            score += 1
            reasons.append("weekend demand pattern")

        if occupancy > baseline_occupancy + 0.12:
            score += 2
            reasons.append("occupancy above similar historical dates")
        elif occupancy < max(0.2, baseline_occupancy - 0.12):
            score -= 2
            reasons.append("occupancy below similar historical dates")

        if pickup_14d >= 4:
            score += 1
            reasons.append("recent 14-day pickup is strong")
        elif days_to_arrival <= 14 and pickup_14d <= 1:
            score -= 1
            reasons.append("weak recent pickup close to arrival")

        if remaining_ratio < 0.25:
            score += 2
            reasons.append("remaining inventory is limited")
        elif days_to_arrival <= 14 and remaining_ratio > 0.55:
            score -= 2
            reasons.append("high remaining inventory close to arrival")

        if days_to_arrival <= 3:
            risk_flags.append("very close to stay date")
        if sellable_rooms <= 0:
            risk_flags.append("missing or invalid inventory")
        if pd.isna(row.baseline_adr):
            risk_flags.append("limited historical baseline")

        bounded_current_price, min_price, max_price = _apply_price_bounds(current_price, row.room_type, room_price_bounds)
        simulation: RevenueSimulationResult = simulate_revenue_maximizing_price(
            current_price=bounded_current_price,
            sellable_rooms=sellable_rooms,
            known_sold_rooms=sold_rooms,
            known_room_revenue=float(getattr(row, "room_revenue", 0) or 0),
            occupancy=occupancy,
            baseline_occupancy=baseline_occupancy,
            pickup_14d=pickup_14d,
            days_to_arrival=days_to_arrival,
            is_weekend=bool(row.is_weekend),
            max_change_pct=max_change_pct,
            rounding_strategy=price_rounding_strategy,
            price_floor=min_price,
            price_ceiling=max_price,
        )
        recommended_price = simulation.recommended_price
        recommended_action = _action(current_price, recommended_price)
        confidence = _confidence_from_simulation(
            score=score,
            action=recommended_action,
            expected_revenue_delta=simulation.expected_revenue_delta,
            current_expected_revenue=simulation.current_expected_revenue,
        )

        if simulation.price_floor_applied:
            risk_flags.append("price floor applied")
        if simulation.price_ceiling_applied:
            risk_flags.append("price ceiling applied")
        if not reasons:
            reasons.append("no strong demand or inventory signal")
        if recommended_action == "hold":
            reasons.append("current price is near simulated revenue optimum")
        else:
            reasons.append("candidate price maximizes simulated expected revenue")
        reasons.append("price elasticity model estimates demand response")

        recommendations.append(
            {
                "stay_date": row.stay_date.date(),
                "hotel_id": row.hotel_id,
                "room_type": row.room_type,
                "current_price": current_price,
                "recommended_price": recommended_price,
                "price_floor": min_price,
                "price_ceiling": max_price,
                "action": recommended_action,
                "expected_revenue_delta": round(float(simulation.expected_revenue_delta), 2),
                "current_expected_revenue": round(float(simulation.current_expected_revenue), 2),
                "recommended_expected_revenue": round(float(simulation.recommended_expected_revenue), 2),
                "demand_forecast_at_current_price": round(float(simulation.demand_forecast_at_current_price), 2),
                "current_expected_sold_rooms": round(float(simulation.current_expected_sold_rooms), 2),
                "expected_sold_rooms": round(float(simulation.expected_sold_rooms), 2),
                "expected_new_sold_rooms": round(float(simulation.expected_new_sold_rooms), 2),
                "demand_elasticity": round(float(simulation.demand_elasticity), 4),
                "candidate_price_count": simulation.candidate_price_count,
                "confidence": confidence,
                "occupancy": round(occupancy, 4),
                "remaining_inventory_ratio": round(remaining_ratio, 4),
                "pickup_14d": pickup_14d,
                "main_reasons": "; ".join(reasons),
                "risk_flags": "; ".join(risk_flags) if risk_flags else "",
            }
        )

    if not recommendations:
        return pd.DataFrame(columns=RECOMMENDATION_COLUMNS)
    return pd.DataFrame(recommendations, columns=RECOMMENDATION_COLUMNS).sort_values(["stay_date", "room_type"])
