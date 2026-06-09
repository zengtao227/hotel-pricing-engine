from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import pandas as pd

from .price_rounding import round_to_price_ending


@dataclass(frozen=True)
class ChannelPricingRule:
    """Configuration for turning an approved base price into a channel price."""

    channel_name: str
    rate_plan_code: str = "BAR"
    commission_rate: float = 0.0
    discount_rate: float = 0.0
    member_discount_rate: float = 0.0
    promotion_discount_rate: float = 0.0
    mobile_discount_rate: float = 0.0
    channel_cost_fixed: float = 0.0
    min_display_price: float | None = None
    max_display_price: float | None = None
    rounding_strategy: str = "chinese_lucky"
    update_frequency: str = "daily"
    requires_manual_approval: bool = True
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


def _clip(value: float, lower: float | None, upper: float | None) -> float:
    out = float(value)
    if lower is not None:
        out = max(out, float(lower))
    if upper is not None:
        out = min(out, float(upper))
    return out


def _combined_discount(rule: ChannelPricingRule) -> float:
    """Combine stacked channel discounts multiplicatively.

    A 10% Genius discount and 5% mobile discount becomes:
    1 - (1 - 0.10) * (1 - 0.05) = 14.5%, not 15%.
    """

    keep_rate = 1.0
    for discount in [
        rule.discount_rate,
        rule.member_discount_rate,
        rule.promotion_discount_rate,
        rule.mobile_discount_rate,
    ]:
        keep_rate *= 1.0 - max(min(float(discount or 0.0), 1.0), 0.0)
    return 1.0 - keep_rate


def apply_channel_rule(approved_base_price: float, rule: ChannelPricingRule) -> dict[str, Any]:
    """Return display price and estimated net revenue for one channel rule."""

    base_price = max(float(approved_base_price or 0.0), 0.0)
    combined_discount = _combined_discount(rule)
    raw_display_price = base_price * (1.0 - combined_discount)
    rounded_display_price = round_to_price_ending(raw_display_price, strategy=rule.rounding_strategy)
    display_price = _clip(rounded_display_price, rule.min_display_price, rule.max_display_price)
    commission = display_price * max(min(float(rule.commission_rate or 0.0), 1.0), 0.0)
    net_revenue = display_price - commission - max(float(rule.channel_cost_fixed or 0.0), 0.0)

    return {
        "channel_name": rule.channel_name,
        "rate_plan_code": rule.rate_plan_code,
        "approved_base_price": round(base_price, 2),
        "combined_discount_rate": round(combined_discount, 4),
        "display_price": round(display_price, 2),
        "commission_rate": round(float(rule.commission_rate or 0.0), 4),
        "commission_amount": round(commission, 2),
        "channel_cost_fixed": round(float(rule.channel_cost_fixed or 0.0), 2),
        "estimated_net_revenue": round(net_revenue, 2),
        "update_frequency": rule.update_frequency,
        "requires_manual_approval": rule.requires_manual_approval,
    }


def generate_channel_prices(approved_prices: pd.DataFrame, rules: Iterable[ChannelPricingRule]) -> pd.DataFrame:
    """Expand approved base prices into channel-specific display prices.

    Expected input columns: hotel_id, room_type, stay_date, approved_price.
    Extra columns are preserved where useful for export templates.
    """

    enabled_rules = [rule for rule in rules if rule.enabled]
    if approved_prices.empty or not enabled_rules:
        return pd.DataFrame(
            columns=[
                "hotel_id",
                "room_type",
                "stay_date",
                "channel_name",
                "rate_plan_code",
                "approved_base_price",
                "display_price",
                "estimated_net_revenue",
                "combined_discount_rate",
                "commission_rate",
                "requires_manual_approval",
                "update_frequency",
            ]
        )

    rows: list[dict[str, Any]] = []
    for row in approved_prices.to_dict("records"):
        approved_price = row.get("approved_price", row.get("recommended_price", row.get("current_price", 0.0)))
        for rule in enabled_rules:
            priced = apply_channel_rule(float(approved_price or 0.0), rule)
            rows.append(
                {
                    "hotel_id": row.get("hotel_id"),
                    "room_type": row.get("room_type"),
                    "stay_date": row.get("stay_date"),
                    **priced,
                }
            )
    return pd.DataFrame(rows)


def default_channel_pricing_rules() -> list[ChannelPricingRule]:
    """Demo-only channel rules. Real hotel contracts must override these."""

    return [
        ChannelPricingRule(channel_name="Direct Website", commission_rate=0.0, discount_rate=0.0, rounding_strategy="chinese_lucky"),
        ChannelPricingRule(channel_name="Website Member", commission_rate=0.0, member_discount_rate=0.05, rounding_strategy="chinese_lucky"),
        ChannelPricingRule(channel_name="Ctrip Promo", commission_rate=0.0, promotion_discount_rate=0.08, rounding_strategy="chinese_lucky"),
        ChannelPricingRule(channel_name="Booking.com Genius", commission_rate=0.15, member_discount_rate=0.10, rounding_strategy="chinese_lucky"),
    ]
