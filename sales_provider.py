from models import GamePrice


class SalesProvider:
    games: list[str]
    url: str = ""
    search_path: str = None
    key: str | None

    def __init__(self, games: list[str], url: str, search_path: str = None, key: str = None):
        self.games = games
        self.url = url
        self.search_path = search_path
        self.key = key

    def get_sale_games(self) -> list[GamePrice]:
        return []
