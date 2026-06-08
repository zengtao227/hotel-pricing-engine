import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.kaggle_adapter import convert_hotel_booking_demand


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Kaggle Hotel Booking Demand data into MVP CSV files.")
    parser.add_argument("--source", required=True, help="Path to Kaggle hotel_bookings.csv")
    parser.add_argument("--output-dir", default="sample_data", help="Where canonical CSV files should be written")
    parser.add_argument("--hotel", default=None, help="Optional hotel filter, e.g. City Hotel or Resort Hotel")
    args = parser.parse_args()

    convert_hotel_booking_demand(Path(args.source), Path(args.output_dir), hotel_filter=args.hotel)
    print(f"Demo data written to {args.output_dir}")


if __name__ == "__main__":
    main()
