from __future__ import annotations

import pytest

from app.upload import uploaded_hotel_data_bytes
from src.security_controls import MAX_FILE_BYTES


class _Upload:
    def __init__(self, payload: bytes, size: int | None = None) -> None:
        self._payload = payload
        if size is not None:
            self.size = size

    def getvalue(self) -> bytes:
        return self._payload


class _ExplodingUpload:
    size: int = MAX_FILE_BYTES + 1

    def getvalue(self) -> bytes:
        raise AssertionError("getvalue must not be called before size validation")


class _UnknownSizeUpload:
    def getvalue(self) -> bytes:
        raise AssertionError("getvalue must not be called when size is unavailable")


def test_uploaded_hotel_data_bytes_reads_after_size_check() -> None:
    assert uploaded_hotel_data_bytes(
        _Upload(b"bookings", len(b"bookings")),
        _Upload(b"inventory", len(b"inventory")),
        _Upload(b"prices", len(b"prices")),
    ) == (b"bookings", b"inventory", b"prices")


def test_uploaded_hotel_data_bytes_rejects_oversized_file_before_getvalue() -> None:
    with pytest.raises(ValueError, match="bookings"):
        uploaded_hotel_data_bytes(
            _ExplodingUpload(),
            _Upload(b"inventory", len(b"inventory")),
            _Upload(b"prices", len(b"prices")),
        )


def test_uploaded_hotel_data_bytes_rejects_unknown_size_before_getvalue() -> None:
    with pytest.raises(ValueError, match="bookings"):
        uploaded_hotel_data_bytes(
            _UnknownSizeUpload(),
            _Upload(b"inventory", len(b"inventory")),
            _Upload(b"prices", len(b"prices")),
        )
