from bs4 import BeautifulSoup

from environment_variables import load_config
from sales_provider import SalesProvider
from web_scraping import download_html
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
            html = download_html(url)

            prices_found = self._get_prices(html)
            for price in prices_found:
                prices.append(price)

        return prices

    def _get_prices(self, _: BeautifulSoup) -> list[GamePrice]:
        return []
