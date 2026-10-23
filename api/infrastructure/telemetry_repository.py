"""SQLite repository for aggregated API request telemetry, separate from user data."""

from __future__ import annotations

import sqlite3
import os
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from api.domain.telemetry import RequestMetric
from storage.paths import data_directory

DEFAULT_TELEMETRY_DB = data_directory() / "api_telemetry.db"


class SqliteTelemetryRepository:
    def __init__(self, db_path=None):
        selected_path = db_path or os.getenv("JARVIS_TELEMETRY_DB") or DEFAULT_TELEMETRY_DB
        self.db_path = Path(selected_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS api_request_stats (
                    day TEXT NOT NULL,
                    method TEXT NOT NULL,
                    route TEXT NOT NULL,
                    request_count INTEGER NOT NULL DEFAULT 0,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    total_duration_ms REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (day, method, route)
                )
            """)

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=5)

    @contextmanager
    def _connection(self):
        db = self._connect()
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, metric: RequestMetric):
        day = date.today().isoformat()
        with self._connection() as db:
            db.execute("""
                INSERT INTO api_request_stats(day,method,route,request_count,error_count,total_duration_ms)
                VALUES(?,?,?,1,?,?)
                ON CONFLICT(day,method,route) DO UPDATE SET
                    request_count=request_count+1,
                    error_count=error_count+excluded.error_count,
                    total_duration_ms=total_duration_ms+excluded.total_duration_ms
            """, (day, metric.method, metric.route, int(metric.status >= 400), metric.duration_ms))

    def statistics(self):
        with self._connection() as db:
            rows = db.execute("""
                SELECT method,route,SUM(request_count),SUM(error_count),SUM(total_duration_ms)
                FROM api_request_stats GROUP BY method,route ORDER BY route,method
            """).fetchall()
            today = db.execute("SELECT COALESCE(SUM(request_count),0) FROM api_request_stats WHERE day=?",
                               (date.today().isoformat(),)).fetchone()[0]
        total = sum(row[2] for row in rows)
        errors = sum(row[3] for row in rows)
        duration = sum(row[4] for row in rows)
        return {
            "requests_total": total,
            "requests_today": today,
            "errors_total": errors,
            "average_duration_ms": round(duration / total, 2) if total else 0,
            "by_route": [
                {"method": method, "route": route, "requests": count,
                 "errors": error_count, "average_duration_ms": round(total_ms / count, 2)}
                for method, route, count, error_count, total_ms in rows
            ],
        }
