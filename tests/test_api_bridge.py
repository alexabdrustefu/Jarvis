import json
import os
import socket
import threading
import unittest
from urllib.request import Request, urlopen

from api.bridge import ChatGateway, LocalBridge, make_http_server, make_socket_server


class FakeRouter:
    def __init__(self):
        self.received = []

    def handle(self, message):
        self.received.append(message)
        return "Ricevuto: " + message


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


if __name__ == "__main__":
    unittest.main()
