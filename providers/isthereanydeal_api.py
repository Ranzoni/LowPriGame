import logging
import requests

from pydantic import BaseModel
from typing import Optional
from sentence_transformers import SentenceTransformer

from shared.models import GamePrice, PriceInfo
from shared.functions import calculate_discount
from providers.sales_provider import SalesProvider
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

        games_ids = {name: game_id for name, game_id in payload.items() if isinstance(game_id, str)}
        self.logger.info("[%s] %s jogos mapeados para IDs na API.", self.provider_name, len(games_ids))
        return games_ids

    def get_sales_games(self) -> list[GamePrice]:
        self.logger.info("[%s] Iniciando busca de promocoes via API.", self.provider_name)
        games_found = self.__get_games_ids()
        games_ids = [game_id for game_id in games_found.values() if isinstance(game_id, str)]

        payload = self.__post_api("/games/overview/v2", games_ids, { "country": "BR"})
        
        sales_response = ApiSaleResponse(**payload)

        if not sales_response:
            raise ValueError("Resposta inesperada da API.")
        
        sales: list[GamePrice] = []
        
        for sale in sales_response.prices:
            title: str = sale.id
            
            for key, value in games_found.items():
                if value == sale.id:
                    title = key
                    break

            platforms = [drm.name for drm in sale.current.drm if drm.name]

            discount, discount_percentage = calculate_discount(
                regular_price=sale.current.regular.amount,
                price_to_compare=sale.current.price.amount
            )

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
    current: ApiCurrentResponse

class ApiSaleResponse(BaseModel):
    prices: list[ApiPricesResponse]
