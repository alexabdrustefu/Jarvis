import unittest
import json
from unittest.mock import patch

from ai.providers import LMStudioProvider, OllamaProvider, choose_provider


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class ProviderSelectionTests(unittest.TestCase):
    def test_simple_request_stays_local(self):
        self.assertEqual(choose_provider("ciao", "auto", groq_available=True), "ollama")

    def test_complex_request_without_local_large_model_stays_free_and_local(self):
        self.assertEqual(choose_provider("Analizza e confronta le alternative.", "auto", groq_available=True), "ollama")

    def test_private_request_stays_local_even_when_complex(self):
        message = "Analizza in dettaglio i miei dati personali e ricordati il mio indirizzo di casa"
        self.assertEqual(choose_provider(message, "auto", groq_available=True), "ollama")

    def test_first_person_sensitive_context_stays_local(self):
        self.assertEqual(choose_provider("Progetta un piano per il mio trasferimento.", "auto", groq_available=True), "ollama")

    def test_sensitive_health_request_stays_local(self):
        self.assertEqual(choose_provider("Analizza in dettaglio il mio referto medico.", "auto",
                                         groq_available=True, lmstudio_available=False), "ollama")

    def test_no_hosted_key_means_local_for_every_context(self):
        self.assertEqual(choose_provider("Progetta in dettaglio una soluzione.", "auto", groq_available=False), "ollama")

    def test_complex_request_prefers_available_local_lm_studio(self):
        self.assertEqual(choose_provider("Analizza le opzioni.", "auto", groq_available=True,
                                          lmstudio_available=True), "lmstudio")

    def test_groq_is_used_only_when_explicitly_selected(self):
        self.assertEqual(choose_provider("Analizza le opzioni.", "auto", groq_available=True,
                                          lmstudio_available=False), "ollama")
        self.assertEqual(choose_provider("ciao", "groq", groq_available=True), "groq")
        self.assertEqual(choose_provider("ciao", "groq", groq_available=False), "ollama")

    def test_explicit_local_preference(self):
        self.assertEqual(choose_provider("Analizza", "ollama", groq_available=True), "ollama")

    def test_explicit_lm_studio_preference(self):
        self.assertEqual(choose_provider("ciao", "lmstudio", groq_available=False), "lmstudio")


class LocalProviderClientTests(unittest.TestCase):
    def test_ollama_client_sends_non_streaming_chat_request(self):
        response = FakeResponse({"message": {"content": "Risposta locale"}})
        with patch("ai.providers.urlopen", return_value=response) as open_url:
            result = OllamaProvider(base_url="http://localhost:11434", model="qwen3:4b").chat(
                [{"role": "user", "content": "ciao"}], 30
            )
        self.assertEqual(result, "Risposta locale")
        request = open_url.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "http://localhost:11434/api/chat")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["num_predict"], 30)

    def test_lm_studio_client_uses_compatible_chat_endpoint(self):
        response = FakeResponse({"choices": [{"message": {"content": "Risposta locale"}}]})
        with patch("ai.providers.urlopen", return_value=response) as open_url:
            result = LMStudioProvider(model="local-model").chat(
                [{"role": "user", "content": "ciao"}], 30
            )
        self.assertEqual(result, "Risposta locale")
        request = open_url.call_args.args[0]
        payload = json.loads(request.data)
        self.assertTrue(request.full_url.endswith("/chat/completions"))
        self.assertEqual(payload["model"], "local-model")
        self.assertFalse(payload["stream"])


if __name__ == "__main__":
    unittest.main()
