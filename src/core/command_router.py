"""Routes recognized requests to the appropriate JARVIS service."""

import re
import threading

from core.text import normalize_text
from core.weather import extract_weather_city, interpret_weather_date
from actions.system_actions_audio import is_volume_command
from core.local_features import LocalCommandService


class CommandRouter:
    def __init__(self, ai, email, news, system, audio, local_commands=None):
        self.ai = ai
        self.email = email
        self.news = news
        self.system = system
        self.audio = audio
        self.local_commands = local_commands or LocalCommandService()
        self._awaiting_weather_date = False
        self._pending_weather_city = None
        self._lock = threading.RLock()

    def _record_action(self, user_message: str, response: str) -> str:
        """Persist deterministic actions so both interfaces share one history."""
        memory = getattr(self.ai, "memory", None)
        if memory is not None:
            memory.add_message("user", user_message)
            memory.add_message("assistant", response)
        return response

    def handle(self, text: str) -> str:
        # The desktop UI, HTTP bridge and TCP bridge can share this router.
        with self._lock:
            return self._handle(text)

    def _handle(self, text: str) -> str:
        normalized = normalize_text(text)

        local_response = self.local_commands.handle(text, self)
        if local_response is not None:
            return self._record_action(text, local_response)

        if normalized in {"aiuto", "help", "comandi", "cosa sai fare", "cosa puoi fare"}:
            return self._record_action(text, (
                "Posso rispondere alle tue domande, salvare promemoria e attività locali, "
                "leggere le email non lette, riassumere le notizie, consultare il meteo, "
                "dirti data e ora, aprire siti o programmi e regolare il volume. "
                "Prova: meteo oggi, leggi le email, dimmi le notizie, "
                "avvia routine, completa promemoria 2, apri calcolatrice oppure alza il volume. "
                "Per aggiungere: ricordami di comprare il latte domani alle 9."
            ))

        if self._awaiting_weather_date:
            requested_date = interpret_weather_date(normalized)
            if requested_date is not None:
                self._awaiting_weather_date = False
                city = extract_weather_city(normalized) or self._pending_weather_city
                self._pending_weather_city = None
                return self._record_action(
                    text, self.system.get_weather_for_date(requested_date, city)
                )
            self._awaiting_weather_date = False
            self._pending_weather_city = None

        if is_volume_command(normalized):
            return self._record_action(text, self.audio.adjust_volume(normalized))

        if any(phrase in normalized for phrase in (
            "leggi le email", "leggi le mail", "controlla le email",
            "nuove mail", "posta in arrivo", "riepilogo delle email",
            "leggi email", "leggi mail", "controlla la posta",
        )):
            return self._record_action(text, self.email.get_unread_emails_summary())

        if any(word in normalized for word in ("notizie", "news", "giornale", "titoli")):
            return self._record_action(text, self.news.get_daily_news_summary())

        if "meteo" in normalized or any(phrase in normalized for phrase in (
            "che tempo fa", "che tempo fara", "temperatura", "piove",
            "piovera", "fara freddo", "fara caldo",
        )):
            requested_date = interpret_weather_date(normalized)
            if requested_date is None:
                self._awaiting_weather_date = True
                self._pending_weather_city = extract_weather_city(normalized)
                return self._record_action(text, (
                    "Per quale giorno vuoi conoscere il meteo? "
                    "Puoi dire oggi, domani o il nome di un giorno."
                ))
            return self._record_action(
                text,
                self.system.get_weather_for_date(
                    requested_date,
                    extract_weather_city(normalized)
                    or self.local_commands.store.get_preferences().get("location")
                    or None,
                ),
            )

        if "che ore sono" in normalized or "dimmi l'ora" in normalized:
            return self._record_action(text, self.system.get_time())
        if "che giorno e" in normalized or "dimmi la data" in normalized:
            return self._record_action(text, self.system.get_date())

        if normalized.startswith("apri "):
            target = normalized[5:].strip()
            if target in {"youtube", "google", "gmail", "wikipedia"}:
                return self._record_action(text, self.system.open_website(target))
            return self._record_action(text, self.system.open_program(target))

        if normalized.startswith("cerca "):
            return self._record_action(
                text, self.system.search_google(text.strip()[6:])
            )

        prompt = re.sub(r"^jarvis\b[,.!?\s]*", "", text.strip(), flags=re.IGNORECASE)
        if not prompt:
            prompt = text
        return self.ai.chat(prompt)
