"""Routes recognized requests to the appropriate JARVIS service."""

import re

from core.text import normalize_text
from core.weather import extract_weather_city, interpret_weather_date
from actions.system_actions_audio import is_volume_command


class CommandRouter:
    def __init__(self, ai, email, news, system, audio):
        self.ai = ai
        self.email = email
        self.news = news
        self.system = system
        self.audio = audio
        self._awaiting_weather_date = False
        self._pending_weather_city = None

    def _record_action(self, user_message: str, response: str) -> str:
        """Persist deterministic actions so both interfaces share one history."""
        memory = getattr(self.ai, "memory", None)
        if memory is not None:
            memory.add_message("user", user_message)
            memory.add_message("assistant", response)
        return response

    def handle(self, text: str) -> str:
        normalized = normalize_text(text)

        if normalized in {"aiuto", "help", "comandi", "cosa sai fare", "cosa puoi fare"}:
            return self._record_action(text, (
                "Posso rispondere alle tue domande, ricordare informazioni, "
                "leggere le email non lette, riassumere le notizie, consultare il meteo, "
                "dirti data e ora, aprire siti o programmi e regolare il volume. "
                "Prova: meteo oggi, leggi le email, dimmi le notizie, "
                "apri calcolatrice oppure alza il volume."
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
                    requested_date, extract_weather_city(normalized)
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
