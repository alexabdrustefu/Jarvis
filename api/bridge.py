"""Loopback HTTP and newline-delimited JSON socket bridge."""

from __future__ import annotations

import json
import base64
import hashlib
import socketserver
import threading
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ChatGateway:
    def __init__(self, router):
        self.router = router
        self.lock = threading.RLock()

    def chat(self, message):
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Il campo 'message' è obbligatorio.")
        if len(message) > 12000:
            raise ValueError("Il messaggio supera il limite di 12000 caratteri.")
        with self.lock:
            return self.router.handle(message.strip())


def make_http_server(gateway, host="127.0.0.1", port=8765):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "JarvisLocalAPI/1.0"

        def _json(self, status, value):
            data = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            origin = self.headers.get("Origin", "")
            if urlparse(origin).hostname in {"localhost", "127.0.0.1"}:
                self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(data)

        def do_OPTIONS(self):
            self._json(200, {})

        def do_GET(self):
            if self.path == "/health":
                ai = getattr(gateway.router, "ai", None)
                status = ai.provider_status() if hasattr(ai, "provider_status") else {}
                self._json(200, {"status": "ok", "service": "J.A.R.V.I.S.", "llm": status})
            elif self.path == "/ws" and self.headers.get("Upgrade", "").casefold() == "websocket":
                origin = self.headers.get("Origin", "")
                if origin and urlparse(origin).hostname not in {"localhost", "127.0.0.1"}:
                    self._json(403, {"error": "WebSocket consentito solo da pagine locali."})
                    return
                key = self.headers.get("Sec-WebSocket-Key")
                if not key:
                    self._json(400, {"error": "Handshake WebSocket non valido."})
                    return
                accept = base64.b64encode(hashlib.sha1(
                    (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
                ).digest()).decode("ascii")
                self.send_response(101, "Switching Protocols")
                self.send_header("Upgrade", "websocket")
                self.send_header("Connection", "Upgrade")
                self.send_header("Sec-WebSocket-Accept", accept)
                self.end_headers()
                self.connection.settimeout(120)
                try:
                    self._websocket_loop()
                except (ConnectionError, OSError, ValueError):
                    return
                finally:
                    self.close_connection = True
            else:
                self._json(404, {"error": "Not found"})

        def _read_exact(self, size):
            data = bytearray()
            while len(data) < size:
                chunk = self.rfile.read(size - len(data))
                if not chunk:
                    raise ConnectionError("WebSocket disconnesso")
                data.extend(chunk)
            return bytes(data)

        def _read_websocket_frame(self):
            first, second = self._read_exact(2)
            if first & 0x70:
                raise ValueError("Estensioni WebSocket non supportate")
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            length = second & 0x7F
            if length == 126:
                length = int.from_bytes(self._read_exact(2), "big")
            elif length == 127:
                length = int.from_bytes(self._read_exact(8), "big")
            if not masked or length > 50000:
                raise ValueError("Frame WebSocket non valido o troppo grande")
            mask = self._read_exact(4)
            payload = self._read_exact(length)
            return opcode, bytes(value ^ mask[index % 4] for index, value in enumerate(payload))

        def _send_websocket_frame(self, opcode, payload):
            length = len(payload)
            header = bytearray([0x80 | opcode])
            if length < 126:
                header.append(length)
            elif length < 65536:
                header.append(126)
                header.extend(length.to_bytes(2, "big"))
            else:
                header.append(127)
                header.extend(length.to_bytes(8, "big"))
            self.wfile.write(bytes(header) + payload)
            self.wfile.flush()

        def _websocket_loop(self):
            while True:
                opcode, payload = self._read_websocket_frame()
                if opcode == 8:
                    self._send_websocket_frame(8, payload[:125])
                    return
                if opcode == 9:
                    self._send_websocket_frame(10, payload[:125])
                    continue
                if opcode != 1:
                    raise ValueError("Sono supportati solo messaggi WebSocket testuali")
                try:
                    data = json.loads(payload.decode("utf-8"))
                    reply = gateway.chat(data.get("message") if isinstance(data, dict) else None)
                    response = {"reply": reply}
                except Exception as error:
                    response = {"error": str(error)}
                self._send_websocket_frame(1, json.dumps(response, ensure_ascii=False).encode("utf-8"))

        def do_POST(self):
            if self.path != "/api/chat":
                self._json(404, {"error": "Not found"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 0 or size > 50000:
                    raise ValueError("Richiesta troppo grande.")
                payload = json.loads(self.rfile.read(size).decode("utf-8"))
                reply = gateway.chat(payload.get("message") if isinstance(payload, dict) else None)
                self._json(200, {"reply": reply})
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
                self._json(400, {"error": str(error)})
            except Exception as error:
                self._json(500, {"error": f"Errore interno: {error}"})

        def log_message(self, *_args):
            return

    return ThreadingHTTPServer((host, port), Handler)


def make_socket_server(gateway, host="127.0.0.1", port=8766):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            while True:
                raw = self.rfile.readline(50002)
                if not raw:
                    return
                try:
                    if len(raw) > 50000:
                        raise ValueError("Richiesta troppo grande.")
                    payload = json.loads(raw.decode("utf-8"))
                    reply = gateway.chat(payload.get("message") if isinstance(payload, dict) else None)
                    response = {"reply": reply}
                except Exception as error:
                    response = {"error": str(error)}
                self.wfile.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
                self.wfile.flush()

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    return Server((host, port), Handler)


class LocalBridge:
    """Owns local API and socket listeners; safe to stop from GUI shutdown."""

    def __init__(self, router, host="127.0.0.1", http_port=8765, socket_port=8766):
        self.gateway = ChatGateway(router)
        self.http = make_http_server(self.gateway, host, http_port)
        try:
            self.socket = make_socket_server(self.gateway, host, socket_port)
        except Exception:
            self.http.server_close()
            raise
        self.threads = []

    def start(self):
        for server in (self.http, self.socket):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.threads.append(thread)
        return self.http.server_address, self.socket.server_address

    def stop(self):
        for server in (self.http, self.socket):
            server.shutdown()
            server.server_close()
