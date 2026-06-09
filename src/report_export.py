from io import BytesIO

import pandas as pd

from .i18n import LANGUAGES, localized_recommendations


SHEET_NAMES = {
    "recommendations": {
        "zh": "调价建议",
        "en": "Price Recommendations",
        "de": "Preisempfehlungen",
        "fr": "Recommandations",
    },
    "metrics": {
        "zh": "每日指标",
        "en": "Daily Metrics",
        "de": "Tageskennzahlen",
        "fr": "Indicateurs journaliers",
    },
}

METRIC_COLUMN_LABELS = {
    "hotel_id": {"zh": "酒店", "en": "Hotel", "de": "Hotel", "fr": "Hôtel"},
    "room_type": {"zh": "房型", "en": "Room Type", "de": "Zimmertyp", "fr": "Type de chambre"},
    "stay_date": {"zh": "入住日期", "en": "Stay Date", "de": "Aufenthaltsdatum", "fr": "Date de séjour"},
    "available_rooms": {"zh": "可用房间数", "en": "Available Rooms", "de": "Verfügbare Zimmer", "fr": "Chambres disponibles"},
    "out_of_order_rooms": {"zh": "维修停用房间", "en": "Out-of-order Rooms", "de": "Gesperrte Zimmer", "fr": "Chambres hors service"},
    "sellable_rooms": {"zh": "可售房间数", "en": "Sellable Rooms", "de": "Verkaufbare Zimmer", "fr": "Chambres vendables"},
    "sold_rooms": {"zh": "已售房间数", "en": "Sold Rooms", "de": "Verkaufte Zimmer", "fr": "Chambres vendues"},
    "room_revenue": {"zh": "房费收入", "en": "Room Revenue", "de": "Zimmerumsatz", "fr": "Revenu chambres"},
    "booking_count": {"zh": "订单数", "en": "Booking Count", "de": "Buchungsanzahl", "fr": "Nombre de réservations"},
    "occupancy": {"zh": "入住率", "en": "Occupancy", "de": "Auslastung", "fr": "Taux d’occupation"},
    "adr": {"zh": "平均房价 ADR", "en": "ADR", "de": "ADR", "fr": "ADR"},
    "revpar": {"zh": "RevPAR", "en": "RevPAR", "de": "RevPAR", "fr": "RevPAR"},
    "day_of_week": {"zh": "星期", "en": "Day of Week", "de": "Wochentag", "fr": "Jour de semaine"},
    "is_weekend": {"zh": "是否周末", "en": "Is Weekend", "de": "Wochenende", "fr": "Week-end"},
}


def _label(mapping: dict, key: str, lang: str) -> str:
    return mapping.get(key, {}).get(lang) or mapping.get(key, {}).get("en") or key


def _sheet_name(key: str, lang: str) -> str:
    return _label(SHEET_NAMES, key, lang)[:31]


def _localize_metrics(metrics: pd.DataFrame, lang: str) -> pd.DataFrame:
    localized = metrics.copy()
    localized = localized.rename(
        columns={column: _label(METRIC_COLUMN_LABELS, column, lang) for column in localized.columns}
    )
    return localized


def build_excel_report(metrics: pd.DataFrame, recommendations: pd.DataFrame, lang: str = "en") -> bytes:
    """Return an in-memory localized Excel workbook for download in Streamlit."""
    if lang not in LANGUAGES:
        lang = "en"

    localized_recs = localized_recommendations(recommendations, lang)
    localized_metrics = _localize_metrics(metrics, lang)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        localized_recs.to_excel(writer, sheet_name=_sheet_name("recommendations", lang), index=False)
        localized_metrics.to_excel(writer, sheet_name=_sheet_name("metrics", lang), index=False)

        workbook = writer.book
        for sheet in workbook.worksheets:
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 44)

    return output.getvalue()
