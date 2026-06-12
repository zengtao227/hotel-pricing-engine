from __future__ import annotations

from src.security_controls import MAX_FILE_BYTES, validate_uploaded_file_size


def uploaded_bytes_after_size_check(
    uploaded_file: object,
    label: str,
    max_bytes: int = MAX_FILE_BYTES,
) -> bytes:
    validate_uploaded_file_size(uploaded_file, label, max_bytes)
    getvalue = getattr(uploaded_file, "getvalue")
    return bytes(getvalue())


def uploaded_hotel_data_bytes(
    bookings_file: object,
    inventory_file: object,
    current_prices_file: object,
) -> tuple[bytes, bytes, bytes]:
    return (
        uploaded_bytes_after_size_check(bookings_file, "bookings"),
        uploaded_bytes_after_size_check(inventory_file, "inventory"),
        uploaded_bytes_after_size_check(current_prices_file, "current_prices"),
    )
