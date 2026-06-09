from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pandas as pd
import streamlit as st

from .i18n import LANGUAGES, t, translate_room_type
from .price_rounding import round_to_price_ending


DEFAULT_HOTEL_CONFIG: dict[str, Any] = {
    "hotel_name": "Demo 4-Star Business Hotel",
    "city": "Wuhan",
    "market_positioning": "Second-tier Chinese 4-star business hotel",
    "currency": "CNY",
    "default_language": "zh",
    "apply_configured_prices": True,
    "default_price_rounding_strategy": "chinese_lucky",
    "default_horizon_days": 30,
    "default_max_change_pct": 0.15,
    "room_types": [
        {"room_type": "Standard Double", "room_code": "STD_DB", "base_price": 388.0, "min_price": 328.0, "max_price": 588.0, "weekend_uplift": 40.0, "enabled": True},
        {"room_type": "Superior Double", "room_code": "SUP_DB", "base_price": 468.0, "min_price": 398.0, "max_price": 688.0, "weekend_uplift": 40.0, "enabled": True},
        {"room_type": "Family Room", "room_code": "FAM", "base_price": 588.0, "min_price": 488.0, "max_price": 888.0, "weekend_uplift": 40.0, "enabled": True},
    ],
}

LABELS = {
    "tab": {"zh": "酒店配置", "en": "Hotel Configuration", "de": "Hotelkonfiguration", "fr": "Configuration hôtel"},
    "intro": {"zh": "为每家酒店设置自己的房型、基准价、最低价、最高价和周末加价。调价建议会基于这些配置生成，而不是只依赖固定 demo 价格。", "en": "Configure each hotel’s room types, base prices, price floors, price ceilings and weekend uplift. Recommendations use this configuration instead of fixed demo prices.", "de": "Konfigurieren Sie Zimmertypen, Basispreise, Mindest- und Höchstpreise sowie Wochenendaufschläge. Empfehlungen verwenden diese Konfiguration statt fixer Demo-Preise.", "fr": "Configurez les types de chambre, prix de base, prix minimums, plafonds et majorations week-end. Les recommandations utilisent cette configuration au lieu de prix de démonstration fixes."},
    "hotel_profile": {"zh": "酒店信息", "en": "Hotel profile", "de": "Hotelprofil", "fr": "Profil hôtel"},
    "pricing_rules": {"zh": "默认价格规则", "en": "Default pricing rules", "de": "Standard-Preisregeln", "fr": "Règles tarifaires par défaut"},
    "room_config": {"zh": "房型价格配置", "en": "Room type price configuration", "de": "Zimmertyp-Preiskonfiguration", "fr": "Configuration tarifaire des chambres"},
    "apply_configured_prices": {"zh": "用配置价覆盖当前价", "en": "Apply configured prices to current prices", "de": "Konfigurierte Preise auf aktuelle Preise anwenden", "fr": "Appliquer les prix configurés aux prix actuels"},
    "apply_help": {"zh": "开启后，只会覆盖配置中存在的房型；上传数据里的未知房型会保留原始 current_price。关闭后，全部使用上传或数据文件中的 current_price。", "en": "When enabled, only room types present in the configuration are overwritten; unknown uploaded room types keep their original current_price. When disabled, all uploaded/data-file current_price values are used.", "de": "Wenn aktiviert, werden nur konfigurierte Zimmertypen überschrieben; unbekannte hochgeladene Zimmertypen behalten ihren ursprünglichen current_price. Wenn deaktiviert, werden alle current_price-Werte aus den Daten verwendet.", "fr": "Activé : seuls les types configurés sont remplacés ; les types inconnus importés conservent leur current_price d’origine. Désactivé : tous les current_price importés sont utilisés."},
    "save_session": {"zh": "应用配置到当前会话", "en": "Apply configuration to session", "de": "Konfiguration auf Sitzung anwenden", "fr": "Appliquer à la session"},
    "reset_default": {"zh": "恢复默认配置", "en": "Reset to default", "de": "Auf Standard zurücksetzen", "fr": "Réinitialiser"},
    "download_json": {"zh": "下载酒店配置 JSON", "en": "Download hotel config JSON", "de": "Hotelkonfiguration JSON herunterladen", "fr": "Télécharger JSON de configuration"},
    "uploaded_config": {"zh": "上传酒店配置 JSON", "en": "Upload hotel config JSON", "de": "Hotelkonfiguration JSON hochladen", "fr": "Importer JSON de configuration"},
    "applied": {"zh": "酒店配置已应用。", "en": "Hotel configuration applied.", "de": "Hotelkonfiguration angewendet.", "fr": "Configuration appliquée."},
    "reset_done": {"zh": "已恢复默认酒店配置。", "en": "Default hotel configuration restored.", "de": "Standardkonfiguration wiederhergestellt.", "fr": "Configuration par défaut restaurée."},
    "upload_done": {"zh": "已导入酒店配置。", "en": "Hotel configuration imported.", "de": "Hotelkonfiguration importiert.", "fr": "Configuration importée."},
    "hotel_name": {"zh": "酒店名称", "en": "Hotel name", "de": "Hotelname", "fr": "Nom de l’hôtel"},
    "city": {"zh": "城市", "en": "City", "de": "Stadt", "fr": "Ville"},
    "market_positioning": {"zh": "市场定位", "en": "Market positioning", "de": "Marktpositionierung", "fr": "Positionnement"},
    "currency": {"zh": "货币", "en": "Currency", "de": "Währung", "fr": "Devise"},
    "room_name": {"zh": "显示房型", "en": "Display room type", "de": "Angezeigter Zimmertyp", "fr": "Type affiché"},
    "base_price": {"zh": "基准价", "en": "Base price", "de": "Basispreis", "fr": "Prix de base"},
    "min_price": {"zh": "最低价", "en": "Minimum price", "de": "Mindestpreis", "fr": "Prix minimum"},
    "max_price": {"zh": "最高价", "en": "Maximum price", "de": "Höchstpreis", "fr": "Prix maximum"},
    "weekend_uplift": {"zh": "周末加价", "en": "Weekend uplift", "de": "Wochenendaufschlag", "fr": "Majoration week-end"},
    "enabled": {"zh": "参与推荐", "en": "Enabled", "de": "Aktiv", "fr": "Actif"},
}


def label(key: str, lang: str = "zh") -> str:
    return LABELS.get(key, {}).get(lang) or LABELS.get(key, {}).get("en") or key


def default_hotel_config() -> dict[str, Any]:
    return deepcopy(DEFAULT_HOTEL_CONFIG)


def ensure_hotel_config() -> dict[str, Any]:
    if "hotel_config" not in st.session_state:
        st.session_state.hotel_config = default_hotel_config()
    return st.session_state.hotel_config


def room_config_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {room["room_type"]: room for room in config.get("room_types", []) if room.get("enabled", True)}


def config_to_json_bytes(config: dict[str, Any]) -> bytes:
    return json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")


def load_config_from_upload(uploaded_file) -> dict[str, Any]:
    return json.loads(uploaded_file.getvalue().decode("utf-8"))


def room_config_dataframe(config: dict[str, Any], lang: str) -> pd.DataFrame:
    rows = []
    for room in config.get("room_types", []):
        rows.append({"enabled": bool(room.get("enabled", True)), "room_type": room.get("room_type", ""), "room_name": translate_room_type(room.get("room_type", ""), lang), "room_code": room.get("room_code", ""), "base_price": float(room.get("base_price", 0)), "min_price": float(room.get("min_price", 0)), "max_price": float(room.get("max_price", 0)), "weekend_uplift": float(room.get("weekend_uplift", 0))})
    return pd.DataFrame(rows)


def dataframe_to_room_config(df: pd.DataFrame) -> list[dict[str, Any]]:
    rooms = []
    for row in df.to_dict("records"):
        base_price = float(row.get("base_price", 0) or 0)
        min_price = float(row.get("min_price", 0) or 0)
        max_price = float(row.get("max_price", 0) or 0)
        if max_price < min_price:
            max_price = min_price
        if base_price < min_price:
            base_price = min_price
        if base_price > max_price and max_price > 0:
            base_price = max_price
        rooms.append({"room_type": str(row.get("room_type", "")).strip(), "room_code": str(row.get("room_code", "")).strip(), "base_price": base_price, "min_price": min_price, "max_price": max_price, "weekend_uplift": float(row.get("weekend_uplift", 0) or 0), "enabled": bool(row.get("enabled", True))})
    return [room for room in rooms if room["room_type"]]


def apply_config_to_current_prices(current_prices: pd.DataFrame, config: dict[str, Any], rounding_strategy: str) -> pd.DataFrame:
    out = current_prices.copy()
    out["stay_date"] = pd.to_datetime(out["stay_date"]).dt.normalize()
    if not config.get("apply_configured_prices", True):
        return out

    room_map = room_config_map(config)

    def price_for(row) -> float:
        room = room_map.get(row["room_type"])
        if not room:
            return float(row["current_price"])
        stay_date = pd.to_datetime(row["stay_date"])
        weekend_uplift = float(room.get("weekend_uplift", 0)) if stay_date.weekday() >= 5 else 0.0
        raw_price = float(room.get("base_price", row["current_price"])) + weekend_uplift
        rounded = round_to_price_ending(raw_price, strategy=rounding_strategy)
        min_price = float(room.get("min_price", rounded) or rounded)
        max_price = float(room.get("max_price", rounded) or rounded)
        return float(min(max(rounded, min_price), max_price))

    out["current_price"] = out.apply(price_for, axis=1)
    return out


def room_bounds_from_config(config: dict[str, Any]) -> dict[str, dict[str, float]]:
    return {room["room_type"]: {"min_price": float(room.get("min_price", 0) or 0), "max_price": float(room.get("max_price", 0) or 0), "base_price": float(room.get("base_price", 0) or 0)} for room in config.get("room_types", []) if room.get("enabled", True)}


def render_hotel_configuration(config: dict[str, Any], lang: str) -> dict[str, Any]:
    st.subheader(label("tab", lang))
    st.write(label("intro", lang))

    uploaded = st.file_uploader(label("uploaded_config", lang), type=["json"])
    if uploaded is not None:
        try:
            st.session_state.hotel_config = load_config_from_upload(uploaded)
            st.success(label("upload_done", lang))
            config = st.session_state.hotel_config
        except Exception as exc:
            st.error(str(exc))

    with st.expander(label("hotel_profile", lang), expanded=True):
        c1, c2 = st.columns(2)
        config["hotel_name"] = c1.text_input(label("hotel_name", lang), value=str(config.get("hotel_name", "")))
        config["city"] = c2.text_input(label("city", lang), value=str(config.get("city", "")))
        config["market_positioning"] = st.text_input(label("market_positioning", lang), value=str(config.get("market_positioning", "")))
        currency_options = ["CNY", "CHF", "EUR", "USD"]
        current_currency = config.get("currency", "CNY")
        config["currency"] = st.selectbox(label("currency", lang), currency_options, index=currency_options.index(current_currency) if current_currency in currency_options else 0)

    with st.expander(label("pricing_rules", lang), expanded=True):
        c1, c2 = st.columns(2)
        config["apply_configured_prices"] = c1.toggle(label("apply_configured_prices", lang), value=bool(config.get("apply_configured_prices", True)), help=label("apply_help", lang))
        current_language = config.get("default_language", "zh")
        config["default_language"] = c2.selectbox(t("language", lang), list(LANGUAGES.keys()), format_func=lambda code: LANGUAGES[code], index=list(LANGUAGES.keys()).index(current_language) if current_language in LANGUAGES else 0)

    st.subheader(label("room_config", lang))
    room_df = room_config_dataframe(config, lang)
    edited = st.data_editor(
        room_df,
        use_container_width=True,
        hide_index=True,
        column_config={"enabled": st.column_config.CheckboxColumn(label("enabled", lang)), "room_name": st.column_config.TextColumn(label("room_name", lang)), "base_price": st.column_config.NumberColumn(label("base_price", lang), min_value=0, step=10, format="%.0f"), "min_price": st.column_config.NumberColumn(label("min_price", lang), min_value=0, step=10, format="%.0f"), "max_price": st.column_config.NumberColumn(label("max_price", lang), min_value=0, step=10, format="%.0f"), "weekend_uplift": st.column_config.NumberColumn(label("weekend_uplift", lang), min_value=0, step=10, format="%.0f")},
        disabled=["room_name"],
        key="hotel_room_config_editor",
    )
    config["room_types"] = dataframe_to_room_config(edited)

    c1, c2, c3 = st.columns(3)
    if c1.button(label("save_session", lang), use_container_width=True):
        st.session_state.hotel_config = config
        st.success(label("applied", lang))
    if c2.button(label("reset_default", lang), use_container_width=True):
        st.session_state.hotel_config = default_hotel_config()
        st.success(label("reset_done", lang))
        config = st.session_state.hotel_config
    c3.download_button(label("download_json", lang), data=config_to_json_bytes(config), file_name="hotel_config.json", mime="application/json", use_container_width=True)
    return config
