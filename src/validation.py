import pandas as pd


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

    if bookings["booking_date"].isna().any():
        errors.append("bookings: `booking_date` contains invalid dates")
    if bookings["check_in_date"].isna().any():
        errors.append("bookings: `check_in_date` contains invalid dates")
    if bookings["check_out_date"].isna().any():
        errors.append("bookings: `check_out_date` contains invalid dates")

    bad_checkout = bookings["check_out_date"] <= bookings["check_in_date"]
    if bad_checkout.any():
        errors.append(f"bookings: {int(bad_checkout.sum())} rows have check_out_date <= check_in_date")

    bad_lead_time = bookings["booking_date"] > bookings["check_in_date"]
    if bad_lead_time.any():
        errors.append(f"bookings: {int(bad_lead_time.sum())} rows have booking_date > check_in_date")

    non_positive_rate = pd.to_numeric(bookings["daily_rate"], errors="coerce") <= 0
    if non_positive_rate.any():
        errors.append(f"bookings: {int(non_positive_rate.sum())} rows have non-positive daily_rate")

    non_positive_rooms = pd.to_numeric(bookings["rooms"], errors="coerce") <= 0
    if non_positive_rooms.any():
        errors.append(f"bookings: {int(non_positive_rooms.sum())} rows have non-positive rooms")

    return errors


def validate_inventory(inventory: pd.DataFrame) -> list[str]:
    errors = validate_required_columns(inventory, "inventory")
    if errors:
        return errors

    if inventory["stay_date"].isna().any():
        errors.append("inventory: `stay_date` contains invalid dates")

    negative_inventory = pd.to_numeric(inventory["available_rooms"], errors="coerce") < 0
    if negative_inventory.any():
        errors.append(f"inventory: {int(negative_inventory.sum())} rows have negative available_rooms")

    duplicated = inventory.duplicated(["hotel_id", "room_type", "stay_date"]).sum()
    if duplicated:
        errors.append(f"inventory: {int(duplicated)} duplicate hotel_id + room_type + stay_date rows")

    return errors


def validate_current_prices(current_prices: pd.DataFrame) -> list[str]:
    errors = validate_required_columns(current_prices, "current_prices")
    if errors:
        return errors

    if current_prices["stay_date"].isna().any():
        errors.append("current_prices: `stay_date` contains invalid dates")

    non_positive_price = pd.to_numeric(current_prices["current_price"], errors="coerce") <= 0
    if non_positive_price.any():
        errors.append(f"current_prices: {int(non_positive_price.sum())} rows have non-positive current_price")

    return errors


def validate_all(bookings: pd.DataFrame, inventory: pd.DataFrame, current_prices: pd.DataFrame) -> list[str]:
    return (
        validate_bookings(bookings)
        + validate_inventory(inventory)
        + validate_current_prices(current_prices)
    )
