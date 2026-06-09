from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from .i18n import t, translate_room_type, translate_reason_list, translate_risk_list
from .pricing_engine import generate_recommendations


BT = {
    "tab": {"zh": "回测分析", "en": "Backtesting", "de": "Backtesting", "fr": "Backtesting"},
    "intro": {
        "zh": "用历史已发生的入住日期，模拟系统在当时会给出的推荐价，并用实际售出房间数做静态销量回测。当前版本用于验证方向和解释逻辑，不代表严格因果收益预测。",
        "en": "Simulate recommendations for historical stay dates and compare them using realized sold rooms. This static-volume backtest validates direction and explainability, not strict causal revenue impact.",
        "de": "Simuliert Empfehlungen für historische Aufenthaltstage und vergleicht sie mit realisierten verkauften Zimmern. Dieser Backtest validiert Richtung und Erklärung, nicht kausale Umsatzwirkung.",
        "fr": "Simule les recommandations sur des dates de séjour historiques et les compare avec les chambres vendues réalisées. Ce backtest valide la direction et l’explication, pas un effet causal strict.",
    },
    "observation_date": {"zh": "回测观察日", "en": "Backtest observation date", "de": "Backtest-Beobachtungstag", "fr": "Date d’observation"},
    "run_hint": {"zh": "选择一个观察日后，系统只使用该日前的历史数据作为基准，并对后续周期生成推荐。", "en": "After selecting an observation date, the system uses only prior history as baseline and generates recommendations for the following horizon.", "de": "Nach Auswahl des Beobachtungstags nutzt das System nur vorherige Historie als Basis und erstellt Empfehlungen für den folgenden Zeitraum.", "fr": "Après sélection de la date d’observation, le système utilise uniquement l’historique antérieur comme référence et génère des recommandations pour l’horizon suivant."},
    "static_volume_note": {"zh": "说明：当前回测假设售出房间数不随价格变化，用于快速比较价格策略方向。后续可升级为带价格弹性的需求模型。", "en": "Note: this backtest assumes sold rooms do not change with price. It is a fast directional comparison and can later be upgraded with price elasticity.", "de": "Hinweis: Dieser Backtest nimmt an, dass die verkauften Zimmer nicht auf Preisänderungen reagieren. Später kann Preiselastizität ergänzt werden.", "fr": "Note : ce backtest suppose que les chambres vendues ne changent pas avec le prix. Il sert à comparer rapidement la direction de la stratégie."},
    "baseline_revenue": {"zh": "基准收入", "en": "Baseline Revenue", "de": "Basisumsatz", "fr": "Revenu de référence"},
    "recommended_revenue": {"zh": "推荐价静态收入", "en": "Recommended Static Revenue", "de": "Empfohlener statischer Umsatz", "fr": "Revenu statique recommandé"},
    "revenue_delta": {"zh": "静态收益变化", "en": "Static Revenue Delta", "de": "Statische Umsatzänderung", "fr": "Variation statique"},
    "revenue_delta_pct": {"zh": "收益变化率", "en": "Revenue Delta %", "de": "Umsatzänderung %", "fr": "Variation %"},
    "changed_rows": {"zh": "建议调价行数", "en": "Changed Recommendations", "de": "Preisänderungen", "fr": "Recommandations modifiées"},
    "download": {"zh": "下载回测明细 Excel", "en": "Download backtest details Excel", "de": "Backtest-Details als Excel herunterladen", "fr": "Télécharger le détail Excel"},
    "details": {"zh": "回测明细", "en": "Backtest Details", "de": "Backtest-Details", "fr": "Détail du backtest"},
    "chart": {"zh": "每日静态收益变化", "en": "Daily Static Revenue Delta", "de": "Tägliche statische Umsatzänderung", "fr": "Variation statique quotidienne"},
    "no_data": {"zh": "当前数据不足以生成回测结果。", "en": "Not enough data to generate backtest results.", "de": "Nicht genügend Daten für Backtest-Ergebnisse.", "fr": "Données insuffisantes pour générer le backtest."},
}

COLUMN_LABELS = {
    "stay_date": {"zh": "入住日期", "en": "Stay Date", "de": "Aufenthaltsdatum", "fr": "Date de séjour"},
    "hotel_id": {"zh": "酒店", "en": "Hotel", "de": "Hotel", "fr": "Hôtel"},
    "room_type": {"zh": "房型", "en": "Room Type", "de": "Zimmertyp", "fr": "Type de chambre"},
    "current_price": {"zh": "当前价", "en": "Current Price", "de": "Aktueller Preis", "fr": "Prix actuel"},
    "recommended_price": {"zh": "推荐价", "en": "Recommended Price", "de": "Empfohlener Preis", "fr": "Prix recommandé"},
    "action": {"zh": "建议动作", "en": "Action", "de": "Aktion", "fr": "Action"},
    "confidence": {"zh": "置信度", "en": "Confidence", "de": "Sicherheit", "fr": "Confiance"},
    "sold_rooms": {"zh": "实际售出房间", "en": "Realized Sold Rooms", "de": "Verkaufte Zimmer", "fr": "Chambres vendues"},
    "baseline_revenue": {"zh": "基准收入", "en": "Baseline Revenue", "de": "Basisumsatz", "fr": "Revenu de référence"},
    "recommended_revenue": {"zh": "推荐价静态收入", "en": "Recommended Static Revenue", "de": "Empfohlener statischer Umsatz", "fr": "Revenu statique recommandé"},
    "static_revenue_delta": {"zh": "静态收益变化", "en": "Static Revenue Delta", "de": "Statische Umsatzänderung", "fr": "Variation statique"},
    "occupancy": {"zh": "入住率", "en": "Occupancy", "de": "Auslastung", "fr": "Occupation"},
    "main_reasons": {"zh": "主要原因", "en": "Main Reasons", "de": "Hauptgründe", "fr": "Raisons principales"},
    "risk_flags": {"zh": "风险提示", "en": "Risk Flags", "de": "Risikohinweise", "fr": "Alertes de risque"},
}


def bt_label(key: str, lang: str = "zh") -> str:
    return BT.get(key, {}).get(lang) or BT.get(key, {}).get("en") or key


def _col_label(key: str, lang: str) -> str:
    return COLUMN_LABELS.get(key, {}).get(lang) or COLUMN_LABELS.get(key, {}).get("en") or key


def run_static_backtest(
    metrics: pd.DataFrame,
    bookings: pd.DataFrame,
    current_prices: pd.DataFrame,
    observation_date,
    horizon_days: int,
    max_change_pct: float,
    price_rounding_strategy: str,
    room_price_bounds: dict | None = None,
) -> tuple[pd.DataFrame, dict]:
    recommendations = generate_recommendations(
        metrics=metrics,
        bookings=bookings,
        current_prices=current_prices,
        observation_date=observation_date,
        horizon_days=horizon_days,
        max_change_pct=max_change_pct,
        price_rounding_strategy=price_rounding_strategy,
        room_price_bounds=room_price_bounds,
    )
    if recommendations.empty:
        return recommendations, {}

    realized = metrics.copy()
    realized["stay_date"] = pd.to_datetime(realized["stay_date"]).dt.date
    detail = recommendations.merge(
        realized[["hotel_id", "room_type", "stay_date", "sold_rooms", "occupancy", "room_revenue"]],
        how="left",
        on=["hotel_id", "room_type", "stay_date"],
    )
    detail[["sold_rooms", "occupancy", "room_revenue"]] = detail[["sold_rooms", "occupancy", "room_revenue"]].fillna(0)
    detail["baseline_revenue"] = detail["current_price"].astype(float) * detail["sold_rooms"].astype(float)
    detail["recommended_revenue"] = detail["recommended_price"].astype(float) * detail["sold_rooms"].astype(float)
    detail["static_revenue_delta"] = detail["recommended_revenue"] - detail["baseline_revenue"]

    baseline_revenue = float(detail["baseline_revenue"].sum())
    recommended_revenue = float(detail["recommended_revenue"].sum())
    revenue_delta = recommended_revenue - baseline_revenue
    summary = {
        "rows": int(len(detail)),
        "changed_rows": int((detail["action"] != "hold").sum()),
        "baseline_revenue": baseline_revenue,
        "recommended_revenue": recommended_revenue,
        "revenue_delta": revenue_delta,
        "revenue_delta_pct": revenue_delta / baseline_revenue if baseline_revenue else 0.0,
    }
    return detail, summary


def localized_backtest_detail(detail: pd.DataFrame, lang: str) -> pd.DataFrame:
    columns = [
        "stay_date",
        "hotel_id",
        "room_type",
        "current_price",
        "recommended_price",
        "action",
        "confidence",
        "sold_rooms",
        "occupancy",
        "baseline_revenue",
        "recommended_revenue",
        "static_revenue_delta",
        "main_reasons",
        "risk_flags",
    ]
    out = detail[[column for column in columns if column in detail.columns]].copy()
    if "room_type" in out.columns:
        out["room_type"] = out["room_type"].map(lambda value: translate_room_type(value, lang))
    if "action" in out.columns:
        out["action"] = out["action"].map(lambda value: t(value, lang))
    if "confidence" in out.columns:
        out["confidence"] = out["confidence"].map(lambda value: t(value, lang))
    if "main_reasons" in out.columns:
        out["main_reasons"] = out["main_reasons"].map(lambda value: translate_reason_list(value, lang))
    if "risk_flags" in out.columns:
        out["risk_flags"] = out["risk_flags"].map(lambda value: translate_risk_list(value, lang))
    return out.rename(columns={column: _col_label(column, lang) for column in out.columns})


def backtest_excel_bytes(detail: pd.DataFrame, lang: str) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        localized_backtest_detail(detail, lang).to_excel(writer, sheet_name=bt_label("details", lang)[:31], index=False)
        workbook = writer.book
        sheet = workbook.worksheets[0]
        sheet.freeze_panes = "A2"
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 44)
    return output.getvalue()


def render_backtesting(
    metrics: pd.DataFrame,
    bookings: pd.DataFrame,
    current_prices: pd.DataFrame,
    lang: str,
    default_horizon_days: int,
    max_change_pct: float,
    price_rounding_strategy: str,
    room_price_bounds: dict | None = None,
) -> None:
    st.subheader(bt_label("tab", lang))
    st.write(bt_label("intro", lang))
    st.info(bt_label("static_volume_note", lang))

    available_dates = sorted(pd.to_datetime(current_prices["stay_date"]).dt.date.unique())
    if not available_dates:
        st.warning(bt_label("no_data", lang))
        return

    default_index = min(max(len(available_dates) // 4, 0), len(available_dates) - 1)
    observation_date = st.selectbox(bt_label("observation_date", lang), available_dates, index=default_index)
    st.caption(bt_label("run_hint", lang))

    detail, summary = run_static_backtest(
        metrics=metrics,
        bookings=bookings,
        current_prices=current_prices,
        observation_date=observation_date,
        horizon_days=default_horizon_days,
        max_change_pct=max_change_pct,
        price_rounding_strategy=price_rounding_strategy,
        room_price_bounds=room_price_bounds,
    )
    if detail.empty or not summary:
        st.warning(bt_label("no_data", lang))
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(bt_label("baseline_revenue", lang), f"{summary['baseline_revenue']:,.0f}")
    c2.metric(bt_label("recommended_revenue", lang), f"{summary['recommended_revenue']:,.0f}")
    c3.metric(bt_label("revenue_delta", lang), f"{summary['revenue_delta']:,.0f}")
    c4.metric(bt_label("revenue_delta_pct", lang), f"{summary['revenue_delta_pct']:.1%}")

    daily = detail.groupby("stay_date", as_index=False)["static_revenue_delta"].sum()
    st.plotly_chart(
        __import__("plotly.express").express.bar(daily, x="stay_date", y="static_revenue_delta", title=bt_label("chart", lang)),
        use_container_width=True,
    )

    st.subheader(bt_label("details", lang))
    st.dataframe(localized_backtest_detail(detail, lang), use_container_width=True, hide_index=True)
    st.download_button(
        bt_label("download", lang),
        data=backtest_excel_bytes(detail, lang),
        file_name="hotel_pricing_backtest.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
