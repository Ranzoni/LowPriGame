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

        super().__init__(
            games=games,
            url=config["url"], 
            sentence_transformer=sentence_transformer,
            key=config["key"],
            timeout=int(config["timeout"])
        )

    def _post_api(self, path: str, payload, params = None):
        url = self.url + path

        response = requests.post(
            url,
            json=payload,
            headers={
                "ITAD-API-Key": self.key
            },
            params=params,
            timeout=self.timeout,
        )
        
        response.raise_for_status()

        return response.json()

    def _get_games_ids(self) -> dict[str, str]:
        payload = self._post_api("/lookup/id/title/v1", self.games)
        
        if not isinstance(payload, dict):
            raise ValueError("Resposta inesperada da API: esperado objeto com mapeamento nome->id.")

        return {name: game_id for name, game_id in payload.items() if isinstance(game_id, str)}

    def get_sales_games(self) -> list[GamePrice]:
        games_found = self._get_games_ids()
        games_ids = [game_id for game_id in games_found.values() if isinstance(game_id, str)]

        payload = self._post_api("/games/overview/v2", games_ids, { "country": "BR"})
        
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
