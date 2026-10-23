"""Background-safe system diagnostics for the desktop settings view."""

import importlib.util


def collect_diagnostics(store, router, microphone, groq_configured=False):
    try:
        store.health_check()
        database = "OK"
    except Exception:
        database = "non accessibile"

    ai = getattr(router, "ai", None) if router is not None else None
    try:
        llm_status = ai.provider_status() if hasattr(ai, "provider_status") else {}
    except Exception:
        llm_status = {}

    checks = [
        f"SQLite locale: {database}",
        f"Ollama {llm_status.get('ollama_model', 'qwen3:4b')}: "
        f"{'pronto' if llm_status.get('ollama_available') else 'non avviato / modello assente'}",
        f"LM Studio: {'pronto' if llm_status.get('lmstudio_available') else 'server locale non avviato'}",
        f"Groq opzionale: {'chiave configurata' if groq_configured else 'non configurato'}",
        "Lettura vocale: " + (
            "OK" if importlib.util.find_spec("edge_tts") and importlib.util.find_spec("playsound")
            else "dipendenze mancanti"
        ),
    ]
    try:
        names = microphone.list_microphone_names() if microphone else []
        checks.append(f"Microfono: {'OK (' + str(len(names)) + ')' if names else 'non rilevato'}")
    except Exception:
        checks.append("Microfono: non disponibile o permesso mancante")
    return checks
