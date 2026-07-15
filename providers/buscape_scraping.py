import json

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from shared.sales_scraping_provider import SalesScrapingProvider
from shared.models import GamePrice
from infra.environment_variables import load_config
from infra.database import Game, Platform, Database


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
    
    def get_best_price(self, game: Game, search_term: str, platform: Platform, html: BeautifulSoup) -> GamePrice:
        products = self.__extract_products(html)

        highest_price = 0
        sale_found = None

        for current_product in products:
            current_product_name = current_product["name"]

            if not self._is_game_looking_for(search_term, current_product_name):
                continue
            
            if self.has_terms_to_ignore(value=current_product_name):
                continue

            product_url = self.url + current_product["url"]

            if self.url_in_blacklist(product_url):
                continue

            current_product_price = float(current_product["price"])
            if current_product_price > highest_price:
                highest_price = current_product_price

            print(f"Jogo encontrado: {current_product_name}")
            print(f"Preço: {current_product_price}")
            print(f"Loja: {current_product["bestOffer"]["merchantName"]}")
            print("")

            if not sale_found or (sale_found.price > current_product_price):
                sale_found = GamePrice(
                    name=current_product_name,
                    price=current_product_price,
                    regular_price=0,
                    store=current_product["bestOffer"]["merchantName"],
                    link=product_url,
                )

        self.register_highest_price(game, platform, highest_price)

        if not sale_found:
            return None
        
        regular_price = self.__get_regular_price(game, platform)
        if regular_price <= sale_found.price:
            sale_found = None
        else:
            sale_found.regular_price = regular_price

        return sale_found
    
    def __extract_products(self, html: BeautifulSoup):
        script = html.find("script", id="__NEXT_DATA__")

        if not script:
            raise Exception("Produtos não encontrados")

        data = json.loads(script.string)

        products = data["props"]["initialReduxState"]["hits"]["hits"]
        return products
    
    def __get_regular_price(self, game: Game, platform: Platform) -> float:
        db = Database()

        game_history = db.get_game_history(game.id, platform.id)
        if not game_history:
            return 0
        
        return game_history.price
