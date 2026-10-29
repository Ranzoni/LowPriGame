from pydantic import BaseModel
from typing import Optional


class PriceInfo(BaseModel):
    regular_price: float
    discont: float
    discount_percentage: float

class GamePrice(BaseModel):
    name: str
    price: float
    price_info: PriceInfo
    store: str
    link: Optional[str] = None
    voucher: Optional[str] = None
    platforms: Optional[list[str]] = None


class GameToMonitor(BaseModel):
    """A game and, optionally, the platforms on which it should be monitored."""

    name: str
    platforms: list[str] | None = None
