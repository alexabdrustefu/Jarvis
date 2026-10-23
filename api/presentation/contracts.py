"""Transport-independent request and response contracts for the HTTP API."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def as_dict(self):
        return {"error": {"code": self.code, "message": self.message}}


@dataclass(frozen=True)
class ChatRequest:
    message: str

    @classmethod
    def parse(cls, payload):
        if not isinstance(payload, dict):
            raise ApiError(400, "invalid_request", "Il body deve essere un oggetto JSON.")
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            raise ApiError(400, "invalid_message", "Il campo 'message' è obbligatorio.")
        if len(message) > 12000:
            raise ApiError(413, "message_too_large", "Il messaggio supera il limite di 12000 caratteri.")
        return cls(message.strip())


@dataclass(frozen=True)
class ReminderRequest:
    title: str
    due_at: datetime | None = None

    @classmethod
    def parse(cls, payload):
        if not isinstance(payload, dict):
            raise ApiError(400, "invalid_request", "Il body deve essere un oggetto JSON.")
        title = payload.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ApiError(400, "invalid_title", "Il campo 'title' è obbligatorio.")
        if len(title.strip()) > 500:
            raise ApiError(400, "invalid_title", "Il titolo non può superare 500 caratteri.")
        due_at = payload.get("due_at")
        if due_at is not None:
            if not isinstance(due_at, str):
                raise ApiError(400, "invalid_due_at", "'due_at' deve essere una data ISO 8601.")
            try:
                due_at = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                if due_at.tzinfo is not None:
                    due_at = due_at.astimezone().replace(tzinfo=None)
            except ValueError as error:
                raise ApiError(400, "invalid_due_at", "'due_at' deve essere una data ISO 8601.") from error
        return cls(title.strip(), due_at)


@dataclass(frozen=True)
class MenuItem:
    id: str
    label: str
    description: str
    href: str
    methods: tuple[str, ...]

    def as_dict(self):
        result = asdict(self)
        result["methods"] = list(self.methods)
        return result
