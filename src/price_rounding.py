import math


PRICE_ROUNDING_STRATEGIES = {
    "chinese_lucky": {
        "zh": "中国酒店吉祥尾数（6/8/9）",
        "en": "Chinese hotel-friendly endings (6/8/9)",
        "de": "China-freundliche Preisendungen (6/8/9)",
        "fr": "Terminaisons favorables Chine (6/8/9)",
    },
    "nearest_5": {
        "zh": "按 5 取整",
        "en": "Round to nearest 5",
        "de": "Auf nächste 5 runden",
        "fr": "Arrondir au multiple de 5",
    },
    "nearest_1": {
        "zh": "按 1 取整",
        "en": "Round to nearest 1",
        "de": "Auf nächste 1 runden",
        "fr": "Arrondir à l’unité",
    },
}


LUCKY_ENDINGS = (6, 8, 9)
ENDING_BONUS = {8: 0.85, 6: 0.45, 9: 0.35}


def _candidate_prices_with_endings(price: float, endings=LUCKY_ENDINGS) -> list[int]:
    base_ten = int(math.floor(price / 10.0) * 10)
    candidates = []
    for offset in range(-40, 51, 10):
        decade = base_ten + offset
        for ending in endings:
            candidate = decade + ending
            if candidate > 0:
                candidates.append(candidate)
    return sorted(set(candidates))


def round_to_price_ending(price: float, strategy: str = "chinese_lucky") -> float:
    """Round a raw recommendation to a market-friendly displayed price."""
    if price is None or math.isnan(float(price)):
        return 0.0

    price = max(float(price), 1.0)

    if strategy == "nearest_1":
        return float(round(price))

    if strategy == "nearest_5":
        return float(round(price / 5.0) * 5)

    candidates = _candidate_prices_with_endings(price)
    if not candidates:
        return float(round(price))

    def score(candidate: int) -> tuple[float, int]:
        ending = candidate % 10
        return (abs(candidate - price) - ENDING_BONUS.get(ending, 0), candidate)

    return float(min(candidates, key=score))
