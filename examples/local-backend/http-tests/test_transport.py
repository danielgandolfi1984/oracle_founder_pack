"""Real loopback and raw-wire transport checks using synthetic test identities."""

import contextlib
import http.client
import io
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from http_transport import build_server
from store import Store


class TransportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="founder-http-tests-")
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "synthetic.sqlite3"
        store = Store(self.path, create=True)
        try:
            store.seed_demo()
        finally:
            store.close()
        self.server = build_server(self.path, {"alice-session": "alice", "amy-session": "amy"}.get)
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.host = f"127.0.0.1:{self.server.server_port}"

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.assertFalse(self.thread.is_alive())

    def request(self, method="GET", path="/healthz", body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=4)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally:
            connection.close()

    def wire(self, *, method="GET", target="/healthz", headers=None, body=b"", host=True):
        fields = ([f"Host: {self.host}"] if host else []) + (headers or [])
        raw = f"{method} {target} HTTP/1.1\r\n" + "\r\n".join(fields) + "\r\n\r\n"
        return self.raw(raw.encode("ascii") + body)

    def raw(self, raw):
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=4) as peer:
            peer.sendall(raw)
            peer.shutdown(socket.SHUT_WR)
            parts = []
            while True:
                data = peer.recv(65536)
                if not data:
                    break
                parts.append(data)
        head, body = b"".join(parts).split(b"\r\n\r\n", 1)
        lines = head.decode("ascii").split("\r\n")
        return int(lines[0].split()[1]), dict(line.split(": ", 1) for line in lines[1:]), json.loads(body)

    def test_loopback_only_and_port_validation(self):
        self.assertEqual("127.0.0.1", self.server.server_address[0])
        for port in (True, False, -1, 65536, "8000", 1.2, None):
            with self.subTest(port=port), self.assertRaises(ValueError):
                build_server(self.path, lambda _token: None, port=port)
        with self.assertRaises(TypeError):
            build_server(self.path, lambda _token: None, host="0.0.0.0")
        for verifier in (None, "alice", {}):
            with self.subTest(verifier=verifier), self.assertRaises(ValueError):
                build_server(self.path, verifier)

    def test_server_binding_does_not_perform_reverse_dns(self):
        with mock.patch("socket.getfqdn", side_effect=AssertionError("No DNS lookup permitted")):
            server = build_server(self.path, lambda _token: None)
            try:
                self.assertEqual("127.0.0.1", server.server_name)
            finally:
                server.server_close()

    def test_health_response_has_safe_headers_and_server_generated_request_id(self):
        status, headers, payload = self.request(headers={"X-Request-ID": "caller-controlled"})
        self.assertEqual(200, status)
        self.assertEqual("ok", payload["status"])
        self.assertEqual("loopback-local-lab", payload["scope"])
        self.assertEqual("no-store", headers["Cache-Control"])
        self.assertEqual("nosniff", headers["X-Content-Type-Options"])
        self.assertEqual("close", headers["Connection"])
        self.assertNotIn("Server", headers)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertRegex(headers["X-Request-ID"], r"^[a-f0-9]{32}$")
        self.assertNotEqual(headers["X-Request-ID"], self.request()[1]["X-Request-ID"])

    def test_business_authentication_and_tenant_authorization(self):
        self.assertEqual(401, self.request(path="/workspaces")[0])
        auth = {"Authorization": "Bearer alice-session"}
        status, _, payload = self.request(path="/workspaces", headers=auth)
        self.assertEqual(200, status)
        self.assertEqual(["w-a"], [row["id"] for row in payload["workspaces"]])
        self.assertEqual(403, self.request(path="/workspaces/w-b/projects", headers=auth)[0])
        self.assertEqual(401, self.request(path="/workspaces", headers={"Authorization": "Bearer bad"})[0])

    def test_json_creation_persists_across_request_scoped_connections(self):
        headers = {"Authorization": "Bearer alice-session", "Idempotency-Key": "http-project",
                   "Content-Type": "application/json; charset=utf-8"}
        status, _, first = self.request("POST", "/workspaces/w-a/projects", b'{"name":"Local"}', headers)
        self.assertEqual(201, status, first)
        self.assertEqual(first, self.request("POST", "/workspaces/w-a/projects", b'{"name":"Local"}', headers)[2])
        status, _, payload = self.request(path="/workspaces/w-a/projects", headers=headers)
        self.assertEqual(200, status)
        self.assertEqual([first], payload["projects"])

    def test_readiness_returns_sanitized_503_for_broken_schema_and_missing_database(self):
        self.assertEqual(200, self.request(path="/readyz")[0])
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("PRAGMA user_version = 999")
        finally:
            connection.close()
        self.assertEqual((503, {"error": "unavailable"}),
                         (self.request(path="/readyz")[0], self.request(path="/readyz")[2]))
        self.assertEqual(200, self.request(path="/healthz")[0])
        self.server.database_path = self.path.parent / "missing.sqlite3"
        self.assertEqual({"error": "unavailable"}, self.request(path="/readyz")[2])
        self.assertEqual(200, self.request(path="/healthz")[0])
        self.assertFalse(self.server.database_path.exists())

    def test_exact_single_host_is_required(self):
        self.assertEqual(400, self.wire(host=False)[0])
        for host in ("localhost", "evil.example", "127.0.0.1", "[::1]:8000", self.host + ".", "user@" + self.host):
            with self.subTest(host=host):
                self.assertEqual(400, self.wire(headers=[f"Host: {host}"], host=False)[0])

    def test_every_duplicate_header_is_rejected_case_insensitively(self):
        for pair in (("Host: " + self.host, "host: " + self.host),
                     ("X-Test: one", "x-test: two"),
                     ("Content-Length: 0", "Content-Length: 0"),
                     ("Authorization: Bearer alice-session", "authorization: Bearer amy-session")):
            with self.subTest(pair=pair):
                self.assertEqual(400, self.wire(headers=list(pair), host=not pair[0].startswith("Host:"))[0])

    def test_browser_origins_are_always_rejected_and_proxy_headers_are_not_trusted(self):
        for origin in ("null", "http://" + self.host, "https://example.com", ""):
            with self.subTest(origin=origin):
                self.assertEqual(400, self.wire(headers=["Origin: " + origin])[0])
        self.assertEqual(400, self.wire(host=False, headers=["Host: evil.example", "X-Forwarded-Host: " + self.host])[0])
        self.assertEqual(401, self.wire(target="/workspaces", headers=["X-Forwarded-User: alice"])[0])

    def test_ambiguous_routes_are_rejected_before_normalization(self):
        for target in ("http://" + self.host + "/healthz", "//healthz", "/healthz?x=1", "/healthz#part",
                       "/%68ealthz", "/healthz/", "/a/../healthz", "/a\\healthz", "*", "/" + "a" * 1024):
            with self.subTest(target=target):
                self.assertEqual(400, self.wire(target=target)[0])

    def test_transfer_encoding_and_expect_are_rejected_without_interim_response(self):
        for field in ("Transfer-Encoding: chunked", "Transfer-Encoding: identity", "Expect: 100-continue", "Expect: anything"):
            with self.subTest(field=field):
                self.assertEqual(400, self.wire(headers=[field])[0])

    def test_content_length_is_bounded_decimal_only(self):
        for value in ("-1", "+1", "1.0", "1, 1", "", "9" * 50):
            with self.subTest(value=value):
                self.assertEqual(400, self.wire(headers=["Content-Length: " + value])[0])
        self.assertEqual(413, self.wire(method="POST", headers=["Content-Length: 16385"])[0])

    def test_body_at_limit_is_accepted_without_truncation(self):
        body = b'{"name":"At limit"}'
        body += b" " * (16384 - len(body))
        status, _, payload = self.wire(method="POST", target="/workspaces/w-a/projects",
                                      headers=["Content-Length: 16384", "Content-Type: application/json",
                                               "Authorization: Bearer alice-session", "Idempotency-Key: at-limit"],
                                      body=body)
        self.assertEqual(201, status, payload)
        self.assertEqual("At limit", payload["name"])

    def test_get_and_delete_bodies_are_rejected(self):
        for method in ("GET", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(400, self.wire(method=method, headers=["Content-Length: 2"], body=b"{}")[0])

    def test_write_requires_framed_nonempty_json_body(self):
        for method in ("POST", "PATCH"):
            with self.subTest(method=method):
                self.assertEqual(400, self.wire(method=method)[0])
                self.assertEqual(400, self.wire(method=method, headers=["Content-Length: 0"])[0])
                self.assertEqual(415, self.wire(method=method, headers=["Content-Length: 2"], body=b"{}")[0])
        self.assertEqual(400, self.wire(method="POST", headers=["Content-Length: 20", "Content-Type: application/json"], body=b"{}")[0])

    def test_strict_json_rejects_duplicates_constants_scalars_and_invalid_utf8(self):
        for body in (b'{"name":"x","name":"y"}', b'{"x":{"y":1,"y":2}}', b'{"name":NaN}',
                     b'{"name":Infinity}', b'{"name":-Infinity}', b'{"name":1e999}', b'[]', b'null',
                     b'"text"', b'1', b'{"name":"\xff"}', b'{"name":', b'{}{}', b'\xef\xbb\xbf{}'):
            with self.subTest(body=body):
                self.assertEqual(400, self.wire(method="POST", headers=[f"Content-Length: {len(body)}",
                                     "Content-Type: application/json"], body=body)[0])

    def test_non_json_and_unsupported_charsets_are_rejected(self):
        for content_type in ("text/plain", "application/json; charset=latin-1", "application/json; extra=x"):
            with self.subTest(content_type=content_type):
                self.assertEqual(415, self.wire(method="POST", headers=["Content-Length: 2", "Content-Type: " + content_type], body=b"{}")[0])

    def test_unsupported_methods_are_405_not_html(self):
        for method in ("OPTIONS", "PUT", "TRACE", "CONNECT", "HEAD", "get"):
            with self.subTest(method=method):
                status, _, payload = self.wire(method=method)
                self.assertEqual(405, status)
                self.assertEqual({"error": "method_not_allowed"}, payload)

    def test_header_count_limit_and_malformed_headers(self):
        self.assertEqual(400, self.wire(headers=[f"X-Test-{index}: value" for index in range(32)])[0])
        self.assertEqual(200, self.wire(headers=[f"X-Test-{index}: value" for index in range(31)])[0])
        for field in ("bad header", "Host : ignored", "X-Test: first\r\n folded", "X-Test: bad\x7f"):
            with self.subTest(field=field):
                self.assertEqual(400, self.wire(headers=[field])[0])

    def test_parser_errors_and_unexpected_errors_do_not_leak_or_log(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            status, _, payload = self.raw(b"GET /healthz?secret=private HTTP/1.1\r\n\r\n")
            self.assertEqual((400, {"error": "invalid_request"}), (status, payload))
            with mock.patch("http_transport.API.handle", side_effect=RuntimeError("private token database path")):
                self.assertEqual((500, {"error": "internal_error"}),
                                 (self.request(path="/workspaces")[0], self.request(path="/workspaces")[2]))
            self.assertEqual(431, self.wire(headers=["X-Test: " + "a" * 65536])[0])
        self.assertEqual("", output.getvalue())

    def test_connection_closes_instead_of_serving_pipelined_request(self):
        one = f"GET /healthz HTTP/1.1\r\nHost: {self.host}\r\nConnection: keep-alive\r\n\r\n".encode()
        status, headers, payload = self.raw(one + one)
        self.assertEqual(200, status)
        self.assertEqual("close", headers["Connection"])
        self.assertEqual("ok", payload["status"])

    def test_slow_incomplete_request_has_absolute_read_deadline(self):
        with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=4) as peer:
            start = time.monotonic()
            peer.sendall(b"GET /healthz HTTP/1.1\r\nHost: ")
            time.sleep(1.1)
            peer.sendall(b"1")
            response = peer.recv(4096)
            self.assertIn(b"408", response.split(b"\r\n", 1)[0])
            self.assertLess(time.monotonic() - start, 2.8)


if __name__ == "__main__":
    unittest.main()
