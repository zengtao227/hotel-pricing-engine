from dataclasses import dataclass
from pathlib import Path

import pandas as pd


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
    base = Path(base_dir)
    return load_hotel_data(
        base / "bookings.csv",
        base / "inventory.csv",
        base / "current_prices.csv",
    )
