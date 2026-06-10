from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from .i18n import t, translate_reason_list, translate_risk_list, translate_room_type
from .metrics import calculate_daily_metrics
from .pricing_engine import generate_recommendations
from .revenue_simulation import simulate_candidate_revenue_curve
from .ui_theme import apply_plotly_theme


BT = {
    "tab": {"zh": "回测分析", "en": "Backtest Analysis", "de": "Backtest-Analyse", "fr": "Analyse de backtest"},
    "intro": {
        "zh": "用历史观察日以前已知的订单数据，模拟系统当时会给出的推荐价；同时展示价格弹性模型的预期收益回测和最终实际销量的静态对照。",
        "en": "Simulate recommendations using only bookings known before the historical observation date, then show elasticity-aware expected revenue and a static realized-volume comparison.",
        "de": "Simuliert Empfehlungen nur mit Buchungen, die vor dem historischen Beobachtungstag bekannt waren, und zeigt erwarteten Umsatz mit Preiselastizität sowie einen statischen Ist-Volumen-Vergleich.",
        "fr": "Simule les recommandations uniquement avec les réservations connues avant la date d’observation historique, puis affiche le revenu attendu avec élasticité-prix et une comparaison statique au volume réalisé.",
    },
    "observation_date": {"zh": "回测观察日", "en": "Backtest observation date", "de": "Backtest-Beobachtungstag", "fr": "Date d’observation"},
    "run_hint": {"zh": "系统只使用该日以前已经产生的订单作为已知信息，并对后续周期生成推荐。", "en": "The system uses only bookings already made by that date and generates recommendations for the following horizon.", "de": "Das System nutzt nur bis dahin bekannte Buchungen und erstellt Empfehlungen für den folgenden Zeitraum.", "fr": "Le système utilise uniquement les réservations déjà connues à cette date et génère des recommandations pour l’horizon suivant."},
    "static_volume_note": {"zh": "说明：弹性收益回测是模型在观察日当时的预期结果，不等同于真实因果收益；静态销量对照保留为保守的合理性校验。", "en": "Note: elasticity revenue backtesting is the model's as-of expected result, not proven causal revenue. The static-volume comparison remains as a conservative sanity check.", "de": "Hinweis: Der preiselastische Umsatz-Backtest ist die damalige Erwartung des Modells, kein bewiesener kausaler Umsatz. Der statische Volumenvergleich bleibt als konservativer Plausibilitätscheck erhalten.", "fr": "Note : le backtest de revenu avec élasticité est le résultat attendu par le modèle à la date d’observation, pas un revenu causal prouvé. La comparaison à volume statique reste un contrôle prudent."},
    "elasticity_section": {"zh": "价格弹性收益回测", "en": "Elasticity Revenue Backtest", "de": "Umsatz-Backtest mit Preiselastizität", "fr": "Backtest de revenu avec élasticité"},
    "static_section": {"zh": "静态实际销量对照", "en": "Static Realized-Volume Comparison", "de": "Statischer Ist-Volumen-Vergleich", "fr": "Comparaison statique au volume réalisé"},
    "elasticity_current_revenue": {"zh": "当前价预期收益", "en": "Current Expected Revenue", "de": "Erwarteter Umsatz aktueller Preis", "fr": "Revenu attendu prix actuel"},
    "elasticity_recommended_revenue": {"zh": "推荐价预期收益", "en": "Recommended Expected Revenue", "de": "Erwarteter Umsatz empfohlener Preis", "fr": "Revenu attendu prix recommandé"},
    "elasticity_delta": {"zh": "弹性预期收益变化", "en": "Elasticity Expected Revenue Delta", "de": "Erwartete Umsatzänderung", "fr": "Variation de revenu attendue"},
    "elasticity_delta_pct": {"zh": "弹性预期收益变化率", "en": "Elasticity Delta %", "de": "Erwartete Umsatzänderung %", "fr": "Variation attendue %"},
    "baseline_revenue": {"zh": "基准收入", "en": "Baseline Revenue", "de": "Basisumsatz", "fr": "Revenu de référence"},
    "recommended_revenue": {"zh": "推荐价静态收入", "en": "Recommended Static Revenue", "de": "Empfohlener statischer Umsatz", "fr": "Revenu statique recommandé"},
    "revenue_delta": {"zh": "静态收益变化", "en": "Static Revenue Delta", "de": "Statische Umsatzänderung", "fr": "Variation statique"},
    "revenue_delta_pct": {"zh": "收益变化率", "en": "Revenue Delta %", "de": "Umsatzänderung %", "fr": "Variation %"},
    "download": {"zh": "下载回测明细 Excel", "en": "Download backtest details Excel", "de": "Backtest-Details als Excel herunterladen", "fr": "Télécharger le détail Excel"},
    "details": {"zh": "回测明细", "en": "Backtest Details", "de": "Backtest-Details", "fr": "Détail du backtest"},
    "chart": {"zh": "每日收益变化对比", "en": "Daily Revenue Delta Comparison", "de": "Täglicher Umsatzänderungsvergleich", "fr": "Comparaison quotidienne des variations"},
    "curve": {"zh": "候选价收益曲线", "en": "Candidate Price Revenue Curve", "de": "Umsatzkurve der Kandidatenpreise", "fr": "Courbe de revenu des prix candidats"},
    "curve_selector": {"zh": "选择曲线样本", "en": "Select curve sample", "de": "Kurvenbeispiel auswählen", "fr": "Choisir un exemple de courbe"},
    "curve_no_data": {"zh": "当前样本无法生成候选价收益曲线。", "en": "The selected sample cannot generate a candidate-price revenue curve.", "de": "Für dieses Beispiel kann keine Kandidatenpreis-Umsatzkurve erzeugt werden.", "fr": "L’exemple sélectionné ne peut pas générer de courbe de revenu."},
    "no_data": {"zh": "当前数据不足以生成回测结果。", "en": "Not enough data to generate backtest results.", "de": "Nicht genügend Daten für Backtest-Ergebnisse.", "fr": "Données insuffisantes pour générer le backtest."},
    "axis_stay_date": {"zh": "入住日期", "en": "Stay Date", "de": "Aufenthaltsdatum", "fr": "Date de séjour"},
    "axis_revenue_delta": {"zh": "收益变化金额", "en": "Revenue Delta", "de": "Umsatzänderung", "fr": "Variation de revenu"},
    "legend_revenue_metric": {"zh": "收益口径", "en": "Revenue Metric", "de": "Umsatzkennzahl", "fr": "Indicateur de revenu"},
    "axis_candidate_price": {"zh": "候选价格", "en": "Candidate Price", "de": "Kandidatenpreis", "fr": "Prix candidat"},
    "axis_expected_revenue": {"zh": "预期收益", "en": "Expected Revenue", "de": "Erwarteter Umsatz", "fr": "Revenu attendu"},
    "expected_sold_rooms": {"zh": "预计售出房间", "en": "Expected Sold Rooms", "de": "Erwartete verkaufte Zimmer", "fr": "Chambres vendues attendues"},
    "expected_new_sold_rooms": {"zh": "预计新增售出", "en": "Expected New Sold Rooms", "de": "Erwartete neue Verkäufe", "fr": "Nouvelles ventes attendues"},
    "current_price_marker": {"zh": "是否当前价", "en": "Is Current Price", "de": "Ist aktueller Preis", "fr": "Prix actuel ?"},
    "recommended_price_marker": {"zh": "是否推荐价", "en": "Is Recommended Price", "de": "Ist empfohlener Preis", "fr": "Prix recommandé ?"},
    "yes": {"zh": "是", "en": "Yes", "de": "Ja", "fr": "Oui"},
    "no": {"zh": "否", "en": "No", "de": "Nein", "fr": "Non"},
}

COLUMN_LABELS = {
    "stay_date": {"zh": "入住日期", "en": "Stay Date", "de": "Aufenthaltsdatum", "fr": "Date de séjour"},
    "hotel_id": {"zh": "酒店", "en": "Hotel", "de": "Hotel", "fr": "Hôtel"},
    "room_type": {"zh": "房型", "en": "Room Type", "de": "Zimmertyp", "fr": "Type de chambre"},
    "current_price": {"zh": "当前价", "en": "Current Price", "de": "Aktueller Preis", "fr": "Prix actuel"},
    "recommended_price": {"zh": "推荐价", "en": "Recommended Price", "de": "Empfohlener Preis", "fr": "Prix recommandé"},
    "action": {"zh": "建议动作", "en": "Action", "de": "Aktion", "fr": "Action"},
    "confidence": {"zh": "置信度", "en": "Confidence", "de": "Sicherheit", "fr": "Confiance"},
    "known_sellable_rooms": {"zh": "观察日可售库存", "en": "Known Sellable Rooms", "de": "Bekannter verkaufbarer Bestand", "fr": "Stock vendable connu"},
    "known_room_revenue": {"zh": "观察日已锁定收入", "en": "Known Room Revenue", "de": "Bekannter Zimmerumsatz", "fr": "Revenu chambres connu"},
    "current_expected_revenue": {"zh": "观察日当前价预期收益", "en": "As-of Current Expected Revenue", "de": "Erwarteter Umsatz aktueller Preis", "fr": "Revenu attendu prix actuel"},
    "recommended_expected_revenue": {"zh": "观察日推荐价预期收益", "en": "As-of Recommended Expected Revenue", "de": "Erwarteter Umsatz empfohlener Preis", "fr": "Revenu attendu prix recommandé"},
    "demand_forecast_at_current_price": {"zh": "观察日需求预测", "en": "As-of Demand Forecast", "de": "Nachfrageprognose", "fr": "Prévision de demande"},
    "current_expected_sold_rooms": {"zh": "当前价预计售出", "en": "Current Expected Sold Rooms", "de": "Erwartete Verkäufe aktueller Preis", "fr": "Chambres attendues prix actuel"},
    "expected_sold_rooms": {"zh": "推荐价预计售出", "en": "Recommended Expected Sold Rooms", "de": "Erwartete Verkäufe empfohlener Preis", "fr": "Chambres attendues prix recommandé"},
    "expected_new_sold_rooms": {"zh": "推荐价预计新增售出", "en": "Recommended Expected New Sold Rooms", "de": "Erwartete neue Verkäufe", "fr": "Nouvelles ventes attendues"},
    "demand_elasticity": {"zh": "价格弹性", "en": "Price Elasticity", "de": "Preiselastizität", "fr": "Élasticité-prix"},
    "known_sold_rooms": {"zh": "观察日已售房间", "en": "Known Sold Rooms", "de": "Bekannte verkaufte Zimmer", "fr": "Chambres vendues connues"},
    "realized_sold_rooms": {"zh": "最终实际售出", "en": "Final Realized Sold Rooms", "de": "Endgültig verkaufte Zimmer", "fr": "Chambres finalement vendues"},
    "known_occupancy": {"zh": "观察日入住率", "en": "Known Occupancy", "de": "Bekannte Auslastung", "fr": "Occupation connue"},
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


def _known_snapshot(as_of_metrics: pd.DataFrame) -> pd.DataFrame:
    known = as_of_metrics.copy()
    known["stay_date"] = pd.to_datetime(known["stay_date"]).dt.date
    return known.rename(
        columns={
            "sellable_rooms": "known_sellable_rooms",
            "sold_rooms": "known_sold_rooms",
            "room_revenue": "known_room_revenue",
            "occupancy": "known_occupancy",
        }
    )[
        ["hotel_id", "room_type", "stay_date", "known_sellable_rooms", "known_sold_rooms", "known_room_revenue", "known_occupancy"]
    ]


def _safe_sum(detail: pd.DataFrame, column: str) -> float:
    if column not in detail.columns:
        return 0.0
    return float(pd.to_numeric(detail[column], errors="coerce").fillna(0).sum())


def _curve_label(row, lang: str) -> str:
    room = translate_room_type(str(row.room_type), lang)
    return f"{row.stay_date} | {room} | {row.current_price:.0f} → {row.recommended_price:.0f}"


def _candidate_curve_from_row(row, max_change_pct: float, price_rounding_strategy: str) -> pd.DataFrame:
    known_room_revenue = float(getattr(row, "known_room_revenue", 0) or 0)
    if known_room_revenue <= 0:
        known_sold_rooms = float(getattr(row, "known_sold_rooms", 0) or 0)
        current_expected_sold = float(getattr(row, "current_expected_sold_rooms", known_sold_rooms) or known_sold_rooms)
        current_expected_revenue = float(getattr(row, "current_expected_revenue", 0) or 0)
        current_price = float(getattr(row, "current_price", 0) or 0)
        known_room_revenue = current_expected_revenue - current_price * max(current_expected_sold - known_sold_rooms, 0)

    curve_rows = simulate_candidate_revenue_curve(
        current_price=float(getattr(row, "current_price", 0) or 0),
        sellable_rooms=float(getattr(row, "known_sellable_rooms", 0) or 0),
        known_sold_rooms=float(getattr(row, "known_sold_rooms", 0) or 0),
        known_room_revenue=max(known_room_revenue, 0),
        demand_forecast_at_current_price=float(getattr(row, "demand_forecast_at_current_price", 0) or 0),
        demand_elasticity=float(getattr(row, "demand_elasticity", 0) or 0),
        max_change_pct=max_change_pct,
        rounding_strategy=price_rounding_strategy,
        price_floor=getattr(row, "price_floor", None),
        price_ceiling=getattr(row, "price_ceiling", None),
    )
    curve = pd.DataFrame(curve_rows)
    if curve.empty:
        return curve
    curve["is_current_price"] = (curve["candidate_price"] - float(row.current_price)).abs() < 0.01
    curve["is_recommended_price"] = (curve["candidate_price"] - float(row.recommended_price)).abs() < 0.01
    return curve


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

    recs = recommendations.drop(columns=["occupancy"], errors="ignore")
    detail = recs.merge(_known_snapshot(as_of_metrics), how="left", on=["hotel_id", "room_type", "stay_date"])

    realized = metrics.copy()
    realized["stay_date"] = pd.to_datetime(realized["stay_date"]).dt.date
    realized = realized.rename(columns={"sold_rooms": "realized_sold_rooms", "occupancy": "realized_occupancy", "room_revenue": "realized_room_revenue"})
    detail = detail.merge(
        realized[["hotel_id", "room_type", "stay_date", "realized_sold_rooms", "realized_occupancy", "realized_room_revenue"]],
        how="left",
        on=["hotel_id", "room_type", "stay_date"],
    )

    fill_cols = ["known_sellable_rooms", "known_sold_rooms", "known_room_revenue", "known_occupancy", "realized_sold_rooms", "realized_occupancy", "realized_room_revenue"]
    detail[fill_cols] = detail[fill_cols].fillna(0)
    detail["baseline_revenue"] = detail["current_price"].astype(float) * detail["realized_sold_rooms"].astype(float)
    detail["recommended_revenue"] = detail["recommended_price"].astype(float) * detail["realized_sold_rooms"].astype(float)
    detail["static_revenue_delta"] = detail["recommended_revenue"] - detail["baseline_revenue"]

    baseline = float(detail["baseline_revenue"].sum())
    recommended = float(detail["recommended_revenue"].sum())
    delta = recommended - baseline
    elasticity_current = _safe_sum(detail, "current_expected_revenue")
    elasticity_recommended = _safe_sum(detail, "recommended_expected_revenue")
    elasticity_delta = elasticity_recommended - elasticity_current
    return detail, {
        "rows": int(len(detail)),
        "changed_rows": int((detail["action"] != "hold").sum()),
        "elasticity_current_revenue": elasticity_current,
        "elasticity_recommended_revenue": elasticity_recommended,
        "elasticity_delta": elasticity_delta,
        "elasticity_delta_pct": elasticity_delta / elasticity_current if elasticity_current else 0.0,
        "baseline_revenue": baseline,
        "recommended_revenue": recommended,
        "revenue_delta": delta,
        "revenue_delta_pct": delta / baseline if baseline else 0.0,
    }


_ROUND_2DP = [
    "known_room_revenue", "current_expected_revenue", "recommended_expected_revenue",
    "demand_forecast_at_current_price", "current_expected_sold_rooms", "expected_sold_rooms",
    "expected_new_sold_rooms", "baseline_revenue", "recommended_revenue", "static_revenue_delta",
]
_ROUND_4DP = ["known_occupancy", "realized_occupancy"]


def localized_backtest_detail(detail: pd.DataFrame, lang: str) -> pd.DataFrame:
    columns = ["stay_date", "hotel_id", "room_type", "current_price", "recommended_price", "action", "confidence", "known_sellable_rooms", "known_sold_rooms", "known_room_revenue", "known_occupancy", "current_expected_revenue", "recommended_expected_revenue", "demand_forecast_at_current_price", "current_expected_sold_rooms", "expected_sold_rooms", "expected_new_sold_rooms", "demand_elasticity", "realized_sold_rooms", "realized_occupancy", "baseline_revenue", "recommended_revenue", "static_revenue_delta", "main_reasons", "risk_flags"]
    out = detail[[c for c in columns if c in detail.columns]].copy()
    for col in _ROUND_2DP:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)
    for col in _ROUND_4DP:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(4)
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


def render_backtesting(metrics, bookings, current_prices, lang, default_horizon_days, max_change_pct, price_rounding_strategy, room_price_bounds=None, ui_theme: str = "light") -> None:
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

    st.subheader(bt_label("elasticity_section", lang))
    e1, e2, e3, e4 = st.columns(4)
    e1.metric(bt_label("elasticity_current_revenue", lang), f"{summary['elasticity_current_revenue']:,.0f}")
    e2.metric(bt_label("elasticity_recommended_revenue", lang), f"{summary['elasticity_recommended_revenue']:,.0f}")
    e3.metric(bt_label("elasticity_delta", lang), f"{summary['elasticity_delta']:,.0f}")
    e4.metric(bt_label("elasticity_delta_pct", lang), f"{summary['elasticity_delta_pct']:.1%}")

    daily_elasticity = detail.groupby("stay_date", as_index=False).agg(
        elasticity_expected_revenue_delta=("expected_revenue_delta", "sum"),
        static_revenue_delta=("static_revenue_delta", "sum"),
    )
    daily_long = daily_elasticity.melt(
        id_vars="stay_date",
        value_vars=["elasticity_expected_revenue_delta", "static_revenue_delta"],
        var_name="metric",
        value_name="revenue_delta",
    )
    daily_long["metric"] = daily_long["metric"].map(
        {
            "elasticity_expected_revenue_delta": bt_label("elasticity_delta", lang),
            "static_revenue_delta": bt_label("revenue_delta", lang),
        }
    )
    daily_fig = px.bar(
        daily_long,
        x="stay_date",
        y="revenue_delta",
        color="metric",
        barmode="group",
        title=bt_label("chart", lang),
        labels={
            "stay_date": bt_label("axis_stay_date", lang),
            "revenue_delta": bt_label("axis_revenue_delta", lang),
            "metric": bt_label("legend_revenue_metric", lang),
        },
    )
    daily_fig.update_layout(
        xaxis_title=bt_label("axis_stay_date", lang),
        yaxis_title=bt_label("axis_revenue_delta", lang),
        legend_title_text=bt_label("legend_revenue_metric", lang),
    )
    st.plotly_chart(apply_plotly_theme(daily_fig, ui_theme), width="stretch")

    st.subheader(bt_label("curve", lang))
    curve_options = detail.copy()
    curve_options["_curve_label"] = curve_options.apply(lambda row: _curve_label(row, lang), axis=1)
    selected_curve_label = st.selectbox(bt_label("curve_selector", lang), curve_options["_curve_label"].tolist())
    selected_curve_row = curve_options[curve_options["_curve_label"] == selected_curve_label].iloc[0]
    curve = _candidate_curve_from_row(selected_curve_row, max_change_pct, price_rounding_strategy)
    if curve.empty:
        st.info(bt_label("curve_no_data", lang))
    else:
        curve_display = curve.copy()
        curve_display["current_price_marker"] = curve_display["is_current_price"].map(
            lambda value: bt_label("yes", lang) if bool(value) else bt_label("no", lang)
        )
        curve_display["recommended_price_marker"] = curve_display["is_recommended_price"].map(
            lambda value: bt_label("yes", lang) if bool(value) else bt_label("no", lang)
        )
        curve_fig = px.line(
            curve_display,
            x="candidate_price",
            y="expected_revenue",
            markers=True,
            title=f"{bt_label('curve', lang)}：{selected_curve_label}",
            hover_data={
                "expected_sold_rooms": ":.2f",
                "expected_new_sold_rooms": ":.2f",
                "current_price_marker": True,
                "recommended_price_marker": True,
                "is_current_price": False,
                "is_recommended_price": False,
            },
            labels={
                "candidate_price": bt_label("axis_candidate_price", lang),
                "expected_revenue": bt_label("axis_expected_revenue", lang),
                "expected_sold_rooms": bt_label("expected_sold_rooms", lang),
                "expected_new_sold_rooms": bt_label("expected_new_sold_rooms", lang),
                "current_price_marker": bt_label("current_price_marker", lang),
                "recommended_price_marker": bt_label("recommended_price_marker", lang),
            },
        )
        curve_fig.update_layout(
            xaxis_title=bt_label("axis_candidate_price", lang),
            yaxis_title=bt_label("axis_expected_revenue", lang),
        )
        st.plotly_chart(apply_plotly_theme(curve_fig, ui_theme), width="stretch")

    st.subheader(bt_label("static_section", lang))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(bt_label("baseline_revenue", lang), f"{summary['baseline_revenue']:,.0f}")
    c2.metric(bt_label("recommended_revenue", lang), f"{summary['recommended_revenue']:,.0f}")
    c3.metric(bt_label("revenue_delta", lang), f"{summary['revenue_delta']:,.0f}")
    c4.metric(bt_label("revenue_delta_pct", lang), f"{summary['revenue_delta_pct']:.1%}")

    st.subheader(bt_label("details", lang))
    st.dataframe(localized_backtest_detail(detail, lang), width="stretch", hide_index=True)
    st.download_button(bt_label("download", lang), data=backtest_excel_bytes(detail, lang), file_name="hotel_pricing_backtest.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
