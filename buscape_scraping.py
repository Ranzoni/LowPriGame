import json

from bs4 import BeautifulSoup

from sales_scraping_provider import SalesScrapingProvider
from models import GamePrice


class Buscape_Provider(SalesScrapingProvider):
    def __init__(self, games: list[str]):
        super().__init__(
            games,
            env_variables={
                "url": "BUSCAPE_URL",
            }
        )
    
    def _get_prices(self, html: BeautifulSoup) -> list[GamePrice]:
        prices: list[GamePrice] = []

        script = html.find("script", id="__NEXT_DATA__")

        if not script:
            raise Exception("Produtos não encontrados")

        data = json.loads(script.string)

        products = data["props"]["initialReduxState"]["hits"]["hits"]

        for product in products:
            game_price = GamePrice(
                name=product["name"],
                price=float(product["price"]),
                regular_price=0,
                store=product["bestOffer"]["merchantName"],
                link=self.url + product["url"],
            )

            prices.append(game_price)

        return prices
