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
    """Expand booking-level data into one row per stay date (vectorized)."""
    if bookings.empty:
        return pd.DataFrame(columns=ROOM_NIGHT_COLUMNS)

    b = bookings.copy()
    b["check_in_date"] = pd.to_datetime(b["check_in_date"])
    b["booking_date"] = pd.to_datetime(b["booking_date"])
    b["nights"] = pd.to_numeric(b.get("nights", 1), errors="coerce").fillna(1).clip(lower=1, upper=365).astype(int)
    b["rooms"] = pd.to_numeric(b.get("rooms", 1), errors="coerce").fillna(1).astype(int)
    b["_status"] = b["status"].astype(str).str.lower()
    b["_active"] = b["_status"].isin(ACTIVE_STATUSES)

    daily_rate = pd.to_numeric(b.get("daily_rate", 0), errors="coerce").fillna(0)
    fallback_total = daily_rate * b["rooms"] * b["nights"]
    gross_total = pd.to_numeric(b.get("gross_room_revenue", fallback_total), errors="coerce").fillna(0)
    net_total = pd.to_numeric(b.get("net_room_revenue", fallback_total), errors="coerce").fillna(0)
    b["_gross_per_night"] = gross_total / b["nights"]
    b["_net_per_night"] = net_total / b["nights"]

    # Repeat each row by its night count, then assign per-night stay dates.
    rep = b.loc[b.index.repeat(b["nights"])].copy()
    rep["_offset"] = rep.groupby(level=0).cumcount()
    rep["stay_date"] = (rep["check_in_date"] + pd.to_timedelta(rep["_offset"], unit="D")).dt.normalize()

    inactive = ~rep["_active"]
    rep.loc[inactive, "rooms"] = 0
    rep.loc[inactive, "_gross_per_night"] = 0.0
    rep.loc[inactive, "_net_per_night"] = 0.0

    rep = rep.drop(columns=["gross_room_revenue", "net_room_revenue"], errors="ignore")
    rep = rep.rename(columns={
        "_gross_per_night": "gross_room_revenue",
        "_net_per_night": "net_room_revenue",
        "_status": "status",
    })
    if "channel" not in rep.columns:
        rep["channel"] = None

    return rep[ROOM_NIGHT_COLUMNS].reset_index(drop=True)


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
    ooo = pd.to_numeric(inv["out_of_order_rooms"], errors="coerce").fillna(0) if "out_of_order_rooms" in inv.columns else 0
    inv["sellable_rooms"] = pd.to_numeric(inv["available_rooms"], errors="coerce").fillna(0) - ooo

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
