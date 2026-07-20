from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from playwright.sync_api import Browser, sync_playwright

from providers.sales_provider import SalesProvider
from shared.models import GamePrice, PriceInfo
from shared.functions import calculate_median, calculate_discount
from infra.database import Database, Game, Platform


class PriceFound(BaseModel):
    product_name: str
    price: float
    store: str
    link: str

class SalesScrapingProvider(SalesProvider):
    def __init__(self, provider_name: str, games: list[str], url: str, search_path: str, sentence_transformer: SentenceTransformer):
        self.__search_path = search_path

        super().__init__(
            provider_name=provider_name,
            games=games,
            url=url,
            sentence_transformer=sentence_transformer
        )

    @property
    def search_path(self) -> str:
        return self.__search_path

    def register_prices(self) -> None:
        print("---------------------------------------------------")
        print(self.provider_name)
        print("")

        try:
            db = Database()
            platforms = db.get_platforms()
            
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True
                )

                for platform in platforms:
                    for game_name in self.games:
                        game = db.get_game_by_name(game=game_name)

                        game_search_term = self.__get_search_game_term(game=game, platform=platform)
                        html = self._download_html(game_search=game_search_term, browser=browser)

                        prices_found = self._scraping_prices(html)

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

                browser.close()
        except Exception as e:
            print(f"Não foi possível registrar os preços: {e}")

    def get_sales_games(self) -> list[GamePrice]:
        prices = []

        print("---------------------------------------------------")
        print(self.provider_name)
        print("")

        try:
            db = Database()
            platforms = db.get_platforms()
            
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True
                )

                for platform in platforms:
                    for game_name in self.games:
                        game = db.get_game_by_name(game=game_name)
                        regular_price = self.__get_regular_price(game, platform)

                        game_search_term = self.__get_search_game_term(game=game, platform=platform)

                        html = self._download_html(game_search=game_search_term, browser=browser)
                        prices_found = self._scraping_prices(html)

                        discount_found = None
                        for price_found in prices_found:
                            print(f"Jogo encontrado: {price_found.product_name}")
                            print(f"Preço: {price_found.price}")
                            print(f"Loja: {price_found.store}")
                            print(f"Link: {price_found.link}")
                            print("")

                            product_match_game = self.__product_match_game(
                                search_term=game_search_term,
                                product_name=price_found.product_name,
                                product_url=price_found.link
                            )

                            if not product_match_game:
                                continue

                            if price_found.price < regular_price and (not discount_found or discount_found.price > price_found.price):
                                discount_found = self.__handle_discount(
                                    game_name=game_name,
                                    platform=platform,
                                    regular_price=regular_price,
                                    price_found=price_found
                                )

                        if discount_found:
                            prices.append(discount_found)

                browser.close()
        except Exception as e:
            print(f"Não foi possível buscar as promoções: {e}")

        return prices

    def _scraping_prices(self, _: BeautifulSoup) -> list[PriceFound]:
        pass

    def __get_search_game_term(self, game: Game, platform: Platform) -> str:
        return f"{game.name} de {platform.name}"

    def _download_html(self, game_search: str, browser: Browser) -> BeautifulSoup:
        url = f"{self.url}/{self.search_path}{game_search.replace(" ", "+")}+game"

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
        )

        html_content = page.content()

        page.close()
        context.close()

        return BeautifulSoup(html_content, "html.parser")

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

    def __handle_discount(self, game_name: str, platform: Platform, regular_price: float, price_found: PriceFound) -> GamePrice:
        discount, discount_percentage = calculate_discount(
            regular_price=regular_price,
            price_to_compare=price_found.price
        )

        return GamePrice(
            name=game_name,
            price=price_found.price,
            price_info=PriceInfo(
                regular_price=regular_price,
                discont=discount,
                discount_percentage=discount_percentage
            ),
            store=price_found.store,
            link=price_found.link,
            platforms=[platform.name]
        )
