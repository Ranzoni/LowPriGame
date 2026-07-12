import json


def get_games_list() -> list[str]:
    with open("games.json", encoding="utf-8") as f:
        return json.load(f)["games"]
    