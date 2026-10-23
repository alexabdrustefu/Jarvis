import tempfile
import unittest
from pathlib import Path

from memory.facts_memory import FactsMemory
from memory.long_term import LongTermMemory


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "memory.db"
        self.messages = LongTermMemory(self.database)
        self.facts = FactsMemory(self.database)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_recent_messages_are_returned_in_chronological_order(self):
        self.messages.add_message("user", "Ciao")
        self.messages.add_message("assistant", "Salve")
        self.messages.add_message("user", "Come stai?")

        self.assertEqual(
            self.messages.get_recent_messages(limit=2),
            [
                {"role": "assistant", "content": "Salve"},
                {"role": "user", "content": "Come stai?"},
            ],
        )

    def test_timestamp_history_and_incremental_sync(self):
        self.messages.add_message("user", "Primo")
        first, = self.messages.get_recent_messages_with_timestamps()
        self.messages.add_message("assistant", "Secondo")

        recent = self.messages.get_recent_messages_with_timestamps()
        self.assertTrue(recent[0]["created_at"])
        self.assertLess(recent[0]["id"], recent[1]["id"])
        self.assertEqual(
            self.messages.get_messages_after_id(first["id"]),
            [recent[1]],
        )

    def test_clear_removes_conversation_but_keeps_facts(self):
        self.messages.add_message("user", "Ciao")
        self.facts.remember("colore", "blu")

        self.messages.clear()

        self.assertEqual(self.messages.get_recent_messages(), [])
        self.assertEqual(self.facts.get("colore"), "blu")

    def test_invalid_message_role_and_limit_are_rejected(self):
        with self.assertRaises(ValueError):
            self.messages.add_message("system", "Prompt")
        with self.assertRaises(ValueError):
            self.messages.get_recent_messages(limit=0)
        with self.assertRaises(ValueError):
            self.messages.get_recent_messages_with_timestamps(limit=0)

    def test_fact_keys_and_values_are_trimmed_and_updated(self):
        self.facts.remember("  city  ", "  Rome  ")
        self.facts.remember("city", "Turin")

        self.assertEqual(self.facts.get(" city "), "Turin")
        self.assertEqual(self.facts.get_all(), {"city": "Turin"})

    def test_empty_facts_are_rejected(self):
        with self.assertRaises(ValueError):
            self.facts.remember("", "value")
        with self.assertRaises(ValueError):
            self.facts.remember("key", " ")

    def test_forget_reports_whether_a_fact_existed(self):
        self.facts.remember("city", "Rome")

        self.assertTrue(self.facts.forget(" city "))
        self.assertFalse(self.facts.forget("city"))
        self.assertIsNone(self.facts.get("city"))


if __name__ == "__main__":
    unittest.main()
