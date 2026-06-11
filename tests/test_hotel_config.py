from __future__ import annotations

import json

import pytest

from src.hotel_config import MAX_CONFIG_UPLOAD_BYTES, load_config_from_upload, normalize_hotel_config


class _Upload:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def getvalue(self) -> bytes:
        return self._payload


def test_normalize_hotel_config_keeps_valid_room_config():
    config = normalize_hotel_config(
        {
            "hotel_name": "Test Hotel",
            "currency": "EUR",
            "default_language": "en",
            "default_horizon_days": 999,
            "default_max_change_pct": 0.99,
            "room_types": [
                {
                    "room_type": "Suite",
                    "room_code": "STE",
                    "base_price": 300,
                    "min_price": 250,
                    "max_price": 500,
                    "weekend_uplift": 50,
                    "enabled": True,
                }
            ],
        }
    )

    assert config["hotel_name"] == "Test Hotel"
    assert config["currency"] == "EUR"
    assert config["default_language"] == "en"
    assert config["default_horizon_days"] == 60
    assert config["default_max_change_pct"] == 0.30
    assert config["room_types"][0]["room_type"] == "Suite"


def test_normalize_hotel_config_rejects_duplicate_room_type():
    with pytest.raises(ValueError, match="duplicate room_type"):
        normalize_hotel_config(
            {
                "room_types": [
                    {"room_type": "Suite", "base_price": 300},
                    {"room_type": "Suite", "base_price": 400},
                ]
            }
        )


def test_normalize_hotel_config_rejects_negative_price():
    with pytest.raises(ValueError, match="non-negative"):
        normalize_hotel_config({"room_types": [{"room_type": "Suite", "base_price": -1}]})


def test_load_config_from_upload_rejects_large_json():
    upload = _Upload(b"{" + b'"x":' + b'"a"' * MAX_CONFIG_UPLOAD_BYTES + b"}")
    with pytest.raises(ValueError, match="exceeds"):
        load_config_from_upload(upload)


def test_load_config_from_upload_normalizes_payload():
    payload = json.dumps({"room_types": [{"room_type": "Suite", "base_price": 300}]}).encode("utf-8")
    config = load_config_from_upload(_Upload(payload))
    assert config["room_types"][0]["room_type"] == "Suite"
