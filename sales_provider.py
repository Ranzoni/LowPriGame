import os

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from dotenv import load_dotenv

from models import GamePrice


class SalesProvider:
    games: list[str]
    url: str = ""
    search_path: str = None
    key: str | None
    similarity_model: SentenceTransformer

    def __init__(self, games: list[str], url: str, search_path: str = None, key: str = None):
        self.games = games
        self.url = url
        self.search_path = search_path
        self.key = key

        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def get_sale_games(self) -> list[GamePrice]:
        return []

    def _is_game_looking_for(self, game_title: str, product_found_title: str) -> bool:
        load_dotenv()

        game_title_embedding = self.model.encode(game_title)
        product_title_embedding = self.model.encode(product_found_title)

        similarity = cos_sim(game_title_embedding, product_title_embedding)

        return similarity >= float(os.getenv("GAME_SIMILARITY"))
