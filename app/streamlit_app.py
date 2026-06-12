from __future__ import annotations
import json
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.approval_workflow import alabel
from src.backtesting import bt_label, render_backtesting
from src.data_loader import HotelData, load_demo_data, load_hotel_data
from src.hotel_config import (
    apply_config_to_current_prices,
    ensure_hotel_config,
    label as hotel_config_label,
    render_hotel_configuration,
    room_bounds_from_config,
)
from src.i18n import LANGUAGES, localize_room_type_values, t
from src.metrics import calculate_daily_metrics, summarize_overview
from src.price_rounding import PRICE_ROUNDING_STRATEGIES
from src.pricing_engine import generate_recommendations
from src.report_export import build_excel_report
from src.security_controls import (
    drop_pii_columns,
)
from src.ui_help import h
from src.validation import validate_all

from app.auth import require_auth
from app.ui_css import _inject_dark_css, _inject_mobile_css
from app.tabs.dashboard import render_sales_dashboard
from app.tabs.recommendations import render_recommendations
from app.tabs.approval import render_price_approval_publishing
from app.tabs._helpers import _expected_recommendation_rows
from app.upload import uploaded_hotel_data_bytes


@st.cache_data(ttl=300)
def _cached_load_demo_data(base_dir: str) -> HotelData:
    return load_demo_data(base_dir)


@st.cache_data(ttl=300)
def _cached_load_uploaded_data(bookings_bytes: bytes, inventory_bytes: bytes, prices_bytes: bytes) -> HotelData:
    # Keyed by file content so re-runs from widget interactions reuse the parse.
    return load_hotel_data(BytesIO(bookings_bytes), BytesIO(inventory_bytes), BytesIO(prices_bytes))


@st.cache_data(ttl=300)
def _cached_calculate_daily_metrics(bookings: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    return calculate_daily_metrics(bookings, inventory)


@st.cache_data(ttl=300)
def _cached_validate_all(
    bookings: pd.DataFrame, inventory: pd.DataFrame, current_prices: pd.DataFrame
) -> list[str]:
    return validate_all(bookings, inventory, current_prices)


@st.cache_data(ttl=300)
def _cached_generate_recommendations(
    metrics: pd.DataFrame,
    bookings: pd.DataFrame,
    current_prices: pd.DataFrame,
    observation_date,
    horizon_days: int,
    max_change_pct: float,
    price_rounding_strategy: str,
    room_price_bounds_json: str,
) -> pd.DataFrame:
    room_price_bounds = json.loads(room_price_bounds_json) if room_price_bounds_json else None
    return generate_recommendations(
        metrics=metrics,
        bookings=bookings,
        current_prices=current_prices,
        observation_date=observation_date,
        horizon_days=horizon_days,
        max_change_pct=max_change_pct,
        price_rounding_strategy=price_rounding_strategy,
        room_price_bounds=room_price_bounds,
    )


st.set_page_config(
    page_title="Hotel Pricing Engine",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)


THEME_LABELS: dict[str, dict[str, str]] = {
    "zh": {"light": "亮色", "dark": "深色"},
    "en": {"light": "Light", "dark": "Dark"},
    "de": {"light": "Hell", "dark": "Dunkel"},
    "fr": {"light": "Clair", "dark": "Sombre"},
}

THEME_CONTROL_LABELS: dict[str, str] = {
    "zh": "界面主题",
    "en": "Interface theme",
    "de": "Oberflächendesign",
    "fr": "Thème de l'interface",
}

EXPORT_LANGUAGE_LABELS: dict[str, str] = {
    "zh": "Excel 导出语言",
    "en": "Excel export language",
    "de": "Excel-Exportsprache",
    "fr": "Langue d'export Excel",
}

PRICE_ROUNDING_LABELS: dict[str, str] = {
    "zh": "价格尾数规则",
    "en": "Price ending style",
    "de": "Preisendungsregel",
    "fr": "Style de terminaison du prix",
}

PRICE_ROUNDING_HELP: dict[str, str] = {
    "zh": "把算法计算出的原始推荐价转换成更像酒店挂牌价的数字。中国演示建议使用 6/8/9 尾数，例如 388、468、588；欧美场景可用按 5 或按 1 取整。",
    "en": "Converts raw algorithmic recommendations into market-friendly displayed prices. For China demos, use 6/8/9 endings such as 388, 468 or 588. For western demos, nearest 5 or nearest 1 may be more suitable.",
    "de": "Wandelt rohe algorithmische Empfehlungen in marktübliche angezeigte Preise um. Für China-Demos 6/8/9-Endungen wie 388, 468 oder 588 verwenden; für westliche Demos eher auf 5 oder 1 runden.",
    "fr": "Convertit les recommandations brutes en prix affichés plus naturels. Pour une démonstration Chine, utilisez les terminaisons 6/8/9 comme 388, 468 ou 588. Pour l'Europe, l'arrondi à 5 ou à 1 peut être plus adapté.",
}

if "app_theme" not in st.session_state:
    st.session_state.app_theme = "light"

_inject_mobile_css()
_inject_dark_css()

AUDIT_LOG_DIR = ROOT / "data" / "audit_logs"


def _language_selector() -> str:
    if "language" not in st.session_state:
        st.session_state["language"] = "zh"
    st.selectbox(
        "🌐 Language / 语言",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code],
        key="language",
        label_visibility="collapsed",
    )
    return st.session_state["language"]


def _theme_selector(lang: str) -> str:
    labels = THEME_LABELS.get(lang, THEME_LABELS["en"])
    selected = st.radio(
        THEME_CONTROL_LABELS.get(lang, THEME_CONTROL_LABELS["en"]),
        options=["light", "dark"],
        format_func=lambda value: labels[value],
        horizontal=True,
        key="app_theme",
    )
    return selected


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


def render_data_preview(hotel_data: HotelData, lang: str) -> None:
    st.subheader(t("data_preview", lang))
    with st.expander(t("bookings", lang), expanded=False):
        st.dataframe(localize_room_type_values(drop_pii_columns(hotel_data.bookings).head(50), lang), width="stretch")
    with st.expander(t("inventory", lang), expanded=False):
        st.dataframe(localize_room_type_values(drop_pii_columns(hotel_data.inventory).head(50), lang), width="stretch")
    with st.expander(t("current_prices", lang), expanded=False):
        st.dataframe(
            localize_room_type_values(drop_pii_columns(hotel_data.current_prices).head(50), lang),
            width="stretch",
        )


# ── Main app ──────────────────────────────────────────────────────────────────

require_auth()

header_left, header_right = st.columns([0.78, 0.22])
with header_right:
    lang = _language_selector()
with header_left:
    st.title(t("app_title", lang))
    st.caption(t("app_caption", lang))

hotel_config = ensure_hotel_config()

with st.sidebar:
    ui_theme = _theme_selector(lang)
    st.divider()
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
        hotel_data = _cached_load_demo_data(str(ROOT / "sample_data"))
    else:
        if not bookings_file or not inventory_file or not current_prices_file:
            st.info(t("upload_hint", lang))
            st.stop()
        bookings_bytes, inventory_bytes, current_prices_bytes = uploaded_hotel_data_bytes(
            bookings_file,
            inventory_file,
            current_prices_file,
        )
        hotel_data = _cached_load_uploaded_data(bookings_bytes, inventory_bytes, current_prices_bytes)
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

validation_errors = _cached_validate_all(hotel_data.bookings, hotel_data.inventory, hotel_data.current_prices)
if validation_errors:
    st.error(t("validation_failed", lang))
    for error in validation_errors:
        st.write(f"- {error}")
    st.stop()

observation_date = pd.to_datetime(hotel_data.current_prices["stay_date"]).min()
# Only use bookings known at observation_date — mirrors the backtest as-of discipline.
# In live production all booking_dates are ≤ today so this is a no-op; for demo data
# it correctly excludes bookings placed after the dataset's snapshot date.
bookings_as_of = hotel_data.bookings[
    pd.to_datetime(hotel_data.bookings["booking_date"]).dt.normalize()
    <= pd.to_datetime(observation_date).normalize()
].copy()
metrics = _cached_calculate_daily_metrics(bookings_as_of, hotel_data.inventory)
room_price_bounds = room_bounds_from_config(hotel_config)

recommendations = _cached_generate_recommendations(
    metrics=metrics,
    bookings=bookings_as_of,
    current_prices=hotel_data.current_prices,
    observation_date=observation_date,
    horizon_days=horizon_days,
    max_change_pct=max_change_pct,
    price_rounding_strategy=price_rounding_strategy,
    room_price_bounds_json=json.dumps(room_price_bounds, sort_keys=True) if room_price_bounds else "",
)
missing_recommendation_rows = (
    _expected_recommendation_rows(hotel_data.current_prices, observation_date, horizon_days)
    - len(recommendations)
)
if missing_recommendation_rows > 0:
    st.warning(t("recommendation_inventory_gap", lang).format(missing_count=missing_recommendation_rows))

overview = summarize_overview(metrics)

with st.sidebar:
    st.divider()
    with st.expander(t("data_preview", lang), expanded=False):
        render_data_preview(hotel_data, lang)

tab_dashboard, tab_recommendations, tab_approval, tab_backtesting = st.tabs(
    [
        f'📊 {t("sales_dashboard", lang)}',
        f'💡 {t("recommendations", lang)}',
        f'✅ {alabel("tab", lang)}',
        f'🧪 {bt_label("tab", lang)}',
    ]
)

with tab_dashboard:
    render_sales_dashboard(metrics, recommendations, overview, lang, ui_theme)

with tab_recommendations:
    render_recommendations(recommendations, lang, ui_theme, observation_date=observation_date)
    export_lang = _export_language_selector(lang)
    st.download_button(
        t("download_excel", lang),
        data=build_excel_report(metrics, recommendations, lang=export_lang),
        file_name=f"hotel_pricing_recommendations_{export_lang}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with tab_approval:
    render_price_approval_publishing(recommendations, lang, AUDIT_LOG_DIR)

with tab_backtesting:
    render_backtesting(
        metrics=metrics,
        bookings=hotel_data.bookings,
        current_prices=hotel_data.current_prices,
        lang=lang,
        default_horizon_days=horizon_days,
        max_change_pct=max_change_pct,
        price_rounding_strategy=price_rounding_strategy,
        room_price_bounds=room_price_bounds,
        ui_theme=ui_theme,
    )
