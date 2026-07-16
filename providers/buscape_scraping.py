import json

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from typing import override

from shared.sales_scraping_provider import SalesScrapingProvider, PriceFound
from infra.environment_variables import load_config


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
    
    @override
    def _scraping_prices(self, html: BeautifulSoup) -> list[PriceFound]:
        prices_found = []
        
        products = self.__extract_products(html)

        for product in products:
            print(f"Jogo encontrado: {product["name"]}")
            print(f"Preço: {float(product["price"])}")
            print(f"Loja: {product["bestOffer"]["merchantName"]}")
            print("")

            prices_found.append(PriceFound(
                price=float(product["price"]),
                link=self.url + product["url"],
                product_name=product["name"],
                store=product["bestOffer"]["merchantName"]
            ))

        return prices_found
    
    def __extract_products(self, html: BeautifulSoup):
        script = html.find("script", id="__NEXT_DATA__")

        if not script:
            raise Exception("Produtos não encontrados")

        data = json.loads(script.string)

        products = data["props"]["initialReduxState"]["hits"]["hits"]
        return products
