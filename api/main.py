"""Run the local HTTP and TCP chat bridges."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
for import_root in (SRC_ROOT, ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from api.bridge import LocalBridge
from composition import create_application


def main():
    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. loopback chat API")
    parser.add_argument("--http-port", type=int, default=8765)
    parser.add_argument("--socket-port", type=int, default=8766)
    args = parser.parse_args()
    application = create_application()
    bridge = LocalBridge(application.router, "127.0.0.1", args.http_port, args.socket_port)
    http_address, socket_address = bridge.start()
    print(f"HTTP API: http://{http_address[0]}:{http_address[1]}/health")
    print(f"TCP JSON socket: {socket_address[0]}:{socket_address[1]} (una richiesta JSON per riga)")
    print("Premi Ctrl+C per terminare.")
    try:
        import threading
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()


if __name__ == "__main__":
    main()
