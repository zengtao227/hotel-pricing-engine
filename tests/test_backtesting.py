import pandas as pd

from src.backtesting import run_static_backtest
from src.data_loader import load_demo_data
from src.metrics import calculate_daily_metrics


def test_realized_sold_rooms_use_full_bookings_not_as_of_snapshot():
    data = load_demo_data("sample_data")
    first_price_date = pd.to_datetime(data.current_prices["stay_date"]).min()
    as_of = data.bookings[pd.to_datetime(data.bookings["booking_date"]) <= first_price_date]
    snapshot_metrics = calculate_daily_metrics(as_of, data.inventory)
    dates = sorted(pd.to_datetime(data.current_prices["stay_date"]).dt.date.unique())

    detail, _ = run_static_backtest(snapshot_metrics, data.bookings, data.current_prices, dates[len(dates) // 4], 30, 0.15, "chinese_lucky")

    full = calculate_daily_metrics(data.bookings, data.inventory)
    full["stay_date"] = full["stay_date"].dt.date
    expected = detail[["hotel_id", "room_type", "stay_date"]].merge(full, on=["hotel_id", "room_type", "stay_date"])
    assert detail["realized_sold_rooms"].sum() == expected["sold_rooms"].sum()
