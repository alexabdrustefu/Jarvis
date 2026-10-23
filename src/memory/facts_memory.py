import sqlite3
from pathlib import Path

DEFAULT_DB = (
    Path(__file__).resolve().parent.parent
    / "storage"
    / "jarvis.db"
)


class FactsMemory:
    """Memoria persistente per informazioni specifiche."""

    def __init__(self, db_path=DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_key TEXT NOT NULL UNIQUE,
                    fact_value TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                )
            """)

    def remember(self, key: str, value: str):
        key = key.strip()
        value = value.strip()

        if not key or not value:
            raise ValueError(
                "La chiave e il valore non possono essere vuoti."
            )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO facts (fact_key, fact_value)
                VALUES (?, ?)
                ON CONFLICT(fact_key)
                DO UPDATE SET
                    fact_value = excluded.fact_value,
                    created_at = strftime(
                        '%Y-%m-%dT%H:%M:%fZ', 'now'
                    )
                """,
                (key, value),
            )

    def get(self, key: str):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT fact_value FROM facts WHERE fact_key = ?",
                (key.strip(),),
            ).fetchone()

        return row[0] if row else None

    def get_all(self):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT fact_key, fact_value
                FROM facts
                ORDER BY fact_key
                """
            ).fetchall()

        return dict(rows)

    def forget(self, key: str):
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM facts WHERE fact_key = ?",
                (key.strip(),),
            )
            return cursor.rowcount > 0
