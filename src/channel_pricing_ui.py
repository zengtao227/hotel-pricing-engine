from __future__ import annotations

import pandas as pd
import streamlit as st

from .channel_pricing_rules import (
    add_channel_review_flags,
    channel_prices_excel_bytes,
    default_channel_pricing_rules,
    generate_channel_prices,
)
from .i18n import translate_room_type
from .ui_theme import status_row_background


CHANNEL_TEXT = {
    "title": {
        "zh": "渠道价预览与管理审批",
        "en": "Channel Price Preview & Management Approval",
        "de": "Kanalpreis-Vorschau & Managementfreigabe",
        "fr": "Aperçu des prix par canal et validation",
    },
    "policy": {
        "zh": "第一阶段不做全自动发布。系统可以自动检查和自动计算，但所有最终价格变更都必须先经过人工审批。渠道价预览只是帮助管理层看到：同一个批准基准价在不同渠道上的展示价、折扣、佣金和净收益。",
        "en": "Phase 1 does not auto-publish. The system may auto-check and auto-calculate, but every final price change must be manually approved first. This preview shows how one approved base price becomes channel display prices, discounts, commissions and net revenue.",
        "de": "Phase 1 veröffentlicht nicht automatisch. Das System kann automatisch prüfen und berechnen, aber jede endgültige Preisänderung braucht zuerst eine manuelle Freigabe.",
        "fr": "La phase 1 ne publie pas automatiquement. Le système peut vérifier et calculer automatiquement, mais chaque changement final de prix doit d’abord être validé manuellement.",
    },
    "no_approved": {
        "zh": "还没有已批准价格可生成渠道价。请先在上方审批表中批准价格。",
        "en": "No approved prices available for channel pricing. Approve prices in the table above first.",
        "de": "Keine freigegebenen Preise für Kanalpreise verfügbar.",
        "fr": "Aucun prix validé disponible pour générer les prix par canal.",
    },
    "download": {
        "zh": "下载渠道价审批 Excel",
        "en": "Download channel price approval Excel",
        "de": "Kanalpreis-Freigabe als Excel herunterladen",
        "fr": "Télécharger Excel des prix par canal",
    },
    "summary": {
        "zh": "需要管理审批的渠道价行数",
        "en": "Channel rows requiring management approval",
        "de": "Kanalpreiszeilen mit Freigabepflicht",
        "fr": "Lignes nécessitant validation",
    },
    "missing_columns": {
        "zh": "审批表缺少生成渠道价所需字段，暂时无法预览渠道价。",
        "en": "The approval table is missing required fields for channel price preview.",
        "de": "Der Freigabetabelle fehlen Pflichtfelder für die Kanalpreisvorschau.",
        "fr": "Le tableau de validation ne contient pas les champs requis pour les prix par canal.",
    },
}


def _label(key: str, lang: str) -> str:
    return CHANNEL_TEXT.get(key, {}).get(lang) or CHANNEL_TEXT.get(key, {}).get("en") or key


def _display_table(channel_prices: pd.DataFrame, lang: str) -> pd.DataFrame:
    columns = [
        "stay_date",
        "hotel_id",
        "room_type",
        "channel_name",
        "rate_plan_code",
        "approved_base_price",
        "display_price",
        "estimated_net_revenue",
        "combined_discount_rate",
        "commission_rate",
        "management_approval_required",
        "approval_reason",
    ]
    out = channel_prices[[c for c in columns if c in channel_prices.columns]].copy()
    if "room_type" in out.columns:
        out["room_type"] = out["room_type"].map(lambda value: translate_room_type(value, lang))
    return out


def _styled_preview(channel_prices: pd.DataFrame, lang: str):
    display = _display_table(channel_prices, lang)
    theme = st.session_state.get("app_theme", "light")

    def style_row(row):
        internal = channel_prices.iloc[row.name]
        reason = str(internal.get("approval_reason", ""))
        if "net revenue below" in reason or "non-positive" in reason or "display price drop" in reason:
            return [f"background-color: {status_row_background('danger', theme)}"] * len(row)
        if bool(internal.get("management_approval_required", False)):
            return [f"background-color: {status_row_background('warning', theme)}"] * len(row)
        return [f"background-color: {status_row_background('success', theme)}"] * len(row)

    return display.style.apply(style_row, axis=1)


def render_channel_price_preview(approval_table: pd.DataFrame, lang: str) -> None:
    st.subheader(_label("title", lang))
    st.info(_label("policy", lang))

    required_columns = {"approval_status", "selected"}
    if not required_columns.issubset(approval_table.columns):
        st.warning(_label("missing_columns", lang))
        return

    approved = approval_table[
        (approval_table["approval_status"] == "approved")
        & approval_table["selected"].astype(bool)
    ].copy()
    if approved.empty:
        st.warning(_label("no_approved", lang))
        return

    channel_prices = generate_channel_prices(approved, default_channel_pricing_rules())
    channel_prices = add_channel_review_flags(channel_prices)
    approval_required = int(channel_prices["management_approval_required"].sum())
    st.metric(_label("summary", lang), approval_required)
    st.dataframe(_styled_preview(channel_prices, lang), width="stretch", hide_index=True)
    st.download_button(
        _label("download", lang),
        data=channel_prices_excel_bytes(channel_prices),
        file_name="channel_price_approval_preview.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
