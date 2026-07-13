import requests

from bs4 import BeautifulSoup

from environment_variables import load_config
from sales_provider import SalesProvider
from models import GamePrice


class SalesScrapingProvider(SalesProvider):
    def __init__(self, games: list[str], env_variables: dict[str, str]):
        config = load_config(env_variables)

        super().__init__(
            games=games,
            url=config["url"],
            search_path="/search?q="
        )

    def get_sale_games(self) -> list[GamePrice]:
        prices: list[GamePrice] = []
        
        for game in self.games:
            url = f"{self.url}/{self.search_path}{game.replace(" ", "+")}+game"
            html = self._download_html(url)

            prices_found = self._get_prices(game, html)
            for price in prices_found:
                prices.append(price)

        return prices

    def _get_prices(self, _: str, __: BeautifulSoup) -> list[GamePrice]:
        return []

    def _download_html(url: str) -> BeautifulSoup:
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