import unittest
from types import SimpleNamespace

from ai.llm_client import LLMClient
from core.prompt_budget import compact_facts, compact_history, estimate_tokens


class FakeMemory:
    def __init__(self, history=None):
        self.history = history or []
        self.saved = []

    def get_recent_messages(self, limit):
        return self.history[-limit:]

    def add_message(self, role, content):
        self.saved.append((role, content))


class FakeFacts:
    def __init__(self, values=None):
        self.values = values or {}

    def get_all(self):
        return self.values.copy()

    def get(self, key):
        return self.values.get(key)

    def remember(self, key, value):
        self.values[key] = value

    def forget(self, key):
        return self.values.pop(key, None) is not None


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Risposta breve."))])


class PromptBudgetTests(unittest.TestCase):
    def test_history_keeps_recent_turns_within_character_budget(self):
        history = [{"role": "user", "content": f"messaggio {index}"} for index in range(20)]
        compacted = compact_history(history, token_budget=30)
        self.assertLessEqual(sum(len(item["content"]) + 12 for item in compacted), 30 * 4)
        self.assertEqual(compacted[-1]["content"], "messaggio 19")
        self.assertLess(len(compacted), len(history))

    def test_oversized_latest_message_is_tail_truncated(self):
        result = compact_history([{"role": "user", "content": "x" * 1000}], token_budget=20)
        self.assertEqual(len(result), 1)
        self.assertLessEqual(estimate_tokens(result[0]["content"]), 20)

    def test_fact_context_is_compacted(self):
        serialized = compact_facts({f"fatto_{index}": "valore" * 40 for index in range(20)}, max_chars=150)
        self.assertLessEqual(len(serialized), 150)

    def make_client(self, facts=None):
        client = LLMClient.__new__(LLMClient)
        completions = FakeCompletions()
        client.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        client.model = "test-model"
        client.memory = FakeMemory([{"role": "assistant", "content": "contesto " * 200} for _ in range(12)])
        client.facts = FakeFacts(facts)
        client.max_history_messages = 12
        client.history_token_budget = 100
        client.max_completion_tokens = 80
        client.system_prompt = "Rispondi in modo conciso."
        return client, completions

    def test_normal_chat_uses_one_request_with_bounded_context_and_output(self):
        client, completions = self.make_client()
        self.assertEqual(client.chat("Spiegami la fotosintesi."), "Risposta breve.")
        self.assertEqual(len(completions.calls), 1)
        request = completions.calls[0]
        self.assertEqual(request["max_completion_tokens"], 80)
        self.assertLessEqual(sum(len(message["content"]) for message in request["messages"]), 500)

    def test_known_fact_query_is_answered_without_ai_request(self):
        client, completions = self.make_client({"colore_preferito": "blu"})
        self.assertIn("blu", client.chat("Qual è il mio colore preferito?"))
        self.assertEqual(completions.calls, [])

    def test_explicit_fact_save_is_local_without_ai_request(self):
        client, completions = self.make_client()
        self.assertIn("memorizzato", client.chat("Ricordati che il mio colore preferito è blu"))
        self.assertEqual(client.facts.values["colore_preferito"], "blu")
        self.assertEqual(completions.calls, [])

    def test_known_fact_deletion_is_local(self):
        client, completions = self.make_client({"colore_preferito": "blu"})
        self.assertIn("eliminato", client.chat("Dimentica il mio colore preferito"))
        self.assertEqual(client.facts.values, {})
        self.assertEqual(completions.calls, [])


if __name__ == "__main__":
    unittest.main()
