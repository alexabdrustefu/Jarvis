import tempfile
import unittest
from datetime import date
from pathlib import Path

from demo import DemoAI, DemoAudio, DemoEmail, DemoNews, DemoSystem


class DemoTests(unittest.TestCase):
    def test_demo_ai_uses_local_history_and_deterministic_offline_reply(self):
        with tempfile.TemporaryDirectory() as folder:
            ai = DemoAI(Path(folder) / "demo.db")

            reply = ai.chat("Ciao")

            self.assertIn("dimostrativa offline", reply)
            self.assertEqual(
                [message["role"] for message in ai.memory.get_recent_messages()],
                ["assistant", "user", "assistant"],
            )

    def test_demo_adapters_never_claim_live_actions(self):
        system = DemoSystem()

        self.assertIn("Dato simulato", system.get_weather_for_date(date.today(), "Milano"))
        self.assertIn("non ho aperto", system.open_website("Google"))
        self.assertIn("simulata", system.search_google("ricette"))
        self.assertIn("non è stato modificato", DemoAudio.adjust_volume("volume 40"))
        self.assertIn("non viene contattata", DemoEmail().get_unread_emails_summary())
        self.assertIn("simulati", DemoNews().get_daily_news_summary())


if __name__ == "__main__":
    unittest.main()
