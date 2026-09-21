"""Safe diagnostic contracts: synthetic public fixtures and no provider calls."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa


EXAMPLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE))
try:
    import provider_auth
    import provider_preflight
    from provider_demo import public_jwk
finally:
    sys.path.pop(0)


AUTH_CODES = {
    "invalid_config_fields", "invalid_issuer", "invalid_audience",
    "invalid_client_allowlist", "invalid_required_scope", "invalid_time_policy",
    "invalid_public_jwks", "invalid_subject_bindings", "invalid_clock", "invalid_snapshot",
}
MARKER = "synthetic-do-not-disclose-marker"


class ProviderDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public = public_jwk(cls.signing_key, "synthetic-public-key")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="founder-diagnostics-private-path-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        now = int(time.time())
        self.config = {
            "issuer": f"https://{MARKER}.example.invalid",
            "audience": f"synthetic-api-{MARKER}",
            "allowed_client_ids": [f"synthetic-client-{MARKER}"],
            "required_scope": "founder:api",
            "max_token_lifetime_seconds": 900,
            "jwks_fetched_at": now - 1,
            "jwks_expires_at": now + 300,
        }
        self.jwks = {"keys": [dict(self.public)]}
        self.bindings = {f"external|{MARKER}": "alice"}
        self.paths = {}
        for name, value in (("config", self.config), ("jwks", self.jwks), ("bindings", self.bindings)):
            path = self.root / f"{name}-{MARKER}.json"
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(value, stream)
            self.paths[name] = path

    def write(self, name, value):
        self.paths[name].write_text(json.dumps(value), encoding="utf-8")

    def arguments(self, **overrides):
        paths = {**self.paths, **overrides}
        return [value for name in ("config", "jwks", "bindings")
                for value in ("--" + name, str(paths[name]))]

    def cli(self, *, diagnostics=True, extra=(), **overrides):
        stdout, stderr = io.StringIO(), io.StringIO()
        arguments = ["provider_preflight.py", *self.arguments(**overrides)]
        if diagnostics:
            arguments.append("--diagnostics")
        arguments.extend(extra)
        with mock.patch.object(sys, "argv", arguments), redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                status = provider_preflight.main()
            except SystemExit as error:
                status = error.code
        return status, stdout.getvalue(), stderr.getvalue()

    def assert_redacted(self, value):
        for forbidden in (
            MARKER, self.config["issuer"], self.config["audience"],
            self.config["allowed_client_ids"][0], next(iter(self.bindings)),
            self.public["n"], str(self.root), self.root.name,
        ):
            self.assertFalse(forbidden in value, "Diagnostic disclosed synthetic input or path")
        self.assertNotIn("Traceback", value)

    def assert_diagnostic(self, input_name, code, **overrides):
        status, stdout, stderr = self.cli(**overrides)
        self.assertEqual(2, status)
        self.assertEqual("", stderr)
        self.assertEqual({
            "status": "invalid_configuration", "provider_connection_tested": False,
            "token_verified": False, "network_calls": 0,
            "diagnostics": [{"input": input_name, "code": code}],
        }, json.loads(stdout))
        self.assert_redacted(stdout)

    def capture_auth_error(self, config=None, jwks=None, bindings=None):
        with self.assertRaises(provider_auth.ProviderConfigurationError) as raised:
            provider_auth.ProviderVerifier(
                self.config if config is None else config,
                self.jwks if jwks is None else jwks,
                self.bindings if bindings is None else bindings,
            )
        error = raised.exception
        self.assertIsInstance(error, ValueError)
        self.assertIn(error.code, AUTH_CODES)
        self.assert_redacted(str(error))
        self.assert_redacted(repr(error))
        return error

    def test_opt_in_success_has_empty_diagnostics_and_no_input_disclosure(self):
        status, stdout, stderr = self.cli()
        self.assertEqual(0, status)
        self.assertEqual("", stderr)
        self.assertEqual({
            "status": "configuration_valid", "provider_connection_tested": False,
            "token_verified": False, "network_calls": 0, "diagnostics": [],
        }, json.loads(stdout))
        self.assert_redacted(stdout)

    def test_default_output_remains_backward_compatible(self):
        for overrides, expected_status, expected_exit in (
            ({}, "configuration_valid", 0),
            ({"config": self.root / f"missing-{MARKER}.json"}, "invalid_configuration", 2),
        ):
            with self.subTest(status=expected_status):
                status, stdout, stderr = self.cli(diagnostics=False, **overrides)
                self.assertEqual(expected_exit, status)
                self.assertEqual("", stderr)
                self.assertEqual({
                    "status": expected_status, "provider_connection_tested": False,
                    "token_verified": False, "network_calls": 0,
                }, json.loads(stdout))
                self.assert_redacted(stdout)

    def test_missing_files_identify_only_the_input_phase(self):
        missing = self.root / f"missing-{MARKER}.json"
        for name in self.paths:
            with self.subTest(input=name):
                self.assert_diagnostic(name, "input_file_unavailable", **{name: missing})
        self.assertFalse(missing.exists())

    def test_directory_and_symlink_have_file_type_diagnostics(self):
        self.assert_diagnostic("config", "input_file_type", config=self.root)
        symlink = self.root / f"symlink-{MARKER}.json"
        symlink.symlink_to(self.paths["jwks"])
        self.assert_diagnostic("jwks", "input_file_type", jwks=symlink)

    def test_oversized_file_has_bounded_size_diagnostic_without_contents(self):
        self.paths["jwks"].write_bytes(b"x" * (provider_preflight.MAX_FILE_BYTES + 1))
        self.assert_diagnostic("jwks", "input_file_too_large")

    @unittest.skipUnless(os.name == "posix", "POSIX permissions are required")
    def test_private_binding_permission_failure_is_specific_and_non_mutating(self):
        self.paths["bindings"].chmod(0o640)
        self.assert_diagnostic("bindings", "input_permissions")
        self.assertEqual(0o640, self.paths["bindings"].stat().st_mode & 0o777)

    def test_invalid_json_reports_its_phase_without_parser_details(self):
        for name in self.paths:
            with self.subTest(input=name):
                original = self.paths[name].read_bytes()
                try:
                    self.paths[name].write_text('{"private":"' + MARKER, encoding="utf-8")
                    self.assert_diagnostic(name, "invalid_json")
                finally:
                    self.paths[name].write_bytes(original)

    def test_nonobject_and_duplicate_key_json_use_the_same_safe_diagnostic(self):
        for payload in ('["' + MARKER + '"]', '{"key":"' + MARKER + '","key":2}'):
            with self.subTest(shape="array" if payload.startswith("[") else "duplicate"):
                self.paths["config"].write_text(payload, encoding="utf-8")
                self.assert_diagnostic("config", "invalid_json")

    def test_configuration_failures_have_specific_allowlisted_codes(self):
        cases = (
            ({**self.config, "unrecognized": MARKER}, "invalid_config_fields"),
            ({**self.config, "issuer": f"http://{MARKER}.example.invalid"}, "invalid_issuer"),
            ({**self.config, "audience": []}, "invalid_audience"),
            ({**self.config, "allowed_client_ids": [MARKER, MARKER]}, "invalid_client_allowlist"),
            ({**self.config, "required_scope": MARKER + " another"}, "invalid_required_scope"),
            ({**self.config, "max_token_lifetime_seconds": 3601}, "invalid_time_policy"),
            ({**self.config, "jwks_expires_at": self.config["jwks_fetched_at"]}, "invalid_time_policy"),
        )
        for config, code in cases:
            with self.subTest(code=code):
                self.assertEqual(code, self.capture_auth_error(config=config).code)
                self.write("config", config)
                self.assert_diagnostic("config", code)

    def test_url_parser_errors_still_classify_as_invalid_issuer(self):
        for issuer in (f"https://{MARKER}.example.invalid:invalid", "https://[broken"):
            with self.subTest(kind="port" if ":invalid" in issuer else "host"):
                config = {**self.config, "issuer": issuer}
                self.assertEqual("invalid_issuer", self.capture_auth_error(config=config).code)
                self.write("config", config)
                self.assert_diagnostic("config", "invalid_issuer")

    def test_public_key_failure_has_jwks_phase_and_no_key_diagnostics(self):
        for jwks in ({"keys": []}, {"keys": [{**self.public, "n": "invalid"}]}):
            with self.subTest(key_count=len(jwks["keys"])):
                self.assertEqual("invalid_public_jwks", self.capture_auth_error(jwks=jwks).code)
                self.write("jwks", jwks)
                self.assert_diagnostic("jwks", "invalid_public_jwks")

    def test_subject_mapping_failure_has_bindings_phase_without_identifiers(self):
        invalid = {f"first|{MARKER}": "alice", f"second|{MARKER}": "alice"}
        self.assertEqual("invalid_subject_bindings", self.capture_auth_error(bindings=invalid).code)
        self.write("bindings", invalid)
        self.assert_diagnostic("bindings", "invalid_subject_bindings")

    def test_clock_fault_has_snapshot_phase_without_clock_details(self):
        with mock.patch("provider_auth.time.monotonic", return_value=float("nan")):
            self.assertEqual("invalid_clock", self.capture_auth_error().code)
            self.assert_diagnostic("snapshot", "invalid_clock")

    def test_unexpected_snapshot_failure_uses_safe_fallback_code(self):
        with mock.patch("provider_auth.deepcopy", side_effect=RuntimeError(MARKER)):
            self.assertEqual("invalid_snapshot", self.capture_auth_error().code)
            self.assert_diagnostic("snapshot", "invalid_snapshot")

    def test_auth_error_constructor_cannot_publish_an_unrecognized_code(self):
        for code in (MARKER, "", None, [], {}, 7):
            with self.subTest(code_type=type(code).__name__):
                error = provider_auth.ProviderConfigurationError(code)
                self.assertIsInstance(error, ValueError)
                self.assertEqual("invalid_snapshot", error.code)
                self.assert_redacted(str(error))
                self.assert_redacted(repr(error))

    def test_preflight_error_constructor_accepts_only_plain_allowlisted_labels(self):
        class UntrustedLabel(str):
            def __str__(self):
                return MARKER

        for input_name, code in (
            (MARKER, MARKER), (None, None), ([], {}), (7, []),
            (UntrustedLabel("config"), UntrustedLabel("invalid_audience")),
        ):
            with self.subTest(input_type=type(input_name).__name__, code_type=type(code).__name__):
                error = provider_preflight.PreflightError(input_name, code)
                self.assertIsInstance(error, ValueError)
                self.assertEqual("snapshot", error.input)
                self.assertEqual("invalid_snapshot", error.code)
                self.assertIs(type(error.input), str)
                self.assertIs(type(error.code), str)
                self.assert_redacted(str(error))
                self.assert_redacted(repr(error))

    def test_unready_snapshot_has_safe_fallback_diagnostic(self):
        with mock.patch.object(provider_preflight.ProviderVerifier, "ready", return_value=False):
            self.assert_diagnostic("snapshot", "invalid_snapshot")

    def test_unexpected_valueerror_cannot_disclose_exception_text(self):
        with mock.patch.object(provider_preflight, "inspect_configuration", side_effect=ValueError(MARKER)):
            self.assert_diagnostic("snapshot", "invalid_snapshot")

    def test_inspection_keeps_none_on_success_and_typed_safe_valueerror_on_failure(self):
        paths = [self.paths[name] for name in ("config", "jwks", "bindings")]
        self.assertIsNone(provider_preflight.inspect_configuration(*paths))
        self.write("config", {**self.config, "audience": []})
        with self.assertRaises(provider_preflight.PreflightError) as raised:
            provider_preflight.inspect_configuration(*paths)
        error = raised.exception
        self.assertIsInstance(error, ValueError)
        self.assertEqual("config", error.input)
        self.assertEqual("invalid_audience", error.code)
        self.assertEqual("Invalid provider configuration", str(error))
        self.assert_redacted(repr(error))

    def test_invalid_reload_keeps_old_state_disabled_until_valid_recovery(self):
        verifier = provider_auth.ProviderVerifier(self.config, self.jwks, self.bindings)
        now = int(time.time())
        token = jwt.encode({
            "iss": self.config["issuer"], "aud": self.config["audience"],
            "sub": next(iter(self.bindings)), "client_id": self.config["allowed_client_ids"][0],
            "iat": now - 1, "exp": now + 200, "jti": "synthetic-memory-only",
            "scope": "founder:api",
        }, self.signing_key, algorithm="RS256", headers={"typ": "at+jwt", "kid": "synthetic-public-key"})
        self.assertEqual("alice", verifier(token))
        cases = (
            ({**self.config, "issuer": "http://invalid.example.invalid"}, self.jwks, self.bindings, "invalid_issuer"),
            (self.config, {"keys": []}, self.bindings, "invalid_public_jwks"),
            (self.config, self.jwks, {MARKER: "../alice"}, "invalid_subject_bindings"),
        )
        for config, jwks, bindings, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(provider_auth.ProviderConfigurationError) as raised:
                    verifier.reload(config, jwks, bindings)
                self.assertEqual(code, raised.exception.code)
                self.assertIs(verifier.ready(), False)
                self.assertIsNone(verifier(token))
                verifier.reload(self.config, self.jwks, self.bindings)
                self.assertIs(verifier.ready(), True)
                self.assertEqual("alice", verifier(token))

    def test_diagnostics_do_not_contact_network_verify_tokens_or_write_files(self):
        before = {name: (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
                  for name, path in self.paths.items()}
        with mock.patch("socket.socket", side_effect=AssertionError("No sockets")) as socket, \
                mock.patch("socket.getaddrinfo", side_effect=AssertionError("No DNS")) as dns, \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("No fetching")) as fetch, \
                mock.patch.object(provider_auth.ProviderVerifier, "__call__",
                                  side_effect=AssertionError("No bearer input")) as verify:
            self.assertEqual(0, self.cli()[0])
        for patched in (socket, dns, fetch, verify):
            patched.assert_not_called()
        after = {name: (path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
                 for name, path in self.paths.items()}
        self.assertEqual(before, after)

    def test_argument_errors_stay_sanitized_with_diagnostics_flag(self):
        status, stdout, stderr = self.cli(extra=("--unknown=" + MARKER,))
        self.assertEqual(2, status)
        self.assertEqual("", stdout)
        self.assertIn("Invalid arguments", stderr)
        self.assert_redacted(stderr)


if __name__ == "__main__":
    unittest.main()
