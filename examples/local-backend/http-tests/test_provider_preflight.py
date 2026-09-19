"""Offline preflight tests: synthetic public files only, never bearer tokens."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from cryptography.hazmat.primitives.asymmetric import rsa


EXAMPLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE))
try:
    import provider_preflight
    from provider_demo import public_jwk
finally:
    sys.path.pop(0)


class ProviderPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Only the public key survives this expression; no signing material
        # or signed token is ever written to a fixture or printed by a test.
        cls.public = public_jwk(
            rsa.generate_private_key(public_exponent=65537, key_size=2048), "synthetic-key")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="founder-provider-preflight-tests-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        now = int(time.time())
        self.config = {
            "issuer": "https://synthetic-provider.example.invalid",
            "audience": "https://synthetic-api.example.invalid",
            "allowed_client_ids": ["synthetic-client"],
            "required_scope": "founder:api",
            "max_token_lifetime_seconds": 900,
            "jwks_fetched_at": now - 1,
            "jwks_expires_at": now + 300,
        }
        self.paths = {}
        for name, value in (("config", self.config), ("jwks", {"keys": [self.public]}),
                            ("bindings", {"synthetic|alice": "alice"})):
            path = self.root / f"{name}.json"
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(value, stream)
            self.paths[name] = path

    def arguments(self, **overrides):
        paths = {**self.paths, **overrides}
        return [item for name in ("config", "jwks", "bindings")
                for item in ("--" + name, str(paths[name]))]

    def cli(self, *extra, **overrides):
        return subprocess.run(
            [sys.executable, "-B", str(EXAMPLE / "provider_preflight.py"),
             *self.arguments(**overrides), *extra],
            capture_output=True, text=True, check=False, timeout=10,
        )

    def expected(self, status):
        return {"status": status, "provider_connection_tested": False,
                "token_verified": False, "network_calls": 0}

    def test_valid_synthetic_configuration_cli_reports_only_qualified_status(self):
        result = self.cli()
        self.assertEqual(0, result.returncode, "Synthetic preflight did not succeed")
        self.assertEqual("", result.stderr)
        self.assertEqual(self.expected("configuration_valid"), json.loads(result.stdout))
        for value in (self.config["issuer"], self.config["audience"], "synthetic-client",
                      "synthetic|alice", self.public["n"], str(self.root)):
            self.assertNotIn(value, result.stdout)

    def test_configuration_validation_never_calls_network_or_verifies_a_token(self):
        with mock.patch("socket.socket", side_effect=AssertionError("No sockets")) as socket, \
                mock.patch("socket.create_connection", side_effect=AssertionError("No connections")) as connection, \
                mock.patch("socket.getaddrinfo", side_effect=AssertionError("No DNS")) as dns, \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("No fetching")) as urlopen, \
                mock.patch.object(provider_preflight.ProviderVerifier, "__call__",
                                  side_effect=AssertionError("No token verification")) as verify:
            self.assertIsNone(provider_preflight.inspect_configuration(
                self.paths["config"], self.paths["jwks"], self.paths["bindings"]))
        for mocked in (socket, connection, dns, urlopen, verify):
            mocked.assert_not_called()

    def test_success_and_failure_leave_files_and_permissions_unchanged(self):
        before = {name: (path.read_bytes(), path.stat().st_mtime_ns,
                         stat.S_IMODE(path.stat().st_mode)) for name, path in self.paths.items()}
        self.assertEqual(0, self.cli().returncode)
        self.assertEqual(2, self.cli(config=self.root / "absent.json").returncode)
        after = {name: (path.read_bytes(), path.stat().st_mtime_ns,
                        stat.S_IMODE(path.stat().st_mode)) for name, path in self.paths.items()}
        self.assertEqual(before, after)
        self.assertEqual({"config.json", "jwks.json", "bindings.json"},
                         {path.name for path in self.root.iterdir()})

    def test_missing_input_fails_without_creating_or_disclosing_path(self):
        missing = self.root / "private-missing-file.json"
        for field in self.paths:
            with self.subTest(field=field):
                result = self.cli(**{field: missing})
                self.assertEqual(2, result.returncode)
                self.assertEqual(self.expected("invalid_configuration"), json.loads(result.stdout))
                self.assertEqual("", result.stderr)
                self.assertNotIn(str(missing), result.stdout)
        self.assertFalse(missing.exists())

    def test_exact_file_size_limit_is_accepted_and_oversize_rejected(self):
        path = self.root / "bounded.json"
        path.write_bytes(b"{}" + b" " * (65536 - 2))
        self.assertEqual({}, provider_preflight.load_object(path))
        path.write_bytes(b"{}" + b" " * (65537 - 2))
        with self.assertRaises(ValueError):
            provider_preflight.load_object(path)
        self.assertEqual(2, self.cli(jwks=path).returncode)

    def test_directory_input_is_rejected(self):
        with self.assertRaises((OSError, ValueError)):
            provider_preflight.load_object(self.root)
        result = self.cli(config=self.root)
        self.assertEqual(2, result.returncode)
        self.assertEqual(self.expected("invalid_configuration"), json.loads(result.stdout))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Named pipes require POSIX")
    def test_fifo_is_rejected_without_blocking_or_reading(self):
        fifo = self.root / "not-a-regular-file"
        os.mkfifo(fifo, mode=0o600)
        result = self.cli(config=fifo)
        self.assertEqual(2, result.returncode)
        self.assertEqual(self.expected("invalid_configuration"), json.loads(result.stdout))

    def test_final_symlink_is_rejected_and_target_unchanged(self):
        link = self.root / "linked.json"
        target = self.paths["config"]
        before = target.read_bytes()
        link.symlink_to(target)
        with self.assertRaises(ValueError):
            provider_preflight.load_object(link)
        self.assertEqual(2, self.cli(config=link).returncode)
        self.assertEqual(before, target.read_bytes())

    def test_strict_json_rejects_duplicate_keys_constants_nonobjects_and_invalid_utf8(self):
        path = self.root / "malformed.json"
        payloads = (
            b'{"issuer":"one","issuer":"two"}', b'{"nested":{"kid":"a","kid":"b"}}',
            b'{"value":NaN}', b'{"value":Infinity}', b'{"value":-Infinity}',
            b'[]', b'null', b'"text"', b'42', b'', b'{}{}', b'{"value":"\xff"}',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                path.write_bytes(payload)
                with self.assertRaises((ValueError, UnicodeError)):
                    provider_preflight.load_object(path)

    @unittest.skipUnless(os.name == "posix", "POSIX permissions are required")
    def test_private_bindings_accept_owner_only_read_or_read_write_permissions(self):
        for mode in (0o400, 0o600):
            with self.subTest(mode=oct(mode)):
                self.paths["bindings"].chmod(mode)
                self.assertEqual(0, self.cli().returncode)
                self.assertEqual(mode, stat.S_IMODE(self.paths["bindings"].stat().st_mode))

    @unittest.skipUnless(os.name == "posix", "POSIX permissions are required")
    def test_bindings_reject_group_or_other_permissions_without_auto_chmod(self):
        for mode in (0o640, 0o604, 0o610, 0o602):
            with self.subTest(mode=oct(mode)):
                self.paths["bindings"].chmod(mode)
                result = self.cli()
                self.assertEqual(2, result.returncode)
                self.assertEqual(self.expected("invalid_configuration"), json.loads(result.stdout))
                self.assertEqual(mode, stat.S_IMODE(self.paths["bindings"].stat().st_mode))

    def test_unknown_arguments_do_not_echo_token_shaped_marker(self):
        marker = ".".join(("synthetic", "not_a_token", "do_not_echo"))
        for extra in (("--token", marker), (marker,), ("--unknown=" + marker,)):
            with self.subTest(argument_kind=extra[0].split("=")[0]):
                result = self.cli(*extra)
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertNotIn(marker, result.stderr)
                self.assertIn("Invalid arguments", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_missing_required_arguments_do_not_trigger_file_discovery(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["provider_preflight.py"]), \
                mock.patch.object(provider_preflight, "load_object") as loader, \
                redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exit_status:
                provider_preflight.main()
        self.assertEqual(2, exit_status.exception.code)
        loader.assert_not_called()
        self.assertEqual("", stdout.getvalue())
        self.assertNotIn(str(self.root), stderr.getvalue())

    def test_invalid_configuration_and_expired_snapshot_are_sanitized(self):
        for change in ({"issuer": "http://unsafe.example.invalid"},
                       {"jwks_expires_at": self.config["jwks_fetched_at"]},
                       {"unexpected_private_field": "synthetic-sensitive-marker"}):
            with self.subTest(changed_field=next(iter(change))):
                self.paths["config"].write_text(json.dumps({**self.config, **change}), encoding="utf-8")
                result = self.cli()
                self.assertEqual(2, result.returncode)
                self.assertEqual(self.expected("invalid_configuration"), json.loads(result.stdout))
                self.assertEqual("", result.stderr)
                self.assertNotIn("synthetic-sensitive-marker", result.stdout)


if __name__ == "__main__":
    unittest.main()
