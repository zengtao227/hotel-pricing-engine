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
    if rows is None or rows.empty:
        return load_audit_log(base_dir)
    path = audit_log_path(base_dir)
    new_rows = rows.reindex(columns=AUDIT_COLUMNS)
    write_header = not path.exists()
    new_rows.to_csv(path, mode="a", index=False, header=write_header)
    return load_audit_log(base_dir)


def clear_audit_log(base_dir: str | Path = "data/audit_logs") -> pd.DataFrame:
    path = audit_log_path(base_dir)
    if path.exists():
        path.unlink()
    return pd.DataFrame(columns=AUDIT_COLUMNS)
