from sentence_transformers import SentenceTransformer

from providers.kabum_scraping import KabumProvider
from providers.psprices_search import PSPricesProvider
from providers.sales_provider import SalesProvider
from providers.sales_scraping_provider import SalesScrapingProvider
from providers.isthereanydeal_api import IsThereAnyDealProvider
from providers.buscape_scraping import BuscapeProvider


def get_scraping_providers(games: list[str], sentence_transformer: SentenceTransformer = None) -> list[SalesScrapingProvider]:
    model = sentence_transformer if sentence_transformer else SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    return [
        BuscapeProvider(games, model),
        KabumProvider(games, model)
    ]

def get_providers(games: list[str]) -> list[SalesProvider]:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    return [
        IsThereAnyDealProvider(games, model),
        PSPricesProvider(games, model),
        *get_scraping_providers(games, model)
    ]
