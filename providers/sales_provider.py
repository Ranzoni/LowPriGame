import re
import unicodedata

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from infra.database import Database
from shared.models import GamePrice
from shared.models import GameToMonitor
from infra.environment_variables import load_config


class SalesProvider:
    def __init__(self, games: list[GameToMonitor], url: str, sentence_transformer: SentenceTransformer, timeout: int = None, provider_name: str = None):
        self.__provider_name = provider_name
        self.__games = games
        self.__url = url
        self.__sentence_transformer = sentence_transformer
        self.__timeout = timeout
        self.__terms_to_ignore_by_game_id: dict[int, list[str]] = {}

    def get_sales_games(self) -> list[GamePrice]:
        raise NotImplementedError("A função não foi implementada.")
    
    @property
    def provider_name(self) -> str | None:
        return self.__provider_name

    @property
    def games(self) -> list[str]:
        return [game.name for game in self.__games]

    @property
    def url(self) -> str:
        return self.__url
    
    @property
    def timeout(self) -> int:
        return self.__timeout
    
    @property
    def sentence_transformer(self) -> SentenceTransformer:
        return self.__sentence_transformer

    def is_platform_enabled(self, game_name: str, platform_name: str) -> bool:
        """Return whether a platform is enabled for a game.

        An omitted or empty list preserves the legacy behaviour: all platforms
        supported by the provider are searched.
        """
        game = next((item for item in self.__games if item.name.casefold() == game_name.casefold()), None)
        if not game or not game.platforms:
            return True

        normalized_platform = self._normalize_text_for_match(platform_name)
        return normalized_platform in {
            self._normalize_text_for_match(platform)
            for platform in game.platforms
        }

    def are_sale_platforms_enabled(self, game_name: str, platform_names: list[str]) -> bool:
        """Check a provider result against a game's optional platform filter."""
        game = next((item for item in self.__games if item.name.casefold() == game_name.casefold()), None)
        if not game or not game.platforms:
            return True

        return any(
            self.is_platform_enabled(game_name, platform_name)
            for platform_name in platform_names
        )
    
    def _normalize_text_for_match(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value or "")
        normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def get_terms_to_ignore_for_game(self, game_id: int, db: Database) -> list[str]:
        if game_id not in self.__terms_to_ignore_by_game_id:
            self.__terms_to_ignore_by_game_id[game_id] = db.get_terms_to_ignore_by_game_id(game_id=game_id)

        return self.__terms_to_ignore_by_game_id[game_id]

    def has_terms_to_ignore(self, value: str, terms_to_ignore: list[str]) -> bool:
        normalized_value = self._normalize_text_for_match(value)

        invalid_terms_found = [
            term_to_ignore
            for term_to_ignore in terms_to_ignore
            if self._normalize_text_for_match(term_to_ignore) in normalized_value
        ]
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
