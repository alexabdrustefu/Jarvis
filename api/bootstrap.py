"""API composition root: select adapters and persistence implementations."""

from api.infrastructure.telemetry_repository import SqliteTelemetryRepository
from api.presentation.http import LocalBridge


def create_local_bridge(application, host="127.0.0.1", http_port=8765, socket_port=8766):
    router = getattr(application, "router", application)
    has_store = getattr(application, "store", None) is not None
    if not has_store:
        has_store = getattr(getattr(router, "local_commands", None), "store", None) is not None
    telemetry = SqliteTelemetryRepository() if has_store else None
    return LocalBridge(application, host, http_port, socket_port, telemetry_repository=telemetry)
