from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from shared.models import GamePrice
from infra.environment_variables import load_config


class SalesProvider:
    def __init__(self, games: list[str], url: str, sentence_transformer: SentenceTransformer, timeout: int = None):
        self.__games = games
        self.__url = url
        self.__sentence_transformer = sentence_transformer
        self.__timeout = timeout

        config = load_config({
            "terms_to_ignore": "TERMS_TO_IGNORE"
        })

        self.__terms_to_ignore: list[str] = config["terms_to_ignore"].split(",")

    def get_sales_games(self) -> list[GamePrice]:
        return []
    
    @property
    def games(self) -> list[str]:
        return self.__games

    @property
    def url(self) -> str:
        return self.__url
    
    @property
    def timeout(self) -> int:
        return self.__timeout
    
    @property
    def sentence_transformer(self) -> SentenceTransformer:
        return self.__sentence_transformer
    
    def has_terms_to_ignore(self, value: str) -> bool: 
        invalid_terms_found = [term_to_ignore for term_to_ignore in self.__terms_to_ignore if term_to_ignore.lower() in value.lower()]
        return bool(invalid_terms_found)

    def is_game_looking_for(self, game_title: str, product_found_title: str, similary_limit: float = None) -> bool:
        game_title_embedding = self.__sentence_transformer.encode(game_title)
        product_title_embedding = self.__sentence_transformer.encode(product_found_title)

        similarity = cos_sim(game_title_embedding, product_title_embedding)

        if not similary_limit:
            config = load_config({
                "similarity": "GAME_SIMILARITY"
            })

            similary_limit = float(config["similarity"])

        return similarity >= similary_limit
