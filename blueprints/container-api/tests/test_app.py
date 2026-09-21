from __future__ import annotations

import importlib.util
import io
import json
import pathlib
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("container_api_app", ROOT / "app" / "app.py")
assert SPEC and SPEC.loader
APP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APP)


class SyntheticRequest:
    """Exercise the real HTTP parser and serializer without opening a socket."""

    def __init__(self, raw: bytes) -> None:
        self.raw = raw
        self.response = bytearray()

    def makefile(self, *_args: object) -> io.BytesIO:
        return io.BytesIO(self.raw)

    def sendall(self, data: bytes) -> None:
        self.response.extend(data)


def handle_request(candidate: bytes) -> tuple[bytes, dict[str, object]]:
    request = SyntheticRequest(
        b"GET /healthz HTTP/1.1\r\nHost: localhost\r\n"
        b"x-request-id: " + candidate + b"\r\nConnection: close\r\n\r\n"
    )
    with mock.patch.object(APP, "emit_log") as log:
        APP.Handler(request, ("127.0.0.1", 12345), object())
    return bytes(request.response), log.call_args.kwargs


class AppContractTests(unittest.TestCase):
    def test_health_contract_is_minimal(self) -> None:
        status, payload = APP.response_for_path("/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok"})
        self.assertEqual(json.dumps(payload, separators=(",", ":")), '{"status":"ok"}')

    def test_readiness_and_not_found(self) -> None:
        self.assertEqual(APP.response_for_path("/readyz"), (200, {"status": "ready"}))
        self.assertEqual(APP.response_for_path("/missing"), (404, {"error": "not_found"}))

    def test_request_id_rejects_header_controls(self) -> None:
        safe = APP.safe_request_id("trace-123:span_456")
        rejected = APP.safe_request_id("trusted\r\nx-injected: yes")
        self.assertEqual(safe, "trace-123:span_456")
        self.assertNotEqual(rejected, "trusted\r\nx-injected: yes")
        self.assertRegex(rejected, r"^[0-9a-f-]{36}$")

    def test_request_id_allowlist_and_length_are_unchanged(self) -> None:
        for candidate in ("A", "a" * 128, "aZ09._:-"):
            with self.subTest(valid=candidate):
                self.assertEqual(APP.safe_request_id(candidate), candidate)
        candidates = ["", "a" * 129, ".trace", "trace value", "caf\u00e9", "trace\n"]
        candidates.extend("trace" + chr(code) for code in (*range(32), 127))
        for candidate in candidates:
            with self.subTest(invalid=repr(candidate)):
                self.assertRegex(APP.safe_request_id(candidate), r"^[0-9a-f-]{36}$")

    def test_real_handler_preserves_valid_request_id_and_contract(self) -> None:
        response, event = handle_request(b"trace-123:span_456")
        headers, body = response.split(b"\r\n\r\n", 1)
        self.assertTrue(headers.startswith(b"HTTP/1.0 200 OK\r\n"))
        self.assertEqual(headers.count(b"\r\nx-request-id: "), 1)
        self.assertIn(b"\r\nx-request-id: trace-123:span_456", headers)
        self.assertIn(b"\r\ncontent-length: " + str(len(body)).encode(), headers)
        self.assertEqual(json.loads(body), {"status": "ok"})
        self.assertEqual(event["request_id"], "trace-123:span_456")

    def test_real_handler_rejects_folded_controls_and_non_ascii_ids(self) -> None:
        for candidate in (
            b"trace\r\n x-injected: yes",
            b"trace\r\n\tx-injected: yes",
            b"trace\n x-injected: yes",
            b"trace\x00value",
            b"caf\xe9",
            b"a" * 129,
        ):
            with self.subTest(candidate=candidate):
                response, event = handle_request(candidate)
                headers, body = response.split(b"\r\n\r\n", 1)
                self.assertEqual(headers.count(b"\r\nx-request-id: "), 1)
                self.assertNotIn(b"x-injected", headers)
                self.assertNotIn(candidate, headers)
                self.assertRegex(event["request_id"], r"^[0-9a-f-]{36}$")
                self.assertIn(b"\r\nx-request-id: " + event["request_id"].encode(), headers)
                self.assertEqual(json.loads(body), {"status": "ok"})

    def test_header_boundary_removes_crlf_even_if_validator_regresses(self) -> None:
        with mock.patch.object(APP, "safe_request_id", return_value="trace\r\nx-injected: yes\n"):
            response, _event = handle_request(b"trace")
        headers, body = response.split(b"\r\n\r\n", 1)
        self.assertNotIn(b"\r\nx-injected:", headers)
        self.assertNotIn(b"\nx-injected:", headers)
        self.assertIn(b"\r\nx-request-id: tracex-injected: yes", headers)
        self.assertEqual(json.loads(body), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
