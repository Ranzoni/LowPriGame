from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from models import GamePrice
from environment_variables import load_config


class SalesProvider:
    def __init__(self, games: list[str], url: str, sentence_transformer: SentenceTransformer, search_path: str = None, key: str = None):
        self.games = games
        self.__url = url
        self.__sentence_transformer = sentence_transformer
        self.search_path = search_path
        self.__key = key

        config = load_config({
            "terms_to_ignore": "TERMS_TO_IGNORE"
        })

        self.__terms_to_ignore: list[str] = config["terms_to_ignore"].split(",")

    def get_sale_games(self) -> list[GamePrice]:
        return []
    
    def get_url(self) -> str:
        return self.__url
    
    def get_key(self) -> str:
        return self.__key
    
    def get_sentence_transformer(self) -> SentenceTransformer:
        return self.__sentence_transformer
    
    def get_terms_to_ignore(self) -> list[str]:
        return self.__terms_to_ignore

    def _is_game_looking_for(self, game_title: str, product_found_title: str) -> bool:
        game_title_embedding = self.__sentence_transformer.encode(game_title)
        product_title_embedding = self.__sentence_transformer.encode(product_found_title)

        similarity = cos_sim(game_title_embedding, product_title_embedding)

        config = load_config({
            "similarity": "GAME_SIMILARITY"
        })

        return similarity >= float(config["similarity"])
