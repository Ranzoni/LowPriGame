import psycopg

from environment_variables import load_config


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

    def delete_games(self, games: list[str]) -> None:
        if not games:
            return

        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        placeholders = ", ".join(["%s"] * len(games))
                        cur.execute(
                            f"DELETE FROM games WHERE name IN ({placeholders});",
                            games,
                        )
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_games_by_name(self) -> list[str]:
        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    query = "SELECT name FROM games;"

                    cur.execute(query)
                    rows = cur.fetchall()

                    return [row[0] for row in rows]

        except Exception as e:
            print(f"An error occurred: {e}")
            return []