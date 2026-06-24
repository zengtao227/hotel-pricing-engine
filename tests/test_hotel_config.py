from __future__ import annotations

import json

import pytest

from src.hotel_config import MAX_CONFIG_UPLOAD_BYTES, get_season_multiplier, load_config_from_upload, normalize_hotel_config
from datetime import date


class _Upload:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.size: int = len(payload)

    def getvalue(self) -> bytes:
        return self._payload


class _LargeUpload:
    size: int = MAX_CONFIG_UPLOAD_BYTES + 1

    def getvalue(self) -> bytes:
        raise AssertionError("getvalue must not be called for oversized uploads")


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


def test_load_config_from_upload_rejects_large_json_before_getvalue():
    with pytest.raises(ValueError, match="hotel_config"):
        load_config_from_upload(_LargeUpload())


def test_load_config_from_upload_normalizes_payload():
    payload = json.dumps({"room_types": [{"room_type": "Suite", "base_price": 300}]}).encode("utf-8")
    config = load_config_from_upload(_Upload(payload))
    assert config["room_types"][0]["room_type"] == "Suite"


def test_normalize_seasons_valid():
    config = normalize_hotel_config({
        "seasons": [
            {"name": "国庆", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0},
        ]
    })
    assert len(config["seasons"]) == 1
    assert config["seasons"][0]["demand_multiplier"] == 2.0


def test_normalize_seasons_invalid_date_raises():
    with pytest.raises(ValueError, match="invalid date"):
        normalize_hotel_config({"seasons": [
            {"name": "X", "start": "bad-date", "end": "2026-10-07", "demand_multiplier": 1.5}
        ]})


def test_normalize_seasons_start_after_end_raises():
    with pytest.raises(ValueError, match="start > end"):
        normalize_hotel_config({"seasons": [
            {"name": "X", "start": "2026-10-08", "end": "2026-10-01", "demand_multiplier": 1.5}
        ]})


def test_normalize_seasons_multiplier_out_of_range_raises():
    with pytest.raises(ValueError, match="demand_multiplier"):
        normalize_hotel_config({"seasons": [
            {"name": "X", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 10.0}
        ]})


def test_normalize_seasons_empty_is_valid():
    config = normalize_hotel_config({"seasons": []})
    assert config["seasons"] == []


def test_normalize_seasons_default_is_empty():
    config = normalize_hotel_config({})
    assert config["seasons"] == []


def test_get_season_multiplier_match():
    seasons = [{"name": "国庆", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0}]
    m, name = get_season_multiplier(date(2026, 10, 3), seasons)
    assert m == 2.0
    assert name == "国庆"


def test_get_season_multiplier_no_match():
    seasons = [{"name": "国庆", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 2.0}]
    m, name = get_season_multiplier(date(2026, 9, 30), seasons)
    assert m == 1.0
    assert name == ""


def test_get_season_multiplier_overlapping_takes_max():
    seasons = [
        {"name": "旺季A", "start": "2026-10-01", "end": "2026-10-07", "demand_multiplier": 1.8},
        {"name": "旺季B", "start": "2026-10-03", "end": "2026-10-10", "demand_multiplier": 2.1},
    ]
    m, name = get_season_multiplier(date(2026, 10, 5), seasons)
    assert m == 2.1
    assert name == "旺季B"


def test_get_season_multiplier_empty_seasons():
    m, name = get_season_multiplier(date(2026, 10, 3), [])
    assert m == 1.0
    assert name == ""


def test_get_season_multiplier_low_season():
    """淡季（multiplier < 1.0）必须正确返回，不能被 1.0 默认值覆盖。"""
    seasons = [{"name": "11月淡季", "start": "2026-11-01", "end": "2026-11-30", "demand_multiplier": 0.6}]
    m, name = get_season_multiplier(date(2026, 11, 15), seasons)
    assert m == pytest.approx(0.6)
    assert name == "11月淡季"


def test_get_season_multiplier_low_overlaps_high_takes_max():
    """淡季和旺季重叠，应返回旺季（较高的 multiplier）。"""
    seasons = [
        {"name": "11月淡季", "start": "2026-11-01", "end": "2026-11-30", "demand_multiplier": 0.6},
        {"name": "特殊活动", "start": "2026-11-10", "end": "2026-11-15", "demand_multiplier": 1.5},
    ]
    m, name = get_season_multiplier(date(2026, 11, 12), seasons)
    assert m == pytest.approx(1.5)
    assert name == "特殊活动"
