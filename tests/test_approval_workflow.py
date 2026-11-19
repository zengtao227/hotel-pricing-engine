import pandas as pd

from src.approval_workflow import (
    _price_within_bounds,
    build_approval_table,
    simulate_push,
    update_manual_flags,
)


def _recommendations(with_bounds: bool = True) -> pd.DataFrame:
    rows = [
        {
            "stay_date": "2026-03-01",
            "hotel_id": "H1",
            "room_type": "Standard Double",
            "current_price": 388.0,
            "recommended_price": 428.0,
            "action": "increase",
            "confidence": "high",
        },
        {
            "stay_date": "2026-03-02",
            "hotel_id": "H1",
            "room_type": "Standard Double",
            "current_price": 388.0,
            "recommended_price": 388.0,
            "action": "hold",
            "confidence": "medium",
        },
    ]
    df = pd.DataFrame(rows)
    if with_bounds:
        df["price_floor"] = 328.0
        df["price_ceiling"] = 588.0
    return df


class TestPriceWithinBounds:
    def test_no_bounds_positive_price_passes(self):
        assert _price_within_bounds(100.0, None, None)

    def test_zero_and_negative_price_always_blocked(self):
        assert not _price_within_bounds(0.0, None, None)
        assert not _price_within_bounds(-5.0, None, None)

    def test_nan_and_non_numeric_blocked(self):
        assert not _price_within_bounds(float("nan"), None, None)
        assert not _price_within_bounds("abc", None, None)
        assert not _price_within_bounds(None, None, None)

    def test_exactly_on_floor_or_ceiling_passes(self):
        assert _price_within_bounds(90.0, 90.0, 110.0)
        assert _price_within_bounds(110.0, 90.0, 110.0)

    def test_outside_bounds_blocked(self):
        assert not _price_within_bounds(89.98, 90.0, 110.0)
        assert not _price_within_bounds(110.02, 90.0, 110.0)

    def test_unconfigured_zero_bounds_ignored(self):
        assert _price_within_bounds(50.0, 0.0, 0.0)


def test_build_approval_table_preserves_floor_and_ceiling_columns():
    table = build_approval_table(_recommendations(with_bounds=True))
    assert "price_floor" in table.columns
    assert "price_ceiling" in table.columns

    table_without = build_approval_table(_recommendations(with_bounds=False))
    assert "price_floor" not in table_without.columns


def test_manual_price_edit_does_not_auto_approve():
    table = build_approval_table(_recommendations())
    assert table.loc[0, "approval_status"] == "pending"

    table.loc[0, "approved_price"] = 500.0
    flagged = update_manual_flags(table)

    assert bool(flagged.loc[0, "manual_override"])
    assert flagged.loc[0, "approval_status"] == "pending"


def test_simulate_push_only_pushes_approved_rows_and_records_actor():
    table = build_approval_table(_recommendations())
    table.loc[0, "approval_status"] = "approved"
    table.loc[0, "selected"] = True

    pushed, log_rows, violations = simulate_push(table, "zh", actor="tester")

    assert violations == 0
    assert len(log_rows) >= 1
    assert (log_rows["actor"] == "tester").all()
    assert pushed.loc[0, "push_status"] == "pushed"


def test_simulate_push_blocks_out_of_bounds_and_zero_prices():
    table = build_approval_table(_recommendations())
    table.loc[0, "approval_status"] = "approved"
    table.loc[0, "selected"] = True
    table.loc[0, "approved_price"] = 9999.0  # above ceiling 588

    table.loc[1, "approval_status"] = "approved"
    table.loc[1, "selected"] = True
    table.loc[1, "approved_price"] = 0.0  # zero price must never publish
    # Avoid manual-override recompute resetting test prices.
    pushed, log_rows, violations = simulate_push(table, "zh")

    assert violations == 2
    # push_blocked rows are now included in log_rows for audit trail
    assert len(log_rows) == 2
    assert (log_rows["event"] == "push_blocked").all()
    assert (pushed["push_status"] != "pushed").all()


def test_signature_changes_when_price_bounds_change():
    from src.approval_workflow import approval_signature

    recs = _recommendations()
    tightened = recs.copy()
    tightened["price_ceiling"] = 450.0
    assert approval_signature(recs) != approval_signature(tightened)


def test_bulk_accept_does_not_touch_pushed_rows():
    from src.approval_workflow import accept_price_changes

    table = build_approval_table(_recommendations())
    table.at[0, "approved_price"] = 500.0
    table.at[0, "approval_status"] = "approved"
    pushed, _, _ = simulate_push(table, "zh")
    assert pushed.at[0, "push_status"] == "pushed"

    after = accept_price_changes(pushed)
    assert after.at[0, "approved_price"] == 500.0


def test_reset_keeps_pushed_rows_so_they_cannot_be_pushed_again():
    from src.approval_workflow import accept_price_changes, reset_approval_table

    pushed, _, _ = simulate_push(accept_price_changes(build_approval_table(_recommendations())), "zh")
    assert pushed.at[0, "push_status"] == "pushed"

    reset = reset_approval_table(pushed)
    assert reset.at[0, "push_status"] == "pushed"
    assert reset.at[0, "pushed_at"] == pushed.at[0, "pushed_at"]

    _, log_rows, _ = simulate_push(accept_price_changes(reset), "zh")
    assert "push" not in set(log_rows.get("event", []))
