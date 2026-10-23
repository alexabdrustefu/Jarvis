
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from storage.paths import data_directory

DEFAULT_DB = data_directory() / "jarvis.db"


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

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self):
        with self._connection() as connection:
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

        with self._connection() as connection:
            connection.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (role, content),
            )

    def get_recent_messages(self, limit: int = 20):
        if limit < 1:
            raise ValueError("Il limite deve essere positivo")

        with self._connection() as connection:
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

        with self._connection() as connection:
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
        with self._connection() as connection:
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

    def get_statistics(self):
        """Return aggregate conversation counts, with no message content."""
        with self._connection() as connection:
            total, today = connection.execute("""
                SELECT COUNT(*), SUM(CASE WHEN date(created_at)=date('now') THEN 1 ELSE 0 END)
                FROM messages
            """).fetchone()
        return {"messages_total": total or 0, "messages_today": today or 0}

    def clear(self):
        with self._connection() as connection:
            connection.execute("DELETE FROM messages")
