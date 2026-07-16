import statistics

from datetime import datetime

from infra.database import GamePriceHistory


def calculate_median(prices_history: list[GamePriceHistory], last_days: int) -> float:
    prices_to_calculate = [
        price_history.price
        for price_history in prices_history if (datetime.now() - price_history.updated_at).days <= last_days
    ]

    if not prices_to_calculate:
        return 0

    return statistics.median(prices_to_calculate)

def calculate_discount(regular_price: float, price_to_compare: float) -> tuple[float, float]:
    discount = regular_price - price_to_compare
    percentual_discount = discount * 100 / regular_price

    return (discount, percentual_discount)
