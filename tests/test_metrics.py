import pytest
import pandas as pd

from src.metrics import calculate_pickup, expand_bookings_to_room_nights


def _booking(**overrides) -> dict:
    base = {
        "booking_id": "B00001",
        "hotel_id": "H1",
        "room_type": "Standard Double",
        "booking_date": "2026-02-01",
        "check_in_date": "2026-02-20",
        "check_out_date": "2026-02-21",
        "nights": 1,
        "rooms": 1,
        "gross_room_revenue": 100.0,
        "net_room_revenue": 100.0,
        "daily_rate": 100.0,
        "channel": "Direct",
        "status": "confirmed",
    }
    base.update(overrides)
    return base


def test_expand_multi_night_booking_splits_revenue_per_night():
    bookings = pd.DataFrame(
        [
            _booking(
                booking_id="B1",
                nights=3,
                rooms=2,
                check_out_date="2026-02-23",
                gross_room_revenue=600.0,
                net_room_revenue=570.0,
            )
        ]
    )
    nights = expand_bookings_to_room_nights(bookings)

    assert len(nights) == 3
    assert sorted(nights["stay_date"].dt.strftime("%Y-%m-%d")) == ["2026-02-20", "2026-02-21", "2026-02-22"]
    assert (nights["rooms"] == 2).all()
    assert nights["net_room_revenue"].tolist() == [190.0, 190.0, 190.0]
    assert nights["gross_room_revenue"].sum() == 600.0


def test_expand_cancelled_booking_contributes_no_rooms_or_revenue():
    bookings = pd.DataFrame([_booking(booking_id="B2", status="cancelled", nights=2, check_out_date="2026-02-22")])
    nights = expand_bookings_to_room_nights(bookings)

    assert len(nights) == 2
    assert (nights["rooms"] == 0).all()
    assert nights["net_room_revenue"].sum() == 0.0


def test_pickup_windows_cut_off_at_observation_date():
    observation_date = "2026-02-15"
    bookings = pd.DataFrame(
        [
            # Inside 7d window (> 02-08 and <= 02-15): counts in 7d and 14d.
            _booking(booking_id="B1", booking_date="2026-02-10", rooms=2),
            # Booked after observation date: must be excluded (no future leakage).
            _booking(booking_id="B2", booking_date="2026-02-16", rooms=5),
            # Inside 14d window only (> 02-01, <= 02-08 boundary excluded for 7d).
            _booking(booking_id="B3", booking_date="2026-02-03", rooms=1),
            # Stay date already in the past: excluded.
            _booking(booking_id="B4", booking_date="2026-02-10", check_in_date="2026-02-10", check_out_date="2026-02-11", rooms=3),
            # Cancelled: excluded.
            _booking(booking_id="B5", booking_date="2026-02-12", status="cancelled", rooms=4),
        ]
    )
    pickup = calculate_pickup(bookings, observation_date=observation_date)

    row = pickup[pickup["stay_date"] == pd.Timestamp("2026-02-20")].iloc[0]
    assert row["pickup_7d"] == 2
    assert row["pickup_14d"] == 3


from src.metrics import calculate_historical_pickup_baseline


def _make_historical_bookings_for_baseline() -> pd.DataFrame:
    """构造历史订单数据，用于验证 pickup baseline 计算。

    H1 / Standard Double，observation_date = 2026-03-01
    - B1: check_in=Jan 10 (Sat, weekend), booked Jan 05 (5天前，在14天窗口内), rooms=2
    - B2: check_in=Jan 10 (Sat, weekend), booked Dec 20 (21天前，NOT in 14d window), rooms=1
    - B3: check_in=Jan 20 (Tue, weekday), booked Jan 15 (5天前，in 14d window), rooms=3
    - B4: check_in=Jan 20 (Tue, weekday), booked Jan 01 (19天前，NOT in 14d window), rooms=2
    - B5: check_in=Feb 15 (Sun, weekend), booked Feb 10 (5天前，in 14d window), rooms=1

    期望结果：
    - weekday (Jan 20): pickup_14d=3 → median=3.0
    - weekend (Jan 10 pickup=2, Feb 15 pickup=1) → median=1.5
    """
    return pd.DataFrame({
        "booking_id": ["B1", "B2", "B3", "B4", "B5"],
        "hotel_id": ["H1"] * 5,
        "room_type": ["Standard Double"] * 5,
        "check_in_date": pd.to_datetime(["2026-01-10", "2026-01-10", "2026-01-20", "2026-01-20", "2026-02-15"]),
        "check_out_date": pd.to_datetime(["2026-01-11", "2026-01-11", "2026-01-21", "2026-01-21", "2026-02-16"]),
        "booking_date": pd.to_datetime(["2026-01-05", "2025-12-20", "2026-01-15", "2026-01-01", "2026-02-10"]),
        "nights": [1] * 5,
        "rooms": [2, 1, 3, 2, 1],
        "gross_room_revenue": [800, 400, 1200, 800, 400],
        "net_room_revenue": [800, 400, 1200, 800, 400],
        "daily_rate": [400] * 5,
        "channel": ["direct"] * 5,
        "status": ["stayed"] * 5,
    })


def test_calculate_historical_pickup_baseline_weekday():
    bookings = _make_historical_bookings_for_baseline()
    result = calculate_historical_pickup_baseline(bookings, pd.to_datetime("2026-03-01"))
    row = result[
        (result["hotel_id"] == "H1") &
        (result["room_type"] == "Standard Double") &
        (~result["is_weekend"])
    ]
    assert len(row) == 1
    assert row.iloc[0]["baseline_pickup_14d"] == pytest.approx(3.0)


def test_calculate_historical_pickup_baseline_weekend():
    bookings = _make_historical_bookings_for_baseline()
    result = calculate_historical_pickup_baseline(bookings, pd.to_datetime("2026-03-01"))
    row = result[
        (result["hotel_id"] == "H1") &
        (result["room_type"] == "Standard Double") &
        (result["is_weekend"])
    ]
    assert len(row) == 1
    # Jan 10: pickup=2, Feb 15: pickup=1 → median = 1.5
    assert row.iloc[0]["baseline_pickup_14d"] == pytest.approx(1.5)


def test_calculate_historical_pickup_baseline_empty():
    empty = pd.DataFrame(columns=[
        "booking_id", "hotel_id", "room_type", "check_in_date", "check_out_date",
        "booking_date", "nights", "rooms", "gross_room_revenue", "net_room_revenue",
        "daily_rate", "channel", "status"
    ])
    result = calculate_historical_pickup_baseline(empty, pd.to_datetime("2026-03-01"))
    assert result.empty
    assert list(result.columns) == ["hotel_id", "room_type", "is_weekend", "baseline_pickup_14d"]


def test_calculate_historical_pickup_baseline_excludes_future_stays():
    """observation_date 之后的入住日期不应计入历史基准。"""
    bookings = _make_historical_bookings_for_baseline()
    # 用更早的 observation_date，Jan 20 就变成了未来日期
    result = calculate_historical_pickup_baseline(bookings, pd.to_datetime("2026-01-15"))
    # 只有 Jan 10 (weekend) 是历史的，Jan 20 / Feb 15 是未来的
    row_weekday = result[
        (result["hotel_id"] == "H1") &
        (result["room_type"] == "Standard Double") &
        (~result["is_weekend"])
    ]
    assert len(row_weekday) == 0  # 没有历史 weekday 数据
