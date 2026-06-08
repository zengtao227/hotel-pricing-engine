from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .sample_data import build_demo_data


DATE_COLUMNS = {
    "bookings": ["booking_date", "check_in_date", "check_out_date", "cancelled_at"],
    "inventory": ["stay_date"],
    "current_prices": ["stay_date"],
}


@dataclass(frozen=True)
class HotelData:
    bookings: pd.DataFrame
    inventory: pd.DataFrame
    current_prices: pd.DataFrame


def _parse_dates(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    df = df.copy()
    for column in DATE_COLUMNS.get(dataset, []):
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def load_hotel_data(bookings_source, inventory_source, current_prices_source) -> HotelData:
    bookings = _parse_dates(pd.read_csv(bookings_source), "bookings")
    inventory = _parse_dates(pd.read_csv(inventory_source), "inventory")
    current_prices = _parse_dates(pd.read_csv(current_prices_source), "current_prices")
    return HotelData(bookings=bookings, inventory=inventory, current_prices=current_prices)


def load_demo_data(base_dir="sample_data") -> HotelData:
    """Load CSV demo data if present; otherwise generate deterministic demo data."""
    base = Path(base_dir)
    bookings_path = base / "bookings.csv"
    inventory_path = base / "inventory.csv"
    current_prices_path = base / "current_prices.csv"

    if bookings_path.exists() and inventory_path.exists() and current_prices_path.exists():
        return load_hotel_data(bookings_path, inventory_path, current_prices_path)

    bookings, inventory, current_prices = build_demo_data()
    return HotelData(
        bookings=_parse_dates(bookings, "bookings"),
        inventory=_parse_dates(inventory, "inventory"),
        current_prices=_parse_dates(current_prices, "current_prices"),
    )
