import numpy as np
import pandas as pd


ACTIVE_STATUSES = {"confirmed", "stayed", "checked_in", "checked_out"}
ROOM_NIGHT_COLUMNS = [
    "booking_id",
    "hotel_id",
    "room_type",
    "booking_date",
    "stay_date",
    "rooms",
    "gross_room_revenue",
    "net_room_revenue",
    "status",
    "channel",
]


def expand_bookings_to_room_nights(bookings: pd.DataFrame) -> pd.DataFrame:
    """Expand booking-level data into one row per stay date."""
    rows = []
    for row in bookings.itertuples(index=False):
        nights = int(getattr(row, "nights", 1) or 1)
        rooms = int(getattr(row, "rooms", 1) or 1)
        status = str(getattr(row, "status", "")).lower()
        active = status in ACTIVE_STATUSES
        daily_rate = float(getattr(row, "daily_rate", 0) or 0)

        for offset in range(nights):
            stay_date = pd.to_datetime(getattr(row, "check_in_date")) + pd.Timedelta(days=offset)
            rows.append(
                {
                    "booking_id": getattr(row, "booking_id"),
                    "hotel_id": getattr(row, "hotel_id"),
                    "room_type": getattr(row, "room_type"),
                    "booking_date": pd.to_datetime(getattr(row, "booking_date")),
                    "stay_date": stay_date.normalize(),
                    "rooms": rooms if active else 0,
                    "gross_room_revenue": daily_rate * rooms if active else 0.0,
                    "net_room_revenue": daily_rate * rooms if active else 0.0,
                    "status": status,
                    "channel": getattr(row, "channel", None),
                }
            )

    return pd.DataFrame(rows, columns=ROOM_NIGHT_COLUMNS)


def calculate_daily_metrics(bookings: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    room_nights = expand_bookings_to_room_nights(bookings)

    sold = (
        room_nights.groupby(["hotel_id", "room_type", "stay_date"], as_index=False)
        .agg(
            sold_rooms=("rooms", "sum"),
            room_revenue=("net_room_revenue", "sum"),
            booking_count=("booking_id", "nunique"),
        )
    )

    inv = inventory.copy()
    inv["stay_date"] = pd.to_datetime(inv["stay_date"]).dt.normalize()
    inv["sellable_rooms"] = inv["available_rooms"] - inv.get("out_of_order_rooms", 0)

    metrics = inv.merge(sold, how="left", on=["hotel_id", "room_type", "stay_date"])
    for column in ["sold_rooms", "room_revenue", "booking_count"]:
        metrics[column] = pd.to_numeric(metrics[column], errors="coerce").fillna(0)

    metrics["sellable_rooms"] = pd.to_numeric(metrics["sellable_rooms"], errors="coerce").fillna(0)
    metrics["occupancy"] = np.nan
    metrics["adr"] = np.nan
    metrics["revpar"] = np.nan

    sellable_mask = metrics["sellable_rooms"] > 0
    sold_mask = metrics["sold_rooms"] > 0
    metrics.loc[sellable_mask, "occupancy"] = metrics.loc[sellable_mask, "sold_rooms"] / metrics.loc[sellable_mask, "sellable_rooms"]
    metrics.loc[sold_mask, "adr"] = metrics.loc[sold_mask, "room_revenue"] / metrics.loc[sold_mask, "sold_rooms"]
    metrics.loc[sellable_mask, "revpar"] = metrics.loc[sellable_mask, "room_revenue"] / metrics.loc[sellable_mask, "sellable_rooms"]
    metrics["day_of_week"] = metrics["stay_date"].dt.day_name()
    metrics["is_weekend"] = metrics["stay_date"].dt.weekday >= 5
    return metrics.sort_values(["stay_date", "room_type"])


def calculate_pickup(bookings: pd.DataFrame, observation_date=None) -> pd.DataFrame:
    b = bookings.copy()
    b["booking_date"] = pd.to_datetime(b["booking_date"]).dt.normalize()
    b["check_in_date"] = pd.to_datetime(b["check_in_date"]).dt.normalize()

    if observation_date is None:
        observation_date = b["booking_date"].max()
    observation_date = pd.to_datetime(observation_date).normalize()

    active = b["status"].str.lower().isin(ACTIVE_STATUSES)
    future = b["check_in_date"] >= observation_date

    def window(days: int) -> pd.DataFrame:
        mask = active & future & (b["booking_date"] > observation_date - pd.Timedelta(days=days)) & (b["booking_date"] <= observation_date)
        return (
            b.loc[mask]
            .groupby(["hotel_id", "room_type", "check_in_date"], as_index=False)
            .agg(**{f"pickup_{days}d": ("rooms", "sum")})
            .rename(columns={"check_in_date": "stay_date"})
        )

    pickup = window(7).merge(window(14), how="outer", on=["hotel_id", "room_type", "stay_date"])
    if pickup.empty:
        return pd.DataFrame(columns=["hotel_id", "room_type", "stay_date", "pickup_7d", "pickup_14d"])

    return pickup.fillna(0)


def summarize_overview(metrics: pd.DataFrame) -> dict[str, float]:
    room_revenue = float(metrics["room_revenue"].sum())
    sold_rooms = float(metrics["sold_rooms"].sum())
    sellable_rooms = float(metrics["sellable_rooms"].sum())
    return {
        "room_revenue": room_revenue,
        "occupancy": sold_rooms / sellable_rooms if sellable_rooms else 0.0,
        "adr": room_revenue / sold_rooms if sold_rooms else 0.0,
        "revpar": room_revenue / sellable_rooms if sellable_rooms else 0.0,
    }
