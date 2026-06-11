from __future__ import annotations

from html import escape
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.i18n import (
    localized_recommendations,
    t,
    translate_reason_list,
    translate_risk_list,
    translate_room_type,
)
from src.ui_help import recommendation_column_config
from src.ui_theme import status_row_background, status_row_border


ATTENTION_TEXT: dict[str, dict[str, str]] = {
    "risk": {
        "zh": "需要特别注意：当前列表中有 {count} 条带风险提示的建议，请优先人工复核。",
        "en": "Needs attention: {count} recommendations include risk flags and should be reviewed first.",
        "de": "Achtung: {count} Empfehlungen enthalten Risikohinweise und sollten zuerst geprüft werden.",
        "fr": "À surveiller : {count} recommandations comportent des alertes de risque et doivent être revues en priorité.",
    },
    "opportunity": {
        "zh": "重点机会：当前列表中有 {count} 条高置信度调价建议，可以优先查看。",
        "en": "Priority opportunity: {count} high-confidence price changes are worth reviewing first.",
        "de": "Priorität: {count} Preisänderungen mit hoher Sicherheit sollten zuerst geprüft werden.",
        "fr": "Opportunité prioritaire : {count} changements de prix à forte confiance méritent une revue prioritaire.",
    },
}


def _format_currency(value: float) -> str:
    return f"{value:,.0f}"


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def _metric_card_html(label: str, value: str | int | float, accent: str) -> str:
    safe_label = escape(str(label))
    safe_value = escape(str(value))
    return (
        f'<div class="hpe-metric-card hpe-metric-{accent}">'
        f'<div class="hpe-metric-label">{safe_label}</div>'
        f'<div class="hpe-metric-value">{safe_value}</div>'
        "</div>"
    )


def _metric_grid(cards: list[tuple[str, str | int | float, str]]) -> None:
    card_html = "".join(_metric_card_html(label, value, accent) for label, value, accent in cards)
    st.markdown(f'<div class="hpe-metric-grid">{card_html}</div>', unsafe_allow_html=True)


def _recommendation_score(row: pd.Series) -> tuple[int, float]:
    confidence_score = {"high": 3, "medium": 2, "low": 1}.get(row.get("confidence"), 0)
    revenue_delta = abs(float(row.get("expected_revenue_delta", 0) or 0))
    return confidence_score, revenue_delta


def _recommendation_attention_status(row: pd.Series) -> str:
    if str(row.get("risk_flags", "") or "").strip():
        return "danger"
    if row.get("action") != "hold" and row.get("confidence") == "high":
        return "success"
    if row.get("action") != "hold":
        return "warning"
    return ""


def _styled_recommendations(df: pd.DataFrame, localized: pd.DataFrame, ui_theme: str):
    def style_row(row):
        source = df.loc[row.name]
        action = str(source.get("action", "") or "")
        has_risk = bool(str(source.get("risk_flags", "") or "").strip())

        bg_key = action if action in ("increase", "decrease", "hold") else ""
        background = status_row_background(bg_key, ui_theme) if bg_key else ""
        border = status_row_border("danger" if has_risk else bg_key, ui_theme)

        if not background and border == "transparent":
            return [""] * len(row)
        parts = []
        if background:
            parts.append(f"background-color: {background}")
        if border != "transparent":
            parts.append(f"box-shadow: inset 4px 0 0 0 {border}")
        return ["; ".join(parts) + ";"] * len(row)

    return localized.style.apply(style_row, axis=1)


def _show_recommendation_table(df: pd.DataFrame, lang: str, ui_theme: str) -> None:
    st.caption(t("table_legend", lang), unsafe_allow_html=True)
    localized = localized_recommendations(df, lang)
    risk_series = df["risk_flags"].fillna("").astype(str).str.strip().ne("").map({True: "⚠️", False: ""})
    risk_series.index = localized.index
    localized.insert(0, "⚠", risk_series)
    st.dataframe(
        _styled_recommendations(df, localized, ui_theme),
        width="stretch",
        hide_index=True,
        column_config={
            "⚠": st.column_config.TextColumn("⚠", width="small"),
            **recommendation_column_config(lang),
        },
    )


def _attention_text(key: str, lang: str, count: int) -> str:
    template = ATTENTION_TEXT.get(key, {}).get(lang) or ATTENTION_TEXT.get(key, {}).get("en") or ""
    return template.format(count=count)


def _show_attention_summary(df: pd.DataFrame, lang: str) -> None:
    if df.empty:
        return
    risk_count = int((df["risk_flags"].fillna("").astype(str).str.strip() != "").sum())
    high_confidence_change_count = int(((df["action"] != "hold") & (df["confidence"] == "high")).sum())
    if risk_count:
        st.warning(_attention_text("risk", lang, risk_count))
    elif high_confidence_change_count:
        st.success(_attention_text("opportunity", lang, high_confidence_change_count))


def _attention_badge(status: str, lang: str) -> str:
    labels: dict[str, dict[str, str]] = {
        "danger": {"zh": "风险优先", "en": "Risk first", "de": "Risiko zuerst", "fr": "Risque prioritaire"},
        "success": {"zh": "高置信度", "en": "High confidence", "de": "Hohe Sicherheit", "fr": "Forte confiance"},
        "warning": {"zh": "需调价", "en": "Price action", "de": "Preisaktion", "fr": "Action tarifaire"},
    }
    return labels.get(status, labels["warning"]).get(lang) or labels.get(status, labels["warning"])["en"]


def _attention_note(row: pd.Series, lang: str) -> str:
    risks = str(row.get("risk_flags", "") or "").strip()
    reasons = str(row.get("main_reasons", "") or "").strip()
    if risks:
        return translate_risk_list(risks, lang)
    if reasons:
        return translate_reason_list(reasons, lang)
    return ""


def _render_attention_cards(df: pd.DataFrame, lang: str) -> None:
    if df.empty:
        return

    candidates = df.copy()
    candidates["_attention_status"] = candidates.apply(_recommendation_attention_status, axis=1)
    candidates = candidates[candidates["_attention_status"] != ""].copy()
    if candidates.empty:
        return

    dedupe_columns = [
        col
        for col in ["stay_date", "room_type", "action", "current_price", "recommended_price", "risk_flags", "main_reasons"]
        if col in candidates.columns
    ]
    if dedupe_columns:
        candidates = candidates.drop_duplicates(subset=dedupe_columns)

    status_order = {"danger": 0, "success": 1, "warning": 2}
    candidates["_status_rank"] = candidates["_attention_status"].map(status_order).fillna(9)
    if "expected_revenue_delta" in candidates.columns:
        candidates["_revenue_abs"] = pd.to_numeric(candidates["expected_revenue_delta"], errors="coerce").fillna(0).abs()
    else:
        candidates["_revenue_abs"] = 0.0
    cards = candidates.sort_values(["_status_rank", "_revenue_abs"], ascending=[True, False]).head(3)

    card_html: list[str] = []
    for _, row in cards.iterrows():
        status = str(row["_attention_status"])
        room = translate_room_type(str(row.get("room_type", "")), lang)
        stay_date = str(row.get("stay_date", ""))[:10]
        action = t(str(row.get("action", "")), lang)
        current_price = float(row.get("current_price", 0) or 0)
        recommended_price = float(row.get("recommended_price", 0) or 0)
        delta = float(row.get("expected_revenue_delta", 0) or 0)
        delta_text = f"+{delta:,.2f}" if delta > 0 else f"{delta:,.2f}"
        note = _attention_note(row, lang)
        revenue_label = t("column_expected_revenue_delta", lang)
        card_html.append(
            f'<div class="hpe-attention-card hpe-attention-{status}">'
            f'<div class="hpe-attention-badge">{escape(_attention_badge(status, lang))}</div>'
            f'<div class="hpe-attention-title">{escape(stay_date)} · {escape(room)} · {escape(action)}</div>'
            f'<div class="hpe-attention-meta">{current_price:,.2f} → {recommended_price:,.2f} · '
            f'{escape(revenue_label)} {escape(delta_text)}</div>'
            f'<div class="hpe-attention-note">{escape(note)}</div>'
            "</div>"
        )

    st.markdown(
        f'<div class="hpe-attention-grid">{"".join(card_html)}</div>',
        unsafe_allow_html=True,
    )


def _expected_recommendation_rows(current_prices: pd.DataFrame, observation_date, horizon_days: int) -> int:
    prices = current_prices.copy()
    prices["stay_date"] = pd.to_datetime(prices["stay_date"]).dt.normalize()
    start_date = pd.to_datetime(observation_date).normalize()
    end_date = start_date + pd.Timedelta(days=horizon_days)
    return int(((prices["stay_date"] >= start_date) & (prices["stay_date"] <= end_date)).sum())
