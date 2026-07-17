from sentence_transformers import SentenceTransformer

from providers.sales_provider import SalesProvider
from providers.sales_scraping_provider import SalesScrapingProvider
from providers.isthereanydeal_api import IsThereAnyDealProvider
from providers.buscape_scraping import BuscapeProvider


def get_scraping_providers(games: list[str]) -> list[SalesScrapingProvider]:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    return [
        BuscapeProvider(games, model)
    ]

def get_providers(games: list[str]) -> list[SalesProvider]:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    return [
        BuscapeProvider(games, model),
        IsThereAnyDealProvider(games, model)
    ]
