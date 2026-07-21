import logging
import requests

from pydantic import BaseModel
from typing import Optional
from sentence_transformers import SentenceTransformer

from shared.models import GamePrice, PriceInfo
from shared.functions import calculate_discount
from providers.sales_provider import SalesProvider
from infra.database import Database
from infra.environment_variables import load_config


class IsThereAnyDealProvider(SalesProvider):
    logger = logging.getLogger(__name__)

    def __init__(self, games: list[str], sentence_transformer: SentenceTransformer):
        config = load_config({
            "url": "ISTHERANYDEAL_API_URL",
            "key": "ISTHERANYDEAL_API_KEY",
            "timeout": "ISTHERANYDEAL_API_TIMEOUT"
        })

        self.__key = config["key"]

        super().__init__(
            provider_name="IsThereAnyDeal",
            games=games,
            url=config["url"], 
            sentence_transformer=sentence_transformer,
            timeout=int(config["timeout"])
        )

    def __normalize_title(self, value: str) -> str:
        return self._normalize_text_for_match(value)

    def __post_api(self, path: str, payload, params = None):
        url = self.url + path
        self.logger.info("[%s] Requisicao POST para %s.", self.provider_name, path)

        response = requests.post(
            url,
            json=payload,
            headers={
                "ITAD-API-Key": self.__key
            },
            params=params,
            timeout=self.timeout,
        )
        
        response.raise_for_status()

        return response.json()

    def __get_games_ids(self) -> dict[str, str]:
        payload = self.__post_api("/lookup/id/title/v1", self.games)
        
        if not isinstance(payload, dict):
            raise ValueError("Resposta inesperada da API: esperado objeto com mapeamento nome->id.")

        games_ids: dict[str, str] = {}
        for game_name in self.games:
            game_id = payload.get(game_name)

            if not isinstance(game_id, str):
                fallback_key = next(
                    (
                        name
                        for name in payload.keys()
                        if isinstance(name, str) and self.__normalize_title(name) == self.__normalize_title(game_name)
                    ),
                    None,
                )
                game_id = payload.get(fallback_key) if fallback_key else None

            if isinstance(game_id, str):
                games_ids[game_name] = game_id
            else:
                self.logger.warning(
                    "[%s] Jogo '%s' nao foi mapeado para ID na API.",
                    self.provider_name,
                    game_name,
                )

        self.logger.info("[%s] %s jogos mapeados para IDs na API.", self.provider_name, len(games_ids))
        return games_ids

    def get_sales_games(self) -> list[GamePrice]:
        self.logger.info("[%s] Iniciando busca de promocoes via API.", self.provider_name)
        db = Database()
        games_found = self.__get_games_ids()
        games_ids = [game_id for game_id in games_found.values() if isinstance(game_id, str)]
        game_name_by_id = {game_id: game_name for game_name, game_id in games_found.items()}

        game_id_by_name: dict[str, int] = {}
        for game_name in games_found.keys():
            game = db.get_game_by_name(game=game_name)
            if game:
                game_id_by_name[game_name] = game.id

        payload = self.__post_api("/games/overview/v2", games_ids, { "country": "BR"})
        
        sales_response = ApiSaleResponse(**payload)

        if not sales_response:
            raise ValueError("Resposta inesperada da API.")
        
        sales: list[GamePrice] = []
        
        for sale in sales_response.prices:
            title = game_name_by_id.get(sale.id)
            if not title:
                self.logger.warning(
                    "[%s] Resultado com id '%s' ignorado por nao mapear para jogo em self.games.",
                    self.provider_name,
                    sale.id,
                )
                continue

            product_title = sale.title or title
            game_id = game_id_by_name.get(title)
            if game_id:
                terms_to_ignore = self.get_terms_to_ignore_for_game(game_id=game_id, db=db)
                if self.has_terms_to_ignore(value=product_title, terms_to_ignore=terms_to_ignore):
                    self.logger.info(
                        "[%s] Resultado ignorado por termo proibido: jogo='%s' produto='%s'.",
                        self.provider_name,
                        title,
                        product_title,
                    )
                    continue

            platforms = [drm.name for drm in sale.current.drm if drm.name]

            discount, discount_percentage = calculate_discount(
                regular_price=sale.current.regular.amount,
                price_to_compare=sale.current.price.amount
            )
            if not discount:
                continue

            game_price = GamePrice(
                name=title,
                price=sale.current.price.amount,
                price_info=PriceInfo(
                    regular_price=sale.current.regular.amount,
                    discont=discount,
                    discount_percentage=discount_percentage
                ),
                voucher=sale.current.voucher,
                store=sale.current.shop.name,
                platforms=platforms,
                link=sale.current.url
            )

            sales.append(game_price)
            self.logger.info(
                "[%s] Resultado encontrado: jogo='%s' preco=%.2f loja='%s' plataformas=%s link='%s'.",
                self.provider_name,
                game_price.name,
                game_price.price,
                game_price.store,
                ", ".join(game_price.platforms or []),
                game_price.link,
            )

        self.logger.info("[%s] Busca via API finalizada com %s promocoes.", self.provider_name, len(sales))

        return sales

class ApiShopResponse(BaseModel):
    name: str

class ApiPriceResponse(BaseModel):
    amount: float

class ApiRegularPriceResponse(BaseModel):
    amount: float

class ApiDrmResponse(BaseModel):
    name: Optional[str]

class ApiPlatformsResponse(BaseModel):
    name: str

class ApiCurrentResponse(BaseModel):
    shop: ApiShopResponse
    price: ApiPriceResponse
    regular: ApiRegularPriceResponse
    voucher: Optional[str]
    drm: list[ApiDrmResponse]
    platforms: list[ApiPlatformsResponse]
    url: str

class ApiPricesResponse(BaseModel):
    id: str
    title: Optional[str] = None
    current: ApiCurrentResponse

class ApiSaleResponse(BaseModel):
    prices: list[ApiPricesResponse]
