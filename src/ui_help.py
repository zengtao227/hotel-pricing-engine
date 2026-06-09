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
- **预计收益变化**：正值表示按推荐价调整后，系统估计收益可能增加；负值表示为了提高成交或降低风险，系统建议接受一定收入下降。
- **14天 Pickup**：最近 14 天新增的预订量。数值越高，说明近期需求更活跃。
- **置信度**：系统对该建议的把握程度。高置信度可以优先处理；低置信度建议仅作为观察信号。
- **风险提示**：提醒人工复核的原因，例如临近入住、库存异常或历史基准不足。
""",
        "en": """
- **Remaining Inventory Ratio** = share of sellable rooms not yet sold. Close to 0 means tight inventory; close to 1 means plenty of inventory. It should normally be between 0 and 1. A negative value usually indicates overbooking or inconsistent inventory/order data and should be checked manually.
- **Expected Revenue Delta**: positive means the recommended change may increase revenue; negative means the system accepts a possible revenue drop to improve conversion or reduce risk.
- **14-day Pickup**: new bookings received in the last 14 days. Higher values indicate stronger recent demand.
- **Confidence**: how strong the recommendation signal is. High-confidence items should be reviewed first; low-confidence items are mainly observation signals.
- **Risk Flags**: reasons for manual review, such as very close stay date, inventory anomalies, or limited historical baseline.
""",
        "de": """
- **Restbestandsquote** = Anteil der verkaufbaren Zimmer, die noch nicht verkauft wurden. Nahe 0 bedeutet knapper Bestand; nahe 1 bedeutet viel Bestand. Normalerweise liegt der Wert zwischen 0 und 1. Ein negativer Wert weist meist auf Überbuchung oder inkonsistente Bestands-/Buchungsdaten hin und sollte manuell geprüft werden.
- **Erwartete Umsatzänderung**: positiv bedeutet, dass die Empfehlung den Umsatz erhöhen kann; negativ bedeutet, dass das System einen möglichen Umsatzrückgang akzeptiert, um Conversion oder Risiko zu verbessern.
- **14-Tage-Pickup**: neue Buchungen der letzten 14 Tage. Höhere Werte zeigen stärkere aktuelle Nachfrage.
- **Sicherheit**: Stärke des Empfehlungssignals. Empfehlungen mit hoher Sicherheit zuerst prüfen; niedrige Sicherheit eher als Beobachtungssignal nutzen.
- **Risikohinweise**: Gründe für manuelle Prüfung, z. B. sehr naher Aufenthaltstag, Bestandsanomalien oder begrenzte historische Basis.
""",
        "fr": """
- **Ratio de stock restant** = part des chambres vendables encore non vendues. Proche de 0 signifie stock limité ; proche de 1 signifie stock abondant. Normalement, la valeur est entre 0 et 1. Une valeur négative indique souvent une surréservation ou une incohérence entre stock et réservations, à vérifier manuellement.
- **Variation de revenu estimée** : positive signifie que le changement recommandé peut augmenter le revenu ; négative signifie que le système accepte une baisse potentielle pour améliorer la conversion ou réduire le risque.
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
        "zh": "系统估计推荐价相对当前价可能带来的收入变化。正值偏机会，负值偏去库存或降低销售风险。",
        "en": "Estimated revenue change from recommended price versus current price. Positive values indicate opportunity; negative values usually indicate inventory clearance or risk reduction.",
        "de": "Geschätzte Umsatzänderung des empfohlenen Preises gegenüber dem aktuellen Preis. Positive Werte zeigen Chancen; negative Werte deuten meist auf Bestandsabbau oder Risikoreduktion hin.",
        "fr": "Variation de revenu estimée entre le prix recommandé et le prix actuel. Les valeurs positives signalent une opportunité ; les valeurs négatives indiquent souvent une réduction du stock ou du risque.",
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
        t("column_remaining_inventory_ratio", lang): st.column_config.NumberColumn(
            t("column_remaining_inventory_ratio", lang),
            help=h("remaining_inventory_ratio_help", lang),
            format="%.1%%",
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
