from __future__ import annotations

import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("container_api_app", ROOT / "app" / "app.py")
assert SPEC and SPEC.loader
APP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APP)


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


if __name__ == "__main__":
    unittest.main()
