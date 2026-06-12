from __future__ import annotations

from app.auth import unauthenticated_access_allowed


def test_local_unauthenticated_access_requires_explicit_flag() -> None:
    assert not unauthenticated_access_allowed("127.0.0.1", {})
    assert unauthenticated_access_allowed(
        "127.0.0.1",
        {"HOTEL_ALLOW_LOCAL_UNAUTHENTICATED": "1"},
    )


def test_public_demo_access_requires_explicit_flag() -> None:
    assert not unauthenticated_access_allowed("198.51.100.5", {})
    assert unauthenticated_access_allowed(
        "198.51.100.5",
        {"HOTEL_ALLOW_UNAUTHENTICATED": "1"},
    )
