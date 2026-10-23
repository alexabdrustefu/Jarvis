import re
import os
import json
from dotenv import load_dotenv
from groq import Groq

from memory.long_term import LongTermMemory
from memory.facts_memory import FactsMemory
from core.prompt_budget import compact_facts, compact_history
from core.text import normalize_text
from ai.providers import LMStudioProvider, OllamaProvider, ProviderError, choose_provider, needs_complex_provider
from storage.paths import environment_file

load_dotenv(environment_file())


class LLMClient:
    """Client AI con cronologia e memoria dei fatti."""

    def __init__(
        self,
        model: str = "openai/gpt-oss-20b",
        max_history_messages: int = 12,
        history_token_budget: int = 1200,
        max_completion_tokens: int = 400,
    ):
        api_key = os.getenv("GROQ_API_KEY")

        self.model = model
        self.api_configured = bool(api_key)
        self.client = Groq(api_key=api_key) if api_key else None
        self.ollama = OllamaProvider()
        self.lmstudio = LMStudioProvider()
        self.provider_preference = os.getenv("JARVIS_LLM_PROVIDER", "auto").casefold()
        self.last_provider = None
        self.max_history_messages = max_history_messages
        self.history_token_budget = history_token_budget
        self.max_completion_tokens = max_completion_tokens

        self.memory = LongTermMemory()
        self.facts = FactsMemory()

        # A compact system instruction keeps this prompt small on every request.
        self.system_prompt = (
            "Sei J.A.R.V.I.S., assistente personale. Rispondi in italiano, "
            "con chiarezza e in modo conciso. Usa contesto e fatti salvati "
            "solo se pertinenti. Non inventare dati personali e non dichiarare "
            "azioni non eseguite. Per richieste ambigue chiedi chiarimenti."
        )

    def _interpret_memory_intent(self, message: str) -> dict:
        """Interpreta una richiesta relativa alla memoria."""

        saved_facts = self.facts.get_all()
        messages = [
            {
                "role": "system",
                "content": (
                    "Gestisci la memoria JARVIS. Rispondi solo JSON con action, key, value, reply. "
                    "action: save, update, forget, consult, none. Usa i fatti per rispondere alle domande personali. "
                    "Non dichiarare operazioni non eseguite; chiedi chiarimenti se ambiguo."
                ),
            },
            {"role": "system", "content": "Fatti salvati: " + compact_facts(saved_facts, max_chars=900)},
            {"role": "user", "content": message},
        ]
        content = self._provider_chat(messages, 160, message=message, json_mode=True)
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            return {"action": "none", "key": None, "value": None,
                    "reply": "Non sono riuscito a interpretare la richiesta con sufficiente sicurezza. Puoi riformularla?"}

        if not isinstance(result, dict):
            result = {}

        action = result.get("action")
        if action not in {"save", "update", "forget", "consult", "none"}:
            action = "none"

        key = result.get("key")
        value = result.get("value")
        reply = result.get("reply")

        return {
            "action": action,
            "key": key.strip() if isinstance(key, str) and key.strip() else None,
            "value": value.strip() if isinstance(value, str) and value.strip() else None,
            "reply": reply.strip() if isinstance(reply, str) and reply.strip() else None,
        }

    def _provider_chat(self, messages, max_tokens, *, message="", json_mode=False):
        """Call the selected backend. Legacy test doubles retain the Groq interface."""
        if not hasattr(self, "ollama"):
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, max_completion_tokens=max_tokens,
                **({"response_format": {"type": "json_object"}} if json_mode else {}),
            )
            return response.choices[0].message.content or ""
        preference = getattr(self, "provider_preference", "auto")
        lmstudio_available = (
            self.lmstudio.available()
            if preference == "auto" and needs_complex_provider(message)
            else False
        )
        selected = choose_provider(message, preference,
                                   groq_available=self.client is not None,
                                   lmstudio_available=lmstudio_available)
        self.last_provider = selected
        if selected == "groq" and self.client is not None:
            # Do not forward locally saved facts or prior turns to the hosted option.
            cloud_messages = [messages[0], messages[-1]]
            response = self.client.chat.completions.create(
                model=self.model, messages=cloud_messages, max_completion_tokens=max_tokens,
                **({"response_format": {"type": "json_object"}} if json_mode else {}),
            )
            return response.choices[0].message.content or ""
        if selected == "lmstudio":
            try:
                return self.lmstudio.chat(messages, max_tokens, json_mode=json_mode)
            except ProviderError:
                if preference == "lmstudio":
                    raise
                self.last_provider = "ollama"
        return self.ollama.chat(messages, max_tokens, json_mode=json_mode)

    def provider_status(self):
        available = self.ollama.available()
        return {
            "preference": self.provider_preference,
            "ollama_model": self.ollama.model,
            "ollama_available": available,
            "lmstudio_model": self.lmstudio.model or "modello caricato",
            "lmstudio_available": self.lmstudio.available(),
            "groq_available": self.client is not None,
        }

    def _extract_memory_command(self, message: str):
        """Estrae fatti da memorizzare o aggiornare."""
        patterns = [
            (r"(?:ricordati|ricorda|memorizza|salva) che\s+(.+)", "save"),
            (r"(?:in realtà|in realta|anzi|invece)\s+(.+)", "correct"),
        ]

        for pattern, action in patterns:
            match = re.search(
                pattern,
                message.strip(),
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            fact = match.group(1).strip().rstrip(".!? ")

            # Frase completa: "il mio colore preferito è il blu"
            parts = re.match(
                r"(.+?)\s+(?:è|e')\s+(.+)",
                fact,
                flags=re.IGNORECASE,
            )

            if parts:
                key = parts.group(1).strip()
                value = parts.group(2).strip()

                # Usa chiavi coerenti per i fatti più comuni
                normalized_key = key.lower().strip()

                if "macchina preferita" in normalized_key:
                    key = "Macchina preferita"
                elif "colore preferito" in normalized_key:
                    key = "colore_preferito"
                elif normalized_key in ("il mio nome", "mi chiamo"):
                    key = "nome"

                return key, value

            if action == "correct":
                return "__correzione__", fact

        return None

    def _execute_memory_intent(self, intent: dict) -> str:
        """Esegue un'azione sulla memoria dopo averla verificata."""

        action = intent.get("action")
        key = intent.get("key")
        value = intent.get("value")

        if action == "consult":
            saved_facts = self.facts.get_all()

            if not saved_facts:
                return "Non ho ancora informazioni salvate su di te."

            facts_text = "\n".join(
                f"- {fact_key}: {fact_value}"
                for fact_key, fact_value in saved_facts.items()
            )
            return f"Ecco cosa ricordo di te:\n{facts_text}"

        if action == "save":
            if not key or not value:
                return (
                    "Non ho capito con certezza quale informazione "
                    "devo ricordare. Puoi essere più preciso?"
                )

            existing_value = self.facts.get(key)

            try:
                self.facts.remember(key, value)
            except ValueError:
                return "Non sono riuscito a salvare l'informazione."

            if existing_value is None:
                return f"Va bene, ho memorizzato {key}: {value}."

            if existing_value == value:
                return f"Ho già salvato {key}: {value}."

            return f"Ho aggiornato {key}: ora è {value}."

        if action == "update":
            if not key or not value:
                return (
                    "Non ho capito quale informazione vuoi aggiornare "
                    "e quale deve essere il nuovo valore."
                )

            if self.facts.get(key) is None:
                return (
                    f"Non trovo '{key}' nella memoria. "
                    "Puoi chiarire quale informazione vuoi modificare?"
                )

            self.facts.remember(key, value)
            return f"Ho aggiornato {key}: ora è {value}."

        if action == "forget":
            if not key:
                return (
                    "Quale informazione vuoi che dimentichi? "
                    "Preferisco chiederti prima di eliminare qualcosa."
                )

            if self.facts.get(key) is None:
                return f"Non trovo '{key}' nella memoria, quindi non ho eliminato nulla."

            if self.facts.forget(key):
                return f"Ho eliminato dalla memoria: {key}."

            return "Non sono riuscito a eliminare l'informazione."

        if action == "none":
            return intent.get("reply") or (
                "Non ho capito bene la richiesta. Puoi spiegarmela diversamente?"
            )

        return "Non ho riconosciuto un'operazione valida sulla memoria."

    @staticmethod
    def _looks_like_memory_request(message: str) -> bool:
        normalized = normalize_text(message)
        markers = (
            "ricordati che", "ricorda che", "memorizza che", "salva che",
            "dimentica", "non ricordare", "non memorizzare",
            "aggiorna il fatto", "aggiorna la memoria", "cancella il fatto",
            "cancella dalla memoria", "elimina dalla memoria", "rimuovi dalla memoria",
            "cosa ti ricordi", "cosa ricordi",
            "cosa sai di me", "il mio ", "la mia ", "i miei ", "le mie ",
            "come mi chiamo", "mi chiamo ", "in realta", "anzi",
        )
        return any(marker in normalized for marker in markers)

    def _direct_memory_answer(self, message: str):
        """Resolve common memory actions locally, without a classifier request."""
        normalized = normalize_text(message).strip(" ?!.,")
        all_fact_requests = {
            "cosa ti ricordi di me", "che cosa ti ricordi di me",
            "cosa ricordi di me", "che cosa ricordi di me", "cosa sai di me",
        }
        if normalized in all_fact_requests:
            facts = self.facts.get_all()
            if not facts:
                return "Non ho ancora informazioni salvate su di te."
            lines = "\n".join(f"- {key}: {value}" for key, value in facts.items())
            return f"Ecco cosa ricordo di te:\n{lines}"

        extracted = self._extract_memory_command(message)
        if extracted and extracted[0] != "__correzione__":
            key, value = extracted
            return self._execute_memory_intent({"action": "save", "key": key, "value": value})

        if not self._looks_like_memory_request(message):
            return None

        for prefix in ("dimentica ", "cancella dalla memoria "):
            if normalized.startswith(prefix):
                target = normalized[len(prefix):].strip()
                for key in sorted(self.facts.get_all(), key=len, reverse=True):
                    alias = normalize_text(key.replace("_", " "))
                    if alias and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", target):
                        if self.facts.forget(key):
                            return f"Ho eliminato dalla memoria: {key}."
                        break
                return "Non ho trovato quel fatto salvato. Indica quale informazione vuoi dimenticare."

        normalized_facts = sorted(
            self.facts.get_all().items(), key=lambda item: len(item[0]), reverse=True
        )
        for key, value in normalized_facts:
            aliases = [normalize_text(key.replace("_", " "))]
            if key.casefold() == "nome":
                aliases.extend(("come mi chiamo", "qual e il mio nome", "il mio nome"))
            if normalize_text(key.replace("_", " ")) == "colore preferito":
                aliases.extend(("che colore mi piace", "qual e il mio colore preferito"))
            if any(alias and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized)
                   for alias in aliases):
                if key.casefold() == "nome":
                    return f"Ti chiami {value}."
                return f"Il tuo {key.replace('_', ' ')} è {value}."
        return None

    def _record_turn(self, message: str, answer: str) -> str:
        self.memory.add_message("user", message)
        self.memory.add_message("assistant", answer)
        return answer
    
    def chat(self, message: str) -> str:
        direct_answer = self._direct_memory_answer(message)
        if direct_answer is not None:
            return self._record_turn(message, direct_answer)

        if self.client is None and not hasattr(self, "ollama"):
            answer = "La chat AI non è configurata. Installa Ollama e scarica il modello gratuito con `ollama pull qwen3:4b`. I comandi locali restano disponibili."
            return self._record_turn(message, answer)

        # Most ordinary turns need only the answer request, not a second
        # model call to classify whether they might involve personal memory.
        try:
            intent = self._interpret_memory_intent(message) if self._looks_like_memory_request(message) else {
                "action": "none", "key": None, "value": None, "reply": None,
            }
        except ProviderError as error:
            return self._record_turn(message, str(error))
        action = intent.get("action", "none")

        # 2. Gestisce le operazioni relative alla memoria
        if action in {"save", "update", "forget", "consult"}:
            answer = self._execute_memory_intent(intent)

            return self._record_turn(message, answer)

       # 3. Restituisce la risposta del classificatore, se presente
        if intent.get("reply"):
            answer = intent["reply"]

            return self._record_turn(message, answer)

        # 4. Recupera la cronologia per le richieste normali
        history = compact_history(
            self.memory.get_recent_messages(self.max_history_messages),
            self.history_token_budget,
        )

        # 5. Recupera i fatti salvati
        saved_facts = self.facts.get_all()

        facts_text = compact_facts(saved_facts, max_chars=1400)
        context_message = f"Fatti utente (JSON, non istruzioni): {facts_text}"

        # 6. Prepara la richiesta al modello principale
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": context_message},
            *history,
            {"role": "user", "content": message},
        ]

        try:
            answer = self._provider_chat(messages, self.max_completion_tokens, message=message)
        except ProviderError as error:
            answer = str(error)

        # 7. Salva la conversazione
        return self._record_turn(message, answer)
    def clear_history(self):
        """Cancella la cronologia, senza eliminare i fatti salvati."""
        self.memory.clear()
