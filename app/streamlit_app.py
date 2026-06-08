import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_demo_data, load_hotel_data
from src.metrics import calculate_daily_metrics, summarize_overview
from src.pricing_engine import generate_recommendations
from src.report_export import build_excel_report
from src.validation import validate_all


st.set_page_config(page_title="Hotel Pricing Engine MVP", layout="wide")

st.title("Hotel Pricing Engine MVP")
st.caption("Upload hotel booking CSV files and generate explainable room-price recommendations.")

with st.sidebar:
    st.header("Data")
    use_demo = st.toggle("Use bundled demo data", value=True)

    bookings_file = inventory_file = current_prices_file = None
    if not use_demo:
        bookings_file = st.file_uploader("bookings.csv", type=["csv"])
        inventory_file = st.file_uploader("inventory.csv", type=["csv"])
        current_prices_file = st.file_uploader("current_prices.csv", type=["csv"])

    horizon_days = st.slider("Recommendation horizon", min_value=7, max_value=60, value=30, step=7)
    max_change_pct = st.slider("Max one-time price change", min_value=0.05, max_value=0.30, value=0.15, step=0.05)

try:
    if use_demo:
        hotel_data = load_demo_data(ROOT / "sample_data")
    else:
        if not bookings_file or not inventory_file or not current_prices_file:
            st.info("Upload all three CSV files or switch on bundled demo data.")
            st.stop()
        hotel_data = load_hotel_data(bookings_file, inventory_file, current_prices_file)
except Exception as exc:
    st.error(f"Could not load data: {exc}")
    st.stop()

validation_errors = validate_all(hotel_data.bookings, hotel_data.inventory, hotel_data.current_prices)
if validation_errors:
    st.error("Data validation failed.")
    for error in validation_errors:
        st.write(f"- {error}")
    st.stop()

metrics = calculate_daily_metrics(hotel_data.bookings, hotel_data.inventory)
observation_date = pd.to_datetime(hotel_data.current_prices["stay_date"]).min()

recommendations = generate_recommendations(
    metrics=metrics,
    bookings=hotel_data.bookings,
    current_prices=hotel_data.current_prices,
    observation_date=observation_date,
    horizon_days=horizon_days,
    max_change_pct=max_change_pct,
)

overview = summarize_overview(metrics)

st.subheader("Core metrics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Room Revenue", f"{overview['room_revenue']:,.0f}")
c2.metric("Occupancy", f"{overview['occupancy']:.1%}")
c3.metric("ADR", f"{overview['adr']:,.2f}")
c4.metric("RevPAR", f"{overview['revpar']:,.2f}")

st.subheader("Daily RevPAR trend")
trend = metrics.groupby("stay_date", as_index=False).agg(revpar=("revpar", "mean"), occupancy=("occupancy", "mean"))
st.plotly_chart(px.line(trend, x="stay_date", y="revpar", title="Average RevPAR by stay date"), use_container_width=True)

st.subheader("Price recommendations")
action_filter = st.multiselect(
    "Filter actions",
    options=sorted(recommendations["action"].unique()),
    default=sorted(recommendations["action"].unique()),
)
filtered = recommendations[recommendations["action"].isin(action_filter)].copy()
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.download_button(
    "Download Excel report",
    data=build_excel_report(metrics, recommendations),
    file_name="hotel_pricing_recommendations.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

with st.expander("Input data preview"):
    st.write("Bookings")
    st.dataframe(hotel_data.bookings.head(50), use_container_width=True)
    st.write("Inventory")
    st.dataframe(hotel_data.inventory.head(50), use_container_width=True)
    st.write("Current prices")
    st.dataframe(hotel_data.current_prices.head(50), use_container_width=True)
