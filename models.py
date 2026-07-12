from decimal import Decimal


class GamePrice:
    name: str
    price: Decimal
    regular_price: Decimal
    voucher: str | None
    store: str
    os_list: list[str] | None
    platforms: list[str] | None

    def __init__(
            self,
            name: str,
            price: Decimal,
            regular_price: Decimal,
            store: str,
            voucher: str = None,
            os_list: list[str] = None,
            platforms: list[str] = None
        ):
        self.name = name
        self.price = price
        self.regular_price = regular_price
        self.voucher = voucher
        self.store = store
        self.os_list = os_list
        self.platforms = platforms