import unittest

from providers.sales_provider import SalesProvider
from shared.models import GameToMonitor


class SalesProviderPlatformFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = SalesProvider(
            games=[
                GameToMonitor(name="Console Game", platforms=["PS5", "Switch"]),
                GameToMonitor(name="Accent Game", platforms=["Platafórma Especial"]),
                GameToMonitor(name="All Platforms Game"),
                GameToMonitor(name="Empty Platforms Game", platforms=[]),
            ],
            url="",
            sentence_transformer=None,
        )

    def test_compares_platform_names_case_and_accent_insensitively(self) -> None:
        self.assertTrue(self.provider.is_platform_enabled("Console Game", "ps5"))
        self.assertTrue(self.provider.is_platform_enabled("Console Game", "SWITCH"))
        self.assertTrue(self.provider.is_platform_enabled("Accent Game", "plataforma especial"))
        self.assertFalse(self.provider.is_platform_enabled("Console Game", "Steam"))

    def test_missing_or_empty_platform_list_keeps_all_platforms_enabled(self) -> None:
        self.assertTrue(self.provider.is_platform_enabled("All Platforms Game", "Steam"))
        self.assertTrue(self.provider.is_platform_enabled("Empty Platforms Game", "PS5"))

    def test_sale_platforms_require_at_least_one_configured_platform(self) -> None:
        self.assertTrue(self.provider.are_sale_platforms_enabled("Console Game", ["Steam", "PS5"]))
        self.assertFalse(self.provider.are_sale_platforms_enabled("Console Game", ["Steam", "GOG"]))
        self.assertTrue(self.provider.are_sale_platforms_enabled("All Platforms Game", []))
