import numpy as np
import pandas as pd

from .metrics import calculate_pickup
from .price_rounding import round_to_price_ending


def _action(current_price: float, recommended_price: float) -> str:
    change = (recommended_price - current_price) / current_price if current_price else 0
    if change > 0.03:
        return "increase"
    if change < -0.03:
        return "decrease"
    return "hold"


def generate_recommendations(
    metrics: pd.DataFrame,
    bookings: pd.DataFrame,
    current_prices: pd.DataFrame,
    observation_date=None,
    horizon_days: int = 30,
    max_change_pct: float = 0.15,
    price_rounding_strategy: str = "chinese_lucky",
) -> pd.DataFrame:
    """Generate simple explainable rule-based price recommendations."""
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
        m[["hotel_id", "room_type", "stay_date", "sellable_rooms", "sold_rooms", "occupancy", "adr", "revpar", "is_weekend"]],
        how="left",
        on=["hotel_id", "room_type", "stay_date"],
    ).merge(pickup, how="left", on=["hotel_id", "room_type", "stay_date"])

    future[["sold_rooms", "pickup_7d", "pickup_14d"]] = future[["sold_rooms", "pickup_7d", "pickup_14d"]].fillna(0)
    future["occupancy"] = future["occupancy"].fillna(0)

    historical = m[m["stay_date"] < observation_date].copy()
    if historical.empty:
        historical = m.copy()

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
        if np.isnan(row.baseline_adr):
            risk_flags.append("limited historical baseline")

        if score >= 4:
            change_pct = 0.12
            confidence = "high"
        elif score >= 2:
            change_pct = 0.07
            confidence = "medium"
        elif score <= -4:
            change_pct = -0.12
            confidence = "high"
        elif score <= -2:
            change_pct = -0.07
            confidence = "medium"
        else:
            change_pct = 0.0
            confidence = "low"

        change_pct = float(np.clip(change_pct, -max_change_pct, max_change_pct))
        raw_recommended_price = current_price * (1 + change_pct)
        recommended_price = round_to_price_ending(raw_recommended_price, strategy=price_rounding_strategy)
        expected_revenue_delta = recommended_price * max(sold_rooms, 1) - current_price * max(sold_rooms, 1)

        if not reasons:
            reasons.append("no strong demand or inventory signal")

        recommendations.append(
            {
                "stay_date": row.stay_date.date(),
                "hotel_id": row.hotel_id,
                "room_type": row.room_type,
                "current_price": current_price,
                "recommended_price": recommended_price,
                "action": _action(current_price, recommended_price),
                "expected_revenue_delta": round(float(expected_revenue_delta), 2),
                "confidence": confidence,
                "occupancy": round(occupancy, 3),
                "remaining_inventory_ratio": round(remaining_ratio, 3),
                "pickup_14d": pickup_14d,
                "main_reasons": "; ".join(reasons),
                "risk_flags": "; ".join(risk_flags) if risk_flags else "",
            }
        )

    return pd.DataFrame(recommendations).sort_values(["stay_date", "room_type"])
