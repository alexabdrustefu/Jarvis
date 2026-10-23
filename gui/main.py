"""GUI entry point."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
for import_root in (SRC_ROOT, PROJECT_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. Windows desktop assistant")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="open a deterministic offline preview without AI keys, network, or microphone",
    )
    arguments = parser.parse_args(argv)

    from gui.ui.app import JarvisApp

    JarvisApp(demo_mode=arguments.demo).run()


if __name__ == "__main__":
    main()
