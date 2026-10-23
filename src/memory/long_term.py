
import sqlite3
from pathlib import Path

DEFAULT_DB = (
    Path(__file__).resolve().parent.parent
    / "storage"
    / "jarvis.db"
)


class LongTermMemory:
    """Memoria persistente locale basata su SQLite."""

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
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL
                        CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                )
            """)

    def add_message(self, role: str, content: str):
        if role not in {"user", "assistant"}:
            raise ValueError("Ruolo non valido")

        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (role, content),
            )

    def get_recent_messages(self, limit: int = 20):
        if limit < 1:
            raise ValueError("Il limite deve essere positivo")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        rows.reverse()

        return [
            {"role": role, "content": content}
            for role, content in rows
        ]

    def get_recent_messages_with_timestamps(self, limit: int = 60):
        """Return recent messages with stored UTC timestamps for display."""
        if limit < 1:
            raise ValueError("Il limite deve essere positivo")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at, id
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        rows.reverse()
        return [
            {"role": role, "content": content, "created_at": created_at, "id": message_id}
            for role, content, created_at, message_id in rows
        ]

    def get_messages_after_id(self, message_id: int):
        """Read newly added messages for another live interface, in order."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, role, content, created_at
                FROM messages
                WHERE id > ?
                ORDER BY id ASC
                """,
                (message_id,),
            ).fetchall()
        return [
            {"id": row_id, "role": role, "content": content, "created_at": created_at}
            for row_id, role, content, created_at in rows
        ]

    def clear(self):
        with self._connect() as connection:
            connection.execute("DELETE FROM messages")
