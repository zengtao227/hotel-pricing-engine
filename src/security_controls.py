from __future__ import annotations

from collections.abc import Mapping
import ipaddress
import os

import pandas as pd


MAX_FILE_BYTES: int = 50 * 1024 * 1024
TRUTHY_ENV_VALUES: frozenset[str] = frozenset({"1", "true", "yes", "on"})
PII_COLUMN_CONTAINS_KEYWORDS: tuple[str, ...] = (
    "name",
    "guest",
    "phone",
    "mobile",
    "email",
    "passport",
    "id_card",
    "id_number",
    "identity_number",
    "document_number",
    "credit_card",
    "bank_card",
    "card_number",
    "address",
    "remark",
    "comment",
    "姓名",
    "客人",
    "电话",
    "手机",
    "邮箱",
    "邮件",
    "证件",
    "身份证",
    "护照",
    "地址",
    "备注",
)
PII_ID_COLUMN_NAMES: frozenset[str] = frozenset(
    {
        "guest_id",
        "customer_id",
        "client_id",
        "visitor_id",
        "identity_id",
        "passport_id",
        "document_id",
        "证件号",
        "证件号码",
        "身份证号",
        "身份证号码",
        "护照号",
        "护照号码",
    }
)


def env_flag(name: str, environ: Mapping[str, str] | None = None) -> bool:
    source: Mapping[str, str] = os.environ if environ is None else environ
    value: str = str(source.get(name, "") or "").strip().lower()
    return value in TRUTHY_ENV_VALUES


def header_value(headers: Mapping[str, object], name: str) -> str:
    direct_value: object | None = headers.get(name)
    if direct_value is None:
        target_name: str = name.lower()
        for key, value in headers.items():
            if str(key).lower() == target_name:
                direct_value = value
                break
    return str(direct_value or "").strip()


def trusted_remote_actor(
    headers: Mapping[str, object],
    environ: Mapping[str, str] | None = None,
) -> str | None:
    if not env_flag("HOTEL_TRUST_REMOTE_USER", environ):
        return None
    actor: str = header_value(headers, "X-Remote-User")
    return actor or None


def strict_actor_enabled(environ: Mapping[str, str] | None = None) -> bool:
    return env_flag("HOTEL_STRICT_ACTOR", environ)


def default_actor_from_headers(
    headers: Mapping[str, object],
    environ: Mapping[str, str] | None = None,
) -> str:
    actor: str | None = trusted_remote_actor(headers, environ)
    return actor or "demo_user"


def is_loopback_ip(ip_address: object | None) -> bool:
    ip_value: str = str(ip_address or "").strip()
    if not ip_value:
        return False
    try:
        return ipaddress.ip_address(ip_value).is_loopback
    except ValueError:
        return ip_value.startswith("127.") or ip_value in {"localhost", "::1", "0:0:0:0:0:0:0:1"}


def proxy_client_key(headers: Mapping[str, object]) -> str | None:
    forwarded_for: str = header_value(headers, "X-Forwarded-For")
    if forwarded_for:
        first_forwarded_ip: str = forwarded_for.split(",", 1)[0].strip()
        if first_forwarded_ip:
            return first_forwarded_ip

    real_ip: str = header_value(headers, "X-Real-IP")
    return real_ip or None


def client_key_from_request(
    ip_address: object | None,
    headers: Mapping[str, object],
    environ: Mapping[str, str] | None = None,
) -> str:
    ip_value: str = str(ip_address or "").strip()

    # Only trust proxy-injected headers when explicitly configured; otherwise an
    # attacker rotates X-Forwarded-For to get a fresh rate-limit bucket each attempt.
    if env_flag("HOTEL_TRUST_PROXY_HEADERS", environ) and (not ip_value or is_loopback_ip(ip_value)):
        proxy_key: str | None = proxy_client_key(headers)
        if proxy_key:
            return proxy_key

    if ip_value:
        return ip_value

    return "unknown"


def pii_columns(columns: pd.Index) -> list[object]:
    contains_keywords: tuple[str, ...] = tuple(
        keyword.casefold() for keyword in PII_COLUMN_CONTAINS_KEYWORDS
    )
    id_column_names: frozenset[str] = frozenset(column.casefold() for column in PII_ID_COLUMN_NAMES)
    matches: list[object] = []
    for column in columns:
        column_name: str = str(column).casefold()
        if column_name in id_column_names or any(keyword in column_name for keyword in contains_keywords):
            matches.append(column)
    return matches


def drop_pii_columns(df: pd.DataFrame) -> pd.DataFrame:
    to_drop: list[object] = pii_columns(df.columns)
    if not to_drop:
        return df
    return df.drop(columns=to_drop)


def uploaded_file_size(uploaded_file: object) -> int | None:
    size_value: object | None = getattr(uploaded_file, "size", None)
    if size_value is None:
        return None
    return int(size_value)


def _format_size_limit(max_bytes: int) -> str:
    bytes_per_mb: int = 1024 * 1024
    if max_bytes >= bytes_per_mb and max_bytes % bytes_per_mb == 0:
        return f"{max_bytes // bytes_per_mb} MB"
    return f"{max_bytes:,} bytes"


def validate_uploaded_file_size(
    uploaded_file: object,
    label: str,
    max_bytes: int = MAX_FILE_BYTES,
    allow_unknown_size: bool = False,
) -> None:
    size: int | None = uploaded_file_size(uploaded_file)
    if size is None:
        if allow_unknown_size:
            return
        raise ValueError(f"{label}: file size is unavailable; upload rejected")
    if size is not None and size > max_bytes:
        raise ValueError(f"{label}: file exceeds {_format_size_limit(max_bytes)} limit")
