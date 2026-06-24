from __future__ import annotations

import json
import math
from copy import deepcopy
from datetime import date as _date
from typing import Any

import pandas as pd
import streamlit as st

from .i18n import LANGUAGES, t, translate_room_type
from .price_rounding import PRICE_ROUNDING_STRATEGIES, round_to_price_ending
from .security_controls import validate_uploaded_file_size


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
    "seasons": [],
}

MAX_CONFIG_UPLOAD_BYTES = 200_000
MAX_ROOM_TYPES = 200

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
    # Keyed by room_type only — if multiple hotels share the same room_type name, the last
    # one wins. For multi-hotel deployments each hotel should have its own config instance.
    return {room["room_type"]: room for room in config.get("room_types", []) if room.get("enabled", True)}


def config_to_json_bytes(config: dict[str, Any]) -> bytes:
    return json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")


def _finite_non_negative_float(value: Any, field_name: str) -> float:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid hotel config: `{field_name}` must be a number") from None
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"Invalid hotel config: `{field_name}` must be a non-negative finite number")
    return number


def normalize_hotel_config(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError("Invalid hotel config: root must be a JSON object")

    normalized = default_hotel_config()
    for field in ["hotel_name", "city", "market_positioning"]:
        if field in config:
            normalized[field] = str(config.get(field, "")).strip()

    currency = str(config.get("currency", normalized["currency"])).strip().upper()
    normalized["currency"] = currency if currency in {"CNY", "CHF", "EUR", "USD"} else normalized["currency"]

    language = str(config.get("default_language", normalized["default_language"])).strip()
    normalized["default_language"] = language if language in LANGUAGES else normalized["default_language"]
    normalized["apply_configured_prices"] = bool(config.get("apply_configured_prices", normalized["apply_configured_prices"]))

    if "default_horizon_days" in config:
        horizon_days = int(_finite_non_negative_float(config["default_horizon_days"], "default_horizon_days"))
        normalized["default_horizon_days"] = min(max(horizon_days, 7), 60)
    if "default_max_change_pct" in config:
        max_change_pct = _finite_non_negative_float(config["default_max_change_pct"], "default_max_change_pct")
        normalized["default_max_change_pct"] = min(max(max_change_pct, 0.05), 0.30)
    if config.get("default_price_rounding_strategy"):
        rounding_strategy = str(config["default_price_rounding_strategy"])
        normalized["default_price_rounding_strategy"] = (
            rounding_strategy if rounding_strategy in PRICE_ROUNDING_STRATEGIES else normalized["default_price_rounding_strategy"]
        )

    room_types = config.get("room_types", normalized["room_types"])
    if not isinstance(room_types, list):
        raise ValueError("Invalid hotel config: `room_types` must be a list")
    if len(room_types) > MAX_ROOM_TYPES:
        raise ValueError(f"Invalid hotel config: `room_types` exceeds {MAX_ROOM_TYPES} entries")

    rooms: list[dict[str, Any]] = []
    seen_room_types: set[str] = set()
    for room in room_types:
        if not isinstance(room, dict):
            raise ValueError("Invalid hotel config: every room type entry must be an object")
        room_type = str(room.get("room_type", "")).strip()
        if not room_type:
            raise ValueError("Invalid hotel config: every room type needs `room_type`")
        if room_type in seen_room_types:
            raise ValueError(f"Invalid hotel config: duplicate room_type `{room_type}`")
        seen_room_types.add(room_type)

        base_price = _finite_non_negative_float(room.get("base_price", 0), "base_price")
        min_price = _finite_non_negative_float(room.get("min_price", 0), "min_price")
        max_price = _finite_non_negative_float(room.get("max_price", 0), "max_price")
        weekend_uplift = _finite_non_negative_float(room.get("weekend_uplift", 0), "weekend_uplift")
        if max_price and max_price < min_price:
            raise ValueError(f"Invalid hotel config: max_price is below min_price for `{room_type}`")
        if min_price and base_price < min_price:
            base_price = min_price
        if max_price and base_price > max_price:
            base_price = max_price

        rooms.append(
            {
                "room_type": room_type,
                "room_code": str(room.get("room_code", "")).strip(),
                "base_price": base_price,
                "min_price": min_price,
                "max_price": max_price,
                "weekend_uplift": weekend_uplift,
                "enabled": bool(room.get("enabled", True)),
            }
        )
    normalized["room_types"] = rooms

    raw_seasons = config.get("seasons", [])
    if not isinstance(raw_seasons, list):
        raise ValueError("Invalid hotel config: `seasons` must be a list")
    if len(raw_seasons) > 50:
        raise ValueError("Invalid hotel config: `seasons` exceeds 50 entries")

    normalized_seasons: list[dict] = []
    for season in raw_seasons:
        if not isinstance(season, dict):
            raise ValueError("Invalid hotel config: season entries must be objects")
        name = str(season.get("name", "")).strip()
        if not name:
            raise ValueError("Invalid hotel config: each season needs a `name`")
        if len(name) > 40:
            raise ValueError("Invalid hotel config: season name exceeds 40 characters")
        try:
            s_start = _date.fromisoformat(str(season.get("start", "")))
            s_end = _date.fromisoformat(str(season.get("end", "")))
        except ValueError:
            raise ValueError(f"Invalid hotel config: invalid date in season `{name}`")
        if s_start > s_end:
            raise ValueError(f"Invalid hotel config: start > end in season `{name}`")
        multiplier = _finite_non_negative_float(season.get("demand_multiplier", 1.0), "demand_multiplier")
        if multiplier < 0.1 or multiplier > 5.0:
            raise ValueError(f"Invalid hotel config: demand_multiplier must be 0.1–5.0 in season `{name}`")
        normalized_seasons.append({
            "name": name,
            "start": s_start.isoformat(),
            "end": s_end.isoformat(),
            "demand_multiplier": round(multiplier, 4),
        })
    normalized["seasons"] = normalized_seasons

    return normalized


def load_config_from_upload(uploaded_file) -> dict[str, Any]:
    validate_uploaded_file_size(uploaded_file, "hotel_config.json", MAX_CONFIG_UPLOAD_BYTES)
    raw = uploaded_file.getvalue()
    if len(raw) > MAX_CONFIG_UPLOAD_BYTES:
        raise ValueError(f"Hotel config JSON exceeds {MAX_CONFIG_UPLOAD_BYTES:,} bytes")
    return normalize_hotel_config(json.loads(raw.decode("utf-8")))


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
    return normalize_hotel_config({"room_types": [room for room in rooms if room["room_type"]]})["room_types"]


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
    # Keyed by room_type only — same multi-hotel limitation as room_config_map.
    return {room["room_type"]: {"min_price": float(room.get("min_price", 0) or 0), "max_price": float(room.get("max_price", 0) or 0), "base_price": float(room.get("base_price", 0) or 0)} for room in config.get("room_types", []) if room.get("enabled", True)}


def get_season_multiplier(stay_date: _date, seasons: list[dict[str, Any]]) -> tuple[float, str]:
    """Return (highest demand_multiplier, season_name) for stay_date, or (1.0, '') if no match.

    When multiple seasons overlap, returns the highest multiplier (peak-season-wins rule).
    Low-season multipliers (< 1.0) are correctly returned when no higher match exists.
    """
    best_multiplier: float | None = None
    best_name: str = ""
    for season in seasons:
        try:
            s_start = _date.fromisoformat(season["start"])
            s_end = _date.fromisoformat(season["end"])
        except (KeyError, ValueError):
            continue
        if s_start <= stay_date <= s_end:
            m = float(season.get("demand_multiplier", 1.0))
            if best_multiplier is None or m > best_multiplier:
                best_multiplier = m
                best_name = str(season.get("name", ""))
    return (best_multiplier, best_name) if best_multiplier is not None else (1.0, "")


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

    with st.expander(t("seasons_config", lang), expanded=False):
        st.caption(t("seasons_intro", lang))
        seasons = config.get("seasons", [])
        season_rows = [
            {
                "name": s.get("name", ""),
                "start": s.get("start", ""),
                "end": s.get("end", ""),
                "demand_multiplier": float(s.get("demand_multiplier", 1.0)),
            }
            for s in seasons
        ]
        season_df = pd.DataFrame(season_rows) if season_rows else pd.DataFrame(
            columns=["name", "start", "end", "demand_multiplier"]
        )
        edited_seasons = st.data_editor(
            season_df,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "name": st.column_config.TextColumn(t("season_name", lang), max_chars=40),
                "start": st.column_config.TextColumn(t("season_start", lang), help="YYYY-MM-DD"),
                "end": st.column_config.TextColumn(t("season_end", lang), help="YYYY-MM-DD"),
                "demand_multiplier": st.column_config.NumberColumn(
                    t("season_multiplier", lang),
                    min_value=0.1,
                    max_value=5.0,
                    step=0.1,
                    format="%.2f",
                    help="1.0 = 无调整，2.0 = 需求翻倍，0.5 = 需求减半",
                ),
            },
            key="seasons_editor",
        )
        try:
            new_seasons = []
            for _, row in edited_seasons.iterrows():
                name = str(row.get("name", "")).strip()
                if not name:
                    continue
                new_seasons.append({
                    "name": name,
                    "start": str(row.get("start", "")),
                    "end": str(row.get("end", "")),
                    "demand_multiplier": float(row.get("demand_multiplier", 1.0)),
                })
            normalize_hotel_config({"seasons": new_seasons})
            config["seasons"] = new_seasons
        except ValueError as exc:
            st.error(str(exc))

    st.subheader(label("room_config", lang))
    room_df = room_config_dataframe(config, lang)
    edited = st.data_editor(
        room_df,
        width="stretch",
        hide_index=True,
        column_config={"enabled": st.column_config.CheckboxColumn(label("enabled", lang)), "room_name": st.column_config.TextColumn(label("room_name", lang)), "base_price": st.column_config.NumberColumn(label("base_price", lang), min_value=0, step=10, format="%.0f"), "min_price": st.column_config.NumberColumn(label("min_price", lang), min_value=0, step=10, format="%.0f"), "max_price": st.column_config.NumberColumn(label("max_price", lang), min_value=0, step=10, format="%.0f"), "weekend_uplift": st.column_config.NumberColumn(label("weekend_uplift", lang), min_value=0, step=10, format="%.0f")},
        disabled=["room_name"],
        key="hotel_room_config_editor",
    )
    try:
        config["room_types"] = dataframe_to_room_config(edited)
    except ValueError as exc:
        st.error(str(exc))

    c1, c2, c3 = st.columns(3)
    if c1.button(label("save_session", lang), width="stretch"):
        st.session_state.hotel_config = config
        st.success(label("applied", lang))
    if c2.button(label("reset_default", lang), width="stretch"):
        st.session_state.hotel_config = default_hotel_config()
        st.success(label("reset_done", lang))
        config = st.session_state.hotel_config
    c3.download_button(label("download_json", lang), data=config_to_json_bytes(config), file_name="hotel_config.json", mime="application/json", width="stretch")
    return config
