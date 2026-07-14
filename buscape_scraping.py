import json

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from sales_scraping_provider import SalesScrapingProvider
from models import GamePrice
from environment_variables import load_config


class BuscapeProvider(SalesScrapingProvider):
    def __init__(self, games: list[str], sentence_transformer: SentenceTransformer):
        config = load_config({
            "url": "BUSCAPE_URL",
        })

        super().__init__(
            games=games,
            url=config["url"],
            sentence_transformer=sentence_transformer
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
            
            invalid_terms_found = [term_to_ignore for term_to_ignore in self.get_terms_to_ignore() if term_to_ignore.lower() in str(product["name"]).lower()]
            if invalid_terms_found:
                continue

            product_url = self.get_url() + product["url"]

            game_price = GamePrice(
                name=product["name"],
                price=float(product["price"]),
                regular_price=0,
                store=product["bestOffer"]["merchantName"],
                link=product_url,
            )

            prices.append(game_price)

        return prices
