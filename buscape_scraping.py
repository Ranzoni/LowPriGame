import json

from bs4 import BeautifulSoup

from sales_scraping_provider import SalesScrapingProvider
from models import GamePrice


class BuscapeProvider(SalesScrapingProvider):
    def __init__(self, games: list[str]):
        super().__init__(
            games,
            env_variables={
                "url": "BUSCAPE_URL",
            }
        )
    
    def _get_prices(self, game: str, html: BeautifulSoup) -> list[GamePrice]:
        prices: list[GamePrice] = []

        script = html.find("script", id="__NEXT_DATA__")

        if not script:
            raise Exception("Produtos não encontrados")

        data = json.loads(script.string)

        products = data["props"]["initialReduxState"]["hits"]["hits"]

        for product in products:
            if not self._is_game_looking_for(game, product["name"]):
                continue

            product_url = self.url + product["url"]

            game_price = GamePrice(
                name=product["name"] + " - " + product["objectId"],
                price=float(product["price"]),
                regular_price=float(product["price"]),
                store=product["bestOffer"]["merchantName"],
                link=product_url,
            )

            prices.append(game_price)

        return prices
