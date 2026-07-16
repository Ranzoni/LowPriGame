import json

from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from shared.sales_provider import SalesProvider
from shared.sales_scraping_provider import SalesScrapingProvider
from shared.models import GamePrice
from infra.email_sender import send_email
from infra.database import Database
from providers.isthereanydeal_api import IsThereAnyDealProvider
from providers.buscape_scraping import BuscapeProvider


load_dotenv()

def _get_games_list() -> list[str]:
    with open("games.json", encoding="utf-8") as f:
        return json.load(f)["games"]

def _register_games(games: list[str]):
    db = Database()
    
    games_registered = db.get_games()

    games_removed = [register for register in games_registered if register.name not in games]

    games_not_registered = [
        game for game in games
        if game not in {register.name for register in games_registered}
    ]

    db.delete_games([game.id for game in games_removed])
    db.add_games(games_not_registered)

def _get_scraping_providers(games: list[str]) -> list[SalesScrapingProvider]:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    return [
        BuscapeProvider(games, model)
    ]

def _get_providers(games: list[str]) -> list[SalesProvider]:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    return [
        BuscapeProvider(games, model),
        IsThereAnyDealProvider(games, model)
    ]

def _register_prices(games: list[str]):
    providers = _get_scraping_providers(games)
    for provider in providers:
        provider.register_prices()

def _format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"

def _format_percentual(value: float) -> str:
    formatted = f"{value:,.2f}"
    return f"{formatted}%"

def _format_game_sale(game_sale: GamePrice) -> str:
    platforms = ", ".join(game_sale.platforms) if game_sale.platforms else "-"
    voucher = game_sale.voucher or "-"

    return "\n".join(
        [
            f"Jogo: {game_sale.name}",
            f"Preço: {_format_currency(game_sale.price)}",
            f"Preço comum: {_format_currency(game_sale.price_info.regular_price)}",
            f"Desconto: {_format_currency(game_sale.price_info.discont)}",
            f"Desconto (%): {_format_percentual(game_sale.price_info.discount_percentage)}",
            f"Cupom: {voucher}",
            f"Loja: {game_sale.store}",
            f"Link: {game_sale.link}",
            f"Plataformas: {platforms}",
        ]
    )

def _build_email_body(sales: list[GamePrice]) -> str:
    if not sales:
        return "Nenhuma promoção foi encontrada no momento."

    sections = ["Promoções encontradas:", ""]

    for index, game_sale in enumerate(sales, start=1):
        sections.append(f"#{index}")
        sections.append(_format_game_sale(game_sale))
        sections.append("-" * 51)

    return "\n".join(sections).rstrip()

def main() -> None:
    games = _get_games_list()
    providers = _get_providers(games)

    _register_games(games)
    _register_prices(games)

    games_price = []

    for provider in providers:
        games_price.extend(provider.get_sales_games())

    if not games_price:
        return

    email_body = _build_email_body(games_price)

    success = send_email("Promoções encontradas!", email_body)

    if not success:
        raise SystemExit("Falha ao enviar e-mail")

if __name__ == "__main__":
    main()
