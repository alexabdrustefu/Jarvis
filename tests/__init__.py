"""Test package; expose the application source package for unittest discovery."""

from pathlib import Path
import sys

SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
