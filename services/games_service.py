import json
import logging

from infra.database import Database


logger = logging.getLogger(__name__)


def get_games_list() -> list[str]:
    logger.info("Carregando lista de jogos do arquivo games.json.")

    with open("games.json", encoding="utf-8") as f:
        games = json.load(f)["games"]

    logger.info("Arquivo games.json carregado com %s jogos.", len(games))
    return games

def register_games(games: list[str]) -> None:
    db = Database()
    logger.info("Sincronizando cadastro de jogos no banco.")
    
    games_registered = db.get_games()

    games_removed = [register for register in games_registered if register.name not in games]

    games_not_registered = [
        game for game in games
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
