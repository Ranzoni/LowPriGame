import re

from typing import override
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from playwright.sync_api import Browser, sync_playwright

from infra.database import Database, Platform
from infra.environment_variables import load_config
from providers.sales_provider import SalesProvider
from shared.enums import PlatformType
from shared.models import GamePrice, PriceInfo


class PSPricesProvider(SalesProvider):
    def __init__(self, games: list[str], sentence_transformer: SentenceTransformer):
        config = load_config({
            "url": "PSDPRICES_URL"
        })

        super().__init__(
            games=games,
            url=config["url"],
            sentence_transformer=sentence_transformer
        )

    @override
    def get_sales_games(self):
        prices = []
        
        db = Database()
        platforms = db.get_platforms()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True
            )

            for platform in platforms:
                for game in self.games:
                    prices.extend(self.__get_game_prices(
                        game=game,
                        platform=platform,
                        browser=browser
                    ))

            browser.close()

        return prices

    def __get_game_prices(self, game: str, platform: Platform, browser: Browser) -> list[GamePrice]:
        prices = []

        products = self.__extract_products(
            game=game,
            platform_type=platform.type,
            browser=browser
        )

        for product in products:
            product_name = product["name"]

            if not self.is_game_looking_for(game, product_name, 0.89):
                continue

            product_price = float(product["current_price"])
            product_regular_price = float(product["old_price"])
            discount = product_regular_price - product_price

            game_price = GamePrice(
                name=product_name,
                price=product_price,
                price_info=PriceInfo(
                    regular_price=product_regular_price,
                    discont=discount,
                    discount_percentage=float(product["discount"])
                ),
                store=self.__get_platform_store(platform.type),
                platforms=[self.__get_platform_type_text(platform.type)],
                link=product["url"]
            )

            prices.append(game_price)

        return prices

    def __get_platform_store(self, platform_type: PlatformType) -> str:
        match platform_type:
            case PlatformType.PS5:
                return "PSN"
            case PlatformType.SWITCH:
                return "Nintendo Online"

    def __get_platform_type_text(self, platform_type: PlatformType) -> str:
        match platform_type:
            case PlatformType.PS5:
                return "PS5"
            case PlatformType.SWITCH:
                return "Switch"
        
    def __download_html(self, game: str, platform_type: PlatformType, browser: Browser) -> BeautifulSoup:
        platform = self.__get_platform_type_text(platform_type)
        url = f"{self.url}/region-br/games/?q={game.replace(" ", "+")}&platform={platform}&discount_min=1&show=games"

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
    
    def __extract_products(self, game: str, platform_type: PlatformType, browser: Browser) -> list:
        html = self.__download_html(
            game=game,
            platform_type=platform_type,
            browser=browser
        )
        
        products = []

        cards = html.select("div[data-test-id^='game-card-']")

        for card in cards:

            container = card.find_parent("div", class_="game-fragment")

            if container is None:
                container = card.parent.parent

            link_dom = next(
                (
                    a for a in container.find_all("a", href=True)
                    if a["href"].startswith("/region-")
                ),
                None,
            )

            link = None
            if link_dom:
                link = self.url + link_dom["href"]

            name = container.find("h3").get_text(" ", strip=True)

            discount = container.select_one(
                "[data-test-id='discount-badge']"
            )

            current_price = container.select_one(
                "span.text-xl"
            )

            old_price = container.select_one(
                ".old-price-strike"
            )

            discount_text = discount.get_text(strip=True) if discount else None
            current_price_text = current_price.get_text(" ", strip=True) if current_price else None
            old_price_text = old_price.get_text(" ", strip=True) if old_price else None

            discount_value = (
                re.sub(r"[^\d]", "", discount_text)
                if discount_text
                else None
            )

            current_price_value = (
                re.sub(r"[^\d,]", "", current_price_text).replace(",", ".")
                if current_price_text
                else None
            )

            old_price_value = (
                re.sub(r"[^\d,]", "", old_price_text).replace(",", ".")
                if old_price_text
                else None
            )

            products.append({
                "name": name,
                "url": link,
                "discount": discount_value,
                "current_price": current_price_value,
                "old_price": old_price_value,
            })

        return products
