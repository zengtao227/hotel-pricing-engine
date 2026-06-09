from datetime import date, timedelta

import numpy as np
import pandas as pd

from .price_rounding import round_to_price_ending


ROOMS_BY_TYPE = {
    "Standard Double": 40,
    "Superior Double": 25,
    "Family Room": 12,
}

# Demo listed prices represent a second-tier Chinese 4-star business hotel.
# These are displayed/listed rates, not necessarily discounted OTA transaction prices.
BASE_PRICES = {
    "Standard Double": 388,
    "Superior Double": 468,
    "Family Room": 588,
}


def _listed_price(base_price: float, weekend_uplift: float = 0) -> float:
    return round_to_price_ending(base_price + weekend_uplift, strategy="chinese_lucky")


def build_demo_data(seed: int = 42):
    """Create a small deterministic demo dataset for the Streamlit MVP."""
    rng = np.random.default_rng(seed)
    hotel_id = "DEMO_HOTEL"
    start = date(2026, 1, 1)
    observation_date = date(2026, 2, 15)
    end = observation_date + timedelta(days=60)

    dates = pd.date_range(start, end, freq="D")

    inventory_rows = []
    for stay_date in dates:
        for room_type, rooms in ROOMS_BY_TYPE.items():
            inventory_rows.append(
                {
                    "hotel_id": hotel_id,
                    "room_type": room_type,
                    "stay_date": stay_date.date(),
                    "available_rooms": rooms,
                    "out_of_order_rooms": 0,
                }
            )
    inventory = pd.DataFrame(inventory_rows)

    price_rows = []
    for stay_date in pd.date_range(observation_date, observation_date + timedelta(days=60), freq="D"):
        for room_type, base_price in BASE_PRICES.items():
            weekend_uplift = 40 if stay_date.weekday() >= 5 else 0
            price_rows.append(
                {
                    "hotel_id": hotel_id,
                    "room_type": room_type,
                    "stay_date": stay_date.date(),
                    "current_price": _listed_price(base_price, weekend_uplift),
                }
            )
    current_prices = pd.DataFrame(price_rows)

    booking_rows = []
    booking_id = 1
    channels = ["Direct", "Booking.com", "Expedia", "Corporate"]
    for stay_date in dates:
        for room_type, total_rooms in ROOMS_BY_TYPE.items():
            weekend_factor = 1.25 if stay_date.weekday() >= 5 else 0.85
            season_factor = 1.15 if stay_date.month == 2 else 1.0
            room_factor = {"Standard Double": 0.55, "Superior Double": 0.48, "Family Room": 0.42}[room_type]
            target_sold = int(np.clip(rng.normal(total_rooms * room_factor * weekend_factor * season_factor, total_rooms * 0.08), 2, total_rooms))
            remaining = target_sold
            while remaining > 0:
                rooms = int(min(remaining, rng.choice([1, 1, 1, 2])))
                remaining -= rooms
                lead_time = int(np.clip(rng.gamma(2.2, 10), 0, 90))
                booking_date = stay_date.date() - timedelta(days=lead_time)
                nights = int(rng.choice([1, 1, 2, 2, 3], p=[0.45, 0.2, 0.2, 0.1, 0.05]))
                check_out_date = stay_date.date() + timedelta(days=nights)
                weekend_uplift = 40 if stay_date.weekday() >= 5 else 0
                daily_rate = round_to_price_ending(
                    BASE_PRICES[room_type] + weekend_uplift + int(rng.normal(0, 18)),
                    strategy="chinese_lucky",
                )
                cancelled = rng.random() < (0.17 if lead_time > 30 else 0.08)
                status = "cancelled" if cancelled else ("stayed" if stay_date.date() < observation_date else "confirmed")
                gross_revenue = daily_rate * rooms * nights
                net_revenue = 0 if cancelled else gross_revenue
                booking_rows.append(
                    {
                        "booking_id": f"B{booking_id:05d}",
                        "hotel_id": hotel_id,
                        "room_type": room_type,
                        "booking_date": booking_date,
                        "check_in_date": stay_date.date(),
                        "check_out_date": check_out_date,
                        "nights": nights,
                        "rooms": rooms,
                        "gross_room_revenue": gross_revenue,
                        "net_room_revenue": net_revenue,
                        "daily_rate": max(50, daily_rate),
                        "channel": rng.choice(channels),
                        "status": status,
                        "cancelled_at": "",
                    }
                )
                booking_id += 1

    bookings = pd.DataFrame(booking_rows)
    return bookings, inventory, current_prices
