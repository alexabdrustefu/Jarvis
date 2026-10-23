import json
import os
import socket
import threading
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request, urlopen

from api.bridge import ChatGateway, LocalBridge, make_http_server, make_socket_server
from api.infrastructure.telemetry_repository import SqliteTelemetryRepository
from core.local_features import LocalStore


class FakeRouter:
    def __init__(self):
        self.received = []

    def handle(self, message):
        self.received.append(message)
        return "Ricevuto: " + message


class FakeMemory:
    def get_statistics(self):
        return {"messages_total": 12, "messages_today": 3}


class FakeFacts:
    def count(self):
        return 2


class FakeAI:
    memory = FakeMemory()
    facts = FakeFacts()
    last_provider = "ollama"

    def provider_status(self):
        return {"ollama_available": True}


class ApiBridgeTests(unittest.TestCase):
    def test_gateway_rejects_empty_and_oversized_messages(self):
        gateway = ChatGateway(FakeRouter())
        for message in ("", "x" * 12001):
            with self.assertRaises(ValueError):
                gateway.chat(message)

    def test_local_bridge_starts_and_stops_http_and_socket_together(self):
        bridge = LocalBridge(FakeRouter(), http_port=0, socket_port=0)
        try:
            http_address, socket_address = bridge.start()
            with urlopen(f"http://127.0.0.1:{http_address[1]}/health", timeout=3) as response:
                self.assertEqual(json.loads(response.read())["status"], "ok")
            with socket.create_connection(socket_address, timeout=3) as client:
                client.sendall(b'{"message":"bridge"}\n')
                self.assertEqual(json.loads(client.makefile("rb").readline())["reply"], "Ricevuto: bridge")
        finally:
            bridge.stop()

    def test_http_chat_endpoint(self):
        router = FakeRouter()
        server = make_http_server(ChatGateway(router), port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/api/chat"
            request = Request(url, data=json.dumps({"message": "ciao"}).encode(),
                              headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=3) as response:
                result = json.loads(response.read().decode())
            self.assertEqual(result["reply"], "Ricevuto: ciao")
            self.assertEqual(router.received, ["ciao"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_socket_uses_one_json_message_per_line(self):
        router = FakeRouter()
        server = make_socket_server(ChatGateway(router), port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with socket.create_connection(server.server_address, timeout=3) as client:
                client.sendall(b'{"message":"salve"}\n')
                result = json.loads(client.makefile("rb").readline().decode())
            self.assertEqual(result["reply"], "Ricevuto: salve")
            self.assertEqual(router.received, ["salve"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_websocket_chat_endpoint(self):
        router = FakeRouter()
        server = make_http_server(ChatGateway(router), port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with socket.create_connection(server.server_address, timeout=3) as client:
                client.settimeout(3)
                reader = client.makefile("rb")
                client.sendall(
                    b"GET /ws HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\n"
                    b"Connection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
                    b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
                )
                headers = []
                while True:
                    line = reader.readline()
                    headers.append(line)
                    if line == b"\r\n":
                        break
                self.assertIn(b"101 Switching Protocols", headers[0])

                payload = json.dumps({"message": "web"}).encode()
                mask = os.urandom(4)
                masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
                client.sendall(bytes((0x81, 0x80 | len(payload))) + mask + masked)
                first, second = reader.read(2)
                length = second & 0x7F
                if length == 126:
                    length = int.from_bytes(reader.read(2), "big")
                response = json.loads(reader.read(length).decode())
            self.assertEqual(response["reply"], "Ricevuto: web")
            self.assertEqual(router.received, ["web"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_swagger_openapi_menu_stats_and_reminder_resources(self):
        with tempfile.TemporaryDirectory() as folder:
            store = LocalStore(Path(folder) / "jarvis.db")
            store.save_routine("Lavoro", ["time"])
            application = SimpleNamespace(router=FakeRouter(), store=store, ai=FakeAI())
            telemetry = SqliteTelemetryRepository(Path(folder) / "telemetry.db")
            server = make_http_server(ChatGateway(application, telemetry), port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            root = f"http://127.0.0.1:{server.server_port}"

            def request(method, path, payload=None):
                data = json.dumps(payload).encode() if payload is not None else None
                req = Request(root + path, data=data, method=method,
                              headers={"Content-Type": "application/json"})
                with urlopen(req, timeout=3) as response:
                    return response.status, json.loads(response.read().decode())

            try:
                with urlopen(root + "/docs", timeout=3) as response:
                    self.assertIn(b"swagger-ui", response.read())
                _, spec = request("GET", "/openapi.json")
                self.assertEqual(spec["openapi"], "3.0.3")
                _, menu = request("GET", "/api/v1/menu")
                self.assertIn("reminders", {item["id"] for item in menu["items"]})
                _, created = request("POST", "/api/v1/reminders", {"title": "Test API"})
                self.assertEqual(created["status"], "pending")
                _, pending = request("GET", "/api/v1/reminders")
                self.assertEqual(len(pending["items"]), 1)
                _, completed = request("PATCH", f"/api/v1/reminders/{created['id']}", {"status": "done"})
                self.assertEqual(completed["status"], "done")
                _, done = request("GET", "/api/v1/reminders?include_done=true")
                self.assertEqual(done["items"][0]["status"], "done")
                _, routines = request("GET", "/api/v1/routines")
                self.assertEqual(routines["items"][0]["name"], "Lavoro")
                _, stats = request("GET", "/api/v1/stats")
                self.assertEqual(stats["conversations"]["messages_total"], 12)
                self.assertEqual(stats["productivity"]["reminders_completed"], 1)
                self.assertGreater(stats["api"]["requests_total"], 0)
                self.assertIn("/api/v1/menu", {item["route"] for item in stats["api"]["by_route"]})
                _, deleted = request("DELETE", f"/api/v1/reminders/{created['id']}")
                self.assertTrue(deleted["deleted"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
