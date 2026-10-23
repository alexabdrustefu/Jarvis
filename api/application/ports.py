"""Ports required by API application use cases."""

from typing import Protocol


class TelemetryRepository(Protocol):
    def record(self, metric) -> None: ...

    def statistics(self) -> dict: ...
