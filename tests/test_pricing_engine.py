"""Tests for pricing_engine.py — recommendation generation."""
from __future__ import annotations

import pandas as pd
import pytest

from src.pricing_engine import RECOMMENDATION_COLUMNS, generate_recommendations


def _metrics(
    stay_dates: list[str] | None = None,
    hotel_id: str = "H1",
    room_type: str = "Standard Double",
) -> pd.DataFrame:
    if stay_dates is None:
        stay_dates = ["2024-02-01", "2024-02-02", "2024-02-03"]
    rows = []
    for date in stay_dates:
        rows.append({
            "hotel_id": hotel_id,
            "room_type": room_type,
            "stay_date": pd.to_datetime(date),
            "sellable_rooms": 10,
            "sold_rooms": 5,
            "room_revenue": 2000.0,
            "occupancy": 0.5,
            "adr": 400.0,
            "revpar": 200.0,
            "is_weekend": pd.to_datetime(date).weekday() >= 5,
            "booking_count": 5,
        })
    return pd.DataFrame(rows)


def _bookings() -> pd.DataFrame:
    return pd.DataFrame({
        "booking_id": ["B1"],
        "hotel_id": ["H1"],
        "room_type": ["Standard Double"],
        "booking_date": pd.to_datetime(["2024-01-15"]),
        "check_in_date": pd.to_datetime(["2024-02-01"]),
        "check_out_date": pd.to_datetime(["2024-02-02"]),
        "nights": [1],
        "rooms": [1],
        "gross_room_revenue": [400.0],
        "net_room_revenue": [360.0],
        "daily_rate": [400.0],
        "channel": ["direct"],
        "status": ["confirmed"],
    })


def _prices(
    stay_dates: list[str] | None = None,
    hotel_id: str = "H1",
    room_type: str = "Standard Double",
) -> pd.DataFrame:
    if stay_dates is None:
        stay_dates = ["2024-02-01", "2024-02-02", "2024-02-03"]
    return pd.DataFrame({
        "hotel_id": [hotel_id] * len(stay_dates),
        "room_type": [room_type] * len(stay_dates),
        "stay_date": pd.to_datetime(stay_dates),
        "current_price": [400.0] * len(stay_dates),
    })


class TestGenerateRecommendations:
    def test_returns_correct_columns(self):
        recs = generate_recommendations(
            metrics=_metrics(),
            bookings=_bookings(),
            current_prices=_prices(),
            observation_date="2024-02-01",
        )
        for col in RECOMMENDATION_COLUMNS:
            assert col in recs.columns, f"Missing column: {col}"

    def test_returns_dataframe_for_empty_prices(self):
        empty_prices = pd.DataFrame({
            "hotel_id": pd.Series([], dtype="str"),
            "room_type": pd.Series([], dtype="str"),
            "stay_date": pd.Series([], dtype="datetime64[ns]"),
            "current_price": pd.Series([], dtype="float64"),
        })
        recs = generate_recommendations(
            metrics=_metrics(),
            bookings=_bookings(),
            current_prices=empty_prices,
            observation_date="2024-02-01",
        )
        assert isinstance(recs, pd.DataFrame)
        assert recs.empty

    def test_action_field_values(self):
        recs = generate_recommendations(
            metrics=_metrics(),
            bookings=_bookings(),
            current_prices=_prices(),
            observation_date="2024-02-01",
        )
        assert set(recs["action"].unique()).issubset({"increase", "decrease", "hold"})

    def test_confidence_field_values(self):
        recs = generate_recommendations(
            metrics=_metrics(),
            bookings=_bookings(),
            current_prices=_prices(),
            observation_date="2024-02-01",
        )
        assert set(recs["confidence"].unique()).issubset({"high", "medium", "low"})

    def test_price_bounds_respected(self):
        recs = generate_recommendations(
            metrics=_metrics(),
            bookings=_bookings(),
            current_prices=_prices(),
            observation_date="2024-02-01",
            room_price_bounds={"Standard Double": {"min_price": 350.0, "max_price": 450.0}},
        )
        assert (recs["recommended_price"] >= 350.0).all()
        assert (recs["recommended_price"] <= 450.0).all()

    def test_multi_hotel_isolation(self):
        """Recommendations for H1 and H2 are independent — baselines don't cross."""
        metrics_h1 = _metrics(hotel_id="H1")
        metrics_h2 = _metrics(hotel_id="H2")
        metrics = pd.concat([metrics_h1, metrics_h2], ignore_index=True)
        prices = pd.concat([_prices(hotel_id="H1"), _prices(hotel_id="H2")], ignore_index=True)
        recs = generate_recommendations(
            metrics=metrics,
            bookings=_bookings(),
            current_prices=prices,
            observation_date="2024-02-01",
        )
        assert set(recs["hotel_id"].unique()) == {"H1", "H2"}

    def test_horizon_limits_output_dates(self):
        recs = generate_recommendations(
            metrics=_metrics(stay_dates=["2024-02-01", "2024-02-15", "2024-03-15"]),
            bookings=_bookings(),
            current_prices=_prices(stay_dates=["2024-02-01", "2024-02-15", "2024-03-15"]),
            observation_date="2024-02-01",
            horizon_days=14,
        )
        assert len(recs) <= 2
