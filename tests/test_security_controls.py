from __future__ import annotations

import pandas as pd
import pytest

from src.security_controls import (
    MAX_FILE_BYTES,
    client_key_from_request,
    default_actor_from_headers,
    drop_pii_columns,
    is_loopback_ip,
    strict_actor_enabled,
    trusted_remote_actor,
    validate_uploaded_file_size,
)


class _ExplodingUpload:
    size: int = MAX_FILE_BYTES + 1

    def getvalue(self) -> bytes:
        raise AssertionError("getvalue must not be called before size validation")


class _UnknownSizeUpload:
    def getvalue(self) -> bytes:
        raise AssertionError("getvalue must not be called when size is unavailable")


def test_remote_actor_ignores_header_without_explicit_trust() -> None:
    headers: dict[str, object] = {"X-Remote-User": "alice"}

    assert trusted_remote_actor(headers, {}) is None
    assert default_actor_from_headers(headers, {}) == "demo_user"


def test_remote_actor_trusts_header_only_when_enabled() -> None:
    headers: dict[str, object] = {"X-Remote-User": "alice"}
    environ: dict[str, str] = {"HOTEL_TRUST_REMOTE_USER": "1"}

    assert trusted_remote_actor(headers, environ) == "alice"
    assert default_actor_from_headers(headers, environ) == "alice"


def test_strict_actor_flag_is_explicit() -> None:
    assert strict_actor_enabled({}) is False
    assert strict_actor_enabled({"HOTEL_STRICT_ACTOR": "1"}) is True


def test_client_key_prefers_non_proxy_streamlit_ip() -> None:
    headers: dict[str, object] = {"X-Forwarded-For": "203.0.113.10"}

    assert client_key_from_request("198.51.100.5", headers) == "198.51.100.5"


def test_client_key_uses_forwarded_for_when_trusted_proxy_ip_is_loopback() -> None:
    headers: dict[str, object] = {"X-Forwarded-For": "203.0.113.10, 198.51.100.9"}
    environ: dict[str, str] = {"HOTEL_TRUST_PROXY_HEADERS": "1"}

    assert client_key_from_request("127.0.0.1", headers, environ) == "203.0.113.10"


def test_client_key_uses_direct_ip_even_when_proxy_headers_are_trusted() -> None:
    headers: dict[str, object] = {"X-Forwarded-For": "203.0.113.10"}
    environ: dict[str, str] = {"HOTEL_TRUST_PROXY_HEADERS": "1"}

    assert client_key_from_request("198.51.100.5", headers, environ) == "198.51.100.5"


def test_client_key_ignores_forwarded_for_without_flag() -> None:
    headers: dict[str, object] = {"X-Forwarded-For": "203.0.113.10"}

    assert client_key_from_request(None, headers, {}) == "unknown"


def test_client_key_falls_back_to_real_ip_when_flag_set() -> None:
    environ: dict[str, str] = {"HOTEL_TRUST_PROXY_HEADERS": "1"}

    assert client_key_from_request(None, {"X-Real-IP": "198.51.100.8"}, environ) == "198.51.100.8"
    assert client_key_from_request(None, {}) == "unknown"


def test_loopback_ip_detection() -> None:
    assert is_loopback_ip("127.0.0.1")
    assert is_loopback_ip("127.12.34.56")
    assert is_loopback_ip("::1")
    assert not is_loopback_ip("198.51.100.5")


def test_drop_pii_columns_filters_pii_without_removing_business_ids() -> None:
    df: pd.DataFrame = pd.DataFrame(
        {
            "stay_date": ["2026-01-01"],
            "room_type": ["Suite"],
            "booking_id": ["B1"],
            "hotel_id": ["H1"],
            "candidate_price_count": [3],
            "guest_name": ["Alice"],
            "customer_id": ["C1"],
            "mobile_phone": ["123"],
            "emailAddress": ["a@example.com"],
            "id_card_number": ["ID123"],
            "护照号码": ["P123"],
            "客户备注": ["VIP"],
            "地址详情": ["Road 1"],
        }
    )

    safe_df: pd.DataFrame = drop_pii_columns(df)

    assert list(safe_df.columns) == ["stay_date", "room_type", "booking_id", "hotel_id", "candidate_price_count"]


def test_validate_uploaded_file_size_rejects_before_reading_bytes() -> None:
    with pytest.raises(ValueError, match="bookings"):
        validate_uploaded_file_size(_ExplodingUpload(), "bookings")


def test_validate_uploaded_file_size_rejects_unknown_size_before_reading_bytes() -> None:
    with pytest.raises(ValueError, match="size is unavailable"):
        validate_uploaded_file_size(_UnknownSizeUpload(), "bookings")
