from __future__ import annotations

from pathlib import Path

import pandas as pd


AUDIT_COLUMNS = [
    "timestamp",
    "actor",
    "hotel_id",
    "room_type",
    "stay_date",
    "current_price",
    "recommended_price",
    "approved_price",
    "manual_override",
    "approval_status",
    "push_status",
    "review_comment",
    "target_system",
]


def audit_log_path(base_dir: str | Path = "data/audit_logs") -> Path:
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / "price_approval_publishing_log.csv"


def load_audit_log(base_dir: str | Path = "data/audit_logs") -> pd.DataFrame:
    path = audit_log_path(base_dir)
    if not path.exists():
        return pd.DataFrame(columns=AUDIT_COLUMNS)
    return pd.read_csv(path)


def append_audit_log(rows: pd.DataFrame, base_dir: str | Path = "data/audit_logs") -> pd.DataFrame:
    existing = load_audit_log(base_dir)
    if rows is None or rows.empty:
        return existing
    combined = pd.concat([existing, rows.reindex(columns=AUDIT_COLUMNS)], ignore_index=True)
    combined.to_csv(audit_log_path(base_dir), index=False)
    return combined


def clear_audit_log(base_dir: str | Path = "data/audit_logs") -> pd.DataFrame:
    path = audit_log_path(base_dir)
    if path.exists():
        path.unlink()
    return pd.DataFrame(columns=AUDIT_COLUMNS)
