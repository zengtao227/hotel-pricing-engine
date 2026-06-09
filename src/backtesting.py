from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from .i18n import t, translate_reason_list, translate_risk_list, translate_room_type
from .metrics import calculate_daily_metrics
from .pricing_engine import generate_recommendations


BT = {
    "tab": {"zh": "回测分析", "en": "Backtesting", "de": "Backtesting", "fr": "Backtesting"},
    "intro": {
        "zh": "用历史观察日以前已知的订单数据，模拟系统当时会给出的推荐价，并用后续真实售出结果做静态销量回测。",
        "en": "Simulate recommendations using only bookings known before the historical observation date, then compare them with later realized results.",
        "de": "Simuliert Empfehlungen nur mit Buchungen, die vor dem historischen Beobachtungstag bekannt waren, und vergleicht sie mit später realisierten Ergebnissen.",
        "fr": "Simule les recommandations uniquement avec les réservations connues avant la date d’observation historique, puis les compare aux résultats réalisés.",
    },
    "observation_date": {"zh": "回测观察日", "en": "Backtest observation date", "de": "Backtest-Beobachtungstag", "fr": "Date d’observation"},
    "run_hint": {"zh": "系统只使用该日以前已经产生的订单作为已知信息，并对后续周期生成推荐。", "en": "The system uses only bookings already made by that date and generates recommendations for the following horizon.", "de": "Das System nutzt nur bis dahin bekannte Buchungen und erstellt Empfehlungen für den folgenden Zeitraum.", "fr": "Le système utilise uniquement les réservations déjà connues à cette date et génère des recommandations pour l’horizon suivant."},
    "static_volume_note": {"zh": "说明：当前回测假设最终售出房间数不随推荐价格变化，用于快速比较价格策略方向。后续可升级为带价格弹性的需求模型。", "en": "Note: this backtest assumes final sold rooms do not change with the recommended price. It can later be upgraded with price elasticity.", "de": "Hinweis: Dieser Backtest nimmt an, dass endgültig verkaufte Zimmer nicht auf den empfohlenen Preis reagieren. Später kann Preiselastizität ergänzt werden.", "fr": "Note : ce backtest suppose que les chambres finalement vendues ne changent pas avec le prix recommandé. Il pourra ensuite intégrer l’élasticité-prix."},
    "baseline_revenue": {"zh": "基准收入", "en": "Baseline Revenue", "de": "Basisumsatz", "fr": "Revenu de référence"},
    "recommended_revenue": {"zh": "推荐价静态收入", "en": "Recommended Static Revenue", "de": "Empfohlener statischer Umsatz", "fr": "Revenu statique recommandé"},
    "revenue_delta": {"zh": "静态收益变化", "en": "Static Revenue Delta", "de": "Statische Umsatzänderung", "fr": "Variation statique"},
    "revenue_delta_pct": {"zh": "收益变化率", "en": "Revenue Delta %", "de": "Umsatzänderung %", "fr": "Variation %"},
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
    "sold_rooms": {"zh": "观察日已售房间", "en": "Known Sold Rooms", "de": "Bekannte verkaufte Zimmer", "fr": "Chambres vendues connues"},
    "realized_sold_rooms": {"zh": "最终实际售出", "en": "Final Realized Sold Rooms", "de": "Endgültig verkaufte Zimmer", "fr": "Chambres finalement vendues"},
    "occupancy": {"zh": "观察日入住率", "en": "Known Occupancy", "de": "Bekannte Auslastung", "fr": "Occupation connue"},
    "realized_occupancy": {"zh": "最终实际入住率", "en": "Final Realized Occupancy", "de": "Endgültige Auslastung", "fr": "Occupation finale"},
    "baseline_revenue": {"zh": "基准收入", "en": "Baseline Revenue", "de": "Basisumsatz", "fr": "Revenu de référence"},
    "recommended_revenue": {"zh": "推荐价静态收入", "en": "Recommended Static Revenue", "de": "Empfohlener statischer Umsatz", "fr": "Revenu statique recommandé"},
    "static_revenue_delta": {"zh": "静态收益变化", "en": "Static Revenue Delta", "de": "Statische Umsatzänderung", "fr": "Variation statique"},
    "main_reasons": {"zh": "主要原因", "en": "Main Reasons", "de": "Hauptgründe", "fr": "Raisons principales"},
    "risk_flags": {"zh": "风险提示", "en": "Risk Flags", "de": "Risikohinweise", "fr": "Alertes de risque"},
}


def bt_label(key: str, lang: str = "zh") -> str:
    return BT.get(key, {}).get(lang) or BT.get(key, {}).get("en") or key


def _col_label(key: str, lang: str) -> str:
    return COLUMN_LABELS.get(key, {}).get(lang) or COLUMN_LABELS.get(key, {}).get("en") or key


def _inventory_from_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    columns = ["hotel_id", "room_type", "stay_date", "available_rooms", "out_of_order_rooms"]
    inventory = metrics[[c for c in columns if c in metrics.columns]].copy()
    if "out_of_order_rooms" not in inventory.columns:
        inventory["out_of_order_rooms"] = 0
    return inventory.drop_duplicates(["hotel_id", "room_type", "stay_date"])


def _bookings_as_of(bookings: pd.DataFrame, observation_date) -> pd.DataFrame:
    b = bookings.copy()
    b["booking_date"] = pd.to_datetime(b["booking_date"]).dt.normalize()
    return b[b["booking_date"] <= pd.to_datetime(observation_date).normalize()].copy()


def run_static_backtest(metrics, bookings, current_prices, observation_date, horizon_days, max_change_pct, price_rounding_strategy, room_price_bounds=None):
    observation_date = pd.to_datetime(observation_date).normalize()
    known_bookings = _bookings_as_of(bookings, observation_date)
    as_of_metrics = calculate_daily_metrics(known_bookings, _inventory_from_metrics(metrics))

    recommendations = generate_recommendations(
        metrics=as_of_metrics,
        bookings=known_bookings,
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
    realized = realized.rename(columns={"sold_rooms": "realized_sold_rooms", "occupancy": "realized_occupancy", "room_revenue": "realized_room_revenue"})
    detail = recommendations.merge(
        realized[["hotel_id", "room_type", "stay_date", "realized_sold_rooms", "realized_occupancy", "realized_room_revenue"]],
        how="left",
        on=["hotel_id", "room_type", "stay_date"],
    )
    fill_cols = ["sold_rooms", "occupancy", "realized_sold_rooms", "realized_occupancy", "realized_room_revenue"]
    detail[fill_cols] = detail[fill_cols].fillna(0)
    detail["baseline_revenue"] = detail["current_price"].astype(float) * detail["realized_sold_rooms"].astype(float)
    detail["recommended_revenue"] = detail["recommended_price"].astype(float) * detail["realized_sold_rooms"].astype(float)
    detail["static_revenue_delta"] = detail["recommended_revenue"] - detail["baseline_revenue"]

    baseline = float(detail["baseline_revenue"].sum())
    recommended = float(detail["recommended_revenue"].sum())
    delta = recommended - baseline
    return detail, {
        "rows": int(len(detail)),
        "changed_rows": int((detail["action"] != "hold").sum()),
        "baseline_revenue": baseline,
        "recommended_revenue": recommended,
        "revenue_delta": delta,
        "revenue_delta_pct": delta / baseline if baseline else 0.0,
    }


def localized_backtest_detail(detail: pd.DataFrame, lang: str) -> pd.DataFrame:
    columns = ["stay_date", "hotel_id", "room_type", "current_price", "recommended_price", "action", "confidence", "sold_rooms", "occupancy", "realized_sold_rooms", "realized_occupancy", "baseline_revenue", "recommended_revenue", "static_revenue_delta", "main_reasons", "risk_flags"]
    out = detail[[c for c in columns if c in detail.columns]].copy()
    if "room_type" in out.columns:
        out["room_type"] = out["room_type"].map(lambda v: translate_room_type(v, lang))
    if "action" in out.columns:
        out["action"] = out["action"].map(lambda v: t(v, lang))
    if "confidence" in out.columns:
        out["confidence"] = out["confidence"].map(lambda v: t(v, lang))
    if "main_reasons" in out.columns:
        out["main_reasons"] = out["main_reasons"].map(lambda v: translate_reason_list(v, lang))
    if "risk_flags" in out.columns:
        out["risk_flags"] = out["risk_flags"].map(lambda v: translate_risk_list(v, lang))
    return out.rename(columns={c: _col_label(c, lang) for c in out.columns})


def backtest_excel_bytes(detail: pd.DataFrame, lang: str) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        localized_backtest_detail(detail, lang).to_excel(writer, sheet_name=bt_label("details", lang)[:31], index=False)
        sheet = writer.book.worksheets[0]
        sheet.freeze_panes = "A2"
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 44)
    return output.getvalue()


def render_backtesting(metrics, bookings, current_prices, lang, default_horizon_days, max_change_pct, price_rounding_strategy, room_price_bounds=None) -> None:
    st.subheader(bt_label("tab", lang))
    st.write(bt_label("intro", lang))
    st.info(bt_label("static_volume_note", lang))

    dates = sorted(pd.to_datetime(current_prices["stay_date"]).dt.date.unique())
    if not dates:
        st.warning(bt_label("no_data", lang))
        return
    observation_date = st.selectbox(bt_label("observation_date", lang), dates, index=min(max(len(dates) // 4, 0), len(dates) - 1))
    st.caption(bt_label("run_hint", lang))

    detail, summary = run_static_backtest(metrics, bookings, current_prices, observation_date, default_horizon_days, max_change_pct, price_rounding_strategy, room_price_bounds)
    if detail.empty or not summary:
        st.warning(bt_label("no_data", lang))
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(bt_label("baseline_revenue", lang), f"{summary['baseline_revenue']:,.0f}")
    c2.metric(bt_label("recommended_revenue", lang), f"{summary['recommended_revenue']:,.0f}")
    c3.metric(bt_label("revenue_delta", lang), f"{summary['revenue_delta']:,.0f}")
    c4.metric(bt_label("revenue_delta_pct", lang), f"{summary['revenue_delta_pct']:.1%}")

    daily = detail.groupby("stay_date", as_index=False)["static_revenue_delta"].sum()
    st.plotly_chart(px.bar(daily, x="stay_date", y="static_revenue_delta", title=bt_label("chart", lang)), use_container_width=True)
    st.subheader(bt_label("details", lang))
    st.dataframe(localized_backtest_detail(detail, lang), use_container_width=True, hide_index=True)
    st.download_button(bt_label("download", lang), data=backtest_excel_bytes(detail, lang), file_name="hotel_pricing_backtest.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
