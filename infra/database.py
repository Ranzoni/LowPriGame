import psycopg
import logging
from typing import Callable, TypeVar

from datetime import datetime, timezone

from infra.environment_variables import load_config
from shared.enums import PlatformType
from shared.models import GamePrice


logger = logging.getLogger(__name__)
T = TypeVar("T")


class Game:
    def __init__(self, id: int, name: str):
        self.__id = id
        self.__name = name

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

class Platform:
    def __init__(self, id: int, name: str, type: PlatformType):
        self.__id = id
        self.__name = name
        self.__type = type

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def type(self) -> PlatformType:
        return self.__type
    
class GamePriceHistory:
    def __init__(self, id: int, price: float, updated_at: datetime):
        self.__id = id
        self.__price = price
        self.__updated_at = updated_at

    @property
    def id(self) -> int:
        return self.__id

    @property
    def price(self) -> int:
        return self.__price

    @property
    def updated_at(self) -> str:
        return self.__updated_at

class Database:
    connection_string: str

    def __init__(self):
        config = load_config({
            "connection_string": "CONNECTION_STRING"
        })

        self.connection_string = config["connection_string"]

    def execute_in_transaction(self, action: Callable[[psycopg.Connection], T]) -> T:
        with psycopg.connect(self.connection_string) as conn:
            with conn.transaction():
                return action(conn)

    def add_games(self, games: list[str]) -> None:
        if not games:
            logger.info("Nenhum jogo novo para cadastrar no banco.")
            return
        
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.transaction():
                    for game in games:
                        with conn.cursor() as cur:
                            cur.execute(
                                "INSERT INTO games (name) VALUES (%s);",
                                (game,)
                            )
            logger.info("%s jogos cadastrados no banco.", len(games))
        except Exception:
            logger.exception("Falha ao cadastrar jogos no banco.")

    def delete_games(self, games_ids: list[int]) -> None:
        if not games_ids:
            logger.info("Nenhum jogo para remover do banco.")
            return

        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        placeholders = ", ".join(["%s"] * len(games_ids))
                        cur.execute(
                            f"DELETE FROM games WHERE id IN ({placeholders});",
                            games_ids,
                        )
            logger.info("%s jogos removidos do banco.", len(games_ids))
        except Exception:
            logger.exception("Falha ao remover jogos do banco.")

    def get_game_by_name(self, game: str) -> Game | None:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, name FROM games WHERE LOWER(name) = LOWER(%s);",
                        (game,)
                    )
                    row = cur.fetchone()

                    return Game(
                        id=int(row[0]),
                        name=row[1]
                    )
        except Exception:
            logger.exception("Falha ao buscar jogo pelo nome '%s'.", game)
            return None

    def get_games(self) -> list[Game]:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, name FROM games;")
                    rows = cur.fetchall()

                    return [
                        Game(
                            id=int(row[0]),
                            name=row[1]
                        )
                        for row in rows
                    ]

        except Exception:
            logger.exception("Falha ao listar jogos cadastrados.")
            return []
        
    def in_blacklist(self, url: str) -> bool:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(1) > 0 FROM blacklist WHERE url = %s;",
                        (url,)
                    )
                    row = cur.fetchone()

                    return row[0] if row else False
        except Exception:
            logger.exception("Falha ao consultar blacklist para a URL '%s'.", url)
            return False

    def add_prices(self, prices_list: list[tuple[int, int, float]]) -> None:
        if not prices_list:
            logger.info("Nenhum preco para registrar no historico.")
            return

        for game_id, _, price in prices_list:
            if not game_id:
                raise ValueError("O ID do jogo não foi informado para registro do preço")
            if price is None:
                raise ValueError(f"O preço do jogo de ID {game_id} não foi informado para registro")
        
        now = datetime.now(timezone.utc)
        data = [
            (game_id, platform_id, price, now) 
            for game_id, platform_id, price in prices_list
        ]

        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    query = """
                        INSERT INTO game_price_history (games_id, platforms_id, price, updated_at) 
                        VALUES (%s, %s, %s, %s);
                    """

                    cur.executemany(query, data)
            logger.info("%s precos adicionados ao historico.", len(prices_list))
        except Exception:
            logger.exception("Falha ao adicionar precos ao historico.")

    def get_last_game_history(self, game_id: int, platform_id: int) -> GamePriceHistory | None:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, price, updated_at
                        FROM game_price_history
                        WHERE games_id = %s
                        AND platforms_id = %s
                        ORDER BY updated_at DESC
                        LIMIT 1;""",
                        (game_id, platform_id,)
                    )
                    row = cur.fetchone()

                    if not row:
                        return None

                    return GamePriceHistory(
                        id=row[0],
                        price=float(row[1]),
                        updated_at=row[2]
                    )

        except Exception:
            logger.exception(
                "Falha ao consultar o ultimo preco do jogo %s na plataforma %s.",
                game_id,
                platform_id,
            )
            return None

    def get_game_prices_history(self, game_id: int, platform_id: int) -> list[GamePriceHistory]:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, price, updated_at
                        FROM game_price_history
                        WHERE games_id = %s
                        AND platforms_id = %s;""",
                        (game_id, platform_id,)
                    )
                    rows = cur.fetchall()

                    return [
                        GamePriceHistory(
                            id=row[0],
                            price=float(row[1]),
                            updated_at=row[2]
                        )
                        for row in rows
                    ]

        except Exception:
            logger.exception(
                "Falha ao consultar historico de precos do jogo %s na plataforma %s.",
                game_id,
                platform_id,
            )
            return []

    def get_platforms(self) -> list[Platform]:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    query = "SELECT id, name, type FROM platforms;"

                    cur.execute(query)
                    rows = cur.fetchall()

                    return [
                        Platform(
                            id=int(row[0]),
                            name=row[1],
                            type=PlatformType(int(row[2]))
                        )
                        for row in rows
                    ]

        except Exception:
            logger.exception("Falha ao listar plataformas.")
            return []

    def get_terms_to_ignore_by_game_id(self, game_id: int) -> list[str]:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT terms FROM terms_to_ignore WHERE games_id = %s;",
                        (game_id,)
                    )
                    rows = cur.fetchall()

                    terms_to_ignore: list[str] = []
                    for row in rows:
                        terms = row[0] if row and row[0] else ""
                        terms_to_ignore.extend([
                            term.strip()
                            for term in terms.split(",")
                            if term and term.strip()
                        ])

                    return terms_to_ignore
        except Exception:
            logger.exception("Falha ao listar termos para ignorar do jogo %s.", game_id)
            return []

    def __normalize_notified_sale_fields(self, sale: GamePrice) -> tuple[str, float, str, str, str]:
        normalized_name = sale.name.strip().lower()
        normalized_price = round(float(sale.price), 2)
        normalized_store = sale.store.strip().lower()
        normalized_link = (sale.link or "").strip().lower()

        platforms = [
            platform.strip().lower()
            for platform in (sale.platforms or [])
            if platform and platform.strip()
        ]
        normalized_platform = ",".join(sorted(platforms))

        return (
            normalized_name,
            normalized_price,
            normalized_store,
            normalized_link,
            normalized_platform,
        )

    def __is_notified_sale_in_history(self, cur, sale: GamePrice) -> bool:
        game_name, discount_price, store, product_link, platform = self.__normalize_notified_sale_fields(sale)

        cur.execute(
            """
            SELECT COUNT(1) > 0
            FROM notified_discount_history
            WHERE game_name = %s
                AND discount_price = %s
                AND store = %s
                AND product_link = %s
                AND platform = %s;
            """,
            (game_name, discount_price, store, product_link, platform),
        )

        row = cur.fetchone()
        return row[0] if row else False

    def get_unnotified_sales(self, sales: list[GamePrice], conn=None) -> list[GamePrice]:

        def handle_unnotified_sales(cur) -> list[GamePrice]:
            unnotified_sales: list[GamePrice] = []
            seen_keys: set[tuple[str, float, str, str, str]] = set()

            for sale in sales:
                sale_key = self.__normalize_notified_sale_fields(sale)

                if sale_key in seen_keys:
                    continue

                seen_keys.add(sale_key)

                if not self.__is_notified_sale_in_history(cur, sale):
                    unnotified_sales.append(sale)

            return unnotified_sales

        if not sales:
            return []

        if conn:
            with conn.cursor() as cur:
                return handle_unnotified_sales(cur)

        try:
            with psycopg.connect(self.connection_string) as local_conn:
                with local_conn.cursor() as cur:
                    return handle_unnotified_sales(cur)
        except Exception:
            logger.exception("Falha ao consultar historico de notificacoes de desconto.")
            return []

    def add_notified_sales(self, sales: list[GamePrice], conn=None) -> None:
        if not sales:
            return

        now = datetime.now(timezone.utc)
        data = [
            (*self.__normalize_notified_sale_fields(sale), now)
            for sale in sales
        ]

        query = """
            INSERT INTO notified_discount_history (
                game_name,
                discount_price,
                store,
                product_link,
                platform,
                notified_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_name, discount_price, store, product_link, platform) DO NOTHING;
        """

        if conn:
            with conn.cursor() as cur:
                cur.executemany(query, data)
            return

        try:
            with psycopg.connect(self.connection_string) as local_conn:
                with local_conn.cursor() as cur:
                    cur.executemany(query, data)
        except Exception:
            logger.exception("Falha ao registrar historico de notificacoes de desconto.")

