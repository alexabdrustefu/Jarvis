"""Resolve writable application paths for source and frozen Windows builds."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return whether the app is running from a PyInstaller executable."""
    return bool(getattr(sys, "frozen", False))


def data_directory() -> Path:
    """Return the writable data directory, honoring an explicit override."""
    override = os.getenv("JARVIS_DATA_DIR")
    if override:
        return Path(override).expanduser()

    if is_frozen():
        root = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        return Path(root).expanduser() / "JARVIS" if root else Path.home() / "AppData" / "Local" / "JARVIS"

    return Path(__file__).resolve().parent


def environment_file() -> Path:
    """Return the user configuration path for this launch mode."""
    if is_frozen():
        return data_directory() / ".env"
    return Path(__file__).resolve().parents[2] / ".env"
