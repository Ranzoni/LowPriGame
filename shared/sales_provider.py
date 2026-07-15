from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from shared.models import GamePrice
from infra.environment_variables import load_config


class SalesProvider:
    def __init__(self, games: list[str], url: str, sentence_transformer: SentenceTransformer, search_path: str = None, key: str = None, timeout: int = None):
        self.games = games
        self.__url = url
        self.__sentence_transformer = sentence_transformer
        self.search_path = search_path
        self.__key = key
        self.__timeout = timeout

        config = load_config({
            "terms_to_ignore": "TERMS_TO_IGNORE"
        })

        self.__terms_to_ignore: list[str] = config["terms_to_ignore"].split(",")

    def get_sale_games(self) -> list[GamePrice]:
        return []
    
    @property
    def url(self) -> str:
        return self.__url
    
    @property
    def key(self) -> str:
        return self.__key
    
    @property
    def timeout(self) -> int:
        return self.__timeout
    
    @property
    def sentence_transformer(self) -> SentenceTransformer:
        return self.__sentence_transformer
    
    def has_terms_to_ignore(self, value: str) -> bool: 
        invalid_terms_found = [term_to_ignore for term_to_ignore in self.__terms_to_ignore if term_to_ignore.lower() in value.lower()]
        return bool(invalid_terms_found)

    def _is_game_looking_for(self, game_title: str, product_found_title: str) -> bool:
        game_title_embedding = self.__sentence_transformer.encode(game_title)
        product_title_embedding = self.__sentence_transformer.encode(product_found_title)

        similarity = cos_sim(game_title_embedding, product_title_embedding)

        config = load_config({
            "similarity": "GAME_SIMILARITY"
        })

        return similarity >= float(config["similarity"])
