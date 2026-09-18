#!/usr/bin/env python3
"""Small, dependency-free HTTP API used by the Container API field preview."""

from __future__ import annotations

import json
import os
import re
import signal
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit


SERVICE_NAME = "oci-founder-container-api"
RELEASE = os.environ.get("OCI_FOUNDER_RELEASE", "local")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
PUBLIC_PATHS = frozenset(("/", "/healthz", "/readyz"))


def response_for_path(path: str) -> tuple[int, dict[str, Any]]:
    """Return the public response contract without exposing process details."""
    if path == "/healthz":
        return 200, {"status": "ok"}
    if path == "/readyz":
        return 200, {"status": "ready"}
    if path == "/":
        return 200, {"service": SERVICE_NAME, "release": RELEASE}
    return 404, {"error": "not_found"}


def emit_log(**fields: Any) -> None:
    """Write one bounded JSON event to stdout; never log headers or query data."""
    record = {"service": SERVICE_NAME, **fields}
    print(json.dumps(record, separators=(",", ":"), sort_keys=True), flush=True)


def safe_request_id(candidate: str) -> str:
    """Return a header-safe request ID without reflecting control characters."""
    return candidate if REQUEST_ID_RE.fullmatch(candidate) else str(uuid.uuid4())


class Handler(BaseHTTPRequestHandler):
    server_version = "oci-founder-api"
    sys_version = ""

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        started = time.monotonic()
        path = urlsplit(self.path).path
        status, payload = response_for_path(path)
        request_id = safe_request_id(self.headers.get("x-request-id", ""))

        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("x-request-id", request_id)
        self.end_headers()
        self.wfile.write(body)

        emit_log(
            event="request",
            method="GET",
            path=path if path in PUBLIC_PATHS else "<unmatched>",
            request_id=request_id,
            status=status,
            duration_ms=round((time.monotonic() - started) * 1000, 2),
        )

    def log_message(self, format: str, *args: Any) -> None:
        # Disable the parent logger because it can include an unsanitized request line.
        return


def main() -> int:
    try:
        port = int(os.environ.get("PORT", "8080"))
    except ValueError:
        print("PORT must be an integer", file=sys.stderr)
        return 2
    if not 1 <= port <= 65535:
        print("PORT must be between 1 and 65535", file=sys.stderr)
        return 2

    stopping = threading.Event()

    def request_stop(signum: int, _frame: Any) -> None:
        emit_log(event="shutdown_requested", signal=signum)
        stopping.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.timeout = 1.0
    emit_log(event="started", port=port, release=RELEASE)
    try:
        while not stopping.is_set():
            server.handle_request()
    finally:
        server.server_close()
        emit_log(event="stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
