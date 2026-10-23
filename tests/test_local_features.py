import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from core.local_features import LocalCommandService, LocalStore, parse_reminder


class FakeActions:
    class System:
        @staticmethod
        def get_time():
            return "Sono le 10:00."
    system = System()


class LocalFeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = LocalStore(Path(self.temp_dir.name) / "test.db")
        self.commands = LocalCommandService(self.store, clock=lambda: datetime(2026, 10, 23, 8, 0))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_relative_and_tomorrow_due_dates(self):
        now = datetime(2026, 10, 23, 8, 0)
        self.assertEqual(parse_reminder("ricordami di chiamare tra 10 minuti", now),
                         ("chiamare", now + timedelta(minutes=10)))
        self.assertEqual(parse_reminder("ricordami di comprare il latte domani alle 9", now),
                         ("comprare il latte", datetime(2026, 10, 24, 9, 0)))
        self.assertEqual(parse_reminder("ricordami di fare pausa tra mezz'ora", now),
                         ("fare pausa", now + timedelta(minutes=30)))
        self.assertEqual(parse_reminder("ricordami di bere acqua tra 1 ora", now),
                         ("bere acqua", now + timedelta(hours=1)))

    def test_create_list_complete_and_delete_reminders(self):
        reply = self.commands.handle("ricordami di fare la spesa domani alle 9", FakeActions())
        self.assertIn("Attività 1 salvata", reply)
        self.assertIn("fare la spesa", self.commands.handle("mostra promemoria", FakeActions()))
        self.assertEqual(self.commands.handle("completa promemoria 1", FakeActions()), "Attività completata.")
        self.assertEqual(self.store.list_reminders(), [])
        self.store.add_reminder("da eliminare")
        self.assertTrue(self.store.delete_reminder(2))

    def test_due_notifications_are_returned_once(self):
        now = datetime(2026, 10, 23, 8, 0)
        self.store.add_reminder("scaduto", now - timedelta(minutes=1))
        self.store.add_reminder("futuro", now + timedelta(hours=1))
        self.assertEqual(len(self.store.take_due(now)), 1)
        self.assertEqual(self.store.take_due(now), [])

    def test_preferences_and_routines_persist_locally(self):
        self.store.set_preference("voice_replies", True)
        self.assertTrue(self.store.get_preferences()["voice_replies"])
        self.store.set_preference("llm_provider", "ollama")
        self.assertEqual(self.store.get_preferences()["llm_provider"], "ollama")
        self.store.save_routine("modalità lavoro", ["time"])
        self.assertEqual(self.store.list_routines(), [("modalità lavoro", ["time"])])
        with self.assertRaises(ValueError):
            self.store.save_routine("pericolosa", ["execute_arbitrary_code"])

    def test_routine_requires_yes_confirmation_and_no_cancels(self):
        self.store.save_routine("modalità lavoro", ["time"])
        prompt = self.commands.handle("avvia modalità lavoro", FakeActions())
        self.assertIn("Vuoi procedere", prompt)
        self.assertEqual(self.commands.handle("no", FakeActions()), "Routine annullata.")
        self.commands.handle("avvia modalità lavoro", FakeActions())
        self.assertIn("completata", self.commands.handle("sì", FakeActions()))


if __name__ == "__main__":
    unittest.main()
