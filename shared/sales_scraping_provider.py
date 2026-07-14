import requests

from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from shared.sales_provider import SalesProvider
from shared.models import GamePrice
from infra.environment_variables import load_config
from infra.database import Database


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

        config = load_config({
            "terms_to_add": "TERMS_TO_ADD"
        })

        terms_to_add = config["terms_to_add"].split(",")
        
        for term_to_add in terms_to_add:
            for game in self.games:
                game_search = f"{game} de {term_to_add}"
                url = f"{self.get_url()}/{self.search_path}{game_search.replace(" ", "+")}+game"
                html = self.__download_html(url)

                prices_found = self.get_prices(game_search, html)
                for price in prices_found:
                    prices.append(price)

        return prices
    
    def url_in_blacklist(self, url: str) -> bool:
        db = Database()

        return db.in_blacklist(url)

    def get_prices(self, _: str, __: BeautifulSoup) -> list[GamePrice]:
        return []

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