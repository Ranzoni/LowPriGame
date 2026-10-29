import json
import logging

from infra.database import Database
from shared.models import GameToMonitor


logger = logging.getLogger(__name__)


def get_games_list(file_path: str = "games.json") -> list[GameToMonitor]:
    logger.info("Carregando lista de jogos do arquivo %s.", file_path)

    with open(file_path, encoding="utf-8") as f:
        games_data = json.load(f)["games"]

    games: list[GameToMonitor] = []
    for game in games_data:
        if isinstance(game, str):
            games.append(GameToMonitor(name=game))
        elif isinstance(game, dict):
            games.append(GameToMonitor(**game))
        else:
            raise ValueError(
                "Cada item de 'games' deve ser um nome de jogo ou um objeto com 'name'."
            )

    logger.info("Arquivo games.json carregado com %s jogos.", len(games))
    return games

def register_games(games: list[GameToMonitor]) -> None:
    db = Database()
    logger.info("Sincronizando cadastro de jogos no banco.")
    
    games_registered = db.get_games()

    game_names = [game.name for game in games]
    games_removed = [register for register in games_registered if register.name not in game_names]

    games_not_registered = [
        game for game in game_names
        if game not in {register.name for register in games_registered}
    ]

    logger.info(
        "Cadastro analisado: %s jogos existentes, %s novos, %s removidos.",
        len(games_registered),
        len(games_not_registered),
        len(games_removed),
    )

    db.delete_games([game.id for game in games_removed])
    db.add_games(games_not_registered)
    logger.info("Sincronizacao de jogos concluida.")
