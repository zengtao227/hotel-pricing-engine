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


CHANNEL_COL = {
    "stay_date": {"zh": "入住日期", "en": "Stay Date", "de": "Aufenthaltsdatum", "fr": "Date de séjour"},
    "hotel_id": {"zh": "酒店ID", "en": "Hotel ID", "de": "Hotel ID", "fr": "ID Hôtel"},
    "room_type": {"zh": "房型", "en": "Room Type", "de": "Zimmertyp", "fr": "Type de chambre"},
    "channel_name": {"zh": "渠道名称", "en": "Channel Name", "de": "Kanalname", "fr": "Nom du canal"},
    "rate_plan_code": {"zh": "价格计划代码", "en": "Rate Plan Code", "de": "Ratenplan-Code", "fr": "Code plan tarifaire"},
    "approved_base_price": {"zh": "批准基准价", "en": "Approved Base Price", "de": "Freigegebener Basispreis", "fr": "Prix de base validé"},
    "display_price": {"zh": "展示价", "en": "Display Price", "de": "Anzeigepreis", "fr": "Prix affiché"},
    "estimated_net_revenue": {"zh": "预估净收益", "en": "Estimated Net Revenue", "de": "Geschätzter Nettoerlös", "fr": "Revenu net estimé"},
    "combined_discount_rate": {"zh": "综合折扣率", "en": "Combined Discount Rate", "de": "Kombinierter Rabattsatz", "fr": "Taux de remise combiné"},
    "commission_rate": {"zh": "佣金率", "en": "Commission Rate", "de": "Provisionssatz", "fr": "Taux de commission"},
    "management_approval_required": {"zh": "需要管理审批", "en": "Approval Required", "de": "Freigabe erforderlich", "fr": "Validation requise"},
    "approval_reason": {"zh": "审批原因 / 异常提醒", "en": "Approval Reason / Alerts", "de": "Freigabegrund / Warnungen", "fr": "Motif de validation / Alertes"},
}


def _col_label(key: str, lang: str = "zh") -> str:
    return CHANNEL_COL.get(key, {}).get(lang) or CHANNEL_COL.get(key, {}).get("en") or key


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
    
    # Translate boolean values
    if "management_approval_required" in out.columns:
        yes_no = {True: {"zh": "是", "en": "Yes", "de": "Ja", "fr": "Oui"}, False: {"zh": "否", "en": "No", "de": "Nein", "fr": "Non"}}
        out["management_approval_required"] = out["management_approval_required"].map(
            lambda value: yes_no[bool(value)].get(lang, yes_no[bool(value)]["en"])
        )
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

    price_format: dict[str, str] = {}
    for col_key in ["approved_base_price", "display_price", "estimated_net_revenue"]:
        col_label = _col_label(col_key, lang)
        if col_label in display.columns:
            price_format[col_label] = "{:.2f}"
    for col_key in ["combined_discount_rate", "commission_rate"]:
        col_label = _col_label(col_key, lang)
        if col_label in display.columns:
            price_format[col_label] = "{:.2%}"

    # Rename display columns first
    renamed_display = display.rename(columns={c: _col_label(c, lang) for c in display.columns})

    return renamed_display.style.apply(style_row, axis=1).format(price_format)


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
    
    st.dataframe(
        _styled_preview(channel_prices, lang),
        width="stretch",
        hide_index=True
    )
    
    st.download_button(
        _label("download", lang),
        data=channel_prices_excel_bytes(channel_prices),
        file_name="channel_price_approval_preview.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
