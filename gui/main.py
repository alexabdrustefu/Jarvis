"""GUI entry point."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
for import_root in (SRC_ROOT, PROJECT_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from gui.ui.app import JarvisApp


def main() -> None:
    JarvisApp().run()


if __name__ == "__main__":
    main()
