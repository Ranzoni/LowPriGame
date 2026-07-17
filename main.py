import argparse

from dotenv import load_dotenv

from services.games_service import get_games_list, register_games
from services.email_service import build_sales_email_body
from providers.bucket_providers import get_providers, get_scraping_providers
from infra.email_sender import send_email


load_dotenv()

def _register_prices(games: list[str]) -> None:
    providers = get_scraping_providers(games)
    for provider in providers:
        provider.register_prices()

def _search_sales(games: list[str]) -> None:
    games_price = []

    providers = get_providers(games)

    for provider in providers:
        games_price.extend(provider.get_sales_games())

    if not games_price:
        return

    email_body = build_sales_email_body(games_price)

    success = send_email("Promoções encontradas!", email_body)

    if not success:
        raise SystemExit("Falha ao enviar e-mail")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=["search-sales", "update-prices-history"]
    )

    args = parser.parse_args()

    games = get_games_list()
    register_games(games)

    match args.action:
        case "search-sales":
            _search_sales(games)

        case "update-prices-history":
            _register_prices(games)

if __name__ == "__main__":
    main()
