import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_demo_data, load_hotel_data
from src.i18n import LANGUAGES, localized_recommendations, t
from src.metrics import calculate_daily_metrics, summarize_overview
from src.pricing_engine import generate_recommendations
from src.report_export import build_excel_report
from src.validation import validate_all


st.set_page_config(page_title="Hotel Pricing Engine", layout="wide")

EXPORT_LANGUAGE_LABELS = {
    "zh": "Excel 导出语言",
    "en": "Excel export language",
    "de": "Excel-Exportsprache",
    "fr": "Langue d’export Excel",
}


def _language_selector() -> str:
    if "language" not in st.session_state:
        st.session_state.language = "zh"

    selected_label = st.selectbox(
        "🌐 Language / 语言",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code],
        index=list(LANGUAGES.keys()).index(st.session_state.language),
        label_visibility="collapsed",
    )
    st.session_state.language = selected_label
    return selected_label


def _export_language_selector(lang: str) -> str:
    previous_ui_lang = st.session_state.get("last_ui_language")
    current_export_lang = st.session_state.get("export_language")

    if current_export_lang is None:
        st.session_state.export_language = lang
        st.session_state.export_language_selectbox = lang
    elif previous_ui_lang and current_export_lang == previous_ui_lang and previous_ui_lang != lang:
        st.session_state.export_language = lang
        st.session_state.export_language_selectbox = lang

    selected = st.selectbox(
        EXPORT_LANGUAGE_LABELS.get(lang, EXPORT_LANGUAGE_LABELS["en"]),
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code],
        index=list(LANGUAGES.keys()).index(st.session_state.export_language),
        key="export_language_selectbox",
    )
    st.session_state.export_language = selected
    st.session_state.last_ui_language = lang
    return selected


def _format_currency(value: float) -> str:
    return f"{value:,.0f}"


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def _recommendation_score(row) -> tuple[int, float]:
    confidence_score = {"high": 3, "medium": 2, "low": 1}.get(row.get("confidence"), 0)
    revenue_delta = abs(float(row.get("expected_revenue_delta", 0) or 0))
    return confidence_score, revenue_delta


def render_sales_dashboard(metrics: pd.DataFrame, recommendations: pd.DataFrame, overview: dict, lang: str) -> None:
    st.subheader(t("sales_dashboard", lang))
    st.write(t("summary_text", lang))

    price_change_count = int((recommendations["action"] != "hold").sum()) if not recommendations.empty else 0
    high_confidence_count = int((recommendations["confidence"] == "high").sum()) if not recommendations.empty else 0
    risk_count = int((recommendations["risk_flags"].fillna("") != "").sum()) if not recommendations.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("room_revenue", lang), _format_currency(overview["room_revenue"]))
    c2.metric(t("occupancy", lang), _format_percent(overview["occupancy"]))
    c3.metric(t("price_change_count", lang), price_change_count)
    c4.metric(t("risk_count", lang), risk_count)

    c5, c6, c7, c8 = st.columns(4)
    c5.metric(t("adr", lang), f"{overview['adr']:,.2f}")
    c6.metric(t("revpar", lang), f"{overview['revpar']:,.2f}")
    c7.metric(t("high_confidence_count", lang), high_confidence_count)
    c8.metric(t("recommendation_horizon", lang), f"{len(recommendations['stay_date'].unique()) if not recommendations.empty else 0}")

    left, right = st.columns([0.48, 0.52])
    with left:
        st.subheader(t("pricing_actions", lang))
        action_counts = recommendations["action"].value_counts().rename_axis("action").reset_index(name="count")
        action_counts["action_label"] = action_counts["action"].map(lambda value: t(value, lang))
        st.plotly_chart(
            px.bar(action_counts, x="action_label", y="count", text="count", title=t("pricing_actions", lang)),
            use_container_width=True,
        )

    with right:
        st.subheader(t("revpar_trend", lang))
        trend = metrics.groupby("stay_date", as_index=False).agg(
            revpar=("revpar", "mean"),
            occupancy=("occupancy", "mean"),
        )
        st.plotly_chart(
            px.line(trend, x="stay_date", y="revpar", title=t("avg_revpar_by_date", lang)),
            use_container_width=True,
        )

    st.subheader(t("top_opportunities", lang))
    priority = recommendations[recommendations["action"] != "hold"].copy()
    if priority.empty:
        st.info(t("no_priority_items", lang))
    else:
        priority["_confidence_score"] = priority.apply(lambda row: _recommendation_score(row)[0], axis=1)
        priority["_revenue_abs"] = priority.apply(lambda row: _recommendation_score(row)[1], axis=1)
        priority = priority.sort_values(["_confidence_score", "_revenue_abs"], ascending=False).drop(columns=["_confidence_score", "_revenue_abs"])
        st.dataframe(localized_recommendations(priority.head(10), lang), use_container_width=True, hide_index=True)


def render_recommendations(recommendations: pd.DataFrame, lang: str) -> None:
    st.subheader(t("recommendations", lang))

    raw_actions = sorted(recommendations["action"].unique())
    action_filter = st.multiselect(
        t("filter_actions", lang),
        options=raw_actions,
        default=raw_actions,
        format_func=lambda value: t(value, lang),
    )
    filtered = recommendations[recommendations["action"].isin(action_filter)].copy()
    st.dataframe(localized_recommendations(filtered, lang), use_container_width=True, hide_index=True)


def render_data_preview(hotel_data, lang: str) -> None:
    st.subheader(t("data_preview", lang))
    with st.expander(t("bookings", lang), expanded=False):
        st.dataframe(hotel_data.bookings.head(50), use_container_width=True)
    with st.expander(t("inventory", lang), expanded=False):
        st.dataframe(hotel_data.inventory.head(50), use_container_width=True)
    with st.expander(t("current_prices", lang), expanded=False):
        st.dataframe(hotel_data.current_prices.head(50), use_container_width=True)


header_left, header_right = st.columns([0.78, 0.22])
with header_right:
    lang = _language_selector()
with header_left:
    st.title(t("app_title", lang))
    st.caption(t("app_caption", lang))

with st.sidebar:
    st.header(t("configuration", lang))
    st.subheader(t("data", lang))
    use_demo = st.toggle(t("use_demo_data", lang), value=True)

    bookings_file = inventory_file = current_prices_file = None
    if not use_demo:
        bookings_file = st.file_uploader("bookings.csv", type=["csv"])
        inventory_file = st.file_uploader("inventory.csv", type=["csv"])
        current_prices_file = st.file_uploader("current_prices.csv", type=["csv"])

    horizon_days = st.slider(t("recommendation_horizon", lang), min_value=7, max_value=60, value=30, step=7)
    max_change_pct = st.slider(t("max_price_change", lang), min_value=0.05, max_value=0.30, value=0.15, step=0.05)

try:
    if use_demo:
        hotel_data = load_demo_data(ROOT / "sample_data")
    else:
        if not bookings_file or not inventory_file or not current_prices_file:
            st.info(t("upload_hint", lang))
            st.stop()
        hotel_data = load_hotel_data(bookings_file, inventory_file, current_prices_file)
except Exception as exc:
    st.error(f"{t('load_error', lang)}: {exc}")
    st.stop()

validation_errors = validate_all(hotel_data.bookings, hotel_data.inventory, hotel_data.current_prices)
if validation_errors:
    st.error(t("validation_failed", lang))
    for error in validation_errors:
        st.write(f"- {error}")
    st.stop()

metrics = calculate_daily_metrics(hotel_data.bookings, hotel_data.inventory)
observation_date = pd.to_datetime(hotel_data.current_prices["stay_date"]).min()

recommendations = generate_recommendations(
    metrics=metrics,
    bookings=hotel_data.bookings,
    current_prices=hotel_data.current_prices,
    observation_date=observation_date,
    horizon_days=horizon_days,
    max_change_pct=max_change_pct,
)

overview = summarize_overview(metrics)

tab_dashboard, tab_recommendations, tab_data = st.tabs(
    [t("sales_dashboard", lang), t("recommendations", lang), t("data_preview", lang)]
)

with tab_dashboard:
    render_sales_dashboard(metrics, recommendations, overview, lang)

with tab_recommendations:
    render_recommendations(recommendations, lang)
    export_lang = _export_language_selector(lang)
    st.download_button(
        t("download_excel", lang),
        data=build_excel_report(metrics, recommendations, lang=export_lang),
        file_name=f"hotel_pricing_recommendations_{export_lang}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with tab_data:
    render_data_preview(hotel_data, lang)
