# MVP Implementation Notes

## Goal

This MVP turns the planning documents into a runnable prototype:

1. Load hotel booking, inventory and current-price CSV files.
2. Validate core data quality.
3. Calculate daily room-type-level metrics.
4. Generate explainable rule-based pricing recommendations.
5. Export recommendations and metrics to Excel.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Canonical CSV files

The app expects three files:

- `bookings.csv`
- `inventory.csv`
- `current_prices.csv`

If `sample_data/` CSV files are absent, the app generates a deterministic synthetic demo dataset automatically.

## Kaggle Hotel Booking Demand adapter

After downloading `hotel_bookings.csv` locally, convert it into the MVP format:

```bash
python scripts/create_demo_data.py --source data/raw/hotel_bookings.csv --output-dir sample_data --hotel "City Hotel"
```

The Kaggle dataset has bookings and ADR, but it does not provide real future inventory snapshots or current listed-price snapshots. The adapter therefore creates reasonable demo inventory and current prices. For a real hotel customer, those files should come from PMS, channel manager, or manual Excel export.

## Current model status

The recommendation engine is deliberately rule-based. It considers:

- occupancy versus similar historical dates
- weekend demand pattern
- 14-day pickup
- remaining inventory ratio
- days to arrival
- maximum one-time price-change guardrail

This is suitable for demos and consulting discussions, but not yet for fully automated price publication.
