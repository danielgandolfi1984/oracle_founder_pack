"""Offline adversarial tests; signing keys and tokens never leave memory."""

from __future__ import annotations

import base64
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import secrets
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
    from api import API
    from provider_auth import ProviderVerifier
    from store import Store
finally:
    sys.path.pop(0)


def b64uint(value: int) -> str:
    encoded = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(encoded).rstrip(b"=").decode("ascii")


def public_jwk(key, kid: str) -> dict:
    public = key.public_key().public_numbers()
    return {"kty": "RSA", "kid": kid, "n": b64uint(public.n), "e": b64uint(public.e)}


class ProviderVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.key_a = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.key_b = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_a = public_jwk(cls.key_a, "key-a")
        cls.public_b = public_jwk(cls.key_b, "key-b")

    def setUp(self) -> None:
        self.now = int(time.time())
        self.config = {
            "issuer": "https://issuer.example.invalid/tenant-a",
            "audience": "founder-api",
            "allowed_client_ids": ["founder-cli"],
            "required_scope": "founder:api",
            "max_token_lifetime_seconds": 900,
            "jwks_fetched_at": self.now - 10,
            "jwks_expires_at": self.now + 300,
        }
        self.jwks = {"keys": [dict(self.public_a)]}
        self.bindings = {
            "provider|alice": "alice",
            "provider|amy": "amy",
            "provider|bob": "bob",
        }
        self.claims = {
            "iss": self.config["issuer"], "aud": self.config["audience"],
            "sub": "provider|alice", "iat": self.now - 10, "exp": self.now + 300,
            "client_id": "founder-cli", "jti": "synthetic-request-1", "scope": "founder:api",
        }
        self.verifier = ProviderVerifier(self.config, self.jwks, self.bindings)

    def token(self, *, claims=None, headers=None, key=None, algorithm="RS256") -> str:
        # Sign adversarial claim shapes without relying on the JWT encoder's
        # own claim validation. This is a fixture generator, not a verifier.
        token_headers = {"typ": "at+jwt", "kid": "key-a"}
        if headers is not None:
            token_headers.update(headers)
        return jwt.PyJWS().encode(
            json.dumps(self.claims if claims is None else claims).encode("utf-8"),
            self.key_a if key is None else key,
            algorithm=algorithm, headers=token_headers,
        )

    def assert_bad_config(self, config=None, jwks=None, bindings=None) -> None:
        with self.assertRaises(ValueError):
            ProviderVerifier(
                self.config if config is None else config,
                self.jwks if jwks is None else jwks,
                self.bindings if bindings is None else bindings,
            )

    def test_valid_access_tokens_map_explicit_subjects_and_accept_type_case(self) -> None:
        self.assertIs(self.verifier.ready(), True)
        for typ in ("at+jwt", "AT+JWT", "application/at+jwt", "Application/AT+JWT"):
            with self.subTest(typ=typ):
                self.assertEqual("alice", self.verifier(self.token(headers={"typ": typ})))

    def test_not_before_is_optional_but_valid_when_present(self) -> None:
        self.assertEqual("alice", self.verifier(self.token()))
        self.assertEqual("alice", self.verifier(self.token(claims={**self.claims, "nbf": self.now - 5})))

    def test_id_token_type_is_rejected_even_with_access_like_claims(self) -> None:
        for typ in ("JWT", "jwt", None, "", "application/jwt"):
            with self.subTest(typ=typ):
                self.assertIsNone(self.verifier(self.token(headers={"typ": typ})))

    def test_original_local_lab_jwt_profile_is_not_a_provider_access_token(self) -> None:
        original_lab = {
            "iss": "https://local-lab.invalid", "aud": "oci-founder-local-backend",
            "sub": "alice", "iat": self.now, "nbf": self.now, "exp": self.now + 300,
        }
        token = jwt.encode(original_lab, self.key_a, algorithm="RS256", headers={"typ": "JWT"})
        self.assertIsNone(self.verifier(token))

    def test_key_id_must_be_present_bounded_and_known(self) -> None:
        missing = jwt.PyJWS().encode(
            json.dumps(self.claims).encode("utf-8"), self.key_a,
            algorithm="RS256", headers={"typ": "at+jwt"},
        )
        self.assertIsNone(self.verifier(missing))
        for kid in (None, "", "unknown-key", "key a", "x" * 129, 7):
            with self.subTest(kid_type=type(kid).__name__):
                # Bypass only the fixture encoder's header-shape guard.
                # Verification runs afterward with all library checks restored.
                with mock.patch.object(jwt.PyJWS, "_validate_headers"):
                    malformed = self.token(headers={"kid": kid})
                self.assertIsNone(self.verifier(malformed))

    def test_headers_cannot_supply_key_urls_claims_or_other_extensions(self) -> None:
        for field in ("jku", "jwk", "x5u", "x5c", "crit", "cty", "unexpected"):
            with self.subTest(field=field):
                self.assertIsNone(self.verifier(self.token(headers={field: None})))

    def test_wrong_signatures_and_other_algorithms_fail_closed(self) -> None:
        self.assertIsNone(self.verifier(self.token(key=self.key_b)))
        for algorithm in ("RS384", "RS512", "PS256"):
            with self.subTest(algorithm=algorithm):
                self.assertIsNone(self.verifier(self.token(algorithm=algorithm)))
        self.assertIsNone(self.verifier(self.token(key=secrets.token_bytes(64), algorithm="HS256")))
        unsigned = jwt.encode(self.claims, key="", algorithm="none", headers={"typ": "at+jwt", "kid": "key-a"})
        self.assertIsNone(self.verifier(unsigned))

    def test_every_required_claim_must_be_present_and_nonnull(self) -> None:
        for field in ("iss", "aud", "sub", "iat", "exp", "client_id", "jti", "scope"):
            with self.subTest(field=field):
                missing = dict(self.claims)
                del missing[field]
                self.assertIsNone(self.verifier(self.token(claims=missing)))
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: None})))

    def test_issuer_and_audience_are_exact_and_single_valued(self) -> None:
        for field, value in (
            ("iss", "https://issuer.example.invalid/tenant-b"),
            ("iss", self.config["issuer"] + "/"),
            ("aud", "another-api"),
            ("aud", [self.config["audience"]]),
            ("aud", [self.config["audience"], "another-api"]),
        ):
            with self.subTest(field=field, value_type=type(value).__name__):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: value})))

    def test_client_allowlist_and_scope_are_both_required(self) -> None:
        self.assertEqual("alice", self.verifier(self.token(claims={**self.claims, "scope": "read founder:api write"})))
        for field, value in (
            ("client_id", "other-client"), ("client_id", ["founder-cli"]),
            ("scope", "read"), ("scope", "founder:api:admin"), ("scope", "prefix-founder:api"),
            ("scope", ["founder:api"]), ("scope", " founder:api"),
            ("scope", "founder:api  read"), ("scope", "founder:api\tread"),
        ):
            with self.subTest(field=field, value_type=type(value).__name__):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: value})))

    def test_unknown_binding_cannot_be_replaced_by_email_roles_or_local_subject(self) -> None:
        for external_subject in ("unknown-provider-user", "alice"):
            spoof = {**self.claims, "sub": external_subject, "email": "alice@example.invalid",
                     "role": "owner", "roles": ["owner"], "workspace": "w-a"}
            self.assertIsNone(self.verifier(self.token(claims=spoof)))
        spoof = {**self.claims, "sub": "provider|amy", "role": "owner", "email": "alice@example.invalid"}
        self.assertEqual("amy", self.verifier(self.token(claims=spoof)))

    def test_bindings_reject_duplicate_local_ids_and_invalid_mappings(self) -> None:
        for bindings in (
            {"first": "alice", "second": "alice"}, {"first": "../alice"},
            {"first": "alice bob"}, {"first": "a" * 129}, {"": "alice"},
            {7: "alice"}, {"first": None}, ["provider|alice", "alice"],
        ):
            with self.subTest(binding_type=type(bindings).__name__):
                self.assert_bad_config(bindings=bindings)

    def test_empty_binding_map_is_ready_but_authenticates_nobody(self) -> None:
        verifier = ProviderVerifier(self.config, self.jwks, {})
        self.assertIs(verifier.ready(), True)
        self.assertIsNone(verifier(self.token()))

    def test_subject_client_and_token_id_are_bounded_noncontrol_strings(self) -> None:
        for field in ("sub", "client_id", "jti"):
            for value in ("", "x" * 257, "contains\x00control", 7, True, [], {}):
                with self.subTest(field=field, value_type=type(value).__name__):
                    self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: value})))

    def test_numeric_dates_require_json_integers_not_coercion(self) -> None:
        for field in ("iat", "exp", "nbf"):
            base = self.claims.get(field, self.now - 5)
            for value in (True, False, str(base), float(base), [], {}):
                with self.subTest(field=field, value_type=type(value).__name__):
                    self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: value})))

    def test_expired_future_and_inverted_time_windows_are_denied(self) -> None:
        for updates in (
            {"exp": self.now}, {"exp": self.now - 1}, {"iat": self.now + 60},
            {"nbf": self.now + 60}, {"exp": self.claims["iat"]},
        ):
            with self.subTest(fields=tuple(updates)):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, **updates})))

    def test_configured_maximum_token_lifetime_is_enforced(self) -> None:
        exact = {**self.claims, "exp": self.claims["iat"] + 900}
        self.assertEqual("alice", self.verifier(self.token(claims=exact)))
        self.assertIsNone(self.verifier(self.token(claims={**exact, "exp": exact["exp"] + 1})))

    def test_expired_snapshot_denies_an_otherwise_unexpired_access_token(self) -> None:
        config = {**self.config, "jwks_expires_at": self.now + 1}
        with mock.patch("provider_auth.time.time", return_value=self.now):
            verifier = ProviderVerifier(config, self.jwks, self.bindings)
        token = self.token()
        with mock.patch("provider_auth.time.time", return_value=self.now + 2):
            self.assertIs(verifier.ready(), False)
            self.assertIsNone(verifier(token))
            with self.assertRaises(ValueError):
                verifier.reload(config, self.jwks, self.bindings)
            self.assertIs(verifier.ready(), False)

    def test_monotonic_expiry_survives_wall_clock_rollback_and_stale_reload(self) -> None:
        config = {**self.config, "jwks_fetched_at": self.now - 600, "jwks_expires_at": self.now + 60}
        with mock.patch("provider_auth.time.time", return_value=self.now), \
                mock.patch("provider_auth.time.monotonic", return_value=1000.0):
            verifier = ProviderVerifier(config, self.jwks, self.bindings)
            self.assertIs(verifier.ready(), True)
        token = self.token()
        # Absolute wall time still appears fresh, but the original TTL elapsed.
        with mock.patch("provider_auth.time.time", return_value=self.now - 20), \
                mock.patch("provider_auth.time.monotonic", return_value=1061.0):
            self.assertIs(verifier.ready(), False)
            self.assertIsNone(verifier(token))
            with self.assertRaises(ValueError):
                verifier.reload(config, self.jwks, self.bindings)
            self.assertIs(verifier.ready(), False)

    def test_rotation_accepts_overlap_then_immediately_rejects_removed_key(self) -> None:
        old_token = self.token()
        new_token = self.token(key=self.key_b, headers={"kid": "key-b"})
        self.assertIsNone(self.verifier(new_token))
        self.verifier.reload(self.config, {"keys": [dict(self.public_a), dict(self.public_b)]}, self.bindings)
        self.assertEqual("alice", self.verifier(old_token))
        self.assertEqual("alice", self.verifier(new_token))
        self.verifier.reload(self.config, {"keys": [dict(self.public_b)]}, self.bindings)
        self.assertIsNone(self.verifier(old_token))
        self.assertEqual("alice", self.verifier(new_token))

    def test_invalid_reload_disables_previous_state_and_valid_reload_recovers(self) -> None:
        token = self.token()
        self.assertEqual("alice", self.verifier(token))
        with self.assertRaises(ValueError):
            self.verifier.reload(self.config, {"keys": []}, self.bindings)
        self.assertIs(self.verifier.ready(), False)
        self.assertIsNone(self.verifier(token))
        self.verifier.reload(self.config, self.jwks, self.bindings)
        self.assertIs(self.verifier.ready(), True)
        self.assertEqual("alice", self.verifier(token))

    def test_caller_mutations_cannot_change_a_loaded_trust_snapshot(self) -> None:
        token = self.token()
        self.config["issuer"] = "https://attacker.example.invalid"
        self.config["allowed_client_ids"].clear()
        self.config["jwks_expires_at"] = 0
        self.jwks["keys"][0]["n"] = "invalid"
        self.jwks["keys"].append(dict(self.public_b))
        self.bindings["provider|alice"] = "bob"
        self.assertIs(self.verifier.ready(), True)
        self.assertEqual("alice", self.verifier(token))

    def test_config_requires_exact_fields(self) -> None:
        for field in self.config:
            with self.subTest(missing=field):
                config = dict(self.config)
                del config[field]
                self.assert_bad_config(config=config)
        self.assert_bad_config(config={**self.config, "discovery_url": "https://other.example.invalid"})
        self.assert_bad_config(config=[])

    def test_issuer_configuration_requires_https_without_credentials_query_or_fragment(self) -> None:
        for issuer in (
            "http://issuer.example.invalid", "https://", "", "ftp://issuer.example.invalid",
            "https://user:password@issuer.example.invalid", "https://issuer.example.invalid?tenant=a",
            "https://issuer.example.invalid#fragment", 7,
        ):
            with self.subTest(issuer_type=type(issuer).__name__):
                self.assert_bad_config(config={**self.config, "issuer": issuer})

    def test_configured_lifetime_clients_audience_and_scope_are_strict(self) -> None:
        for field, value in (
            ("max_token_lifetime_seconds", 0), ("max_token_lifetime_seconds", 3601),
            ("max_token_lifetime_seconds", True), ("max_token_lifetime_seconds", 300.0),
            ("allowed_client_ids", []), ("allowed_client_ids", "founder-cli"),
            ("allowed_client_ids", ["founder-cli", "founder-cli"]),
            ("allowed_client_ids", [""]), ("audience", ""), ("audience", ["founder-api"]),
            ("required_scope", ""), ("required_scope", "founder:api other"),
            ("required_scope", 'scope"quoted'), ("required_scope", "scope\\escaped"),
        ):
            with self.subTest(field=field, value_type=type(value).__name__):
                self.assert_bad_config(config={**self.config, field: value})

    def test_snapshot_metadata_rejects_future_stale_and_oversized_windows(self) -> None:
        for updates in (
            {"jwks_fetched_at": self.now + 1}, {"jwks_expires_at": self.now},
            {"jwks_expires_at": self.now - 10}, {"jwks_fetched_at": self.now - 4000},
            {"jwks_fetched_at": True}, {"jwks_expires_at": float(self.now + 300)},
            {"jwks_fetched_at": str(self.now - 10)},
        ):
            with self.subTest(fields=tuple(updates)):
                self.assert_bad_config(config={**self.config, **updates})

    def test_public_jwk_optional_signature_metadata_is_accepted(self) -> None:
        decorated = {**self.public_a, "alg": "RS256", "use": "sig", "key_ops": ["verify"]}
        verifier = ProviderVerifier(self.config, {"keys": [decorated]}, self.bindings)
        self.assertEqual("alice", verifier(self.token()))

    def test_jwks_requires_one_to_eight_public_keys_and_unique_kids(self) -> None:
        variants = (
            {}, {"keys": []}, {"keys": "not-a-list"}, {"keys": [dict(self.public_a)], "extra": True},
            {"keys": [dict(self.public_a), dict(self.public_a)]},
            {"keys": [{**self.public_a, "kid": f"key-{number}"} for number in range(9)]},
        )
        for index, jwks in enumerate(variants):
            with self.subTest(case=index):
                self.assert_bad_config(jwks=jwks)

    def test_private_symmetric_and_nonrsa_jwk_material_is_rejected(self) -> None:
        for field in ("d", "p", "q", "dp", "dq", "qi", "oth"):
            with self.subTest(field=field):
                self.assert_bad_config(jwks={"keys": [{**self.public_a, field: "synthetic-invalid-field"}]})
        self.assert_bad_config(jwks={"keys": [{"kty": "oct", "kid": "key-a", "k": "c3ludGhldGlj"}]})
        self.assert_bad_config(jwks={"keys": [{**self.public_a, "kty": "EC"}]})

    def test_rsa_public_numbers_require_valid_encoding_size_and_exponent(self) -> None:
        for field, value in (
            ("n", "not+base64"), ("n", ""), ("n", 7), ("n", b64uint(257)),
            ("n", b64uint((1 << 8192) | 1)), ("e", b64uint(3)), ("e", ""),
            ("kid", ""), ("kid", "x" * 129), ("kid", "with space"),
        ):
            with self.subTest(field=field, value_type=type(value).__name__):
                self.assert_bad_config(jwks={"keys": [{**self.public_a, field: value}]})

    def test_jwk_metadata_cannot_select_other_algorithms_operations_or_urls(self) -> None:
        for field, value in (
            ("alg", "RS512"), ("use", "enc"), ("key_ops", ["sign"]),
            ("key_ops", ["verify", "sign"]), ("key_ops", "verify"),
            ("x5u", "https://keys.example.invalid"), ("unexpected", None),
        ):
            with self.subTest(field=field):
                self.assert_bad_config(jwks={"keys": [{**self.public_a, field: value}]})

    def test_malformed_tokens_and_decoder_errors_are_sanitized(self) -> None:
        for token in (None, 7, False, [], {}, b"bytes", "", "a.b.c", "a.b", "a.b.c.d"):
            with self.subTest(token_type=type(token).__name__):
                self.assertIsNone(self.verifier(token))
        token = self.token()
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("provider_auth.jwt.decode", side_effect=RuntimeError("synthetic private diagnostic")), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertIsNone(self.verifier(token))
        self.assertEqual("", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        self.assertFalse(token in repr(self.verifier), "Verifier repr must not contain a bearer value")

    def test_valid_provider_token_still_obeys_current_membership_and_owner_rules(self) -> None:
        with tempfile.TemporaryDirectory(prefix="oci-founder-provider-test-") as directory:
            store = Store(Path(directory) / "synthetic.sqlite3", create=True)
            try:
                store.seed_demo()
                api = API(store, self.verifier)
                alice = {"Authorization": "Bearer " + self.token()}
                amy_token = self.token(claims={**self.claims, "sub": "provider|amy", "role": "owner"})
                amy = {"Authorization": "Bearer " + amy_token, "Idempotency-Key": "amy-project"}
                project_path = "/workspaces/w-a/projects"
                body = {"name": "Synthetic provider project"}
                self.assertEqual(201, api.handle("POST", project_path, amy, body)[0])
                self.assertEqual(403, api.handle("DELETE", "/workspaces/w-a/members/alice", amy)[0])
                self.assertEqual(200, api.handle("DELETE", "/workspaces/w-a/members/amy", alice)[0])
                self.assertEqual("amy", self.verifier(amy_token))
                self.assertEqual(403, api.handle("GET", project_path, amy)[0])
                self.assertEqual(403, api.handle("POST", project_path, amy, body)[0])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
