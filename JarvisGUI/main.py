"""GUI entry point."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(PROJECT_ROOT))

from ui.app import JarvisApp


def main() -> None:
    JarvisApp().run()


if __name__ == "__main__":
    main()
