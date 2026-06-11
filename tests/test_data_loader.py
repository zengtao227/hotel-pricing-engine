"""Tests for data_loader.py — row limit and date parsing."""
from __future__ import annotations

import io

import pandas as pd
import pytest

from src.data_loader import MAX_UPLOAD_ROWS, load_hotel_data, _check_row_limit


def _csv(rows: int, dataset: str = "bookings") -> io.StringIO:
    if dataset == "bookings":
        header = "booking_id,hotel_id,room_type,booking_date,check_in_date,check_out_date,nights,rooms,gross_room_revenue,net_room_revenue,daily_rate,channel,status\n"
        row = "B1,H1,Standard Double,2024-01-01,2024-02-01,2024-02-02,1,1,400,360,400,direct,confirmed\n"
    elif dataset == "inventory":
        header = "hotel_id,room_type,stay_date,available_rooms,out_of_order_rooms\n"
        row = "H1,Standard Double,2024-02-01,10,0\n"
    else:
        header = "hotel_id,room_type,stay_date,current_price\n"
        row = "H1,Standard Double,2024-02-01,400\n"
    return io.StringIO(header + row * rows)


class TestCheckRowLimit:
    def test_within_limit_passes(self):
        df = pd.DataFrame({"x": range(10)})
        _check_row_limit(df, "test")  # no exception

    def test_over_limit_raises(self):
        df = pd.DataFrame({"x": range(MAX_UPLOAD_ROWS + 1)})
        with pytest.raises(ValueError, match="upload limit"):
            _check_row_limit(df, "test_dataset")

    def test_exact_limit_passes(self):
        df = pd.DataFrame({"x": range(MAX_UPLOAD_ROWS)})
        _check_row_limit(df, "test")  # no exception


class TestLoadHotelData:
    def test_dates_parsed_correctly(self):
        data = load_hotel_data(
            _csv(1, "bookings"),
            _csv(1, "inventory"),
            _csv(1, "current_prices"),
        )
        assert pd.api.types.is_datetime64_any_dtype(data.bookings["check_in_date"])
        assert pd.api.types.is_datetime64_any_dtype(data.inventory["stay_date"])
        assert pd.api.types.is_datetime64_any_dtype(data.current_prices["stay_date"])

    def test_row_limit_enforced_on_bookings(self):
        with pytest.raises(ValueError, match="bookings"):
            load_hotel_data(
                _csv(MAX_UPLOAD_ROWS + 1, "bookings"),
                _csv(1, "inventory"),
                _csv(1, "current_prices"),
            )

    def test_row_limit_enforced_on_inventory(self):
        with pytest.raises(ValueError, match="inventory"):
            load_hotel_data(
                _csv(1, "bookings"),
                _csv(MAX_UPLOAD_ROWS + 1, "inventory"),
                _csv(1, "current_prices"),
            )
