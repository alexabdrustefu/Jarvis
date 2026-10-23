import unittest

from gui.services.diagnostics import collect_diagnostics


class Store:
    def health_check(self):
        return True


class AI:
    def provider_status(self):
        return {"ollama_available": True, "ollama_model": "qwen3:4b", "lmstudio_available": False}


class Microphone:
    def list_microphone_names(self):
        return ["Microphone"]


class DiagnosticsTests(unittest.TestCase):
    def test_collects_statuses_without_ui_dependencies(self):
        checks = collect_diagnostics(Store(), type("Router", (), {"ai": AI()})(), Microphone(), True)
        self.assertIn("SQLite locale: OK", checks)
        self.assertIn("Ollama qwen3:4b: pronto", checks)
        self.assertIn("Groq opzionale: chiave configurata", checks)
        self.assertIn("Microfono: OK (1)", checks)

    def test_reports_database_and_microphone_failures(self):
        class BrokenStore:
            def health_check(self):
                raise OSError("unavailable")

        class BrokenMicrophone:
            def list_microphone_names(self):
                raise RuntimeError("permission denied")

        checks = collect_diagnostics(BrokenStore(), None, BrokenMicrophone())
        self.assertIn("SQLite locale: non accessibile", checks)
        self.assertIn("Microfono: non disponibile o permesso mancante", checks)


if __name__ == "__main__":
    unittest.main()
