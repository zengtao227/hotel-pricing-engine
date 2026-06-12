from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.i18n import t
from src.ui_help import render_interpretation_expander
from src.ui_theme import apply_plotly_theme

from app.tabs._helpers import (
    _format_currency,
    _format_percent,
    _has_risk_flags,
    _metric_grid,
    _recommendation_score,
    _render_attention_cards,
    _show_attention_summary,
    _show_recommendation_table,
)


def render_sales_dashboard(
    metrics: pd.DataFrame,
    recommendations: pd.DataFrame,
    overview: dict,
    lang: str,
    ui_theme: str,
) -> None:
    st.subheader(t("sales_dashboard", lang))
    st.write(t("summary_text", lang))
    render_interpretation_expander(lang)

    price_change_count = int((recommendations["action"] != "hold").sum()) if not recommendations.empty else 0
    high_confidence_count = int((recommendations["confidence"] == "high").sum()) if not recommendations.empty else 0
    risk_count = int(_has_risk_flags(recommendations["risk_flags"]).sum()) if not recommendations.empty else 0
    horizon_count = len(recommendations["stay_date"].unique()) if not recommendations.empty else 0

    _metric_grid(
        [
            (t("room_revenue", lang), _format_currency(overview["room_revenue"]), "blue"),
            (t("occupancy", lang), _format_percent(overview["occupancy"]), "green"),
            (t("price_change_count", lang), price_change_count, "gold"),
            (t("risk_count", lang), risk_count, "rose"),
            (t("adr", lang), f"{overview['adr']:,.2f}", "sky"),
            (t("revpar", lang), f"{overview['revpar']:,.2f}", "violet"),
            (t("high_confidence_count", lang), high_confidence_count, "teal"),
            (t("recommendation_horizon", lang), horizon_count, "amber"),
        ]
    )

    left, right = st.columns([0.48, 0.52])
    with left:
        st.subheader(t("pricing_actions", lang))
        action_counts = recommendations["action"].value_counts().rename_axis("action").reset_index(name="count")
        action_counts["action_label"] = action_counts["action"].map(lambda value: t(value, lang))

        if ui_theme == "dark":
            action_color_map = {
                t("increase", lang): "#34D399",
                t("hold", lang): "#60A5FA",
                t("decrease", lang): "#FC8181",
            }
        else:
            action_color_map = {
                t("increase", lang): "#34D399",
                t("hold", lang): "#1D4ED8",
                t("decrease", lang): "#FC8181",
            }

        action_fig = px.bar(
            action_counts,
            x="action_label",
            y="count",
            text="count",
            color="action_label",
            color_discrete_map=action_color_map,
            title=t("pricing_actions", lang),
            labels={
                "action_label": t("column_action", lang),
                "count": t("chart_count", lang),
            },
        )
        action_fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            marker=dict(
                line=dict(
                    width=2,
                    color="rgba(255, 255, 255, 0.3)" if ui_theme == "dark" else "rgba(0, 0, 0, 0.1)",
                ),
            ),
            textfont=dict(size=13, color="#94A3B8" if ui_theme == "dark" else "#334155"),
        )
        action_fig.update_layout(
            xaxis_title=t("column_action", lang),
            yaxis_title=t("chart_count", lang),
            showlegend=False,
            bargap=0.2,
            yaxis=dict(autorange=True),
        )
        st.plotly_chart(apply_plotly_theme(action_fig, ui_theme), width="stretch")

    with right:
        st.subheader(t("revpar_trend", lang))
        trend = metrics.groupby("stay_date", as_index=False).agg(
            room_revenue=("room_revenue", "sum"),
            sellable_rooms=("sellable_rooms", "sum"),
        )
        trend["revpar"] = (
            pd.to_numeric(trend["room_revenue"], errors="coerce").fillna(0)
            / pd.to_numeric(trend["sellable_rooms"], errors="coerce").replace(0, pd.NA)
        ).fillna(0)

        trend_fig = px.line(
            trend,
            x="stay_date",
            y="revpar",
            title=t("avg_revpar_by_date", lang),
            labels={
                "stay_date": t("column_stay_date", lang),
                "revpar": t("revpar", lang),
            },
        )
        if ui_theme == "dark":
            trend_fig.update_traces(line_color="#2DD4BF", line_width=3, line_shape="spline")
        else:
            trend_fig.update_traces(line_width=2.5, line_shape="spline")
        trend_fig.update_layout(
            xaxis_title=t("column_stay_date", lang),
            yaxis_title=t("revpar", lang),
        )
        st.plotly_chart(apply_plotly_theme(trend_fig, ui_theme), width="stretch")

    st.subheader(t("top_opportunities", lang))
    has_risk = _has_risk_flags(recommendations["risk_flags"])
    priority = recommendations[(recommendations["action"] != "hold") | has_risk].copy()
    if priority.empty:
        st.info(t("no_priority_items", lang))
    else:
        _show_attention_summary(priority, lang)
        _render_attention_cards(priority, lang)
        priority["_risk_score"] = _has_risk_flags(priority["risk_flags"]).astype(int)
        priority["_confidence_score"] = priority.apply(lambda row: _recommendation_score(row)[0], axis=1)
        priority["_revenue_abs"] = priority.apply(lambda row: _recommendation_score(row)[1], axis=1)
        priority = priority.sort_values(
            ["_risk_score", "_confidence_score", "_revenue_abs"], ascending=False
        ).drop(columns=["_risk_score", "_confidence_score", "_revenue_abs"])
        _show_recommendation_table(priority, lang, ui_theme)
