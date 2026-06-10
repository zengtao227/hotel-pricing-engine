from __future__ import annotations
import sys
from html import escape
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
from src.i18n import LANGUAGES, localized_recommendations, localize_room_type_values, t, translate_reason_list, translate_risk_list, translate_room_type
from src.metrics import calculate_daily_metrics, summarize_overview
from src.price_rounding import PRICE_ROUNDING_STRATEGIES
from src.pricing_engine import generate_recommendations
from src.report_export import build_excel_report
from src.ui_help import h, recommendation_column_config, render_interpretation_expander
from src.ui_theme import apply_plotly_theme, status_row_background, status_row_border
from src.validation import validate_all


st.set_page_config(page_title="Hotel Pricing Engine", layout="wide")


THEME_LABELS = {
    "zh": {"light": "亮色", "dark": "深色"},
    "en": {"light": "Light", "dark": "Dark"},
    "de": {"light": "Hell", "dark": "Dunkel"},
    "fr": {"light": "Clair", "dark": "Sombre"},
}

THEME_CONTROL_LABELS = {
    "zh": "界面主题",
    "en": "Interface theme",
    "de": "Oberflächendesign",
    "fr": "Thème de l’interface",
}

ATTENTION_TEXT = {
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

if "app_theme" not in st.session_state:
    st.session_state.app_theme = "light"


def _inject_mobile_css() -> None:
    st.markdown(
        """
        <style>
        /* ════════════════════════════════════════════════
           Global theme overrides — Hotel Pricing Engine
           Design: Navy #1E3A8A + Royal Blue #1D4ED8
           palette: ui-ux-pro-max Hotel/Hospitality Result 1
           ════════════════════════════════════════════════ */

        /* ── 1. Base typography ─────────────────────── */
        html, body, [class*="css"] {
            font-family: "Inter", -apple-system, "PingFang SC",
                         "Microsoft YaHei UI", "Microsoft YaHei",
                         "Noto Sans SC", sans-serif;
        }

        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .main {
            background: #EEF2F7 !important;
            color: #0F172A !important;
        }

        [data-testid="stHeader"] {
            background: rgba(238, 242, 247, 0.86) !important;
            backdrop-filter: blur(14px);
        }

        /* ── 2. Main container breathing room ───────── */
        .main .block-container {
            padding-top: 1.25rem !important;
            padding-bottom: 2rem !important;
        }

        /* ── 3. Sidebar — light, clean, branded ──────── */
        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] {
            background: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }
        section[data-testid="stSidebar"] > div:first-child,
        div[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }
        /* Sidebar section headers */
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] h2,
        div[data-testid="stSidebar"] h3 {
            color: #1E293B !important;
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 0.5rem !important;
        }

        /* ── 4. Metric cards — signature redesign ───── */
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-top: 3px solid #DBEAFE;
            border-radius: 8px;
            padding: 1rem 1.1rem 0.85rem !important;
            box-shadow:
                0 14px 32px rgba(15, 23, 42, 0.08),
                0 2px 7px rgba(15, 23, 42, 0.05);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow:
                0 22px 44px rgba(30, 58, 138, 0.14),
                0 6px 16px rgba(15, 23, 42, 0.08);
        }

        .hpe-metric-card {
            position: relative;
            overflow: hidden;
            min-height: 96px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem 1.1rem 0.9rem;
            box-shadow:
                0 14px 32px rgba(15, 23, 42, 0.08),
                0 2px 7px rgba(15, 23, 42, 0.05);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }
        .hpe-metric-card:hover {
            transform: translateY(-2px);
            box-shadow:
                0 22px 44px rgba(30, 58, 138, 0.14),
                0 6px 16px rgba(15, 23, 42, 0.08);
        }
        .hpe-metric-card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 3px;
            background: var(--metric-accent, #1D4ED8);
        }
        .hpe-metric-label {
            color: #1E293B;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }
        .hpe-metric-value {
            color: var(--metric-accent, #1D4ED8);
            font-size: 1.72rem;
            line-height: 1.12;
            font-weight: 850;
            letter-spacing: 0;
            font-variant-numeric: tabular-nums;
        }
        .hpe-metric-blue { --metric-accent: #1D4ED8; }
        .hpe-metric-green { --metric-accent: #059669; }
        .hpe-metric-gold { --metric-accent: #D97706; }
        .hpe-metric-rose { --metric-accent: #DC2626; }
        .hpe-metric-sky { --metric-accent: #0284C7; }
        .hpe-metric-violet { --metric-accent: #6366F1; }
        .hpe-metric-teal { --metric-accent: #0D9488; }
        .hpe-metric-amber { --metric-accent: #B45309; }

        .hpe-metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
            margin: 0.65rem 0 1rem;
        }

        .hpe-attention-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 0.8rem;
            margin: 0.65rem 0 1rem;
        }
        .hpe-attention-card {
            position: relative;
            overflow: hidden;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 5px solid var(--attention-accent, #D97706);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            box-shadow:
                0 16px 34px rgba(15, 23, 42, 0.08),
                0 2px 7px rgba(15, 23, 42, 0.05);
        }
        .hpe-attention-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, color-mix(in srgb, var(--attention-accent) 11%, transparent), transparent 55%);
            pointer-events: none;
        }
        .hpe-attention-card > * {
            position: relative;
            z-index: 1;
        }
        .hpe-attention-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            padding: 0.18rem 0.55rem;
            background: color-mix(in srgb, var(--attention-accent) 13%, #FFFFFF);
            color: var(--attention-accent);
            font-size: 0.74rem;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }
        .hpe-attention-title {
            color: #0F172A;
            font-weight: 780;
            line-height: 1.25;
            margin-bottom: 0.35rem;
        }
        .hpe-attention-meta,
        .hpe-attention-note {
            color: #475569;
            font-size: 0.84rem;
            line-height: 1.35;
        }
        .hpe-attention-note {
            margin-top: 0.45rem;
        }
        .hpe-attention-danger { --attention-accent: #DC2626; }
        .hpe-attention-warning { --attention-accent: #D97706; }
        .hpe-attention-success { --attention-accent: #059669; }
        [data-testid="stMetricLabel"] {
            color: #1E293B !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0;
        }
        [data-testid="stMetricValue"] {
            color: #1D4ED8 !important;
            font-weight: 800 !important;
            font-size: 1.65rem !important;
            letter-spacing: 0;
            line-height: 1.15 !important;
        }
        [data-testid="stMetricDelta"] {
            font-weight: 600 !important;
            font-size: 0.82rem !important;
        }

        /* ── 5. Tab bar — crisp navy indicator ───────── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 2px solid #E2E8F0;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            font-size: 0.92rem;
            color: #1E293B;
            padding: 10px 22px;
            border-radius: 0;
            background: transparent;
        }
        .stTabs [aria-selected="true"] {
            color: #1E3A8A !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #1E3A8A !important;
            height: 3px;
            border-radius: 3px 3px 0 0;
        }

        /* ── 6. Buttons — navy primary ───────────────── */
        .stButton > button[kind="primary"],
        .stDownloadButton > button {
            background: #1E3A8A !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.45rem 1.25rem !important;
            box-shadow: 0 2px 8px rgba(30, 58, 138, 0.25);
            transition: all 0.18s ease !important;
        }
        .stButton > button[kind="primary"]:hover,
        .stDownloadButton > button:hover {
            background: #1E40AF !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(30, 58, 138, 0.35) !important;
        }
        .stButton > button[kind="secondary"] {
            border-color: #1E3A8A !important;
            color: #1E3A8A !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }

        /* ── 7. Expander — card-like borders ─────────── */
        [data-testid="stExpander"] {
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            background: #FFFFFF !important;
            margin-bottom: 0.5rem;
        }
        [data-testid="stExpander"] summary {
            font-weight: 600 !important;
            color: #1E293B !important;
        }

        /* ── 8. Subheaders ───────────────────────────── */
        h3[data-testid="stHeading"] {
            color: #1E293B !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
        }

        /* ── 9. Data tables ──────────────────────────── */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
            background: #FFFFFF;
            box-shadow:
                0 16px 34px rgba(15, 23, 42, 0.08),
                0 2px 7px rgba(15, 23, 42, 0.05);
        }

        [data-testid="stPlotlyChart"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.35rem;
            box-shadow:
                0 16px 34px rgba(15, 23, 42, 0.08),
                0 2px 7px rgba(15, 23, 42, 0.05);
        }

        /* ── 10. Select box / slider accent ──────────── */
        [data-baseweb="select"] [data-baseweb="tag"] {
            background: #EFF6FF !important;
            color: #1E3A8A !important;
        }

        /* ── 11. Info / callout boxes ────────────────── */
        .stAlert[data-baseweb="notification"][kind="info"] {
            background: #EFF6FF !important;
            border-color: #BFDBFE !important;
            color: #1E40AF !important;
        }

        /* ── Mobile responsive (≤640px) ─────────────── */
        @media screen and (max-width: 640px) {
            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"],
            .main {
                overflow-x: hidden !important;
            }
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                max-width: 100vw !important;
                overflow-x: hidden !important;
            }
            h1 {
                font-size: 1.9rem !important;
                line-height: 1.18 !important;
                word-break: keep-all !important;
                overflow-wrap: normal !important;
            }
            .stTabs [data-baseweb="tab-list"] {
                overflow-x: auto !important;
                flex-wrap: nowrap !important;
                scrollbar-width: none;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
                display: none;
            }
            .stTabs [data-baseweb="tab"] {
                flex: 0 0 auto !important;
                padding: 10px 14px !important;
                white-space: nowrap !important;
            }
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
            .hpe-metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.75rem;
            }
            .hpe-metric-card {
                min-height: 84px;
                padding: 0.85rem 0.9rem 0.8rem;
            }
            .hpe-metric-label {
                font-size: 0.72rem;
            }
            .hpe-metric-value {
                font-size: 1.35rem;
                line-height: 1.15;
            }
            .hpe-attention-grid {
                grid-template-columns: 1fr;
                gap: 0.7rem;
            }
            .hpe-attention-card {
                padding: 0.85rem 0.9rem;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.1rem !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.7rem !important;
            }
            [data-testid="stDataFrame"] > div,
            [data-testid="stDataEditor"] > div {
                overflow-x: auto !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_dark_css() -> None:
    if st.session_state.get("app_theme") != "dark":
        return

    st.markdown(
        """
        <style>
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .main {
            background: #0D1B2A !important;
            color: #FFFFFF !important;
        }

        [data-testid="stHeader"] {
            background: rgba(13, 27, 42, 0.88) !important;
            border-bottom: 1px solid rgba(255,255,255,0.08) !important;
            backdrop-filter: blur(14px);
        }

        .main .block-container,
        h1, h2, h3, h4, h5, h6,
        p, span, label,
        [data-testid="stMarkdown"],
        [data-testid="stCaptionContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stExpander"] summary {
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] {
            background: rgba(6,12,22,0.97) !important;
            border-right: 1px solid rgba(255,255,255,0.10) !important;
        }

        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] h2,
        div[data-testid="stSidebar"] h3 {
            color: #FFFFFF !important;
        }

        [data-testid="stMetric"],
        [data-testid="stExpander"],
        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"],
        [data-testid="stPlotlyChart"] {
            background: rgba(255,255,255,0.05) !important;
            border-color: rgba(255,255,255,0.10) !important;
            box-shadow:
                0 24px 52px rgba(0,0,0,0.42),
                inset 0 1px 0 rgba(255,255,255,0.08) !important;
        }

        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] details > summary,
        [data-testid="stExpander"] summary {
            background: rgba(255,255,255,0.05) !important;
            color: #FFFFFF !important;
            border-color: rgba(255,255,255,0.12) !important;
        }

        [data-testid="stExpander"] summary {
            border-radius: 8px 8px 0 0 !important;
        }

        [data-testid="stExpander"] summary:hover {
            background: rgba(96,165,250,0.13) !important;
        }

        [data-testid="stExpander"] summary *,
        [data-testid="stExpander"] [data-testid="stExpanderDetails"] *,
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
            color: #FFFFFF !important;
        }

        [data-testid="stExpander"] svg {
            fill: #C8DAE8 !important;
            color: #C8DAE8 !important;
        }

        [data-testid="stMetric"] {
            border-top: 3px solid rgba(96,165,250,0.80) !important;
        }

        [data-testid="stMetric"]:hover {
            box-shadow:
                0 32px 64px rgba(0,0,0,0.52),
                0 0 26px rgba(96,165,250,0.12),
                inset 0 1px 0 rgba(255,255,255,0.10) !important;
        }

        .hpe-metric-card {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.045)) !important;
            border-color: rgba(255,255,255,0.12) !important;
            box-shadow:
                0 24px 52px rgba(0,0,0,0.42),
                inset 0 1px 0 rgba(255,255,255,0.10) !important;
        }
        .hpe-metric-card:hover {
            box-shadow:
                0 32px 64px rgba(0,0,0,0.52),
                0 0 26px color-mix(in srgb, var(--metric-accent) 26%, transparent),
                inset 0 1px 0 rgba(255,255,255,0.12) !important;
        }
        .hpe-metric-label {
            color: #FFFFFF !important;
        }
        .hpe-metric-value {
            color: var(--metric-accent) !important;
            text-shadow: 0 0 18px color-mix(in srgb, var(--metric-accent) 32%, transparent);
        }
        .hpe-metric-blue { --metric-accent: #60A5FA; }
        .hpe-metric-green { --metric-accent: #34D399; }
        .hpe-metric-gold { --metric-accent: #FCD34D; }
        .hpe-metric-rose { --metric-accent: #FC8181; }
        .hpe-metric-sky { --metric-accent: #38BDF8; }
        .hpe-metric-violet { --metric-accent: #A5B4FC; }
        .hpe-metric-teal { --metric-accent: #2DD4BF; }
        .hpe-metric-amber { --metric-accent: #F6AD55; }

        .hpe-attention-card {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.045)) !important;
            border-color: rgba(255,255,255,0.12) !important;
            box-shadow:
                0 24px 52px rgba(0,0,0,0.42),
                inset 0 1px 0 rgba(255,255,255,0.10) !important;
        }
        .hpe-attention-badge {
            background: color-mix(in srgb, var(--attention-accent) 18%, transparent) !important;
            color: var(--attention-accent) !important;
        }
        .hpe-attention-title {
            color: #FFFFFF !important;
        }
        .hpe-attention-meta,
        .hpe-attention-note {
            color: #D8E6F3 !important;
        }
        .hpe-attention-danger { --attention-accent: #FC8181; }
        .hpe-attention-warning { --attention-accent: #FCD34D; }
        .hpe-attention-success { --attention-accent: #34D399; }

        [data-testid="stMetricLabel"] {
            color: #FFFFFF !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: #60A5FA !important;
            text-shadow: 0 0 18px rgba(96,165,250,0.24);
        }

        [data-testid="stMetric"]:nth-of-type(4n + 1) [data-testid="stMetricValue"],
        [data-testid="stMetric"]:nth-of-type(4n + 1) [data-testid="stMetricValue"] * {
            color: #60A5FA !important;
        }

        [data-testid="stMetric"]:nth-of-type(4n + 2) [data-testid="stMetricValue"],
        [data-testid="stMetric"]:nth-of-type(4n + 2) [data-testid="stMetricValue"] * {
            color: #34D399 !important;
        }

        [data-testid="stMetric"]:nth-of-type(4n + 3) [data-testid="stMetricValue"],
        [data-testid="stMetric"]:nth-of-type(4n + 3) [data-testid="stMetricValue"] * {
            color: #FCD34D !important;
        }

        [data-testid="stMetric"]:nth-of-type(4n + 4) [data-testid="stMetricValue"],
        [data-testid="stMetric"]:nth-of-type(4n + 4) [data-testid="stMetricValue"] * {
            color: #FC8181 !important;
        }

        [data-testid="stMetricDelta"] {
            color: #C8DAE8 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            border-bottom-color: rgba(255,255,255,0.10) !important;
        }

        .stTabs [data-baseweb="tab"] {
            color: #FFFFFF !important;
        }

        .stTabs [aria-selected="true"] {
            color: #60A5FA !important;
        }

        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #60A5FA !important;
        }

        .stButton > button[kind="primary"],
        .stDownloadButton > button {
            background: #2563EB !important;
            color: #FFFFFF !important;
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35) !important;
        }

        .stButton > button[kind="secondary"] {
            border-color: rgba(96,165,250,0.72) !important;
            color: #FFFFFF !important;
            background: rgba(255,255,255,0.04) !important;
        }

        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="radio"] {
            background: rgba(15, 31, 51, 0.92) !important;
            color: #FFFFFF !important;
            border-color: rgba(148, 163, 184, 0.32) !important;
        }

        [data-baseweb="select"] *,
        [data-baseweb="input"] *,
        [data-baseweb="textarea"] *,
        input,
        textarea {
            color: #FFFFFF !important;
            caret-color: #60A5FA !important;
        }

        [data-baseweb="select"] input,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            background: transparent !important;
            color: #FFFFFF !important;
        }

        [data-baseweb="select"] [data-baseweb="tag"] {
            background: rgba(96,165,250,0.18) !important;
            border: 1px solid rgba(96,165,250,0.34) !important;
            color: #EAF2FF !important;
        }

        [data-baseweb="select"] [data-baseweb="tag"] * {
            color: #EAF2FF !important;
        }

        section[data-testid="stSidebar"] [data-baseweb="radio"],
        div[data-testid="stSidebar"] [data-baseweb="radio"] {
            background: transparent !important;
        }

        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        div[data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(15, 31, 51, 0.96) !important;
            border: 1px solid rgba(148, 163, 184, 0.34) !important;
            border-radius: 8px !important;
        }

        section[data-testid="stSidebar"] [data-testid="stExpander"],
        div[data-testid="stSidebar"] [data-testid="stExpander"],
        section[data-testid="stSidebar"] [data-testid="stExpander"] details > summary,
        div[data-testid="stSidebar"] [data-testid="stExpander"] details > summary {
            background: rgba(15, 31, 51, 0.96) !important;
            border-color: rgba(148, 163, 184, 0.28) !important;
        }

        section[data-testid="stSidebar"] button,
        div[data-testid="stSidebar"] button,
        section[data-testid="stSidebar"] input,
        div[data-testid="stSidebar"] input {
            color: #FFFFFF !important;
        }

        [data-testid="stFileUploader"],
        [data-testid="stFileUploader"] section,
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(15, 31, 51, 0.92) !important;
            border-color: rgba(148, 163, 184, 0.32) !important;
            color: #D8E6F3 !important;
        }

        [data-testid="stFileUploader"] *,
        [data-testid="stFileUploaderDropzone"] * {
            color: #D8E6F3 !important;
        }

        [data-testid="stFileUploader"] button,
        [data-testid="stFileUploaderDropzone"] button {
            background: rgba(96,165,250,0.18) !important;
            border: 1px solid rgba(96,165,250,0.38) !important;
            color: #FFFFFF !important;
            box-shadow: none !important;
        }

        [data-testid="stFileUploader"] button *,
        [data-testid="stFileUploaderDropzone"] button * {
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] [role="slider"],
        div[data-testid="stSidebar"] [role="slider"] {
            box-shadow: 0 0 0 3px rgba(96,165,250,0.18) !important;
        }

        [data-testid="stAlert"] {
            background: rgba(96,165,250,0.12) !important;
            border-color: rgba(96,165,250,0.24) !important;
            color: #FFFFFF !important;
        }

        [data-testid="stDataFrame"] div,
        [data-testid="stDataEditor"] div {
            color: #FFFFFF !important;
        }

        [data-testid="stPlotlyChart"] svg {
            background: transparent !important;
        }

        [data-testid="stPlotlyChart"] svg .bg {
            fill: rgba(255,255,255,0.03) !important;
        }

        [data-testid="stPlotlyChart"] svg text {
            fill: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_mobile_css()
_inject_dark_css()

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
        status = _recommendation_attention_status(source)
        if not status:
            return [""] * len(row)
        background = status_row_background(status, ui_theme)
        border = status_row_border(status, ui_theme)
        return [f"background-color: {background}; border-left: 4px solid {border};"] * len(row)

    return localized.style.apply(style_row, axis=1)


def _show_recommendation_table(df: pd.DataFrame, lang: str, ui_theme: str) -> None:
    localized = localized_recommendations(df, lang)
    st.dataframe(
        _styled_recommendations(df, localized, ui_theme),
        use_container_width=True,
        hide_index=True,
        column_config=recommendation_column_config(lang),
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
    labels = {
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
        column
        for column in ["stay_date", "room_type", "action", "current_price", "recommended_price", "risk_flags", "main_reasons"]
        if column in candidates.columns
    ]
    if dedupe_columns:
        candidates = candidates.drop_duplicates(subset=dedupe_columns)

    status_order = {"danger": 0, "success": 1, "warning": 2}
    candidates["_status_rank"] = candidates["_attention_status"].map(status_order).fillna(9)
    if "expected_revenue_delta" in candidates.columns:
        revenue_delta = pd.to_numeric(candidates["expected_revenue_delta"], errors="coerce").fillna(0)
        candidates["_revenue_abs"] = revenue_delta.abs()
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


def render_sales_dashboard(metrics: pd.DataFrame, recommendations: pd.DataFrame, overview: dict, lang: str, ui_theme: str) -> None:
    st.subheader(t("sales_dashboard", lang))
    st.write(t("summary_text", lang))
    render_interpretation_expander(lang)

    price_change_count = int((recommendations["action"] != "hold").sum()) if not recommendations.empty else 0
    high_confidence_count = int((recommendations["confidence"] == "high").sum()) if not recommendations.empty else 0
    risk_count = int((recommendations["risk_flags"].fillna("") != "").sum()) if not recommendations.empty else 0

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
        
        # 语义化配色：上调用绿色，保持用蓝色，下调用红色
        if ui_theme == "dark":
            action_color_map = {
                t("increase", lang): "#34D399",  # 青绿色 - 上调
                t("hold", lang): "#60A5FA",      # 蓝色 - 保持
                t("decrease", lang): "#FC8181",  # 玫瑰红 - 下调
            }
        else:
            action_color_map = {
                t("increase", lang): "#34D399",  # 青绿色 - 上调
                t("hold", lang): "#1D4ED8",      # 深蓝色 - 保持
                t("decrease", lang): "#FC8181",  # 玫瑰红 - 下调
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
        
        # 添加立体感：渐变效果和阴影
        action_fig.update_traces(
            marker=dict(
                line=dict(
                    width=2,
                    color="rgba(255, 255, 255, 0.3)" if ui_theme == "dark" else "rgba(0, 0, 0, 0.1)"
                ),
                # 添加柱子顶部的高光效果
                pattern=dict(shape=""),
            ),
            textfont=dict(size=14, color="#FFFFFF" if ui_theme == "dark" else "#0F172A"),
        )
        
        action_fig.update_layout(
            xaxis_title=t("column_action", lang),
            yaxis_title=t("chart_count", lang),
            showlegend=False,
            # 添加整体立体感
            bargap=0.15,
            bargroupgap=0.1,
        )
        
        st.plotly_chart(
            apply_plotly_theme(action_fig, ui_theme),
            use_container_width=True,
        )

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
        
        # 深色主题使用醒目的青色，亮色主题使用默认配色
        if ui_theme == "dark":
            trend_fig.update_traces(
                line_color="#2DD4BF",
                line_width=3,
                # 添加阴影效果增强立体感
                line_shape="spline",  # 平滑曲线
            )
        else:
            trend_fig.update_traces(
                line_width=2.5,
                line_shape="spline",
            )
        
        trend_fig.update_layout(
            xaxis_title=t("column_stay_date", lang),
            yaxis_title=t("revpar", lang),
        )
        st.plotly_chart(
            apply_plotly_theme(trend_fig, ui_theme),
            use_container_width=True,
        )

    st.subheader(t("top_opportunities", lang))
    has_risk = recommendations["risk_flags"].fillna("").astype(str).str.strip() != ""
    priority = recommendations[(recommendations["action"] != "hold") | has_risk].copy()
    if priority.empty:
        st.info(t("no_priority_items", lang))
    else:
        _show_attention_summary(priority, lang)
        _render_attention_cards(priority, lang)
        priority["_risk_score"] = priority["risk_flags"].fillna("").astype(str).str.strip().ne("").astype(int)
        priority["_confidence_score"] = priority.apply(lambda row: _recommendation_score(row)[0], axis=1)
        priority["_revenue_abs"] = priority.apply(lambda row: _recommendation_score(row)[1], axis=1)
        priority = priority.sort_values(["_risk_score", "_confidence_score", "_revenue_abs"], ascending=False).drop(
            columns=["_risk_score", "_confidence_score", "_revenue_abs"]
        )
        _show_recommendation_table(priority.head(10), lang, ui_theme)


def render_recommendations(recommendations: pd.DataFrame, lang: str, ui_theme: str) -> None:
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
    _show_attention_summary(filtered, lang)
    _render_attention_cards(filtered, lang)
    _show_recommendation_table(filtered, lang, ui_theme)


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
            if st.button(alabel("bulk_accept", lang), use_container_width=True):
                st.session_state.approval_table = accept_price_changes(st.session_state.approval_table)
        with c2:
            if st.button(alabel("reset", lang), use_container_width=True):
                st.session_state.approval_table = build_approval_table(recommendations)

        st.caption(alabel("editor_caption", lang))
        editor_display = to_editor_display(st.session_state.approval_table, lang)
        edited_display = st.data_editor(
            editor_display,
            use_container_width=True,
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
    st.dataframe(styled_preview(st.session_state.approval_table, lang), use_container_width=True, hide_index=True)
    render_channel_price_preview(st.session_state.approval_table, lang)

    if st.button(alabel("simulate_push", lang), type="primary", use_container_width=True):
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
        # 配置审批日志的列格式
        audit_log_column_config = {
            "current_price": st.column_config.NumberColumn("当前价" if lang == "zh" else "Current Price", format="%.2f"),
            "recommended_price": st.column_config.NumberColumn("系统推荐价" if lang == "zh" else "Recommended Price", format="%.2f"),
            "approved_price": st.column_config.NumberColumn("最终批准价" if lang == "zh" else "Approved Price", format="%.0f"),
        }
        st.dataframe(
            st.session_state.approval_log, 
            use_container_width=True, 
            hide_index=True,
            column_config=audit_log_column_config
        )
        st.download_button(
            alabel("download_audit", lang),
            data=audit_log_bytes(st.session_state.approval_log),
            file_name="price_approval_publishing_log.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def render_data_preview(hotel_data, lang: str) -> None:
    st.subheader(t("data_preview", lang))
    with st.expander(t("bookings", lang), expanded=False):
        st.dataframe(localize_room_type_values(hotel_data.bookings.head(50), lang), use_container_width=True)
    with st.expander(t("inventory", lang), expanded=False):
        st.dataframe(localize_room_type_values(hotel_data.inventory.head(50), lang), use_container_width=True)
    with st.expander(t("current_prices", lang), expanded=False):
        st.dataframe(localize_room_type_values(hotel_data.current_prices.head(50), lang), use_container_width=True)


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
    with st.expander(t("data_preview", lang), expanded=False):
        render_data_preview(hotel_data, lang)

tab_dashboard, tab_recommendations, tab_approval, tab_backtesting = st.tabs(
    [
        t("sales_dashboard", lang),
        t("recommendations", lang),
        alabel("tab", lang),
        bt_label("tab", lang),
    ]
)

with tab_dashboard:
    render_sales_dashboard(metrics, recommendations, overview, lang, ui_theme)

with tab_recommendations:
    render_recommendations(recommendations, lang, ui_theme)
    export_lang = _export_language_selector(lang)
    st.download_button(
        t("download_excel", lang),
        data=build_excel_report(metrics, recommendations, lang=export_lang),
        file_name=f"hotel_pricing_recommendations_{export_lang}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with tab_approval:
    render_price_approval_publishing(recommendations, lang)

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
