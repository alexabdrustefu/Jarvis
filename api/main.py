"""Run the local HTTP and TCP chat bridges."""

import argparse
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = ROOT / "src"
for import_root in (SRC_ROOT, ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

def main():
    from api.bootstrap import create_local_bridge
    from composition import create_application

    parser = argparse.ArgumentParser(description="J.A.R.V.I.S. loopback chat API")
    parser.add_argument("--http-port", type=int, default=8765)
    parser.add_argument("--socket-port", type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true", help="non aprire automaticamente Swagger UI")
    args = parser.parse_args()
    application = create_application()
    bridge = create_local_bridge(application, "127.0.0.1", args.http_port, args.socket_port)
    http_address, socket_address = bridge.start()
    docs_url = f"http://{http_address[0]}:{http_address[1]}/docs"
    print(f"Swagger UI: {docs_url}")
    print(f"OpenAPI schema: http://{http_address[0]}:{http_address[1]}/openapi.json")
    print(f"TCP JSON socket: {socket_address[0]}:{socket_address[1]} (una richiesta JSON per riga)")
    print("Premi Ctrl+C per terminare.")
    if not args.no_browser:
        try:
            webbrowser.open(docs_url, new=2)
        except Exception as error:
            print(f"Apertura automatica del browser non riuscita: {error}")
    try:
        import threading
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()


if __name__ == "__main__":
    main()
