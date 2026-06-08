import calendar
from pathlib import Path

import pandas as pd


MONTH_TO_NUMBER = {month: index for index, month in enumerate(calendar.month_name) if month}


def convert_hotel_booking_demand(source_csv, output_dir="sample_data", hotel_filter=None) -> None:
    """Convert Kaggle Hotel Booking Demand data into the MVP canonical CSV files.

    The Kaggle file contains booking and ADR data, but not true inventory snapshots
    or current listed-price snapshots. This adapter creates demo inventory and
    current-price files so the Streamlit MVP can run without a real PMS export.
    """
    source_csv = Path(source_csv)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(source_csv)
    if hotel_filter:
        raw = raw[raw["hotel"] == hotel_filter].copy()

    raw["arrival_month_number"] = raw["arrival_date_month"].map(MONTH_TO_NUMBER)
    raw["check_in_date"] = pd.to_datetime(
        dict(
            year=raw["arrival_date_year"],
            month=raw["arrival_month_number"],
            day=raw["arrival_date_day_of_month"],
        ),
        errors="coerce",
    )
    raw["nights"] = raw["stays_in_weekend_nights"].fillna(0).astype(int) + raw["stays_in_week_nights"].fillna(0).astype(int)
    raw = raw[raw["nights"] > 0].copy()
    raw["check_out_date"] = raw["check_in_date"] + pd.to_timedelta(raw["nights"], unit="D")
    raw["booking_date"] = raw["check_in_date"] - pd.to_timedelta(raw["lead_time"].fillna(0).astype(int), unit="D")

    raw["rooms"] = 1
    raw["daily_rate"] = pd.to_numeric(raw["adr"], errors="coerce").fillna(0).clip(lower=1)
    raw["gross_room_revenue"] = raw["daily_rate"] * raw["nights"] * raw["rooms"]
    raw["status"] = raw["is_canceled"].map({0: "stayed", 1: "cancelled"}).fillna("confirmed")
    raw["net_room_revenue"] = raw.apply(lambda r: 0 if r["status"] == "cancelled" else r["gross_room_revenue"], axis=1)
    raw["hotel_id"] = raw["hotel"].str.replace(" ", "_").str.upper()
    raw["room_type"] = raw["reserved_room_type"].astype(str)
    raw["channel"] = raw["market_segment"].fillna(raw.get("distribution_channel", "unknown"))
    raw["cancelled_at"] = ""

    bookings = pd.DataFrame(
        {
            "booking_id": [f"KAGGLE_{i:06d}" for i in range(len(raw))],
            "hotel_id": raw["hotel_id"],
            "room_type": raw["room_type"],
            "booking_date": raw["booking_date"].dt.date,
            "check_in_date": raw["check_in_date"].dt.date,
            "check_out_date": raw["check_out_date"].dt.date,
            "nights": raw["nights"],
            "rooms": raw["rooms"],
            "gross_room_revenue": raw["gross_room_revenue"].round(2),
            "net_room_revenue": raw["net_room_revenue"].round(2),
            "daily_rate": raw["daily_rate"].round(2),
            "channel": raw["channel"],
            "status": raw["status"],
            "cancelled_at": raw["cancelled_at"],
        }
    )
    bookings.to_csv(output_dir / "bookings.csv", index=False)

    stay_dates = pd.date_range(bookings["check_in_date"].min(), bookings["check_out_date"].max(), freq="D")
    room_types = sorted(bookings["room_type"].dropna().unique())
    hotel_ids = sorted(bookings["hotel_id"].dropna().unique())

    inventory_rows = []
    for hotel_id in hotel_ids:
        for room_type in room_types:
            historical_peak = bookings[(bookings["hotel_id"] == hotel_id) & (bookings["room_type"] == room_type)].groupby("check_in_date")["rooms"].sum().max()
            available_rooms = int(max(5, historical_peak * 1.25 if pd.notna(historical_peak) else 10))
            for stay_date in stay_dates:
                inventory_rows.append(
                    {
                        "hotel_id": hotel_id,
                        "room_type": room_type,
                        "stay_date": stay_date.date(),
                        "available_rooms": available_rooms,
                        "out_of_order_rooms": 0,
                    }
                )
    pd.DataFrame(inventory_rows).to_csv(output_dir / "inventory.csv", index=False)

    recent_start = pd.to_datetime(bookings["check_in_date"]).max() - pd.Timedelta(days=60)
    price_rows = []
    for hotel_id in hotel_ids:
        for room_type in room_types:
            subset = bookings[(bookings["hotel_id"] == hotel_id) & (bookings["room_type"] == room_type)]
            base_price = float(subset["daily_rate"].median()) if not subset.empty else 100.0
            for stay_date in pd.date_range(recent_start, recent_start + pd.Timedelta(days=60), freq="D"):
                weekend_uplift = 1.15 if stay_date.weekday() >= 5 else 1.0
                price_rows.append(
                    {
                        "hotel_id": hotel_id,
                        "room_type": room_type,
                        "stay_date": stay_date.date(),
                        "current_price": round(base_price * weekend_uplift, 2),
                    }
                )
    pd.DataFrame(price_rows).to_csv(output_dir / "current_prices.csv", index=False)
