"""Routes messages through deterministic command handlers before the LLM."""

from __future__ import annotations

import re
import threading
from collections.abc import Callable

from actions.system_actions_audio import is_volume_command
from core.local_features import LocalCommandService
from core.text import normalize_text
from core.weather import extract_weather_city, interpret_weather_date


class CommandRouter:
    """A small chain of responsibility for JARVIS intents.

    Handler order is intentional: local commands and known actions run before
    the LLM fallback, keeping deterministic actions cheap and predictable.
    """

    def __init__(self, ai, email, news, system, audio, local_commands=None):
        self.ai = ai
        self.email = email
        self.news = news
        self.system = system
        self.audio = audio
        self.local_commands = local_commands if local_commands is not None else LocalCommandService()
        self._awaiting_weather_date = False
        self._pending_weather_city = None
        self._lock = threading.RLock()
        self._handlers: tuple[Callable[[str, str], str | None], ...] = (
            self._route_local_features,
            self._route_help,
            self._route_weather_follow_up,
            self._route_volume,
            self._route_email,
            self._route_news,
            self._route_weather,
            self._route_clock,
            self._route_open,
            self._route_search,
        )

    def _record_action(self, user_message: str, response: str) -> str:
        """Persist deterministic actions so all interfaces share one history."""
        memory = getattr(self.ai, "memory", None)
        if memory is not None:
            memory.add_message("user", user_message)
            memory.add_message("assistant", response)
        return response

    def handle(self, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return "Scrivi o pronuncia una richiesta."
        with self._lock:
            return self._handle(text.strip())

    def _handle(self, text: str) -> str:
        normalized = normalize_text(text)
        for handler in self._handlers:
            response = handler(text, normalized)
            if response is not None:
                return response

        prompt = re.sub(r"^jarvis\b[,.!?\s]*", "", text, flags=re.IGNORECASE).strip()
        return self.ai.chat(prompt or text)

    def _route_local_features(self, text: str, _normalized: str) -> str | None:
        response = self.local_commands.handle(text, self)
        return self._record_action(text, response) if response is not None else None

    def _route_help(self, text: str, normalized: str) -> str | None:
        if normalized not in {"aiuto", "help", "comandi", "cosa sai fare", "cosa puoi fare"}:
            return None
        answer = (
            "Posso rispondere alle tue domande, salvare promemoria e attività locali, "
            "leggere le email non lette, riassumere le notizie, consultare il meteo, "
            "dirti data e ora, aprire siti o programmi e regolare il volume. "
            "Prova: meteo oggi, leggi le email, dimmi le notizie, "
            "avvia routine, completa promemoria 2, apri calcolatrice oppure alza il volume. "
            "Per aggiungere: ricordami di comprare il latte domani alle 9."
        )
        return self._record_action(text, answer)

    def _route_weather_follow_up(self, text: str, normalized: str) -> str | None:
        if not self._awaiting_weather_date:
            return None
        requested_date = interpret_weather_date(normalized)
        if requested_date is not None:
            city = extract_weather_city(normalized) or self._pending_weather_city
            self._clear_weather_follow_up()
            return self._record_action(text, self.system.get_weather_for_date(requested_date, city))
        self._clear_weather_follow_up()
        return None

    def _clear_weather_follow_up(self) -> None:
        self._awaiting_weather_date = False
        self._pending_weather_city = None

    def _route_volume(self, text: str, normalized: str) -> str | None:
        return self._record_action(text, self.audio.adjust_volume(normalized)) if is_volume_command(normalized) else None

    def _route_email(self, text: str, normalized: str) -> str | None:
        phrases = (
            "leggi le email", "leggi le mail", "controlla le email", "nuove mail",
            "posta in arrivo", "riepilogo delle email", "leggi email", "leggi mail",
            "controlla la posta",
        )
        if not any(phrase in normalized for phrase in phrases):
            return None
        return self._record_action(text, self.email.get_unread_emails_summary())

    def _route_news(self, text: str, normalized: str) -> str | None:
        if not any(word in normalized for word in ("notizie", "news", "giornale", "titoli")):
            return None
        return self._record_action(text, self.news.get_daily_news_summary())

    def _route_weather(self, text: str, normalized: str) -> str | None:
        phrases = ("che tempo fa", "che tempo fara", "temperatura", "piove", "piovera", "fara freddo", "fara caldo")
        if "meteo" not in normalized and not any(phrase in normalized for phrase in phrases):
            return None
        requested_date = interpret_weather_date(normalized)
        if requested_date is None:
            self._awaiting_weather_date = True
            self._pending_weather_city = extract_weather_city(normalized)
            return self._record_action(text, "Per quale giorno vuoi conoscere il meteo? Puoi dire oggi, domani o il nome di un giorno.")
        city = (
            extract_weather_city(normalized)
            or self.local_commands.store.get_preferences().get("location")
            or None
        )
        return self._record_action(text, self.system.get_weather_for_date(requested_date, city))

    def _route_clock(self, text: str, normalized: str) -> str | None:
        if "che ore sono" in normalized or "dimmi l'ora" in normalized:
            return self._record_action(text, self.system.get_time())
        if "che giorno e" in normalized or "dimmi la data" in normalized:
            return self._record_action(text, self.system.get_date())
        return None

    def _route_open(self, text: str, normalized: str) -> str | None:
        if not normalized.startswith("apri "):
            return None
        target = normalized[5:].strip()
        if target in {"youtube", "google", "gmail", "wikipedia"}:
            response = self.system.open_website(target)
        else:
            response = self.system.open_program(target)
        return self._record_action(text, response)

    def _route_search(self, text: str, normalized: str) -> str | None:
        if not normalized.startswith("cerca "):
            return None
        return self._record_action(text, self.system.search_google(text.strip()[6:]))
