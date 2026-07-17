import json

from typing import override
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from infra.environment_variables import load_config
from providers.sales_scraping_provider import PriceFound, SalesScrapingProvider


class KabumProvider(SalesScrapingProvider):
    def __init__(self, games: list[str], sentence_transformer: SentenceTransformer):
        config = load_config({
            "url": "KABUM_URL",
        })

        super().__init__(
            games=games,
            url=config["url"],
            search_path="busca/",
            sentence_transformer=sentence_transformer
        )

    @override
    def _scraping_prices(self, html: BeautifulSoup) -> list[PriceFound]:
        prices_found = []

        products = self.__extract_products(html)

        for product in products:
            product_name = product["name"]
            product_price = float(product["priceWithDiscount"])
            product_store = "Kabum!"
            product_link = f"{self.url}/produto/{product['code']}"

            print(f"Jogo encontrado: {product_name}")
            print(f"Preço: {product_price}")
            print(f"Loja: {product_store}")
            print(f"Link: {product_link}")
            print("")

            prices_found.append(PriceFound(
                price=product_price,
                link=product_link,
                product_name=product_name,
                store=product_store
            ))

        return prices_found
    
    def __extract_products(self, html: BeautifulSoup):
        script = html.find("script", id="__NEXT_DATA__")

        data = json.loads(script.string)

        return data["props"]["pageProps"]["data"]["catalogServer"]["data"]