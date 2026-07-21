from bs4 import BeautifulSoup
import logging
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
    logger = logging.getLogger(__name__)

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
        self.logger.info("[%s] Iniciando registro de historico de precos.", self.provider_name)

        db = Database()
        platforms = db.get_platforms()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True
            )

            try:
                for platform in platforms:
                    self.logger.info("[%s] Iterando plataforma %s para registro.", self.provider_name, platform.name)

                    for game_name in self.games:
                        try:
                            self.__register_game_prices(
                                db=db,
                                game_name=game_name,
                                platform=platform,
                                browser=browser,
                            )
                        except Exception:
                            self.logger.exception(
                                "[%s] Falha ao registrar historico do jogo '%s' na plataforma %s.",
                                self.provider_name,
                                game_name,
                                platform.name,
                            )
            finally:
                browser.close()

        self.logger.info("[%s] Registro de historico finalizado.", self.provider_name)

    def get_sales_games(self) -> list[GamePrice]:
        prices = []

        self.logger.info("[%s] Iniciando busca de promocoes.", self.provider_name)

        db = Database()
        platforms = db.get_platforms()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True
            )

            try:
                for platform in platforms:
                    self.logger.info("[%s] Iterando plataforma %s na busca de promocoes.", self.provider_name, platform.name)

                    for game_name in self.games:
                        try:
                            discount_found = self.__search_discount_for_game(
                                db=db,
                                game_name=game_name,
                                platform=platform,
                                browser=browser,
                            )

                            if discount_found:
                                prices.append(discount_found)
                        except Exception:
                            self.logger.exception(
                                "[%s] Falha ao buscar promocao do jogo '%s' na plataforma %s.",
                                self.provider_name,
                                game_name,
                                platform.name,
                            )
            finally:
                browser.close()

        self.logger.info("[%s] Busca de promocoes finalizada com %s promocoes.", self.provider_name, len(prices))

        return prices

    def _scraping_prices(self, _: BeautifulSoup) -> list[PriceFound]:
        pass

    def __get_search_game_term(self, game: Game, platform: Platform) -> str:
        return f"{game.name} de {platform.name}"

    def _download_html(self, game_search: str, browser: Browser) -> BeautifulSoup:
        url = f"{self.url}/{self.search_path}{game_search.replace(" ", "+")}+game"
        self.logger.info("[%s] Baixando HTML para a busca '%s'.", self.provider_name, game_search)

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

    def __register_game_prices(self, db: Database, game_name: str, platform: Platform, browser: Browser) -> None:
        game = db.get_game_by_name(game=game_name)

        if not game:
            self.logger.warning(
                "[%s] Jogo '%s' nao encontrado no banco para registro de historico.",
                self.provider_name,
                game_name,
            )
            return

        game_search_term = self.__get_search_game_term(game=game, platform=platform)
        self.logger.info(
            "[%s] Registrando historico para plataforma=%s jogo='%s' busca='%s'.",
            self.provider_name,
            platform.name,
            game_name,
            game_search_term,
        )

        html = self._download_html(game_search=game_search_term, browser=browser)
        prices_found = self._scraping_prices(html)
        terms_to_ignore = self.get_terms_to_ignore_for_game(game_id=game.id, db=db)
        self.logger.info(
            "[%s] %s resultados brutos encontrados para plataforma=%s jogo='%s'.",
            self.provider_name,
            len(prices_found),
            platform.name,
            game_name,
        )

        products_match_game = []
        for price_found in prices_found:
            self.__log_price_found(platform.name, game_name, price_found)

            if self.__product_match_game(
                search_term=game_search_term,
                product_name=price_found.product_name,
                product_url=price_found.link,
                terms_to_ignore=terms_to_ignore,
                db=db,
            ):
                products_match_game.append(price_found)

        data = [
            (game.id, platform.id, price_found.price)
            for price_found in products_match_game
        ]
        db.add_prices(data)
        self.logger.info(
            "[%s] %s resultados validos registrados para plataforma=%s jogo='%s'.",
            self.provider_name,
            len(products_match_game),
            platform.name,
            game_name,
        )

    def __search_discount_for_game(self, db: Database, game_name: str, platform: Platform, browser: Browser) -> GamePrice | None:
        game = db.get_game_by_name(game=game_name)

        if not game:
            self.logger.warning(
                "[%s] Jogo '%s' nao encontrado no banco durante a busca de promocoes.",
                self.provider_name,
                game_name,
            )
            return None

        regular_price = self.__get_regular_price(game, platform)
        if regular_price <= 0:
            self.logger.warning(
                "[%s] Historico insuficiente para comparar promocao do jogo '%s' na plataforma %s.",
                self.provider_name,
                game_name,
                platform.name,
            )
            return None

        game_search_term = self.__get_search_game_term(game=game, platform=platform)
        self.logger.info(
            "[%s] Buscando promocao para plataforma=%s jogo='%s' busca='%s' preco_base=%.2f.",
            self.provider_name,
            platform.name,
            game_name,
            game_search_term,
            regular_price,
        )

        html = self._download_html(game_search=game_search_term, browser=browser)
        prices_found = self._scraping_prices(html)
        terms_to_ignore = self.get_terms_to_ignore_for_game(game_id=game.id, db=db)
        self.logger.info(
            "[%s] %s resultados brutos encontrados para plataforma=%s jogo='%s'.",
            self.provider_name,
            len(prices_found),
            platform.name,
            game_name,
        )

        discount_found = None
        for price_found in prices_found:
            self.__log_price_found(platform.name, game_name, price_found)

            product_match_game = self.__product_match_game(
                search_term=game_search_term,
                product_name=price_found.product_name,
                product_url=price_found.link,
                terms_to_ignore=terms_to_ignore,
                db=db,
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
            self.logger.info(
                "[%s] Promocao encontrada para plataforma=%s jogo='%s': preco=%.2f loja='%s'.",
                self.provider_name,
                platform.name,
                game_name,
                discount_found.price,
                discount_found.store,
            )
        else:
            self.logger.info(
                "[%s] Nenhuma promocao valida para plataforma=%s jogo='%s'.",
                self.provider_name,
                platform.name,
                game_name,
            )

        return discount_found

    def __log_price_found(self, platform_name: str, game_name: str, price_found: PriceFound) -> None:
        self.logger.info(
            "[%s] Resultado encontrado: plataforma=%s jogo='%s' produto='%s' preco=%.2f loja='%s' link='%s'.",
            self.provider_name,
            platform_name,
            game_name,
            price_found.product_name,
            price_found.price,
            price_found.store,
            price_found.link,
        )

    def __product_match_game(self, search_term: str, product_name: str, product_url: str, terms_to_ignore: list[str], db: Database) -> bool:
        if not self.is_game_looking_for(search_term, product_name):
            return False
            
        if self.has_terms_to_ignore(value=product_name, terms_to_ignore=terms_to_ignore):
            return False

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
