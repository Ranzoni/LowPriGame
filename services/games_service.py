import json

from infra.database import Database


def get_games_list() -> list[str]:
    with open("games.json", encoding="utf-8") as f:
        return json.load(f)["games"]

def register_games(games: list[str]) -> None:
    db = Database()
    
    games_registered = db.get_games()

    games_removed = [register for register in games_registered if register.name not in games]

    games_not_registered = [
        game for game in games
        if game not in {register.name for register in games_registered}
    ]

    db.delete_games([game.id for game in games_removed])
    db.add_games(games_not_registered)
