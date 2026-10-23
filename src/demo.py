"""Deterministic offline adapters for previews and first-run demonstrations."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from memory.long_term import LongTermMemory


class DemoAI:
    """Small predictable AI substitute that never opens a network connection."""

    def __init__(self, db_path: Path):
        self.memory = LongTermMemory(db_path)
        if not self.memory.get_recent_messages(limit=1):
            self.memory.add_message(
                "assistant",
                "Modalità demo offline attiva. Prova un promemoria o una delle azioni rapide.",
            )

    def chat(self, message: str) -> str:
        self.memory.add_message("user", message)
        reply = (
            "Questa è una risposta dimostrativa offline. La modalità demo non contatta "
            "provider AI; installa Ollama per usare la chat locale completa."
        )
        self.memory.add_message("assistant", reply)
        return reply

    def clear_history(self) -> None:
        self.memory.clear()


class DemoEmail:
    def get_unread_emails_summary(self) -> str:
        return "Demo offline: la posta non viene contattata. Configura Gmail per collegare una casella."


class DemoNews:
    def get_daily_news_summary(self) -> str:
        return "Demo offline: i titoli RSS sono simulati. La modalità completa legge i feed configurati."


class DemoSystem:
    def get_weather_for_date(self, requested_date: date, city_name: str | None = None) -> str:
        day = "oggi" if requested_date == date.today() else requested_date.strftime("%d/%m")
        city = city_name or "la tua città"
        return f"Previsione dimostrativa per {city}, {day}: 18 °C e cielo sereno. Dato simulato, nessuna rete usata."

    @staticmethod
    def get_time() -> str:
        return f"Demo offline: sono le {datetime.now():%H:%M}."

    @staticmethod
    def get_date() -> str:
        return f"Demo offline: oggi è il {datetime.now():%d/%m/%Y}."

    @staticmethod
    def open_website(website: str) -> str:
        return f"Demo offline: non ho aperto {website}. Nessuna azione esterna viene eseguita."

    @staticmethod
    def open_program(program: str) -> str:
        return f"Demo offline: non ho avviato {program}. Nessuna azione di sistema viene eseguita."

    @staticmethod
    def search_google(query: str) -> str:
        return f"Demo offline: la ricerca '{query}' è simulata; non è stato aperto un browser."


class DemoAudio:
    @staticmethod
    def adjust_volume(_command: str) -> str:
        return "Demo offline: il volume di Windows non è stato modificato."
