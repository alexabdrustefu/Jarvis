import unittest
from datetime import date, timedelta

from core.command_router import CommandRouter


class FakeMemory:
    def __init__(self):
        self.messages = []

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})


class FakeAI:
    def __init__(self):
        self.memory = FakeMemory()
        self.prompts = []

    def chat(self, prompt):
        self.prompts.append(prompt)
        return "Risposta AI"


class FakeEmail:
    def __init__(self):
        self.calls = 0

    def get_unread_emails_summary(self):
        self.calls += 1
        return "Hai due email non lette."


class FakeNews:
    def __init__(self):
        self.calls = 0

    def get_daily_news_summary(self):
        self.calls += 1
        return "Ecco le notizie."


class FakeSystem:
    def __init__(self):
        self.weather_calls = []
        self.programs = []
        self.websites = []
        self.searches = []

    def get_weather_for_date(self, requested_date, city_name=None):
        self.weather_calls.append((requested_date, city_name))
        return "Meteo simulato."

    def get_time(self):
        return "Sono le 12:00."

    def get_date(self):
        return "Oggi è il 23/10/2026."

    def open_program(self, target):
        self.programs.append(target)
        return "Programma aperto."

    def open_website(self, target):
        self.websites.append(target)
        return "Sito aperto."

    def search_google(self, query):
        self.searches.append(query)
        return "Ricerca avviata."


class FakeAudio:
    def __init__(self):
        self.commands = []

    def adjust_volume(self, command):
        self.commands.append(command)
        return "Volume aggiornato."


class CommandRouterTests(unittest.TestCase):
    def setUp(self):
        self.ai = FakeAI()
        self.email = FakeEmail()
        self.news = FakeNews()
        self.system = FakeSystem()
        self.audio = FakeAudio()
        self.router = CommandRouter(
            self.ai, self.email, self.news, self.system, self.audio
        )

    def test_general_prompt_strips_jarvis_wake_word(self):
        response = self.router.handle("Jarvis, spiegami la memoria locale")

        self.assertEqual(response, "Risposta AI")
        self.assertEqual(self.ai.prompts, ["spiegami la memoria locale"])
        self.assertEqual(self.ai.memory.messages, [])

    def test_email_command_routes_and_records_both_messages(self):
        response = self.router.handle("Controlla la posta in arrivo")

        self.assertEqual(response, "Hai due email non lette.")
        self.assertEqual(self.email.calls, 1)
        self.assertEqual(
            self.ai.memory.messages,
            [
                {"role": "user", "content": "Controlla la posta in arrivo"},
                {"role": "assistant", "content": "Hai due email non lette."},
            ],
        )

    def test_news_command_routes_to_news_service(self):
        self.assertEqual(self.router.handle("Dimmi le notizie"), "Ecco le notizie.")
        self.assertEqual(self.news.calls, 1)

    def test_weather_follow_up_keeps_city_until_date_is_given(self):
        prompt = self.router.handle("Meteo a Milano")
        self.assertIn("quale giorno", prompt.lower())
        self.assertEqual(self.system.weather_calls, [])

        result = self.router.handle("domani")

        self.assertEqual(result, "Meteo simulato.")
        self.assertEqual(
            self.system.weather_calls,
            [(date.today() + timedelta(days=1), "Milano")],
        )

    def test_weather_with_date_and_city_routes_immediately(self):
        result = self.router.handle("Che tempo fa domani a Torino?")

        self.assertEqual(result, "Meteo simulato.")
        self.assertEqual(
            self.system.weather_calls,
            [(date.today() + timedelta(days=1), "Torino")],
        )

    def test_open_site_and_program_use_their_matching_actions(self):
        self.assertEqual(self.router.handle("Apri Gmail"), "Sito aperto.")
        self.assertEqual(self.router.handle("Apri calcolatrice"), "Programma aperto.")
        self.assertEqual(self.system.websites, ["gmail"])
        self.assertEqual(self.system.programs, ["calcolatrice"])

    def test_search_preserves_the_user_query(self):
        self.assertEqual(
            self.router.handle("Cerca ricette per la cena"),
            "Ricerca avviata.",
        )
        self.assertEqual(self.system.searches, ["ricette per la cena"])


if __name__ == "__main__":
    unittest.main()
