"""Free local and optional hosted chat providers."""

from __future__ import annotations

import json
import os
import re
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


def needs_complex_provider(message: str) -> bool:
    text = message.casefold()
    return len(text.split()) >= 35 or any(
        re.search(pattern, text) for pattern in (
            r"\b(analizza|confronta|progetta|scrivi|debug|spiega|piano|approfondisci)\b",
            r"\b(passaggio per passaggio|in dettaglio|più opzioni)\b",
        )
    )


def choose_provider(message: str, preference: str, *, groq_available: bool,
                    lmstudio_available: bool = False) -> str:
    """Choose a local model automatically; cloud use requires explicit selection."""
    if preference == "groq":
        return "groq" if groq_available else "ollama"
    if preference == "ollama":
        return preference
    if preference == "lmstudio":
        return "lmstudio"
    if preference != "auto":
        return "ollama"
    text = " " + message.casefold() + " "
    private = any(word in text for word in (
        "ricord", "memorizz", "password", "indirizzo", "telefono", "personale",
        "medic", "salute", "diagnos", "finanz", "banca", "conto corrente",
        "carta di credito", "codice fiscale", "documento personale", " email ",
        " mio ", " mia ", " miei ", " mie ", " mi chiamo ", " mio ",
    ))
    complex_request = needs_complex_provider(message)
    if complex_request and not private and lmstudio_available:
        return "lmstudio"
    # Automatic mode never reaches a hosted service, even when a cloud key exists.
    return "ollama"


class OllamaProvider:
    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")
        self.timeout = float(timeout or os.getenv("OLLAMA_TIMEOUT", "90"))

    def chat(self, messages, max_tokens, *, json_mode=False):
        payload = {"model": self.model, "messages": messages, "stream": False,
                   "options": {"num_predict": max_tokens}}
        if json_mode:
            payload["format"] = "json"
        request = Request(self.base_url + "/api/chat", data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body.get("message", {}).get("content", "")
        except Exception as error:
            raise ProviderError(
                f"Ollama non disponibile ({self.model}). Installa Ollama e avvia il modello con: ollama pull {self.model}. Dettaglio: {error}"
            ) from error

    def available(self):
        try:
            with urlopen(self.base_url + "/api/tags", timeout=1) as response:
                models = json.loads(response.read().decode("utf-8")).get("models", [])
            return any(item.get("name", "").split(":")[0] == self.model.split(":")[0] for item in models)
        except Exception:
            return False


class LMStudioProvider:
    """LM Studio's local OpenAI-compatible endpoint; no paid SDK is required."""

    def __init__(self, base_url=None, model=None, timeout=None, api_key=None):
        self.base_url = (base_url or os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1")).rstrip("/")
        self.model = model or os.getenv("LM_STUDIO_MODEL", "")
        self.timeout = float(timeout or os.getenv("LM_STUDIO_TIMEOUT", "0.5"))
        self.api_key = api_key or os.getenv("LM_STUDIO_API_KEY")

    def _models(self):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        request = Request(self.base_url + "/models", headers=headers)
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8")).get("data", [])

    def available(self):
        try:
            models = self._models()
            return bool(models) and (not self.model or any(item.get("id") == self.model for item in models))
        except Exception:
            return False

    def chat(self, messages, max_tokens, *, json_mode=False):
        try:
            models = self._models() if not self.model else []
            model = self.model or (models[0].get("id") if models else None)
            if not model:
                raise ProviderError("Carica un modello nel server LM Studio.")
            payload = {"model": model, "messages": messages, "stream": False,
                       "max_tokens": max_tokens}
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            request = Request(self.base_url + "/chat/completions", data=json.dumps(payload).encode(),
                              headers=headers, method="POST")
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"].get("content", "") or ""
        except Exception as error:
            if isinstance(error, ProviderError):
                raise
            raise ProviderError(f"LM Studio non disponibile. Avvia il server locale e carica un modello. Dettaglio: {error}") from error
