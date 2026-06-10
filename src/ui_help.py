import streamlit as st

from .i18n import t


HELP_TEXT = {
    "recommendation_horizon_help": {
        "zh": "系统会为未来多少天生成调价建议。演示或日常查看建议用 30 天；只看短期销售压力可用 7–14 天；做月度计划可用 45–60 天。周期越长，远期建议的不确定性越高。",
        "en": "How many future days the system should generate price recommendations for. Use 30 days for demos and daily reviews, 7–14 days for short-term pressure, and 45–60 days for monthly planning. Longer horizons are more uncertain.",
        "de": "Anzahl der zukünftigen Tage, für die Preisempfehlungen erstellt werden. 30 Tage eignen sich für Demos und tägliche Reviews, 7–14 Tage für kurzfristigen Druck, 45–60 Tage für Monatsplanung. Längere Zeiträume sind unsicherer.",
        "fr": "Nombre de jours futurs pour lesquels le système génère des recommandations. Utilisez 30 jours pour les démonstrations et revues quotidiennes, 7–14 jours pour la pression court terme, 45–60 jours pour la planification mensuelle. Les horizons longs sont plus incertains.",
    },
    "max_price_change_help": {
        "zh": "限制系统单次建议的最大涨跌幅，避免价格波动过大。演示和保守运营建议用 10%–15%；价格敏感型酒店用 5%–10%；旺季或库存紧张时可临时提高到 20%–30%，但仍应人工复核。",
        "en": "Caps the maximum one-time increase or decrease to avoid excessive volatility. Use 10%–15% for demos and conservative operation, 5%–10% for price-sensitive hotels, and 20%–30% only during peak demand or tight inventory with manual review.",
        "de": "Begrenzt die maximale einmalige Preisänderung, um starke Preisschwankungen zu vermeiden. 10–15 % für Demos und konservativen Betrieb, 5–10 % für preissensible Hotels, 20–30 % nur bei hoher Nachfrage oder knappem Bestand mit manueller Prüfung.",
        "fr": "Limite la variation tarifaire maximale en une seule recommandation afin d’éviter une volatilité excessive. Utilisez 10–15 % pour les démonstrations et une gestion prudente, 5–10 % pour les hôtels sensibles au prix, et 20–30 % seulement en forte demande ou stock limité avec validation humaine.",
    },
    "interpretation_title": {
        "zh": "如何解读这些指标",
        "en": "How to interpret these indicators",
        "de": "So interpretieren Sie diese Kennzahlen",
        "fr": "Comment interpréter ces indicateurs",
    },
    "interpretation_markdown": {
        "zh": """
- **剩余库存比例** = 还没卖出的可售房间比例。接近 0 表示库存紧张；接近 1 表示库存充足。正常情况下应在 0 到 1 之间；如果出现负值，通常代表该日期/房型出现超售或库存数据与订单数据不一致，需要人工检查。
- **RevPAR（Revenue Per Available Room，每间可售房平均收入）** = 房费收入 ÷ 可售房间数。它不是卖出去房间的平均房价；平均房价看 ADR。这个指标会同时反映价格和入住率，例如房价高但没卖出去，数值也不会好看。
- **预计收益变化**：系统用候选价收益模拟计算推荐价相对当前价的预期收入差。模型会把已知订单收入固定下来，只估计剩余库存未来新增需求对价格的响应。
- **价格弹性**：负值表示价格上升会压低需求。绝对值越大，说明客户越价格敏感；绝对值越小，说明需求更刚性。
- **14天新增预订**：最近 14 天新增的预订量。数值越高，说明近期需求更活跃。
- **置信度**：系统对该建议的把握程度。高置信度可以优先处理；低置信度建议仅作为观察信号。
- **风险提示**：提醒人工复核的原因，例如临近入住、库存异常或历史基准不足。
""",
        "en": """
- **Remaining Inventory Ratio** = share of sellable rooms not yet sold. Close to 0 means tight inventory; close to 1 means plenty of inventory. It should normally be between 0 and 1. A negative value usually indicates overbooking or inconsistent inventory/order data and should be checked manually.
- **RevPAR** = room revenue divided by sellable rooms. It is not the average price of sold rooms; that is ADR. RevPAR reflects both price and occupancy, so a high price with weak sales will still show weak RevPAR.
- **Expected Revenue Delta**: expected revenue difference from the candidate-price simulation. Known booked revenue is fixed; only future demand for remaining inventory responds to price.
- **Price Elasticity**: a negative value means higher price reduces demand. Larger absolute values mean more price-sensitive demand; smaller absolute values mean more inelastic demand.
- **14-day Pickup**: new bookings received in the last 14 days. Higher values indicate stronger recent demand.
- **Confidence**: how strong the recommendation signal is. High-confidence items should be reviewed first; low-confidence items are mainly observation signals.
- **Risk Flags**: reasons for manual review, such as very close stay date, inventory anomalies, or limited historical baseline.
""",
        "de": """
- **Restbestandsquote** = Anteil der verkaufbaren Zimmer, die noch nicht verkauft wurden. Nahe 0 bedeutet knapper Bestand; nahe 1 bedeutet viel Bestand. Normalerweise liegt der Wert zwischen 0 und 1. Ein negativer Wert weist meist auf Überbuchung oder inkonsistente Bestands-/Buchungsdaten hin und sollte manuell geprüft werden.
- **RevPAR** = Zimmerumsatz geteilt durch verkaufbare Zimmer. Das ist nicht der Durchschnittspreis der verkauften Zimmer; dafür steht ADR. RevPAR kombiniert Preis und Auslastung.
- **Erwartete Umsatzänderung**: Umsatzdifferenz aus der Kandidatenpreis-Simulation. Bereits gebuchter Umsatz bleibt fix; nur zukünftige Nachfrage für Restbestand reagiert auf den Preis.
- **Preiselastizität**: Ein negativer Wert bedeutet, dass ein höherer Preis die Nachfrage senkt. Größere Beträge bedeuten preissensiblere Nachfrage.
- **14-Tage-Pickup**: neue Buchungen der letzten 14 Tage. Höhere Werte zeigen stärkere aktuelle Nachfrage.
- **Sicherheit**: Stärke des Empfehlungssignals. Empfehlungen mit hoher Sicherheit zuerst prüfen; niedrige Sicherheit eher als Beobachtungssignal nutzen.
- **Risikohinweise**: Gründe für manuelle Prüfung, z. B. sehr naher Aufenthaltstag, Bestandsanomalien oder begrenzte historische Basis.
""",
        "fr": """
- **Ratio de stock restant** = part des chambres vendables encore non vendues. Proche de 0 signifie stock limité ; proche de 1 signifie stock abondant. Normalement, la valeur est entre 0 et 1. Une valeur négative indique souvent une surréservation ou une incohérence entre stock et réservations, à vérifier manuellement.
- **RevPAR** = revenu chambres divisé par chambres vendables. Ce n’est pas le prix moyen des chambres vendues ; cela correspond à l’ADR. Le RevPAR combine prix et occupation.
- **Variation de revenu estimée** : différence de revenu issue de la simulation des prix candidats. Le revenu déjà réservé reste fixe ; seule la demande future du stock restant réagit au prix.
- **Élasticité-prix** : une valeur négative signifie qu’un prix plus élevé réduit la demande. Plus la valeur absolue est grande, plus la demande est sensible au prix.
- **Pickup 14 jours** : nouvelles réservations reçues sur les 14 derniers jours. Plus la valeur est élevée, plus la demande récente est forte.
- **Confiance** : force du signal de recommandation. Les recommandations à forte confiance doivent être traitées en priorité ; les faibles confiances sont surtout des signaux d’observation.
- **Alertes de risque** : raisons de validation humaine, comme date très proche, anomalie de stock ou référence historique limitée.
""",
    },
    "action_help": {
        "zh": "系统建议的动作：上调、下调或保持。它不是自动改价指令，而是给收益经理或店长复核的建议。",
        "en": "Recommended action: increase, decrease or hold. This is not an automatic price update, but a review suggestion for the revenue manager or hotel operator.",
        "de": "Empfohlene Aktion: erhöhen, senken oder halten. Dies ist keine automatische Preisänderung, sondern eine Empfehlung zur manuellen Prüfung.",
        "fr": "Action recommandée : augmenter, baisser ou maintenir. Ce n’est pas une modification automatique, mais une suggestion à valider.",
    },
    "expected_revenue_delta_help": {
        "zh": "候选价收益模拟中的推荐价预期收益减去当前价预期收益。已知订单收入固定，只对剩余库存未来需求建模。",
        "en": "Recommended expected revenue minus current expected revenue in the candidate-price simulation. Known booked revenue is fixed; only future demand for remaining inventory is modeled.",
        "de": "Erwarteter Umsatz des empfohlenen Preises minus erwarteter Umsatz des aktuellen Preises in der Kandidatenpreis-Simulation. Bereits gebuchter Umsatz bleibt fix.",
        "fr": "Revenu attendu du prix recommandé moins revenu attendu du prix actuel dans la simulation des prix candidats. Le revenu déjà réservé reste fixe.",
    },
    "expected_revenue_help": {
        "zh": "模型估计在该价格下最终可获得的房费收入，包含已知订单收入和未来预计新增成交收入。",
        "en": "Estimated final room revenue at this price, including known booked revenue and expected future new-booking revenue.",
        "de": "Geschätzter endgültiger Zimmerumsatz bei diesem Preis, inklusive bereits gebuchtem Umsatz und erwarteten neuen Buchungen.",
        "fr": "Revenu chambres final estimé à ce prix, incluant le revenu déjà réservé et les nouvelles réservations attendues.",
    },
    "demand_forecast_help": {
        "zh": "在不改变当前价的情况下，模型预测该入住日期和房型最终会售出的间夜数。",
        "en": "Forecast final sold room-nights for this stay date and room type if the current price is kept.",
        "de": "Prognose der final verkauften Zimmernächte für dieses Datum und diesen Zimmertyp bei unverändertem aktuellem Preis.",
        "fr": "Prévision des nuitées finalement vendues pour cette date et ce type de chambre si le prix actuel est conservé.",
    },
    "expected_sold_rooms_help": {
        "zh": "模型估计在推荐价下最终售出的间夜数。它不是保证销量，而是价格弹性假设下的期望值。",
        "en": "Estimated final sold room-nights at the recommended price. This is an expectation under the elasticity assumption, not a guaranteed volume.",
        "de": "Geschätzte final verkaufte Zimmernächte beim empfohlenen Preis. Erwartungswert unter Elastizitätsannahme, keine garantierte Menge.",
        "fr": "Nuitées finales estimées au prix recommandé. C’est une espérance sous hypothèse d’élasticité, pas un volume garanti.",
    },
    "demand_elasticity_help": {
        "zh": "价格弹性。通常为负数，例如 -1.2 表示价格提高 1% 时，未来未成交需求大约下降 1.2%。",
        "en": "Price elasticity. Usually negative; for example, -1.2 means a 1% price increase reduces future unbooked demand by about 1.2%.",
        "de": "Preiselastizität. Üblicherweise negativ; -1,2 bedeutet, dass 1 % Preiserhöhung die zukünftige ungebuchte Nachfrage um ca. 1,2 % senkt.",
        "fr": "Élasticité-prix. Généralement négative ; -1,2 signifie qu’une hausse de prix de 1 % réduit la demande future non réservée d’environ 1,2 %.",
    },
    "candidate_price_count_help": {
        "zh": "本次模拟实际比较的可执行候选价格数量，已考虑单次调价幅度、价格上下限和尾数规则。",
        "en": "Number of feasible candidate prices compared in this simulation after change caps, price bounds and rounding rules.",
        "de": "Anzahl machbarer Kandidatenpreise nach Änderungsgrenzen, Preisgrenzen und Rundungsregeln.",
        "fr": "Nombre de prix candidats faisables après limites de variation, bornes tarifaires et règles d’arrondi.",
    },
    "remaining_inventory_ratio_help": {
        "zh": "还未售出的可售库存比例。0 表示基本售罄，1 表示几乎还没卖。负值通常意味着超售或数据不一致。",
        "en": "Share of sellable inventory still unsold. 0 means almost sold out; 1 means almost nothing sold. Negative values usually mean overbooking or inconsistent data.",
        "de": "Anteil des noch unverkauften Bestands. 0 bedeutet nahezu ausverkauft; 1 bedeutet fast nichts verkauft. Negative Werte deuten meist auf Überbuchung oder Datenprobleme hin.",
        "fr": "Part du stock vendable encore non vendu. 0 signifie presque complet ; 1 signifie presque rien vendu. Les valeurs négatives indiquent souvent une surréservation ou des données incohérentes.",
    },
    "pickup_14d_help": {
        "zh": "最近 14 天内新增的预订量，用来判断近期需求是否变强。",
        "en": "New bookings received in the last 14 days, used to judge whether recent demand is strengthening.",
        "de": "Neue Buchungen der letzten 14 Tage, um zu beurteilen, ob die aktuelle Nachfrage steigt.",
        "fr": "Nouvelles réservations sur les 14 derniers jours, utilisées pour juger si la demande récente augmente.",
    },
    "confidence_help": {
        "zh": "建议的可靠程度。高置信度优先处理；低置信度说明信号不强，需要结合人工经验。",
        "en": "Reliability of the recommendation. High confidence should be reviewed first; low confidence means the signal is weak and needs human judgment.",
        "de": "Zuverlässigkeit der Empfehlung. Hohe Sicherheit zuerst prüfen; niedrige Sicherheit bedeutet schwaches Signal und erfordert menschliche Einschätzung.",
        "fr": "Fiabilité de la recommandation. Les fortes confiances sont prioritaires ; une faible confiance indique un signal faible nécessitant un jugement humain.",
    },
    "risk_flags_help": {
        "zh": "需要人工注意的风险，例如临近入住、库存异常或历史数据不足。",
        "en": "Risks requiring human attention, such as close stay date, inventory anomaly or limited history.",
        "de": "Risiken, die manuelle Aufmerksamkeit erfordern, z. B. nahes Aufenthaltsdatum, Bestandsanomalie oder begrenzte Historie.",
        "fr": "Risques nécessitant une attention humaine, par exemple date proche, anomalie de stock ou historique limité.",
    },
}


def h(key: str, lang: str = "zh") -> str:
    return HELP_TEXT.get(key, {}).get(lang) or HELP_TEXT.get(key, {}).get("en") or key


def render_interpretation_expander(lang: str) -> None:
    with st.expander(h("interpretation_title", lang), expanded=False):
        st.markdown(h("interpretation_markdown", lang))


def recommendation_column_config(lang: str):
    return {
        t("column_action", lang): st.column_config.TextColumn(
            t("column_action", lang),
            help=h("action_help", lang),
        ),
        t("column_expected_revenue_delta", lang): st.column_config.NumberColumn(
            t("column_expected_revenue_delta", lang),
            help=h("expected_revenue_delta_help", lang),
            format="%.0f",
        ),
        t("column_current_expected_revenue", lang): st.column_config.NumberColumn(
            t("column_current_expected_revenue", lang),
            help=h("expected_revenue_help", lang),
            format="%.0f",
        ),
        t("column_recommended_expected_revenue", lang): st.column_config.NumberColumn(
            t("column_recommended_expected_revenue", lang),
            help=h("expected_revenue_help", lang),
            format="%.0f",
        ),
        t("column_demand_forecast_at_current_price", lang): st.column_config.NumberColumn(
            t("column_demand_forecast_at_current_price", lang),
            help=h("demand_forecast_help", lang),
            format="%.1f",
        ),
        t("column_expected_sold_rooms", lang): st.column_config.NumberColumn(
            t("column_expected_sold_rooms", lang),
            help=h("expected_sold_rooms_help", lang),
            format="%.1f",
        ),
        t("column_expected_new_sold_rooms", lang): st.column_config.NumberColumn(
            t("column_expected_new_sold_rooms", lang),
            help=h("expected_sold_rooms_help", lang),
            format="%.1f",
        ),
        t("column_demand_elasticity", lang): st.column_config.NumberColumn(
            t("column_demand_elasticity", lang),
            help=h("demand_elasticity_help", lang),
            format="%.2f",
        ),
        t("column_candidate_price_count", lang): st.column_config.NumberColumn(
            t("column_candidate_price_count", lang),
            help=h("candidate_price_count_help", lang),
            format="%.0f",
        ),
        t("column_occupancy", lang): st.column_config.NumberColumn(
            t("column_occupancy", lang),
            format="%.2%%",
        ),
        t("column_remaining_inventory_ratio", lang): st.column_config.NumberColumn(
            t("column_remaining_inventory_ratio", lang),
            help=h("remaining_inventory_ratio_help", lang),
            format="%.2%%",
        ),
        t("column_pickup_14d", lang): st.column_config.NumberColumn(
            t("column_pickup_14d", lang),
            help=h("pickup_14d_help", lang),
            format="%.0f",
        ),
        t("column_confidence", lang): st.column_config.TextColumn(
            t("column_confidence", lang),
            help=h("confidence_help", lang),
        ),
        t("column_risk_flags", lang): st.column_config.TextColumn(
            t("column_risk_flags", lang),
            help=h("risk_flags_help", lang),
        ),
    }
