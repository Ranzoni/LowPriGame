import os
import unittest
from unittest.mock import Mock, patch

from infra.database import Game
from providers.isthereanydeal_api import IsThereAnyDealProvider
from shared.models import GameToMonitor


class FakeDatabase:
    def get_game_by_name(self, game: str):
        return Game(id=1, name=game)

    def get_terms_to_ignore_by_game_id(self, game_id: int) -> list[str]:
        return []


class IsThereAnyDealPlatformFilterIntegrationTests(unittest.TestCase):
    @patch("providers.isthereanydeal_api.Database", FakeDatabase)
    @patch.dict(os.environ, {
        "ISTHERANYDEAL_API_URL": "https://example.test",
        "ISTHERANYDEAL_API_KEY": "test-key",
        "ISTHERANYDEAL_API_TIMEOUT": "1",
    }, clear=False)
    def test_returns_only_sales_from_configured_platforms(self) -> None:
        provider = IsThereAnyDealProvider(
            games=[GameToMonitor(name="Configured Game", platforms=["Steam"])],
            sentence_transformer=None,
        )
        provider._IsThereAnyDealProvider__post_api = Mock(side_effect=[
            {"Configured Game": "game-id"},
            {
                "prices": [
                    self._sale("Steam", 50),
                    self._sale("GOG", 40),
                ]
            },
        ])

        sales = provider.get_sales_games()

        self.assertEqual(len(sales), 1)
        self.assertEqual(sales[0].price, 50)
        self.assertEqual(sales[0].platforms, ["Steam"])

    @staticmethod
    def _sale(drm: str, price: float) -> dict:
        return {
            "id": "game-id",
            "title": "Configured Game",
            "current": {
                "shop": {"name": "Test Store"},
                "price": {"amount": price},
                "regular": {"amount": 100},
                "voucher": None,
                "drm": [{"name": drm}],
                "platforms": [],
                "url": "https://example.test/product",
            },
        }
