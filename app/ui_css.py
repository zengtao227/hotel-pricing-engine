from __future__ import annotations

import streamlit as st


def _inject_mobile_css() -> None:
    st.markdown(
        """
        <style>
        /* ════════════════════════════════════════════════
           Global theme overrides — Hotel Pricing Engine
           Design: Navy #1E3A8A + Royal Blue #1D4ED8
           palette: ui-ux-pro-max Hotel/Hospitality Result 1
           ════════════════════════════════════════════════ */

        /* ── 0. Hide Streamlit deploy button for a clean client-facing demo ── */
        .stAppDeployButton { display: none !important; }

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
