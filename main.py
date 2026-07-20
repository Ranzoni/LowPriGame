import argparse
import logging

from dotenv import load_dotenv

from services.games_service import get_games_list, register_games
from services.email_service import build_sales_email_body
from providers.bucket_providers import get_providers, get_scraping_providers
from infra.email_sender import send_email


load_dotenv()


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


logger = logging.getLogger(__name__)

def _register_prices(games: list[str]) -> None:
    logger.info("Iniciando atualização do histórico de preços para %s jogos.", len(games))
    providers = get_scraping_providers(games)

    for provider in providers:
        logger.info("Atualizando histórico com o provedor %s.", provider.provider_name)

        try:
            provider.register_prices()
        except Exception:
            logger.exception(
                "Falha ao atualizar histórico de preços com o provedor %s.",
                provider.provider_name,
            )

def _search_sales(games: list[str]) -> None:
    games_price = []

    logger.info("Iniciando busca de promoções para %s jogos.", len(games))
    providers = get_providers(games)

    for provider in providers:
        provider_name = provider.provider_name or provider.__class__.__name__
        logger.info("Consultando promoções com o provedor %s.", provider_name)

        try:
            games_price.extend(provider.get_sales_games())
        except Exception:
            logger.exception(
                "Falha ao consultar promoções com o provedor %s.",
                provider_name,
            )

    if not games_price:
        logger.info("Nenhuma promoção encontrada.")
        return

    logger.info("Foram encontradas %s promoções. Montando e-mail.", len(games_price))
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

    _configure_logging()
    logger.info("Aplicação iniciada com a ação %s.", args.action)

    games = get_games_list()
    logger.info("Lista de jogos carregada com %s itens.", len(games))
    register_games(games)

    match args.action:
        case "search-sales":
            _search_sales(games)

        case "update-prices-history":
            _register_prices(games)

if __name__ == "__main__":
    main()
