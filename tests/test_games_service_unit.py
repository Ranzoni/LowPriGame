import json
import tempfile
import unittest
from pathlib import Path

from services.games_service import get_games_list


class GetGamesListTests(unittest.TestCase):
    def _write_games_file(self, games: list[object]) -> str:
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        with temp_file:
            json.dump({"games": games}, temp_file)
        self.addCleanup(Path(temp_file.name).unlink)
        return temp_file.name

    def test_parses_legacy_and_platform_configurations(self) -> None:
        games_file = self._write_games_file([
            "Legacy Game",
            {"name": "Console Game", "platforms": ["PS5", "Switch"]},
            {"name": "All Platforms Game", "platforms": []},
        ])

        games = get_games_list(games_file)

        self.assertEqual([game.name for game in games], [
            "Legacy Game",
            "Console Game",
            "All Platforms Game",
        ])
        self.assertIsNone(games[0].platforms)
        self.assertEqual(games[1].platforms, ["PS5", "Switch"])
        self.assertEqual(games[2].platforms, [])

    def test_rejects_invalid_game_entry(self) -> None:
        games_file = self._write_games_file([42])

        with self.assertRaisesRegex(ValueError, "Cada item de 'games'"):
            get_games_list(games_file)
