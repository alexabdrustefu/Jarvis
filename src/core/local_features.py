"""SQLite backed reminders, routines and preferences. No network services required."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from storage.paths import data_directory

DEFAULT_DB = data_directory() / "jarvis.db"


class LocalStore:
    def __init__(self, db_path=DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_at TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    notified INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS routines (
                    name TEXT PRIMARY KEY COLLATE NOCASE,
                    steps TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=5)

    def health_check(self):
        with self._connection() as db:
            db.execute("SELECT 1").fetchone()
        return True

    @contextmanager
    def _connection(self):
        db = self._connect()
        try:
            with db:
                yield db
        finally:
            db.close()

    def add_reminder(self, title, due_at=None):
        title = title.strip()
        if not title:
            raise ValueError("Scrivi il testo dell'attività.")
        due = due_at.isoformat(timespec="minutes") if due_at else None
        with self._connection() as db:
            cur = db.execute("INSERT INTO reminders(title,due_at,created_at) VALUES(?,?,?)",
                             (title, due, datetime.now().isoformat(timespec="seconds")))
            return cur.lastrowid

    def list_reminders(self, include_done=False):
        query = "SELECT id,title,due_at,status FROM reminders"
        if not include_done:
            query += " WHERE status='pending'"
        query += " ORDER BY CASE WHEN due_at IS NULL THEN 1 ELSE 0 END,due_at,id"
        with self._connection() as db:
            return db.execute(query).fetchall()

    def complete_reminder(self, reminder_id):
        with self._connection() as db:
            return db.execute("UPDATE reminders SET status='done' WHERE id=? AND status='pending'",
                              (int(reminder_id),)).rowcount > 0

    def delete_reminder(self, reminder_id):
        with self._connection() as db:
            return db.execute("DELETE FROM reminders WHERE id=?", (int(reminder_id),)).rowcount > 0

    def take_due(self, now=None):
        now = now or datetime.now()
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute("SELECT id,title,due_at FROM reminders WHERE status='pending' AND notified=0 AND due_at<=? ORDER BY due_at",
                              (now.isoformat(timespec="minutes"),)).fetchall()
            if rows:
                db.executemany("UPDATE reminders SET notified=1 WHERE id=?", [(row[0],) for row in rows])
            return rows

    def save_routine(self, name, steps):
        name = name.strip()
        if not name or not steps:
            raise ValueError("La routine richiede un nome e almeno un'azione.")
        allowed = {"weather", "news", "time", "volume_down", "open_browser"}
        if any(step not in allowed for step in steps):
            raise ValueError("La routine contiene un'azione non supportata.")
        with self._connection() as db:
            db.execute("INSERT INTO routines(name,steps) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET steps=excluded.steps",
                       (name, json.dumps(steps)))

    def list_routines(self):
        with self._connection() as db:
            return [(name, json.loads(steps)) for name, steps in db.execute("SELECT name,steps FROM routines ORDER BY name")]

    def delete_routine(self, name):
        with self._connection() as db:
            return db.execute("DELETE FROM routines WHERE name=?", (name,)).rowcount > 0

    def get_statistics(self):
        """Return aggregate task counts without exposing reminder contents."""
        now = datetime.now().isoformat(timespec="minutes")
        with self._connection() as db:
            row = db.execute("""
                SELECT
                    SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status='pending' AND due_at IS NOT NULL AND due_at<=? THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status='done' THEN 1 ELSE 0 END),
                    (SELECT COUNT(*) FROM routines)
                FROM reminders
            """, (now,)).fetchone()
        return {
            "reminders_pending": row[0] or 0,
            "reminders_overdue": row[1] or 0,
            "reminders_completed": row[2] or 0,
            "routines": row[3] or 0,
        }

    def get_preferences(self):
        defaults = {"voice_replies": False, "speech_rate": "normal", "voice": "it-IT-IsabellaNeural", "location": "", "llm_provider": "auto"}
        with self._connection() as db:
            defaults.update({key: json.loads(value) for key, value in db.execute("SELECT key,value FROM preferences")})
        return defaults

    def set_preference(self, key, value):
        if key not in {"voice_replies", "speech_rate", "voice", "location", "llm_provider"}:
            raise ValueError("Preferenza non riconosciuta.")
        with self._connection() as db:
            db.execute("INSERT INTO preferences(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                       (key, json.dumps(value)))


def parse_reminder(text, now=None):
    """Parse common Italian due phrases; returns (title, due datetime or None)."""
    now = now or datetime.now()
    raw = text.strip()
    normalized = raw.casefold()
    if normalized.startswith("ricordami di "):
        raw = raw[len("ricordami di "):]
    elif normalized.startswith("aggiungi attività "):
        raw = raw[len("aggiungi attività "):]
    elif normalized.startswith("aggiungi attivita "):
        raw = raw[len("aggiungi attivita "):]
    title = raw
    due = None
    half_hour = re.search(r"\s+tra\s+mezz'ora\s*$", raw, re.I)
    if half_hour:
        due, title = now + timedelta(minutes=30), raw[:half_hour.start()]
        m = None
    else:
        m = re.search(r"\s+(?:tra|fra)\s+(\d+)\s+(minut[oi]|or[ae]|giorn[oi])\s*$", raw, re.I)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).casefold()
        delta = timedelta(minutes=amount) if unit.startswith("minut") else timedelta(hours=amount) if unit.startswith("or") else timedelta(days=amount)
        due, title = now + delta, raw[:m.start()]
    else:
        m = re.search(r"\s+(oggi|domani)(?:\s+alle\s+(\d{1,2})(?::(\d{2}))?)?\s*$", raw, re.I)
        explicit = re.search(r"\s+alle\s+(\d{1,2})(?::(\d{2}))?\s*$", raw, re.I)
        if m:
            day = now.date() + (timedelta(days=1) if m.group(1).casefold() == "domani" else timedelta())
            hour, minute = int(m.group(2) or ("9" if m.group(1).casefold() == "domani" else "23")), int(m.group(3) or ("0" if m.group(2) else "59"))
            due, title = datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute), raw[:m.start()]
        elif explicit:
            due = now.replace(hour=int(explicit.group(1)), minute=int(explicit.group(2) or 0), second=0, microsecond=0)
            if due <= now:
                due += timedelta(days=1)
            title = raw[:explicit.start()]
    return title.strip(" .,!"), due


class LocalCommandService:
    def __init__(self, store=None, clock=None):
        self.store = store or LocalStore()
        self.clock = clock or datetime.now
        self.pending_routine = None

    def handle(self, text, actions):
        normalized = text.casefold().strip()
        if self.pending_routine:
            routine = self.pending_routine
            self.pending_routine = None
            if normalized in {"si", "sì", "confermo", "conferma", "procedi"}:
                return self._execute(routine, actions)
            return "Routine annullata."
        if normalized in {"mostra promemoria", "mostra attività", "mostra attivita", "elenca promemoria", "attività", "attivita"}:
            rows = self.store.list_reminders()
            return "Non hai attività aperte." if not rows else "Attività aperte:\n" + "\n".join(self._format_reminder(r) for r in rows)
        m = re.match(r"^(?:completa|segna completato)\s+(?:promemoria\s+)?(\d+)$", normalized)
        if m:
            return "Attività completata." if self.store.complete_reminder(m.group(1)) else "Non trovo quell'attività aperta."
        m = re.match(r"^elimina\s+(?:promemoria\s+)?(\d+)$", normalized)
        if m:
            return "Attività eliminata." if self.store.delete_reminder(m.group(1)) else "Non trovo quell'attività."
        if normalized.startswith(("ricordami di ", "aggiungi attività ", "aggiungi attivita ")):
            title, due = parse_reminder(text, self.clock())
            if not title:
                return "Dimmi cosa devo ricordarti."
            ident = self.store.add_reminder(title, due)
            return f"Attività {ident} salvata" + (f" per {due:%d/%m alle %H:%M}." if due else ".")
        routines = self.store.list_routines()
        for name, steps in routines:
            if normalized in {f"avvia {name.casefold()}", name.casefold()}:
                self.pending_routine = (name, steps)
                return f"La routine {name} include {len(steps)} azioni. Vuoi procedere? Rispondi sì o no."
        return None

    @staticmethod
    def _format_reminder(row):
        due = datetime.fromisoformat(row[2]).strftime("%d/%m %H:%M") if row[2] else "senza scadenza"
        return f"#{row[0]} · {row[1]} · {due}"

    @staticmethod
    def _execute(routine, actions):
        name, steps = routine
        output = []
        for step in steps:
            if step == "weather":
                output.append(actions.system.get_weather_for_date(datetime.now().date(), None))
            elif step == "news":
                output.append(actions.news.get_daily_news_summary())
            elif step == "time":
                output.append(actions.system.get_time())
            elif step == "volume_down":
                output.append(actions.audio.adjust_volume("abbassa volume"))
            elif step == "open_browser":
                output.append(actions.system.open_website("google"))
        return f"Routine {name} completata. " + " ".join(output)
