import numpy as np
import pandas as pd


ACTIVE_STATUSES = {"confirmed", "stayed", "checked_in", "checked_out"}
ALLOWED_STATUSES = ACTIVE_STATUSES | {"cancelled"}


REQUIRED_COLUMNS = {
    "bookings": [
        "booking_id",
        "hotel_id",
        "room_type",
        "booking_date",
        "check_in_date",
        "check_out_date",
        "nights",
        "rooms",
        "gross_room_revenue",
        "net_room_revenue",
        "daily_rate",
        "channel",
        "status",
    ],
    "inventory": [
        "hotel_id",
        "room_type",
        "stay_date",
        "available_rooms",
        "out_of_order_rooms",
    ],
    "current_prices": [
        "hotel_id",
        "room_type",
        "stay_date",
        "current_price",
    ],
}


def validate_required_columns(df: pd.DataFrame, dataset: str) -> list[str]:
    missing = [c for c in REQUIRED_COLUMNS[dataset] if c not in df.columns]
    return [f"{dataset}: missing column `{column}`" for column in missing]


def validate_bookings(bookings: pd.DataFrame) -> list[str]:
    errors = validate_required_columns(bookings, "bookings")
    if errors:
        return errors

    booking_dates = pd.to_datetime(bookings["booking_date"], errors="coerce")
    check_in_dates = pd.to_datetime(bookings["check_in_date"], errors="coerce")
    check_out_dates = pd.to_datetime(bookings["check_out_date"], errors="coerce")

    if booking_dates.isna().any():
        errors.append("bookings: `booking_date` contains invalid dates")
    if check_in_dates.isna().any():
        errors.append("bookings: `check_in_date` contains invalid dates")
    if check_out_dates.isna().any():
        errors.append("bookings: `check_out_date` contains invalid dates")

    bad_checkout = check_out_dates <= check_in_dates
    if bad_checkout.any():
        errors.append(f"bookings: {int(bad_checkout.sum())} rows have check_out_date <= check_in_date")

    status_normalized = bookings["status"].astype(str).str.lower()
    non_cancelled = status_normalized != "cancelled"
    bad_lead_time = non_cancelled & (booking_dates > check_in_dates)
    if bad_lead_time.any():
        errors.append(f"bookings: {int(bad_lead_time.sum())} rows have booking_date > check_in_date")

    invalid_status = ~status_normalized.isin(ALLOWED_STATUSES)
    if invalid_status.any():
        errors.append(f"bookings: {int(invalid_status.sum())} rows have unsupported status")

    daily_rate_numeric = pd.to_numeric(bookings["daily_rate"], errors="coerce")
    invalid_rate = daily_rate_numeric.isna() | ~np.isfinite(daily_rate_numeric) | (daily_rate_numeric <= 0)
    if invalid_rate.any():
        errors.append(f"bookings: {int(invalid_rate.sum())} rows have invalid or non-positive daily_rate")

    rooms_numeric = pd.to_numeric(bookings["rooms"], errors="coerce")
    invalid_rooms = rooms_numeric.isna() | ~np.isfinite(rooms_numeric) | (rooms_numeric <= 0) | (rooms_numeric % 1 != 0)
    if invalid_rooms.any():
        errors.append(f"bookings: {int(invalid_rooms.sum())} rows have invalid rooms (must be positive whole numbers)")

    nights_numeric = pd.to_numeric(bookings["nights"], errors="coerce")
    invalid_nights = nights_numeric.isna() | ~np.isfinite(nights_numeric) | (nights_numeric <= 0) | (nights_numeric > 365) | (nights_numeric % 1 != 0)
    if invalid_nights.any():
        errors.append(f"bookings: {int(invalid_nights.sum())} rows have invalid nights (must be whole numbers from 1–365)")

    valid_stay_dates = check_in_dates.notna() & check_out_dates.notna()
    valid_night_values = ~invalid_nights
    expected_nights = (check_out_dates - check_in_dates).dt.days
    mismatched_nights = valid_stay_dates & valid_night_values & (nights_numeric != expected_nights)
    if mismatched_nights.any():
        errors.append(f"bookings: {int(mismatched_nights.sum())} rows have nights inconsistent with check_in/check_out dates")

    for revenue_column in ["gross_room_revenue", "net_room_revenue"]:
        revenue_numeric = pd.to_numeric(bookings[revenue_column], errors="coerce")
        invalid_revenue = revenue_numeric.isna() | ~np.isfinite(revenue_numeric) | (revenue_numeric < 0)
        if invalid_revenue.any():
            errors.append(f"bookings: {int(invalid_revenue.sum())} rows have invalid or negative {revenue_column}")

    return errors


def validate_inventory(inventory: pd.DataFrame) -> list[str]:
    errors = validate_required_columns(inventory, "inventory")
    if errors:
        return errors

    stay_dates = pd.to_datetime(inventory["stay_date"], errors="coerce")
    if stay_dates.isna().any():
        errors.append("inventory: `stay_date` contains invalid dates")

    available_numeric = pd.to_numeric(inventory["available_rooms"], errors="coerce")
    invalid_available = available_numeric.isna() | ~np.isfinite(available_numeric) | (available_numeric % 1 != 0)
    if invalid_available.any():
        errors.append(f"inventory: {int(invalid_available.sum())} rows have invalid available_rooms (must be whole numbers)")
    negative_inventory = available_numeric < 0
    if negative_inventory.any():
        errors.append(f"inventory: {int(negative_inventory.sum())} rows have negative available_rooms")

    out_of_order_numeric = pd.to_numeric(inventory["out_of_order_rooms"], errors="coerce")
    invalid_out_of_order = out_of_order_numeric.isna() | ~np.isfinite(out_of_order_numeric) | (out_of_order_numeric % 1 != 0)
    if invalid_out_of_order.any():
        errors.append(f"inventory: {int(invalid_out_of_order.sum())} rows have invalid out_of_order_rooms (must be whole numbers)")
    negative_out_of_order = out_of_order_numeric < 0
    if negative_out_of_order.any():
        errors.append(f"inventory: {int(negative_out_of_order.sum())} rows have negative out_of_order_rooms")
    sellable_negative = (available_numeric - out_of_order_numeric) < 0
    if sellable_negative.any():
        errors.append(f"inventory: {int(sellable_negative.sum())} rows have out_of_order_rooms greater than available_rooms")

    duplicated = inventory.duplicated(["hotel_id", "room_type", "stay_date"]).sum()
    if duplicated:
        errors.append(f"inventory: {int(duplicated)} duplicate hotel_id + room_type + stay_date rows")

    return errors


def validate_current_prices(current_prices: pd.DataFrame) -> list[str]:
    errors = validate_required_columns(current_prices, "current_prices")
    if errors:
        return errors

    stay_dates = pd.to_datetime(current_prices["stay_date"], errors="coerce")
    if stay_dates.isna().any():
        errors.append("current_prices: `stay_date` contains invalid dates")

    price_numeric = pd.to_numeric(current_prices["current_price"], errors="coerce")
    invalid_price = price_numeric.isna() | ~np.isfinite(price_numeric) | (price_numeric <= 0)
    if invalid_price.any():
        errors.append(f"current_prices: {int(invalid_price.sum())} rows have invalid or non-positive current_price")

    duplicated = current_prices.duplicated(["hotel_id", "room_type", "stay_date"]).sum()
    if duplicated:
        errors.append(f"current_prices: {int(duplicated)} duplicate hotel_id + room_type + stay_date rows")

    return errors


def validate_cross_table_consistency(
    bookings: pd.DataFrame,
    inventory: pd.DataFrame,
    current_prices: pd.DataFrame,
) -> list[str]:
    errors: list[str] = []

    booking_hotels = set(bookings["hotel_id"].dropna().astype(str).unique())
    inv_hotels = set(inventory["hotel_id"].dropna().astype(str).unique())
    prices_hotels = set(current_prices["hotel_id"].dropna().astype(str).unique())

    missing_in_inventory = booking_hotels - inv_hotels
    if missing_in_inventory:
        errors.append(
            f"inventory: hotel_id(s) {sorted(missing_in_inventory)} appear in bookings but not in inventory"
        )

    missing_in_prices = booking_hotels - prices_hotels
    if missing_in_prices:
        errors.append(
            f"current_prices: hotel_id(s) {sorted(missing_in_prices)} appear in bookings but not in current_prices"
        )

    # hotel_id + room_type coverage
    booking_pairs = set(
        bookings[["hotel_id", "room_type"]].dropna().astype(str).drop_duplicates().itertuples(index=False, name=None)
    )
    inv_pairs = set(
        inventory[["hotel_id", "room_type"]].dropna().astype(str).drop_duplicates().itertuples(index=False, name=None)
    )
    prices_pairs = set(
        current_prices[["hotel_id", "room_type"]].dropna().astype(str).drop_duplicates().itertuples(index=False, name=None)
    )
    missing_inv_pairs = booking_pairs - inv_pairs
    if missing_inv_pairs:
        errors.append(
            f"inventory: {len(missing_inv_pairs)} hotel+room_type combination(s) in bookings have no inventory rows"
        )
    missing_price_pairs = booking_pairs - prices_pairs
    if missing_price_pairs:
        errors.append(
            f"current_prices: {len(missing_price_pairs)} hotel+room_type combination(s) in bookings have no price rows"
        )

    inventory_keys = set(
        inventory[["hotel_id", "room_type", "stay_date"]]
        .dropna()
        .assign(stay_date=lambda df: pd.to_datetime(df["stay_date"], errors="coerce").dt.normalize())
        .dropna()
        .astype(str)
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    price_keys = set(
        current_prices[["hotel_id", "room_type", "stay_date"]]
        .dropna()
        .assign(stay_date=lambda df: pd.to_datetime(df["stay_date"], errors="coerce").dt.normalize())
        .dropna()
        .astype(str)
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )
    price_without_inventory_keys = price_keys - inventory_keys
    if price_without_inventory_keys:
        errors.append(
            f"inventory: {len(price_without_inventory_keys)} current_price date row(s) have no matching inventory"
        )

    # Overbooking check: aggregate confirmed bookings per check_in_date vs inventory
    _ACTIVE = {"confirmed", "stayed", "checked_in", "checked_out"}
    if not bookings.empty and not inventory.empty and "status" in bookings.columns:
        active = bookings[bookings["status"].astype(str).str.lower().isin(_ACTIVE)].copy()
        if not active.empty:
            active["check_in_date"] = pd.to_datetime(active["check_in_date"], errors="coerce")
            # Expand to stay nights so a 3-night booking counts against all 3 nights,
            # not just check-in date (which would miss overbooking on nights 2+).
            active["nights"] = pd.to_numeric(active.get("nights", 1), errors="coerce").fillna(1).clip(lower=1, upper=365).astype(int)
            rep = active.loc[active.index.repeat(active["nights"])].copy()
            rep["_offset"] = rep.groupby(level=0).cumcount()
            rep["stay_date"] = (rep["check_in_date"] + pd.to_timedelta(rep["_offset"], unit="D")).dt.normalize()
            booked_per_date = (
                rep.groupby(["hotel_id", "room_type", "stay_date"], as_index=False)["rooms"]
                .sum()
            )
            inv_avail = inventory.copy()
            inv_avail["stay_date"] = pd.to_datetime(inv_avail["stay_date"], errors="coerce")
            inv_avail["sellable_rooms"] = (
                pd.to_numeric(inv_avail["available_rooms"], errors="coerce").fillna(0)
                - pd.to_numeric(inv_avail["out_of_order_rooms"], errors="coerce").fillna(0)
            )
            merged = booked_per_date.merge(
                inv_avail[["hotel_id", "room_type", "stay_date", "sellable_rooms"]],
                on=["hotel_id", "room_type", "stay_date"],
                how="left",
            )
            merged["rooms"] = pd.to_numeric(merged["rooms"], errors="coerce").fillna(0)
            merged["sellable_rooms"] = pd.to_numeric(merged["sellable_rooms"], errors="coerce").fillna(0)
            overbooked = merged["rooms"] > merged["sellable_rooms"]
            if overbooked.any():
                errors.append(
                    f"bookings: {int(overbooked.sum())} date(s) have total confirmed rooms exceeding available inventory"
                )

    if not current_prices.empty and not inventory.empty:
        inv_dates = pd.to_datetime(inventory["stay_date"], errors="coerce").dropna()
        price_dates = pd.to_datetime(current_prices["stay_date"], errors="coerce").dropna()
        if not inv_dates.empty and not price_dates.empty:
            inv_max = inv_dates.max()
            price_max = price_dates.max()
            if price_max < inv_max:
                errors.append(
                    f"current_prices: max stay_date {price_max.date()} is earlier than "
                    f"inventory max stay_date {inv_max.date()} — some dates may lack pricing"
                )

    return errors


def validate_all(bookings: pd.DataFrame, inventory: pd.DataFrame, current_prices: pd.DataFrame) -> list[str]:
    return (
        validate_bookings(bookings)
        + validate_inventory(inventory)
        + validate_current_prices(current_prices)
        + validate_cross_table_consistency(bookings, inventory, current_prices)
    )
