import requests

from datetime import datetime
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from shared.sales_provider import SalesProvider
from shared.models import GamePrice
from infra.database import Database, Game, Platform, GamePriceHistory


class SalesScrapingProvider(SalesProvider):
    def __init__(self, games: list[str], url: str, sentence_transformer: SentenceTransformer):
        super().__init__(
            games=games,
            url=url,
            sentence_transformer=sentence_transformer,
            search_path="/search?q="
        )

    def get_sale_games(self) -> list[GamePrice]:
        prices: list[GamePrice] = []

        db = Database()
        platforms = db.get_platforms()
        
        for platform in platforms:
            for game_name in self.games:
                db = Database()

                game = db.get_game_by_name(game_name)

                game_search = f"{game.name} de {platform.name}"
                url = f"{self.url}/{self.search_path}{game_search.replace(" ", "+")}+game"
                html = self.__download_html(url)

                price_found = self.get_best_price(
                    game=game,
                    search_term=game_search,
                    platform=platform,
                    html=html
                )

                if price_found:
                    prices.append(price_found)

        return prices
    
    def url_in_blacklist(self, url: str) -> bool:
        db = Database()

        return db.in_blacklist(url)

    def get_best_price(self, game: str, search_term: str, platform: Platform, html: BeautifulSoup) -> GamePrice:
        return []

    def register_highest_price(self, game: Game, platform: Platform, highest_price: float) -> None:
        if not highest_price:
            return

        db = Database()

        game_price_history = db.get_game_history(game.id, platform.id)
        if not game_price_history:
            db.add_price(game.id, platform.id, highest_price)
        elif game_price_history.price != highest_price:
            difference = datetime.now() - game_price_history.updated_at
            if difference.days > 10:
                db.udpate_price(game_price_history.id, highest_price)

        return db.get_game_history(game.id, platform.id)

    def __download_html(self, url: str) -> BeautifulSoup:
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
    
