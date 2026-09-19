"""Strictly loopback HTTP teaching adapter; never a production web server.

No TLS, proxy trust, CORS, background workers, or public listener is provided.
Use only synthetic local data. Python's http.server is not production hosting.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import re
import socket
from socketserver import TCPServer
import sqlite3
import time
from uuid import uuid4

from api import API
from store import DomainError, Store


MAX_BODY = 16384
REQUEST_TIMEOUT = 2.0
_TARGET = re.compile(rb"/(?:[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*)?\Z")
_CONTENT_TYPE = re.compile(r"application/json(?:\s*;\s*charset=utf-8)?\Z", re.I)


class _DeadlineReader:
    """Bound the entire request read, including a peer trickling header bytes."""

    def __init__(self, stream, connection):
        self.stream, self.connection = stream, connection
        self.deadline = time.monotonic() + REQUEST_TIMEOUT
        self.buffer = bytearray()

    def _more(self, size):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        self.connection.settimeout(remaining)
        data = self.stream.read1(size)
        self.buffer.extend(data)
        return bool(data)

    def readline(self, limit=-1):
        limit = 65537 if limit < 0 else limit
        while True:
            newline = self.buffer.find(b"\n", 0, limit)
            size = newline + 1 if newline >= 0 else limit
            if newline >= 0 or len(self.buffer) >= limit:
                break
            if not self._more(min(4096, limit - len(self.buffer))):
                size = len(self.buffer)
                break
        result = bytes(self.buffer[:size])
        del self.buffer[:size]
        return result

    def read(self, size):
        while len(self.buffer) < size:
            if not self._more(size - len(self.buffer)):
                break
        result = bytes(self.buffer[:size])
        del self.buffer[:size]
        return result


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _constant(_value):
    raise ValueError("Non-finite JSON constant")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Non-finite JSON number")
    return result


class _LocalServer(HTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        # HTTPServer's default performs reverse DNS, unnecessary for loopback.
        TCPServer.server_bind(self)
        self.server_name = "127.0.0.1"
        self.server_port = self.server_address[1]

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(REQUEST_TIMEOUT)
        return connection, address

    def handle_error(self, request, client_address):
        # socketserver's default prints tracebacks, potentially including data.
        pass


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def handle_one_request(self):
        self.close_connection = True
        self.request_version = "HTTP/1.1"
        self.command = None
        self.request_id = uuid4().hex
        original_stream = self.rfile
        self.rfile = _DeadlineReader(original_stream, self.connection)
        try:
            self.raw_requestline = self.rfile.readline(8193)
            if not self.raw_requestline:
                return
            parts = self.raw_requestline.removesuffix(b"\r\n").split(b" ")
            if (len(self.raw_requestline) > 8192
                    or not self.raw_requestline.endswith(b"\r\n")
                    or len(parts) != 3
                    or re.fullmatch(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]{1,32}", parts[0]) is None
                    or len(parts[1]) > 1024 or _TARGET.fullmatch(parts[1]) is None
                    or parts[2] not in (b"HTTP/1.0", b"HTTP/1.1")):
                self._reply(400, {"error": "invalid_request"})
                return
            if self.parse_request():
                self.close_connection = True
                self._dispatch()
        except (TimeoutError, socket.timeout):
            self._reply(408, {"error": "request_timeout"})
        except (BrokenPipeError, ConnectionError, OSError):
            pass
        except Exception:
            self._reply(500, {"error": "internal_error"})
        finally:
            self.close_connection = True
            self.rfile = original_stream

    def handle_expect_100(self):
        self._reply(400, {"error": "invalid_request"})
        return False

    def send_error(self, code, message=None, explain=None):
        self._reply(code, {"error": "invalid_request"})

    def _reply(self, status, payload):
        encoded = json.dumps(payload, allow_nan=False, separators=(",", ":")).encode("utf-8")
        self.close_connection = True
        try:
            self.connection.settimeout(REQUEST_TIMEOUT)
            self.send_response_only(status)
            for name, value in (
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(encoded))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
                ("X-Request-ID", self.request_id),
                ("Connection", "close"),
            ):
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(encoded)
        except (OSError, ConnectionError):
            pass

    def _input(self):
        pairs = list(self.headers.raw_items())
        if self.headers.defects or len(pairs) > 32:
            raise DomainError(400, "invalid_request")
        names = [key.lower() for key, _value in pairs]
        if len(names) != len(set(names)):
            raise DomainError(400, "invalid_request")
        headers = API._headers(dict(pairs))
        if (headers.get("host") != f"127.0.0.1:{self.server.server_port}"
                or "origin" in headers or "transfer-encoding" in headers
                or "expect" in headers):
            raise DomainError(400, "invalid_request")
        length = headers.get("content-length", "0")
        if re.fullmatch(r"[0-9]{1,10}", length) is None:
            raise DomainError(400, "invalid_request")
        size = int(length)
        if size > MAX_BODY:
            raise DomainError(413, "body_too_large")
        if self.command not in {"GET", "POST", "PATCH", "DELETE"}:
            raise DomainError(405, "method_not_allowed")
        if self.command in {"GET", "DELETE"}:
            if size:
                raise DomainError(400, "invalid_request")
            return headers, None
        if not size:
            raise DomainError(400, "invalid_request")
        if _CONTENT_TYPE.fullmatch(headers.get("content-type", "")) is None:
            raise DomainError(415, "unsupported_media_type")
        raw = self.rfile.read(size)
        if len(raw) != size:
            raise DomainError(400, "invalid_request")
        try:
            body = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                              parse_constant=_constant, parse_float=_float)
        except (UnicodeError, ValueError, RecursionError):
            raise DomainError(400, "invalid_json") from None
        if not isinstance(body, dict):
            raise DomainError(400, "invalid_json")
        return headers, body

    def _dispatch(self):
        try:
            headers, body = self._input()
        except DomainError as exc:
            self._reply(exc.status, {"error": exc.code})
            return
        if self.command == "GET" and self.path == "/healthz":
            self._reply(200, {"status": "ok", "scope": "loopback-local-lab"})
            return
        try:
            store = Store(self.server.database_path)
        except (sqlite3.Error, OSError, ValueError, RuntimeError):
            self._reply(503, {"error": "unavailable"})
            return
        try:
            status, payload = API(store, self.server.verify_token).handle(
                self.command, self.path, headers, body)
        finally:
            store.close()
        self._reply(status, payload)


def build_server(database_path, verify_token, *, port=0) -> HTTPServer:
    """Build a serial 127.0.0.1-only listener; the caller owns serve/close."""
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("Port must be an integer from 0 to 65535")
    if not callable(verify_token):
        raise ValueError("An explicit token verifier is required")
    server = _LocalServer(("127.0.0.1", port), _Handler)
    server.database_path = database_path
    server.verify_token = verify_token
    return server
