from decimal import Decimal


class GamePrice:
    def __init__(
            self,
            name: str,
            price: Decimal,
            regular_price: Decimal,
            store: str,
            link: str = None,
            voucher: str = None,
            platforms: list[str] = None
        ):
        self.name = name
        self.price = price
        self.regular_price = regular_price
        self.voucher = voucher
        self.store = store
        self.link = link
        self.platforms = platforms