import json

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from typing import override

from providers.sales_scraping_provider import SalesScrapingProvider, PriceFound
from infra.environment_variables import load_config


class BuscapeProvider(SalesScrapingProvider):
    def __init__(self, games: list[str], sentence_transformer: SentenceTransformer):
        config = load_config({
            "url": "BUSCAPE_URL",
        })

        super().__init__(
            provider_name="Buscapé",
            games=games,
            url=config["url"],
            search_path="search?q=",
            sentence_transformer=sentence_transformer
        )
    
    @override
    def _scraping_prices(self, html: BeautifulSoup) -> list[PriceFound]:
        prices_found = []
        
        products = self.__extract_products(html)

        for product in products:
            product_name = product["name"]
            product_price = float(product["price"])
            product_store = f"[{self.provider_name}] {product["bestOffer"]["merchantName"]}"
            product_link = self.url + product["url"]

            prices_found.append(PriceFound(
                price=product_price,
                link=product_link,
                product_name=product_name,
                store=product_store
            ))

        return prices_found
    
    def __extract_products(self, html: BeautifulSoup):
        script = html.find("script", id="__NEXT_DATA__")

        if not script:
            raise Exception("Produtos não encontrados")

        data = json.loads(script.string)

        products = data["props"]["initialReduxState"]["hits"]["hits"]
        return products
