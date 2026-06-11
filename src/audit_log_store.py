from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


AUDIT_COLUMNS = [
    "timestamp",
    "actor",
    "event",
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

_DB_FILENAME = "price_approval_publishing_log.sqlite"
_LEGACY_CSV_FILENAME = "price_approval_publishing_log.csv"

# Bump this when a new migration step is added (e.g. new tables, new indices).
_SCHEMA_VERSION = 2

_COLUMN_DDL = """
    timestamp TEXT,
    actor TEXT,
    event TEXT,
    hotel_id TEXT,
    room_type TEXT,
    stay_date TEXT,
    current_price REAL,
    recommended_price REAL,
    approved_price REAL,
    manual_override INTEGER,
    approval_status TEXT,
    push_status TEXT,
    review_comment TEXT,
    target_system TEXT
"""

_DRAFT_DDL = """
    signature TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    table_json TEXT NOT NULL
"""


def _column_type_map() -> dict[str, str]:
    """Parse _COLUMN_DDL into {column_name: SQL_type}."""
    result: dict[str, str] = {}
    for line in _COLUMN_DDL.strip().splitlines():
        line = line.strip().rstrip(",")
        if not line:
            continue
        parts = re.split(r"\s+", line, maxsplit=2)
        if len(parts) >= 2:
            result[parts[0]] = parts[1]
    return result


def audit_log_path(base_dir: str | Path = "data/audit_logs") -> Path:
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / _DB_FILENAME


def _legacy_csv_path(base_dir: str | Path) -> Path:
    return Path(base_dir) / _LEGACY_CSV_FILENAME


def _connect(base_dir: str | Path) -> sqlite3.Connection:
    # isolation_level=None: autocommit mode, transactions managed explicitly
    # with BEGIN IMMEDIATE so concurrent sessions cannot interleave writes.
    conn = sqlite3.connect(audit_log_path(base_dir), timeout=30, isolation_level=None)
    conn.execute(f"CREATE TABLE IF NOT EXISTS audit_log ({_COLUMN_DDL})")
    conn.execute(f"CREATE TABLE IF NOT EXISTS audit_log_archive ({_COLUMN_DDL}, archived_at TEXT)")
    conn.execute(f"CREATE TABLE IF NOT EXISTS approval_draft ({_DRAFT_DDL})")
    _upgrade_schema(conn)
    _ensure_indices(conn)
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version < _SCHEMA_VERSION:
        _migrate_legacy_csv(conn, base_dir)
        conn.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
    return conn


def _upgrade_schema(conn: sqlite3.Connection) -> None:
    """Add any missing columns to existing tables using types derived from _COLUMN_DDL."""
    type_map = _column_type_map()
    for table in ("audit_log", "audit_log_archive"):
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column in AUDIT_COLUMNS:
            if column not in existing:
                col_type = type_map.get(column, "TEXT")
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    draft_existing = {row[1] for row in conn.execute("PRAGMA table_info(approval_draft)")}
    if "signature" not in draft_existing:
        conn.execute(f"CREATE TABLE IF NOT EXISTS approval_draft ({_DRAFT_DDL})")


def _ensure_indices(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_hotel_stay ON audit_log(hotel_id, stay_date)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_draft_signature ON approval_draft(signature)")


def _migrate_legacy_csv(conn: sqlite3.Connection, base_dir: str | Path) -> None:
    csv_path = _legacy_csv_path(base_dir)
    if not csv_path.exists():
        return
    legacy = pd.read_csv(csv_path)
    _insert_rows(conn, legacy)
    csv_path.rename(csv_path.with_name("price_approval_publishing_log.migrated.csv"))


def _insert_rows(conn: sqlite3.Connection, rows: pd.DataFrame) -> None:
    if rows is None or rows.empty:
        return
    prepared = rows.reindex(columns=AUDIT_COLUMNS).copy()
    prepared["manual_override"] = prepared["manual_override"].fillna(False).astype(bool).astype(int)
    for column in ["current_price", "recommended_price", "approved_price"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    text_columns = [c for c in AUDIT_COLUMNS if c not in {"current_price", "recommended_price", "approved_price", "manual_override"}]
    for column in text_columns:
        prepared[column] = prepared[column].astype(str).where(prepared[column].notna(), None)

    records: list[tuple] = [
        tuple(None if pd.isna(value) else (value.item() if hasattr(value, "item") else value) for value in record)
        for record in prepared.itertuples(index=False, name=None)
    ]
    placeholders = ", ".join(["?"] * len(AUDIT_COLUMNS))
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.executemany(f"INSERT INTO audit_log ({', '.join(AUDIT_COLUMNS)}) VALUES ({placeholders})", records)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def load_audit_log(base_dir: str | Path = "data/audit_logs") -> pd.DataFrame:
    conn = _connect(base_dir)
    try:
        log = pd.read_sql_query(f"SELECT {', '.join(AUDIT_COLUMNS)} FROM audit_log ORDER BY rowid", conn)
    finally:
        conn.close()
    if log.empty:
        return pd.DataFrame(columns=AUDIT_COLUMNS)
    log["manual_override"] = log["manual_override"].fillna(0).astype(bool)
    return log


def append_audit_log(rows: pd.DataFrame, base_dir: str | Path = "data/audit_logs") -> pd.DataFrame:
    if rows is None or rows.empty:
        return load_audit_log(base_dir)
    conn = _connect(base_dir)
    try:
        _insert_rows(conn, rows)
    finally:
        conn.close()
    return load_audit_log(base_dir)


def clear_audit_log(base_dir: str | Path = "data/audit_logs") -> pd.DataFrame:
    """Soft delete: move all rows to the archive table; the database file is never removed."""
    archived_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    conn = _connect(base_dir)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                f"INSERT INTO audit_log_archive ({', '.join(AUDIT_COLUMNS)}, archived_at) "
                f"SELECT {', '.join(AUDIT_COLUMNS)}, ? FROM audit_log",
                (archived_at,),
            )
            conn.execute("DELETE FROM audit_log")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    return pd.DataFrame(columns=AUDIT_COLUMNS)


def save_approval_draft(df: pd.DataFrame, signature: str, base_dir: str | Path = "data/audit_logs") -> None:
    """Persist the approval table so it survives session resets."""
    saved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    table_json = df.to_json(orient="records", date_format="iso", default_handler=str)
    conn = _connect(base_dir)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(
                "INSERT OR REPLACE INTO approval_draft (signature, saved_at, table_json) VALUES (?, ?, ?)",
                (signature, saved_at, table_json),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def load_approval_draft(signature: str, base_dir: str | Path = "data/audit_logs") -> pd.DataFrame | None:
    """Return the saved approval draft for this signature, or None if not found."""
    conn = _connect(base_dir)
    try:
        row = conn.execute(
            "SELECT table_json FROM approval_draft WHERE signature = ? ORDER BY rowid DESC LIMIT 1",
            (signature,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    records = json.loads(row[0])
    if not records:
        return None
    df = pd.DataFrame(records)
    for col in ("selected", "manual_override"):
        if col in df.columns:
            df[col] = df[col].astype(bool)
    if "approved_price" in df.columns:
        df["approved_price"] = pd.to_numeric(df["approved_price"], errors="coerce")
    return df
