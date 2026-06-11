"""Tests for channel_pricing_rules.py."""
from __future__ import annotations

import pandas as pd
import pytest

from src.channel_pricing_rules import (
    ChannelApprovalGuardrails,
    ChannelPricingRule,
    apply_channel_rule,
    generate_channel_prices,
)


def _rule(**kwargs) -> ChannelPricingRule:
    defaults = dict(channel_name="Booking.com", commission_rate=0.15, rounding_strategy="nearest_integer")
    defaults.update(kwargs)
    return ChannelPricingRule(**defaults)


def _approved_prices() -> pd.DataFrame:
    return pd.DataFrame({
        "hotel_id": ["H1", "H1"],
        "room_type": ["Standard Double", "Superior Double"],
        "stay_date": pd.to_datetime(["2024-02-01", "2024-02-01"]),
        "approved_price": [400.0, 480.0],
        "approval_status": ["approved", "approved"],
        "push_status": ["not_pushed", "not_pushed"],
        "manual_override": [False, False],
    })


class TestApplyChannelRule:
    def test_commission_reduces_net_revenue(self):
        result = apply_channel_rule(400.0, _rule(commission_rate=0.15, discount_rate=0.0))
        assert result["estimated_net_revenue"] < 400.0
        # Commission is on display_price (after rounding), so allow ±1 unit tolerance.
        assert result["commission_amount"] == pytest.approx(result["display_price"] * 0.15, abs=0.02)

    def test_discount_reduces_display_price(self):
        result = apply_channel_rule(400.0, _rule(discount_rate=0.10))
        assert result["display_price"] < 400.0

    def test_stacked_discounts_are_multiplicative(self):
        result = apply_channel_rule(
            1000.0,
            _rule(discount_rate=0.10, mobile_discount_rate=0.05, commission_rate=0.0),
        )
        expected = 1000.0 * (1 - 0.10) * (1 - 0.05)
        assert result["display_price"] == pytest.approx(expected, abs=1.0)

    def test_min_display_price_floor_applied(self):
        result = apply_channel_rule(400.0, _rule(discount_rate=0.50, min_display_price=250.0))
        assert result["display_price"] >= 250.0

    def test_max_display_price_ceiling_applied(self):
        result = apply_channel_rule(400.0, _rule(max_display_price=380.0))
        assert result["display_price"] <= 380.0

    def test_zero_base_price_returns_zero_commission(self):
        # Rounding strategies may snap 0 to a non-zero display price; the key
        # invariant is that commission is always proportional to display_price.
        result = apply_channel_rule(0.0, _rule(commission_rate=0.15))
        assert result["commission_amount"] == pytest.approx(result["display_price"] * 0.15, abs=0.02)


class TestGenerateChannelPrices:
    def test_output_has_one_row_per_price_per_channel(self):
        rules = [_rule(channel_name="Booking.com"), _rule(channel_name="Expedia")]
        out = generate_channel_prices(_approved_prices(), rules)
        assert len(out) == 4  # 2 prices × 2 channels

    def test_disabled_rule_excluded(self):
        rules = [_rule(channel_name="Booking.com", enabled=True), _rule(channel_name="Expedia", enabled=False)]
        out = generate_channel_prices(_approved_prices(), rules)
        assert "Expedia" not in out["channel_name"].values

    def test_empty_prices_returns_empty_dataframe(self):
        out = generate_channel_prices(pd.DataFrame(), [_rule()])
        assert out.empty

    def test_no_enabled_rules_returns_empty_dataframe(self):
        out = generate_channel_prices(_approved_prices(), [_rule(enabled=False)])
        assert out.empty
