"""Domain value object for privacy-preserving API usage metrics."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class RequestMetric:
    method: str
    route: str
    status: int
    duration_ms: float

    def __post_init__(self):
        if self.method not in {"GET", "POST", "PATCH", "DELETE"}:
            raise ValueError("Metodo HTTP non supportato per le metriche.")
        if not self.route.startswith("/api/") or "?" in self.route:
            raise ValueError("Le metriche accettano solo route API senza query string.")
        if not 100 <= self.status <= 599 or not isfinite(self.duration_ms) or self.duration_ms < 0:
            raise ValueError("Stato o durata della richiesta non validi.")
