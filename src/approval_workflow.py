from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
import streamlit as st

from .i18n import LANGUAGES, t


A = {
    "tab": {"zh": "价格审批与发布", "en": "Price Approval & Publishing", "de": "Preisfreigabe & Veröffentlichung", "fr": "Validation et publication des prix"},
    "intro": {
        "zh": "在这里先审核系统推荐价，可以采纳、手动修改或拒绝。当前版本为模拟推送，用于演示真实 PMS / Channel Manager 接入前的业务闭环。",
        "en": "Review system recommendations here: accept, override, or reject. This version simulates publishing to demonstrate the workflow before a real PMS / Channel Manager integration.",
        "de": "Prüfen Sie hier die Systemempfehlungen: übernehmen, überschreiben oder ablehnen. Diese Version simuliert die Veröffentlichung vor einer echten PMS-/Channel-Manager-Integration.",
        "fr": "Validez ici les recommandations : accepter, modifier ou rejeter. Cette version simule la publication avant une intégration réelle PMS / Channel Manager.",
    },
    "bulk_accept": {"zh": "批量采纳需调价项", "en": "Accept all price changes", "de": "Alle Preisänderungen übernehmen", "fr": "Accepter tous les changements"},
    "reset": {"zh": "重置审批表", "en": "Reset review table", "de": "Prüftabelle zurücksetzen", "fr": "Réinitialiser le tableau"},
    "simulate_push": {"zh": "一键模拟推送已批准价格", "en": "Simulate publishing approved prices", "de": "Freigegebene Preise simuliert veröffentlichen", "fr": "Simuler la publication des prix validés"},
    "download_audit": {"zh": "下载审批与推送日志", "en": "Download approval and publishing log", "de": "Freigabe- und Veröffentlichungslog herunterladen", "fr": "Télécharger le journal de validation et publication"},
    "no_rows": {"zh": "还没有已批准且勾选的价格可推送。", "en": "No approved and selected prices to publish.", "de": "Keine freigegebenen und ausgewählten Preise zur Veröffentlichung.", "fr": "Aucun prix validé et sélectionné à publier."},
    "push_success": {"zh": "模拟推送完成", "en": "Simulated publishing completed", "de": "Simulierte Veröffentlichung abgeschlossen", "fr": "Publication simulée terminée"},
    "editor_caption": {"zh": "可编辑列：是否推送、最终批准价、审核状态、审核备注。手动修改最终价后会自动标记为人工修改。", "en": "Editable columns: publish, approved price, review status and comment. Manual price changes are automatically flagged.", "de": "Editierbare Spalten: veröffentlichen, freigegebener Preis, Prüfstatus und Kommentar. Manuelle Preisänderungen werden automatisch markiert.", "fr": "Colonnes modifiables : publier, prix validé, statut et commentaire. Les modifications manuelles sont signalées automatiquement."},
    "preview_caption": {"zh": "颜色提示：黄色 = 人工修改；绿色 = 已推送；红色 = 已拒绝。", "en": "Colors: yellow = manual override; green = published; red = rejected.", "de": "Farben: gelb = manuelle Änderung; grün = veröffentlicht; rot = abgelehnt.", "fr": "Couleurs : jaune = modification manuelle ; vert = publié ; rouge = rejeté."},
    "audit_empty": {"zh": "暂无审批或推送日志。", "en": "No approval or publishing log yet.", "de": "Noch kein Freigabe- oder Veröffentlichungslog.", "fr": "Aucun journal de validation ou de publication pour le moment."},
}

COL = {
    "selected": {"zh": "推送", "en": "Publish", "de": "Veröffentlichen", "fr": "Publier"},
    "stay_date": {"zh": "入住日期", "en": "Stay Date", "de": "Aufenthaltsdatum", "fr": "Date de séjour"},
    "hotel_id": {"zh": "酒店", "en": "Hotel", "de": "Hotel", "fr": "Hôtel"},
    "room_type": {"zh": "房型", "en": "Room Type", "de": "Zimmertyp", "fr": "Type de chambre"},
    "current_price": {"zh": "当前价", "en": "Current Price", "de": "Aktueller Preis", "fr": "Prix actuel"},
    "recommended_price": {"zh": "系统推荐价", "en": "Recommended Price", "de": "Empfohlener Preis", "fr": "Prix recommandé"},
    "approved_price": {"zh": "最终批准价", "en": "Approved Price", "de": "Freigegebener Preis", "fr": "Prix validé"},
    "action": {"zh": "建议动作", "en": "Action", "de": "Aktion", "fr": "Action"},
    "confidence": {"zh": "置信度", "en": "Confidence", "de": "Sicherheit", "fr": "Confiance"},
    "manual_override": {"zh": "人工修改", "en": "Manual Override", "de": "Manuelle Änderung", "fr": "Modification manuelle"},
    "approval_status": {"zh": "审核状态", "en": "Review Status", "de": "Prüfstatus", "fr": "Statut de validation"},
    "review_comment": {"zh": "审核备注", "en": "Review Comment", "de": "Prüfkommentar", "fr": "Commentaire"},
    "push_status": {"zh": "推送状态", "en": "Publishing Status", "de": "Veröffentlichungsstatus", "fr": "Statut de publication"},
    "pushed_at": {"zh": "推送时间", "en": "Published At", "de": "Veröffentlicht am", "fr": "Publié le"},
}

STATUS = {
    "pending": {"zh": "待审核", "en": "Pending", "de": "Ausstehend", "fr": "En attente"},
    "approved": {"zh": "已批准", "en": "Approved", "de": "Freigegeben", "fr": "Validé"},
    "rejected": {"zh": "已拒绝", "en": "Rejected", "de": "Abgelehnt", "fr": "Rejeté"},
}

PUSH_STATUS = {
    "not_pushed": {"zh": "未推送", "en": "Not published", "de": "Nicht veröffentlicht", "fr": "Non publié"},
    "pushed": {"zh": "已推送", "en": "Published", "de": "Veröffentlicht", "fr": "Publié"},
    "skipped": {"zh": "已跳过", "en": "Skipped", "de": "Übersprungen", "fr": "Ignoré"},
}

BOOL_LABEL = {
    True: {"zh": "是", "en": "Yes", "de": "Ja", "fr": "Oui"},
    False: {"zh": "否", "en": "No", "de": "Nein", "fr": "Non"},
}

DISPLAY_COLUMNS = [
    "selected",
    "stay_date",
    "hotel_id",
    "room_type",
    "current_price",
    "recommended_price",
    "approved_price",
    "action",
    "confidence",
    "manual_override",
    "approval_status",
    "review_comment",
    "push_status",
    "pushed_at",
]


def alabel(key: str, lang: str = "zh") -> str:
    return A.get(key, {}).get(lang) or A.get(key, {}).get("en") or key


def clabel(key: str, lang: str = "zh") -> str:
    return COL.get(key, {}).get(lang) or COL.get(key, {}).get("en") or key


def _value_label(mapping: dict, value: str, lang: str) -> str:
    return mapping.get(value, {}).get(lang) or mapping.get(value, {}).get("en") or value


def _reverse_value(mapping: dict, label: str, lang: str) -> str:
    for key, labels in mapping.items():
        if label in {labels.get(lang), labels.get("en"), key}:
            return key
    return label


def build_approval_table(recommendations: pd.DataFrame) -> pd.DataFrame:
    df = recommendations.copy()
    df["selected"] = df["action"] != "hold"
    df["approved_price"] = df["recommended_price"].astype(float)
    df["approval_status"] = "pending"
    df.loc[df["action"] == "hold", "approval_status"] = "approved"
    df["manual_override"] = False
    df["review_comment"] = ""
    df["push_status"] = "not_pushed"
    df["pushed_at"] = ""
    return df[DISPLAY_COLUMNS].copy()


def approval_signature(recommendations: pd.DataFrame) -> str:
    cols = ["stay_date", "hotel_id", "room_type", "current_price", "recommended_price"]
    source = recommendations[cols].astype(str).to_csv(index=False)
    return str(hash(source))


def accept_price_changes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    mask = out["action"] != "hold"
    out.loc[mask, "selected"] = True
    out.loc[mask, "approval_status"] = "approved"
    out.loc[mask, "approved_price"] = out.loc[mask, "recommended_price"]
    out["manual_override"] = (out["approved_price"].astype(float) - out["recommended_price"].astype(float)).abs() > 0.01
    return out


def update_manual_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["approved_price"] = pd.to_numeric(out["approved_price"], errors="coerce").fillna(out["recommended_price"])
    out["manual_override"] = (out["approved_price"].astype(float) - out["recommended_price"].astype(float)).abs() > 0.01
    changed_pending = out["manual_override"] & (out["approval_status"] == "pending")
    out.loc[changed_pending, "approval_status"] = "approved"
    return out


def to_editor_display(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    display = df[DISPLAY_COLUMNS].copy()
    display["action"] = display["action"].map(lambda value: t(value, lang))
    display["confidence"] = display["confidence"].map(lambda value: t(value, lang))
    display["manual_override"] = display["manual_override"].map(lambda value: BOOL_LABEL[bool(value)].get(lang, BOOL_LABEL[bool(value)]["en"]))
    display["approval_status"] = display["approval_status"].map(lambda value: _value_label(STATUS, value, lang))
    display["push_status"] = display["push_status"].map(lambda value: _value_label(PUSH_STATUS, value, lang))
    return display.rename(columns={column: clabel(column, lang) for column in DISPLAY_COLUMNS})


def from_editor_display(display: pd.DataFrame, lang: str) -> pd.DataFrame:
    reverse_columns = {clabel(column, lang): column for column in DISPLAY_COLUMNS}
    df = display.rename(columns=reverse_columns).copy()
    df["approval_status"] = df["approval_status"].map(lambda value: _reverse_value(STATUS, value, lang))
    # action, confidence and push_status are displayed for context only and restored later by index if not editable.
    df["manual_override"] = df["manual_override"].map(lambda value: value in {BOOL_LABEL[True].get(lang), BOOL_LABEL[True].get("en"), True, "True", "true", "是"})
    return df


def editor_column_config(lang: str):
    status_labels = [_value_label(STATUS, key, lang) for key in ["pending", "approved", "rejected"]]
    return {
        clabel("selected", lang): st.column_config.CheckboxColumn(clabel("selected", lang)),
        clabel("approved_price", lang): st.column_config.NumberColumn(clabel("approved_price", lang), min_value=0, step=1, format="%.0f"),
        clabel("approval_status", lang): st.column_config.SelectboxColumn(clabel("approval_status", lang), options=status_labels),
        clabel("review_comment", lang): st.column_config.TextColumn(clabel("review_comment", lang)),
    }


def disabled_columns(lang: str) -> list[str]:
    editable = {clabel("selected", lang), clabel("approved_price", lang), clabel("approval_status", lang), clabel("review_comment", lang)}
    return [clabel(column, lang) for column in DISPLAY_COLUMNS if clabel(column, lang) not in editable]


def styled_preview(df: pd.DataFrame, lang: str):
    display = to_editor_display(df, lang)

    def style_row(row):
        idx = row.name
        internal = df.iloc[idx]
        if internal["push_status"] == "pushed":
            return ["background-color: #d1e7dd"] * len(row)
        if internal["approval_status"] == "rejected":
            return ["background-color: #f8d7da"] * len(row)
        if bool(internal["manual_override"]):
            return ["background-color: #fff3cd"] * len(row)
        return [""] * len(row)

    return display.style.apply(style_row, axis=1)


def simulate_push(df: pd.DataFrame, lang: str, actor: str = "demo_user") -> tuple[pd.DataFrame, pd.DataFrame]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    out = update_manual_flags(df)
    mask = (out["selected"] == True) & (out["approval_status"] == "approved")
    rows = []
    for idx, row in out[mask].iterrows():
        out.at[idx, "push_status"] = "pushed"
        out.at[idx, "pushed_at"] = now
        rows.append(
            {
                "timestamp": now,
                "actor": actor,
                "hotel_id": row["hotel_id"],
                "room_type": row["room_type"],
                "stay_date": row["stay_date"],
                "current_price": row["current_price"],
                "recommended_price": row["recommended_price"],
                "approved_price": row["approved_price"],
                "manual_override": bool(row["manual_override"]),
                "approval_status": row["approval_status"],
                "push_status": "pushed",
                "review_comment": row["review_comment"],
                "target_system": "SIMULATED_CHANNEL_MANAGER",
            }
        )
    return out, pd.DataFrame(rows)


def audit_log_bytes(log: pd.DataFrame) -> bytes:
    if log.empty:
        return b""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        log.to_excel(writer, sheet_name="approval_log", index=False)
        workbook = writer.book
        sheet = workbook["approval_log"]
        sheet.freeze_panes = "A2"
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 44)
    return output.getvalue()
