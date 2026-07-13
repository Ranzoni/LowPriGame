import logging
import os
import requests

from decimal import Decimal
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from models import GamePrice


logger = logging.getLogger(__name__)


def _load_api_config() -> dict[str, str]:
    """Carrega e valida as variáveis de ambiente necessárias para a API."""
    load_dotenv()

    config = {
        "url": os.getenv("ISTHERANYDEAL_API_URL"),
        "key": os.getenv("ISTHERANYDEAL_API_KEY"),
    }

    missing = [key for key, value in config.items() if not value]
    if missing:
        formatted = ", ".join(missing)
        raise ValueError(f"Variáveis de ambiente ausentes: {formatted}")
    
    return config

def _post_api(path: str, payload, params = None):
    config = _load_api_config()

    url = config["url"] + path

    response = requests.post(
        url,
        json=payload,
        headers={
            "ITAD-API-Key": config["key"]
        },
        params=params,
        timeout=10,
    )
    
    response.raise_for_status()

    return response.json()

def _get_games_ids(games: list[str]) -> dict[str, str]:
    payload = _post_api("/lookup/id/title/v1", games)
    
    if not isinstance(payload, dict):
        raise ValueError("Resposta inesperada da API: esperado objeto com mapeamento nome->id.")

    return {name: game_id for name, game_id in payload.items() if isinstance(game_id, str)}

def get_sale_games_itad(games_names: list[str]) -> list[GamePrice]:
    games = _get_games_ids(games_names)
    games_ids = [game_id for game_id in games.values() if isinstance(game_id, str)]

    payload = _post_api("/games/overview/v2", games_ids, { "country": "BR"})
    
    sales_response = ApiSaleResponse(**payload)

    if not sales_response:
        raise ValueError("Resposta inesperada da API.")
    
    sales: list[GamePrice] = []
    
    for sale in sales_response.prices:
        title: str = sale.id
        
        for key, value in games.items():
            if value == sale.id:
                title = key
                break

        os_list = [platform.name for platform in sale.current.platforms]
        platforms = [drm.name for drm in sale.current.drm]

        game_price = GamePrice(
            name=title,
            price=sale.current.price.amount,
            regular_price=sale.current.regular.amount,
            voucher=sale.current.voucher,
            store=sale.current.shop.name,
            os_list=os_list,
            platforms=platforms
        )

        sales.append(game_price)

    return sales

class ApiShopResponse(BaseModel):
    name: str

class ApiPriceResponse(BaseModel):
    amount: Decimal

class ApiRegularPriceResponse(BaseModel):
    amount: Decimal

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

class ApiPricesResponse(BaseModel):
    id: str
    current: ApiCurrentResponse

class ApiSaleResponse(BaseModel):
    prices: list[ApiPricesResponse]
