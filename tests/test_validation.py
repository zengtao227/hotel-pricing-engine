"""Tests for validation.py — covers new validators added in the security review."""
from __future__ import annotations

import pandas as pd
import pytest

from src.validation import (
    validate_bookings,
    validate_cross_table_consistency,
    validate_current_prices,
    validate_inventory,
)


def _bookings(**overrides) -> pd.DataFrame:
    base = {
        "booking_id": ["B1"],
        "hotel_id": ["H1"],
        "room_type": ["Standard Double"],
        "booking_date": pd.to_datetime(["2024-01-01"]),
        "check_in_date": pd.to_datetime(["2024-02-01"]),
        "check_out_date": pd.to_datetime(["2024-02-03"]),
        "nights": [2],
        "rooms": [1],
        "gross_room_revenue": [800.0],
        "net_room_revenue": [720.0],
        "daily_rate": [400.0],
        "channel": ["direct"],
        "status": ["confirmed"],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _inventory(**overrides) -> pd.DataFrame:
    base = {
        "hotel_id": ["H1"],
        "room_type": ["Standard Double"],
        "stay_date": pd.to_datetime(["2024-02-01"]),
        "available_rooms": [10],
        "out_of_order_rooms": [0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _prices(**overrides) -> pd.DataFrame:
    base = {
        "hotel_id": ["H1"],
        "room_type": ["Standard Double"],
        "stay_date": pd.to_datetime(["2024-02-01"]),
        "current_price": [400.0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


class TestValidateBookings:
    def test_valid_returns_no_errors(self):
        assert validate_bookings(_bookings()) == []

    def test_invalid_nights_zero(self):
        errors = validate_bookings(_bookings(nights=[0]))
        assert any("invalid nights" in e for e in errors)

    def test_invalid_nights_over_365(self):
        errors = validate_bookings(_bookings(nights=[366]))
        assert any("invalid nights" in e for e in errors)

    def test_invalid_nights_nan(self):
        errors = validate_bookings(_bookings(nights=["bad"]))
        assert any("invalid nights" in e for e in errors)

    def test_invalid_rooms_zero(self):
        errors = validate_bookings(_bookings(rooms=[0]))
        assert any("invalid rooms" in e for e in errors)

    def test_fractional_rooms_rejected(self):
        errors = validate_bookings(_bookings(rooms=[1.5]))
        assert any("invalid rooms" in e for e in errors)

    def test_invalid_daily_rate_nan(self):
        errors = validate_bookings(_bookings(daily_rate=["N/A"]))
        assert any("invalid or non-positive daily_rate" in e for e in errors)

    def test_nights_must_match_checkin_checkout_dates(self):
        errors = validate_bookings(_bookings(nights=[1]))
        assert any("nights inconsistent" in e for e in errors)

    def test_invalid_status_rejected(self):
        errors = validate_bookings(_bookings(status=["tentative_unknown"]))
        assert any("unsupported status" in e for e in errors)

    def test_negative_revenue_rejected(self):
        errors = validate_bookings(_bookings(net_room_revenue=[-1.0]))
        assert any("negative net_room_revenue" in e for e in errors)

    def test_checkout_before_checkin(self):
        df = _bookings()
        df["check_out_date"] = df["check_in_date"]
        errors = validate_bookings(df)
        assert any("check_out_date <= check_in_date" in e for e in errors)


class TestValidateInventory:
    def test_valid_returns_no_errors(self):
        assert validate_inventory(_inventory()) == []

    def test_nan_available_rooms(self):
        errors = validate_inventory(_inventory(available_rooms=[None]))
        assert any("invalid available_rooms" in e for e in errors)

    def test_negative_available_rooms(self):
        errors = validate_inventory(_inventory(available_rooms=[-1]))
        assert any("negative available_rooms" in e for e in errors)

    def test_invalid_out_of_order_rooms(self):
        errors = validate_inventory(_inventory(out_of_order_rooms=["bad"]))
        assert any("invalid out_of_order_rooms" in e for e in errors)

    def test_negative_out_of_order_rooms(self):
        errors = validate_inventory(_inventory(out_of_order_rooms=[-1]))
        assert any("negative out_of_order_rooms" in e for e in errors)

    def test_out_of_order_cannot_exceed_available(self):
        errors = validate_inventory(_inventory(available_rooms=[3], out_of_order_rooms=[4]))
        assert any("out_of_order_rooms greater than available_rooms" in e for e in errors)

    def test_duplicate_rows(self):
        inv = pd.concat([_inventory(), _inventory()], ignore_index=True)
        errors = validate_inventory(inv)
        assert any("duplicate" in e for e in errors)


class TestValidateCurrentPrices:
    def test_valid_returns_no_errors(self):
        assert validate_current_prices(_prices()) == []

    def test_zero_price(self):
        errors = validate_current_prices(_prices(current_price=[0.0]))
        assert any("invalid or non-positive current_price" in e for e in errors)

    def test_nan_price(self):
        errors = validate_current_prices(_prices(current_price=[None]))
        assert any("invalid or non-positive current_price" in e for e in errors)

    def test_negative_price(self):
        errors = validate_current_prices(_prices(current_price=[-10.0]))
        assert any("invalid or non-positive current_price" in e for e in errors)

    def test_duplicate_price_rows(self):
        prices = pd.concat([_prices(), _prices()], ignore_index=True)
        errors = validate_current_prices(prices)
        assert any("duplicate" in e for e in errors)


class TestCrossTableConsistency:
    def test_missing_hotel_in_inventory(self):
        bk = _bookings(hotel_id=["UNKNOWN"])
        errors = validate_cross_table_consistency(bk, _inventory(), _prices())
        assert any("inventory" in e and "UNKNOWN" in e for e in errors)

    def test_overbooking_detection_single_night(self):
        bk = _bookings(rooms=[15])  # 15 rooms, only 10 available
        errors = validate_cross_table_consistency(bk, _inventory(), _prices())
        assert any("exceeding available inventory" in e for e in errors)

    def test_overbooking_detection_multi_night(self):
        """A 2-night booking should be checked against inventory on both nights."""
        bk = _bookings(
            nights=[2],
            rooms=[15],
            check_in_date=pd.to_datetime(["2024-02-01"]),
            check_out_date=pd.to_datetime(["2024-02-03"]),
        )
        inv = pd.DataFrame({
            "hotel_id": ["H1", "H1"],
            "room_type": ["Standard Double", "Standard Double"],
            "stay_date": pd.to_datetime(["2024-02-01", "2024-02-02"]),
            "available_rooms": [10, 10],
            "out_of_order_rooms": [0, 0],
        })
        errors = validate_cross_table_consistency(bk, inv, _prices())
        assert any("exceeding available inventory" in e for e in errors)

    def test_overbooking_uses_sellable_rooms_after_out_of_order(self):
        bk = _bookings(
            nights=[1],
            rooms=[5],
            check_out_date=pd.to_datetime(["2024-02-02"]),
        )
        inv = _inventory(available_rooms=[10], out_of_order_rooms=[6])
        errors = validate_cross_table_consistency(bk, inv, _prices())
        assert any("exceeding available inventory" in e for e in errors)

    def test_no_overbooking_within_limits(self):
        # 1-night booking: rooms=5 ≤ available=10, no overbooking.
        bk = _bookings(
            nights=[1],
            rooms=[5],
            check_out_date=pd.to_datetime(["2024-02-02"]),
        )
        errors = validate_cross_table_consistency(bk, _inventory(), _prices())
        assert not any("exceeding available inventory" in e for e in errors)

    def test_missing_room_type_pair(self):
        bk = _bookings(room_type=["Suite"])
        errors = validate_cross_table_consistency(bk, _inventory(), _prices())
        assert any("hotel+room_type combination" in e for e in errors)

    def test_current_price_date_requires_matching_inventory(self):
        prices = _prices(stay_date=pd.to_datetime(["2024-02-02"]))
        errors = validate_cross_table_consistency(_bookings(), _inventory(), prices)
        assert any("current_price date row" in e for e in errors)

    def test_historical_inventory_does_not_require_matching_price(self):
        inv = pd.concat(
            [
                _inventory(stay_date=pd.to_datetime(["2024-01-01"])),
                _inventory(stay_date=pd.to_datetime(["2024-02-01"])),
            ],
            ignore_index=True,
        )
        errors = validate_cross_table_consistency(_bookings(nights=[1], check_out_date=pd.to_datetime(["2024-02-02"])), inv, _prices())
        assert not any("current_price date row" in e for e in errors)
