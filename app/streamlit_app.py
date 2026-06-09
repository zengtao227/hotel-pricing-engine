import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.approval_workflow import (
    accept_price_changes,
    alabel,
    approval_signature,
    audit_log_bytes,
    build_approval_table,
    disabled_columns,
    editor_column_config,
    from_editor_display,
    render_approval_cards,
    simulate_push,
    styled_preview,
    to_editor_display,
    update_manual_flags,
    _card_label,
)
from src.audit_log_store import append_audit_log, load_audit_log
from src.backtesting import bt_label, render_backtesting
from src.channel_pricing_ui import render_channel_price_preview
from src.data_loader import HotelData, load_demo_data, load_hotel_data
from src.hotel_config import (
    apply_config_to_current_prices,
    ensure_hotel_config,
    label as hotel_config_label,
    render_hotel_configuration,
    room_bounds_from_config,
)
from src.i18n import LANGUAGES, localized_recommendations, localize_room_type_values, t
from src.metrics import calculate_daily_metrics, summarize_overview
from src.price_rounding import PRICE_ROUNDING_STRATEGIES
from src.pricing_engine import generate_recommendations
from src.report_export import build_excel_report
from src.ui_help import h, recommendation_column_config, render_interpretation_expander
from src.validation import validate_all


st.set_page_config(page_title="Hotel Pricing Engine", layout="wide")


def _inject_mobile_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Mobile responsive overrides (≤640px) ── */
        @media screen and (max-width: 640px) {
            /* Prevent horizontal overflow from wide layout */
            .main .block-container {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
                max-width: 100vw !important;
                overflow-x: hidden !important;
            }
            /* Wrap column groups so 4-col metrics become 2×2 */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                min-width: calc(50% - 0.5rem) !important;
                flex: 1 1 calc(50% - 0.5rem) !important;
            }
            /* Smaller metric text so values aren't clipped */
            [data-testid="stMetricValue"] {
                font-size: 1.1rem !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.7rem !important;
            }
            /* Sidebar: full-width slide-over on mobile */
            section[data-testid="stSidebar"] {
                width: 85vw !important;
                min-width: 85vw !important;
            }
            /* Tables: horizontal scroll instead of overflow */
            [data-testid="stDataFrame"] > div,
            [data-testid="stDataEditor"] > div {
                overflow-x: auto !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_mobile_css()

AUDIT_LOG_DIR = ROOT / "data" / "audit_logs"

EXPORT_LANGUAGE_LABELS = {
    "zh": "Excel 导出语言",
    "en": "Excel export language",
    "de": "Excel-Exportsprache",
    "fr": "Langue d’export Excel",
}

PRICE_ROUNDING_LABELS = {
    "zh": "价格尾数规则",
    "en": "Price ending style",
    "de": "Preisendungsregel",
    "fr": "Style de terminaison du prix",
}

PRICE_ROUNDING_HELP = {
    "zh": "把算法计算出的原始推荐价转换成更像酒店挂牌价的数字。中国演示建议使用 6/8/9 尾数，例如 388、468、588；欧美场景可用按 5 或按 1 取整。",
    "en": "Converts raw algorithmic recommendations into market-friendly displayed prices. For China demos, use 6/8/9 endings such as 388, 468 or 588. For western demos, nearest 5 or nearest 1 may be more suitable.",
    "de": "Wandelt rohe algorithmische Empfehlungen in marktübliche angezeigte Preise um. Für China-Demos 6/8/9-Endungen wie 388, 468 oder 588 verwenden; für westliche Demos eher auf 5 oder 1 runden.",
    "fr": "Convertit les recommandations brutes en prix affichés plus naturels. Pour une démonstration Chine, utilisez les terminaisons 6/8/9 comme 388, 468 ou 588. Pour l’Europe, l’arrondi à 5 ou à 1 peut être plus adapté.",
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


def _show_recommendation_table(df: pd.DataFrame, lang: str) -> None:
    localized = localized_recommendations(df, lang)
    st.dataframe(
        localized,
        width="stretch",
        hide_index=True,
        column_config=recommendation_column_config(lang),
    )


def _expected_recommendation_rows(current_prices: pd.DataFrame, observation_date, horizon_days: int) -> int:
    prices = current_prices.copy()
    prices["stay_date"] = pd.to_datetime(prices["stay_date"]).dt.normalize()
    start_date = pd.to_datetime(observation_date).normalize()
    end_date = start_date + pd.Timedelta(days=horizon_days)
    return int(((prices["stay_date"] >= start_date) & (prices["stay_date"] <= end_date)).sum())


def render_sales_dashboard(metrics: pd.DataFrame, recommendations: pd.DataFrame, overview: dict, lang: str) -> None:
    st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] { color: #0f766e; font-weight: 700; }
        [data-testid="stMetricDelta"] { font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.subheader(t("sales_dashboard", lang))
    st.write(t("summary_text", lang))
    render_interpretation_expander(lang)

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
        _show_recommendation_table(priority.head(10), lang)


def render_recommendations(recommendations: pd.DataFrame, lang: str) -> None:
    st.subheader(t("recommendations", lang))
    render_interpretation_expander(lang)

    raw_actions = sorted(recommendations["action"].unique())
    action_filter = st.multiselect(
        t("filter_actions", lang),
        options=raw_actions,
        default=raw_actions,
        format_func=lambda value: t(value, lang),
    )
    filtered = recommendations[recommendations["action"].isin(action_filter)].copy()
    _show_recommendation_table(filtered, lang)


def render_price_approval_publishing(recommendations: pd.DataFrame, lang: str) -> None:
    st.subheader(alabel("tab", lang))
    st.write(alabel("intro", lang))

    if "approval_log" not in st.session_state:
        st.session_state.approval_log = load_audit_log(AUDIT_LOG_DIR)

    signature = approval_signature(recommendations)
    if st.session_state.get("approval_signature") != signature or "approval_table" not in st.session_state:
        st.session_state.approval_table = build_approval_table(recommendations)
        st.session_state.approval_signature = signature

    # View toggle: card view (mobile-friendly) vs table view (desktop power user)
    view_card = _card_label("view_card", lang)
    view_table = _card_label("view_table", lang)
    view_mode = st.radio(
        _card_label("view_label", lang),
        options=[view_card, view_table],
        horizontal=True,
        label_visibility="collapsed",
        key="approval_view_mode",
        index=0,
    )

    if view_mode == view_card:
        render_approval_cards(recommendations, lang)
    else:
        c1, c2 = st.columns([0.35, 0.65])
        with c1:
            if st.button(alabel("bulk_accept", lang), width="stretch"):
                st.session_state.approval_table = accept_price_changes(st.session_state.approval_table)
        with c2:
            if st.button(alabel("reset", lang), width="stretch"):
                st.session_state.approval_table = build_approval_table(recommendations)

        st.caption(alabel("editor_caption", lang))
        editor_display = to_editor_display(st.session_state.approval_table, lang)
        edited_display = st.data_editor(
            editor_display,
            width="stretch",
            hide_index=True,
            column_config=editor_column_config(lang),
            disabled=disabled_columns(lang),
            key=f"approval_editor_{signature}_{lang}",
        )

        edited_internal = from_editor_display(edited_display, lang)
        approval_table = st.session_state.approval_table.copy()
        for column in ["selected", "approved_price", "approval_status", "review_comment"]:
            approval_table[column] = edited_internal[column].values
        st.session_state.approval_table = update_manual_flags(approval_table)

    # Common to both views: full preview, channel prices, push button, audit log
    st.caption(alabel("preview_caption", lang))
    st.dataframe(styled_preview(st.session_state.approval_table, lang), width="stretch", hide_index=True)
    render_channel_price_preview(st.session_state.approval_table, lang)

    if st.button(alabel("simulate_push", lang), type="primary", width="stretch"):
        pushed_table, log_rows = simulate_push(st.session_state.approval_table, lang)
        st.session_state.approval_table = pushed_table
        if log_rows.empty:
            st.info(alabel("no_rows", lang))
        else:
            st.session_state.approval_log = append_audit_log(log_rows, AUDIT_LOG_DIR)
            st.success(f"{alabel('push_success', lang)}: {len(log_rows)}")

    if st.session_state.approval_log.empty:
        st.info(alabel("audit_empty", lang))
    else:
        st.dataframe(st.session_state.approval_log, width="stretch", hide_index=True)
        st.download_button(
            alabel("download_audit", lang),
            data=audit_log_bytes(st.session_state.approval_log),
            file_name="price_approval_publishing_log.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_data_preview(hotel_data, lang: str) -> None:
    st.subheader(t("data_preview", lang))
    with st.expander(t("bookings", lang), expanded=False):
        st.dataframe(localize_room_type_values(hotel_data.bookings.head(50), lang), width="stretch")
    with st.expander(t("inventory", lang), expanded=False):
        st.dataframe(localize_room_type_values(hotel_data.inventory.head(50), lang), width="stretch")
    with st.expander(t("current_prices", lang), expanded=False):
        st.dataframe(localize_room_type_values(hotel_data.current_prices.head(50), lang), width="stretch")


header_left, header_right = st.columns([0.78, 0.22])
with header_right:
    lang = _language_selector()
with header_left:
    st.title(t("app_title", lang))
    st.caption(t("app_caption", lang))

hotel_config = ensure_hotel_config()

with st.sidebar:
    st.header(t("configuration", lang))
    st.subheader(t("data", lang))
    use_demo = st.toggle(t("use_demo_data", lang), value=True)

    bookings_file = inventory_file = current_prices_file = None
    if not use_demo:
        bookings_file = st.file_uploader("bookings.csv", type=["csv"])
        inventory_file = st.file_uploader("inventory.csv", type=["csv"])
        current_prices_file = st.file_uploader("current_prices.csv", type=["csv"])

    horizon_days = st.slider(
        t("recommendation_horizon", lang),
        min_value=7,
        max_value=60,
        value=int(hotel_config.get("default_horizon_days", 30)),
        step=7,
        help=h("recommendation_horizon_help", lang),
    )
    max_change_pct = st.slider(
        t("max_price_change", lang),
        min_value=0.05,
        max_value=0.30,
        value=float(hotel_config.get("default_max_change_pct", 0.15)),
        step=0.05,
        help=h("max_price_change_help", lang),
    )
    rounding_keys = list(PRICE_ROUNDING_STRATEGIES.keys())
    default_rounding = hotel_config.get("default_price_rounding_strategy", "chinese_lucky")
    price_rounding_strategy = st.selectbox(
        PRICE_ROUNDING_LABELS.get(lang, PRICE_ROUNDING_LABELS["en"]),
        options=rounding_keys,
        format_func=lambda key: PRICE_ROUNDING_STRATEGIES[key].get(lang, PRICE_ROUNDING_STRATEGIES[key]["en"]),
        index=rounding_keys.index(default_rounding) if default_rounding in rounding_keys else 0,
        help=PRICE_ROUNDING_HELP.get(lang, PRICE_ROUNDING_HELP["en"]),
    )

    st.divider()
    with st.expander(hotel_config_label("tab", lang), expanded=False):
        hotel_config = render_hotel_configuration(hotel_config, lang)

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

effective_current_prices = apply_config_to_current_prices(
    hotel_data.current_prices,
    hotel_config,
    price_rounding_strategy,
)
hotel_data = HotelData(
    bookings=hotel_data.bookings,
    inventory=hotel_data.inventory,
    current_prices=effective_current_prices,
)

validation_errors = validate_all(hotel_data.bookings, hotel_data.inventory, hotel_data.current_prices)
if validation_errors:
    st.error(t("validation_failed", lang))
    for error in validation_errors:
        st.write(f"- {error}")
    st.stop()

metrics = calculate_daily_metrics(hotel_data.bookings, hotel_data.inventory)
observation_date = pd.to_datetime(hotel_data.current_prices["stay_date"]).min()
room_price_bounds = room_bounds_from_config(hotel_config)

recommendations = generate_recommendations(
    metrics=metrics,
    bookings=hotel_data.bookings,
    current_prices=hotel_data.current_prices,
    observation_date=observation_date,
    horizon_days=horizon_days,
    max_change_pct=max_change_pct,
    price_rounding_strategy=price_rounding_strategy,
    room_price_bounds=room_price_bounds,
)
missing_recommendation_rows = _expected_recommendation_rows(hotel_data.current_prices, observation_date, horizon_days) - len(recommendations)
if missing_recommendation_rows > 0:
    st.warning(t("recommendation_inventory_gap", lang).format(missing_count=missing_recommendation_rows))

overview = summarize_overview(metrics)

with st.sidebar:
    st.divider()
    with st.expander(bt_label("tab", lang), expanded=False):
        render_backtesting(
            metrics=metrics,
            bookings=hotel_data.bookings,
            current_prices=hotel_data.current_prices,
            lang=lang,
            default_horizon_days=horizon_days,
            max_change_pct=max_change_pct,
            price_rounding_strategy=price_rounding_strategy,
            room_price_bounds=room_price_bounds,
        )
    with st.expander(t("data_preview", lang), expanded=False):
        render_data_preview(hotel_data, lang)

tab_dashboard, tab_recommendations, tab_approval = st.tabs(
    [
        t("sales_dashboard", lang),
        t("recommendations", lang),
        alabel("tab", lang),
    ]
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

with tab_approval:
    render_price_approval_publishing(recommendations, lang)
