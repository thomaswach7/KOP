"""HTTP-Server, der CREOSON nachbildet (POST /creoson). Nur stdlib, läuft in einem Hintergrund-Thread."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .handlers import handle_request
from .state import MockCreo


@dataclass
class MockServerHandle:
    server: ThreadingHTTPServer
    thread: threading.Thread
    state: MockCreo

    @property
    def url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}/creoson"

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _make_handler(state: MockCreo, lock: threading.Lock) -> type[BaseHTTPRequestHandler]:
    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 (stdlib-Name)
            if self.path.rstrip("/") != "/creoson":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except json.JSONDecodeError:
                payload = None
            with lock:
                if isinstance(payload, dict):
                    response = handle_request(state, payload)
                else:
                    response = {"status": {"error": True, "message": "Invalid JSON input"}}
            body = json.dumps(response, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=UTF-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return  # keine Ausgabe (stdout gehört dem MCP-Protokoll)

    return _Handler


def start_mock_server(host: str = "127.0.0.1", port: int = 0, state: MockCreo | None = None) -> MockServerHandle:
    state = state or MockCreo.demo()
    server = ThreadingHTTPServer((host, port), _make_handler(state, threading.Lock()))
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, name="creoson-mock", daemon=True)
    thread.start()
    return MockServerHandle(server=server, thread=thread, state=state)
