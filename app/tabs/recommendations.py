from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.i18n import t
from src.ui_help import render_interpretation_expander

from app.tabs._helpers import (
    _render_attention_cards,
    _show_attention_summary,
    _show_recommendation_table,
)


_OBSERVATION_DATE_TEXT: dict[str, str] = {
    "zh": "推荐基准观察日：**{date}**（取自价格表最早日期）。系统仅使用该日之前已知的订单生成推荐；如需基于今天生成推荐，请确保 current_prices 从今天开始。",
    "en": "Recommendation observation date: **{date}** (earliest date in the price table). Only bookings known by that date are used; to generate recommendations as of today, make sure current_prices starts from today.",
    "de": "Beobachtungstag der Empfehlungen: **{date}** (frühestes Datum der Preistabelle). Nur bis dahin bekannte Buchungen werden verwendet; für Empfehlungen ab heute muss current_prices ab heute beginnen.",
    "fr": "Date d'observation des recommandations : **{date}** (première date du tableau des prix). Seules les réservations connues à cette date sont utilisées ; pour des recommandations à partir d'aujourd'hui, current_prices doit commencer aujourd'hui.",
}

_ELASTICITY_NOTE: dict[str, str] = {
    "zh": (
        "**模型说明**：推荐价由等弹性需求模型在允许调价带内枚举得出，"
        "结果通常是调价带的端点（涨价或降价上限）或恰好清空剩余库存的价格。"
        "当前价格弹性参数（默认 −1.25）未经真实订单数据校准，"
        "`最大调价幅度` 是实际有效的风险护栏。"
    ),
    "en": (
        "**Model note**: The recommended price is found by scanning candidate prices within the "
        "allowed change band using an iso-elastic demand model. The result is almost always "
        "a band boundary (max increase or max decrease) or the price that just clears remaining "
        "inventory — not a smooth interior optimum. The default elasticity (−1.25) is not "
        "calibrated from real booking data; `max price change %` is the effective risk guardrail."
    ),
    "de": (
        "**Modellhinweis**: Der empfohlene Preis wird durch Abtasten von Kandidatenpreisen im "
        "erlaubten Änderungsband ermittelt. Das Ergebnis ist fast immer ein Bandrand oder der "
        "Preis, der das verbleibende Inventar abverkauft — kein glatter innerer Optimalwert. "
        "Die Standard-Preiselastizität (−1,25) ist nicht aus echten Buchungsdaten kalibriert."
    ),
    "fr": (
        "**Note modèle** : Le prix recommandé est obtenu en balayant les prix candidats dans "
        "la plage autorisée avec un modèle d'élasticité-prix. Le résultat est presque toujours "
        "une borne de la plage ou le prix qui écoule le stock restant — pas un optimum intérieur. "
        "L'élasticité par défaut (−1,25) n'est pas calibrée sur des données de réservation réelles."
    ),
}


def render_recommendations(
    recommendations: pd.DataFrame,
    lang: str,
    ui_theme: str,
    observation_date=None,
) -> None:
    st.subheader(t("recommendations", lang))
    if observation_date is not None:
        obs_template = _OBSERVATION_DATE_TEXT.get(lang, _OBSERVATION_DATE_TEXT["en"])
        st.caption(obs_template.format(date=pd.to_datetime(observation_date).date()))
    render_interpretation_expander(lang)
    st.info(_ELASTICITY_NOTE.get(lang, _ELASTICITY_NOTE["en"]))

    raw_actions = sorted(recommendations["action"].unique())
    action_filter = st.multiselect(
        t("filter_actions", lang),
        options=raw_actions,
        default=raw_actions,
        format_func=lambda value: t(value, lang),
        help=t("filter_actions_help", lang),
    )
    filtered = recommendations[recommendations["action"].isin(action_filter)].copy()

    if not filtered.empty:
        action_order = {"increase": 0, "decrease": 1, "hold": 2}
        filtered["_has_risk"] = filtered["risk_flags"].fillna("").astype(str).str.strip().ne("").astype(int)
        filtered["_action_order"] = filtered["action"].map(action_order).fillna(9)
        filtered["_rev_abs"] = pd.to_numeric(filtered.get("expected_revenue_delta", 0), errors="coerce").abs().fillna(0)
        filtered = filtered.sort_values(
            ["_has_risk", "_action_order", "_rev_abs"], ascending=[False, True, False]
        ).drop(columns=["_has_risk", "_action_order", "_rev_abs"])

    _show_attention_summary(filtered, lang)
    _render_attention_cards(filtered, lang)
    _show_recommendation_table(filtered, lang, ui_theme)
