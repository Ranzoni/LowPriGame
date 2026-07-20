from typing import override
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from playwright.sync_api import Browser

from infra.environment_variables import load_config
from providers.sales_scraping_provider import PriceFound, SalesScrapingProvider


class MercadoLivreProvider(SalesScrapingProvider):
    def __init__(self, games: list[str], sentence_transformer: SentenceTransformer):
        config = load_config({
            "url": "MERCADOLIVRE_URL",
        })

        super().__init__(
            provider_name="Mercado Livre",
            games=games,
            url=config["url"],
            search_path="",
            sentence_transformer=sentence_transformer
        )

    @override
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

        page.wait_for_selector('li.ui-search-layout__item', timeout=60000)

        html_content = page.content()

        page.close()
        context.close()

        return BeautifulSoup(html_content, "html.parser")

    @override
    def _scraping_prices(self, html: BeautifulSoup) -> list[PriceFound]:
        prices_found = []
        
        products = self.__extract_products(html)

        for product in products:
            product_name = product["name"]
            product_price = float(product["price"])
            product_store = f"[{self.provider_name}] {product['store']}"
            product_link = product["link"]

            prices_found.append(PriceFound(
                price=product_price,
                link=product_link,
                product_name=product_name,
                store=product_store
            ))

        return prices_found

    def __extract_products(self, html: BeautifulSoup):
        products = html.find_all('li', class_='ui-search-layout__item')

        results = []

        for product in products:
            title_tag = product.find('a', class_='poly-component__title')
            if not title_tag:
                continue

            name = title_tag.text.strip()
            link = title_tag['href']
                
            seller_tag = product.find('span', class_='poly-component__seller')
            seller = seller_tag.text.strip() if seller_tag else self.provider_name

            preco_atual_container = product.find('div', class_='poly-price__current')
            if not preco_atual_container:
                continue

            fraction = preco_atual_container.find('span', class_='andes-money-amount__fraction')
            cents = preco_atual_container.find('span', class_='andes-money-amount__cents')

            texto_fraction = fraction.text.strip().replace('.', '') if fraction else "0"
            texto_cents = cents.text.strip() if cents else "00"
            price = float(f"{texto_fraction}.{texto_cents}")

            results.append({
                "name": name,
                "price": price,
                "link": link,
                "store": seller,
            })

        return results
