import psycopg

from datetime import datetime, timezone

from infra.environment_variables import load_config


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
    def __init__(self, id: int, name: str):
        self.__id = id
        self.__name = name

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name
    
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

    def add_games(self, games: list[str]) -> None:
        if not games:
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
        except Exception as e:
            print(f"An error occurred: {e}")

    def delete_games(self, games_ids: list[int]) -> None:
        if not games_ids:
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
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_game_by_name(self, game: str) -> Game:
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
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

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

        except Exception as e:
            print(f"An error occurred: {e}")
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
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def add_prices(self, prices_list: list[tuple[int, int, float]]) -> None:
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
        except Exception as e:
            print(f"An error occurred: {e}")

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

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

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

        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def get_platforms(self) -> list[Platform]:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    query = "SELECT id, name FROM platforms;"

                    cur.execute(query)
                    rows = cur.fetchall()

                    return [
                        Platform(
                            id=int(row[0]),
                            name=row[1]
                        )
                        for row in rows
                    ]

        except Exception as e:
            print(f"An error occurred: {e}")
            return []
