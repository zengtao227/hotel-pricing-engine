import sqlite3

import pandas as pd

from src.audit_log_store import (
    AUDIT_COLUMNS,
    append_audit_log,
    audit_log_path,
    clear_audit_log,
    load_audit_log,
)


def _log_rows(n: int = 2) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": "2026-06-11 00:00:00 UTC",
                "actor": "tester",
                "hotel_id": "H1",
                "room_type": "Standard Double",
                "stay_date": f"2026-03-{day:02d}",
                "current_price": 388.0,
                "recommended_price": 428.0,
                "approved_price": 428.0,
                "manual_override": False,
                "approval_status": "approved",
                "push_status": "pushed",
                "review_comment": "",
                "target_system": "SIMULATED_CHANNEL_MANAGER",
            }
            for day in range(1, n + 1)
        ]
    )


def test_append_and_load_roundtrip(tmp_path):
    log = append_audit_log(_log_rows(2), base_dir=tmp_path)
    assert list(log.columns) == AUDIT_COLUMNS
    assert len(log) == 2
    assert log["actor"].tolist() == ["tester", "tester"]
    assert log["approved_price"].tolist() == [428.0, 428.0]
    assert log["manual_override"].tolist() == [False, False]

    log = append_audit_log(_log_rows(1), base_dir=tmp_path)
    assert len(log) == 3


def test_clear_is_soft_delete_into_archive(tmp_path):
    append_audit_log(_log_rows(2), base_dir=tmp_path)
    cleared = clear_audit_log(base_dir=tmp_path)

    assert cleared.empty
    assert load_audit_log(base_dir=tmp_path).empty
    db_path = audit_log_path(tmp_path)
    assert db_path.exists(), "database file must never be deleted"

    with sqlite3.connect(db_path) as conn:
        archived = conn.execute("SELECT COUNT(*), MAX(archived_at) FROM audit_log_archive").fetchone()
    assert archived[0] == 2
    assert archived[1]


def test_legacy_csv_is_migrated_once(tmp_path):
    legacy_csv = tmp_path / "price_approval_publishing_log.csv"
    _log_rows(2).to_csv(legacy_csv, index=False)

    log = load_audit_log(base_dir=tmp_path)
    assert len(log) == 2
    assert not legacy_csv.exists(), "legacy CSV should be renamed after migration"
    assert (tmp_path / "price_approval_publishing_log.migrated.csv").exists()

    # A second load must not re-import the archived CSV.
    assert len(load_audit_log(base_dir=tmp_path)) == 2
