import requests

from datetime import datetime
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

from shared.sales_provider import SalesProvider
from shared.models import GamePrice, PriceInfo
from shared.functions import calculate_median, calculate_discount
from infra.database import Database, Game, Platform


class PriceFound(BaseModel):
    product_name: str
    price: float
    store: str
    link: str

class SalesScrapingProvider(SalesProvider):
    def __init__(self, games: list[str], url: str, sentence_transformer: SentenceTransformer):
        super().__init__(
            games=games,
            url=url,
            sentence_transformer=sentence_transformer,
            search_path="/search?q="
        )

    def register_prices(self) -> None:
        db = Database()
        platforms = db.get_platforms()
        
        for platform in platforms:
            for game_name in self.games:
                game = db.get_game_by_name(game=game_name)

                if not self.__should_update_price_history(game=game, platform=platform):
                    continue

                game_search_term = self.__get_search_game_term(game=game, platform=platform)
                html = self.__download_html(game_search=game_search_term)

                prices_found = self._scraping_prices(html=html)

                products_match_game = [
                    price
                    for price in prices_found if self.__product_match_game(
                        search_term=game_search_term,
                        product_name=price.product_name,
                        product_url=price.link
                    )
                ]

                data = [
                    (game.id, platform.id, price_found.price)
                    for price_found in products_match_game
                ]
                db.add_prices(data)

    def get_sales_games(self) -> list[GamePrice]:
        prices = []

        db = Database()
        platforms = db.get_platforms()
        
        for platform in platforms:
            for game_name in self.games:
                game = db.get_game_by_name(game=game_name)
                regular_price = self.__get_regular_price(game, platform)
                game_search_term = self.__get_search_game_term(game=game, platform=platform)

                html = self.__download_html(game_search=game_search_term)
                prices_found = self._scraping_prices(html)

                discount_found = None
                for price_found in prices_found:
                    product_match_game = self.__product_match_game(
                        search_term=game_search_term,
                        product_name=price_found.product_name,
                        product_url=price_found.link
                    )

                    if not product_match_game:
                        continue

                    if price_found.price < regular_price and (not discount_found or discount_found.price > price_found.price):
                        discount_found = self.__handle_discount(
                            regular_price=regular_price,
                            price_found=price_found
                        )

                if discount_found:
                    prices.append(discount_found)

        return prices

    def _scraping_prices(self, _: BeautifulSoup) -> list[PriceFound]:
        pass

    def __should_update_price_history(self, game: Game, platform: Platform) -> bool:
        db = Database()

        game_price_history = db.get_last_game_history(game.id, platform.id)
        if not game_price_history:
            return True
        
        difference = datetime.now() - game_price_history.updated_at
        return difference.days < 10

    def __get_search_game_term(self, game: Game, platform: Platform) -> str:
        return f"{game.name} de {platform.name}"

    def __download_html(self, game_search: str) -> BeautifulSoup:
        url = f"{self.url}/{self.search_path}{game_search.replace(" ", "+")}+game"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError("Não foi possível baixar HTML do site.")

        return BeautifulSoup(response.text, "lxml")

    def __product_match_game(self, search_term: str, product_name: str, product_url: str) -> bool:
        if not self.is_game_looking_for(search_term, product_name):
            return False
            
        if self.has_terms_to_ignore(value=product_name):
            return False

        db = Database()
        if db.in_blacklist(product_url):
            return False

        return True
    
    def __get_regular_price(self, game: Game, platform: Platform) -> float:
        db = Database()

        game_prices_history = db.get_game_prices_history(
            game_id=game.id,
            platform_id=platform.id
        )

        return calculate_median(prices_history=game_prices_history, last_days=90)

    def __handle_discount(self, regular_price: float, price_found: PriceFound) -> GamePrice:
        discount, discount_percentage = calculate_discount(
            regular_price=regular_price,
            price_to_compare=price_found.price
        )

        return GamePrice(
            name=price_found.product_name,
            price=price_found.price,
            price_info=PriceInfo(
                regular_price=regular_price,
                discont=discount,
                discount_percentage=discount_percentage
            ),
            store=price_found.store,
            link=price_found.link,
        )
