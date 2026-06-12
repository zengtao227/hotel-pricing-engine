"""Regression coverage for bundled demo data generation."""
from __future__ import annotations

from src.sample_data import build_demo_data
from src.validation import validate_all


def test_demo_data_passes_validation() -> None:
    bookings, inventory, current_prices = build_demo_data()

    assert validate_all(bookings, inventory, current_prices) == []
