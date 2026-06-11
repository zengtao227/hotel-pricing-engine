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
