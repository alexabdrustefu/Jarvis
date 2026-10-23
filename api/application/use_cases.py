"""Application services exposed by the versioned REST adapter."""

from __future__ import annotations

from datetime import datetime

from api.application.ports import TelemetryRepository
from api.presentation.contracts import ApiError, MenuItem, ReminderRequest


class ApiService:
    """Use-case layer between HTTP routes and the shared JARVIS core."""

    MENU = (
        MenuItem("chat", "Chat", "Invia una richiesta all'assistente.", "/api/v1/chat", ("POST",)),
        MenuItem("reminders", "Promemoria", "Elenca e gestisce le attività locali.", "/api/v1/reminders", ("GET", "POST", "PATCH", "DELETE")),
        MenuItem("routines", "Routine", "Elenca le routine configurate.", "/api/v1/routines", ("GET",)),
        MenuItem("statistics", "Statistiche", "Mostra conteggi aggregati locali.", "/api/v1/stats", ("GET",)),
        MenuItem("diagnostics", "Diagnostica", "Stato API e provider AI.", "/api/v1/health", ("GET",)),
    )

    def __init__(self, router, store, ai=None, telemetry: TelemetryRepository | None = None):
        self.router = router
        self.store = store
        self.ai = ai or getattr(router, "ai", None)
        self.telemetry = telemetry

    def menu(self):
        return {"items": [item.as_dict() for item in self.MENU]}

    def health(self):
        ai = self.ai
        provider_status = ai.provider_status() if hasattr(ai, "provider_status") else {}
        return {"status": "ok", "service": "J.A.R.V.I.S.", "version": "1.0.0", "providers": provider_status}

    def statistics(self):
        ai = self.ai
        memory = getattr(ai, "memory", None)
        facts = getattr(ai, "facts", None)
        return {
            "conversations": memory.get_statistics() if hasattr(memory, "get_statistics") else {},
            "facts": {"saved": facts.count() if hasattr(facts, "count") else 0},
            "productivity": self.store.get_statistics(),
            "api": self.telemetry.statistics() if self.telemetry is not None else {},
            "provider": getattr(ai, "last_provider", None),
        }

    def reminders(self, include_done=False):
        return {"items": [self._reminder(row) for row in self.store.list_reminders(include_done=include_done)]}

    def create_reminder(self, payload):
        request = ReminderRequest.parse(payload)
        reminder_id = self.store.add_reminder(request.title, request.due_at)
        return {"id": reminder_id, "title": request.title,
                "due_at": self._iso_datetime(request.due_at),
                "status": "pending"}

    def complete_reminder(self, reminder_id, payload):
        if not isinstance(payload, dict) or payload.get("status") != "done":
            raise ApiError(400, "invalid_status", "Per completare un promemoria invia {\"status\":\"done\"}.")
        if not self.store.complete_reminder(reminder_id):
            raise ApiError(404, "reminder_not_found", "Promemoria inesistente o già completato.")
        return {"id": reminder_id, "status": "done"}

    def delete_reminder(self, reminder_id):
        if not self.store.delete_reminder(reminder_id):
            raise ApiError(404, "reminder_not_found", "Promemoria non trovato.")
        return {"id": reminder_id, "deleted": True}

    def routines(self):
        return {"items": [{"name": name, "steps": steps} for name, steps in self.store.list_routines()]}

    @staticmethod
    def _reminder(row):
        due_at = None
        if row[2]:
            due_at = ApiService._iso_datetime(datetime.fromisoformat(row[2]))
        return {"id": row[0], "title": row[1], "due_at": due_at, "status": row[3]}

    @staticmethod
    def _iso_datetime(value):
        return value.astimezone().isoformat(timespec="minutes") if value else None
