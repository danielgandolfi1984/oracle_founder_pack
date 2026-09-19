"""Offline verifier tests; ephemeral keys and tokens exist only in memory."""

from __future__ import annotations

import json
import secrets
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


EXAMPLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE))
try:
    from jwt_auth import JWTVerifier, MAX_TOKEN_LENGTH
finally:
    sys.path.pop(0)


class JWTVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = cls.key.public_key()
        cls.issuer = "urn:founder-toolkit:local-lab"
        cls.audience = "founder-toolkit-local-api"

    def setUp(self) -> None:
        self.verifier = JWTVerifier(self.public_key, issuer=self.issuer, audience=self.audience)
        now = int(time.time())
        self.claims = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": "alice",
            "iat": now - 10,
            "nbf": now - 10,
            "exp": now + 300,
        }

    def token(self, *, claims=None, headers=None, key=None, algorithm="RS256") -> str:
        # The JWS API signs deliberately malformed claims as well. The normal
        # JWT encoder itself rejects some malformed issuer claims in PyJWT 2.14.
        return jwt.PyJWS().encode(
            json.dumps(self.claims if claims is None else claims).encode("utf-8"),
            self.key if key is None else key,
            algorithm=algorithm,
            headers=headers,
        )

    def test_valid_token_returns_subject(self) -> None:
        self.assertEqual("alice", self.verifier(self.token()))

    def test_optional_key_id_does_not_select_a_key(self) -> None:
        self.assertEqual("alice", self.verifier(self.token(headers={"kid": "unselected-label"})))
        self.assertIsNone(self.verifier(self.token(key=self.other_key, headers={"kid": "unselected-label"})))

    def test_only_subject_is_returned_not_untrusted_roles(self) -> None:
        claims = {**self.claims, "role": "owner", "workspace": "w-b", "admin": True}
        self.assertEqual("alice", self.verifier(self.token(claims=claims)))

    def test_wrong_signing_key_is_denied(self) -> None:
        self.assertIsNone(self.verifier(self.token(key=self.other_key)))

    def test_signature_tampering_is_denied(self) -> None:
        header, payload, signature = self.token().split(".")
        replacement = "A" if signature[0] != "A" else "B"
        self.assertIsNone(self.verifier(".".join((header, payload, replacement + signature[1:]))))

    def test_payload_tampering_is_denied(self) -> None:
        header, _, signature = self.token().split(".")
        other_payload = self.token(claims={**self.claims, "sub": "bob"}).split(".")[1]
        self.assertIsNone(self.verifier(".".join((header, other_payload, signature))))

    def test_unsigned_token_is_denied(self) -> None:
        self.assertIsNone(self.verifier(jwt.encode(self.claims, key="", algorithm="none")))

    def test_hmac_and_rsa_hmac_confusion_are_denied(self) -> None:
        # Even a public key reinterpreted as an HMAC secret must never verify.
        public_der = self.public_key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
        self.assertIsNone(self.verifier(self.token(key=secrets.token_bytes(64), algorithm="HS256")))
        # PyJWT also blocks asymmetric keys in its HMAC encoder. Bypass only
        # that encoder guard to build the adversarial fixture; the verifier is
        # invoked after the mock has been removed, with all checks intact.
        with mock.patch("jwt.algorithms.HMACAlgorithm.prepare_key", return_value=public_der):
            forged = self.token(key=public_der, algorithm="HS256")
        self.assertIsNone(self.verifier(forged))

    def test_other_rsa_algorithms_are_denied(self) -> None:
        for algorithm in ("RS384", "RS512", "PS256"):
            with self.subTest(algorithm=algorithm):
                self.assertIsNone(self.verifier(self.token(algorithm=algorithm)))

    def test_token_type_must_be_explicit_jwt(self) -> None:
        for value in (None, "jwt", "at+jwt", "", 7):
            with self.subTest(value=value):
                self.assertIsNone(self.verifier(self.token(headers={"typ": value})))

    def test_key_sources_and_critical_headers_are_denied_even_if_empty(self) -> None:
        for field in ("crit", "jku", "jwk", "x5u"):
            for value in (None, "", [], {}):
                with self.subTest(field=field, value=value):
                    self.assertIsNone(self.verifier(self.token(headers={field: value})))

    def test_required_claims_cannot_be_missing_or_null(self) -> None:
        for field in ("iss", "aud", "sub", "iat", "nbf", "exp"):
            claims = dict(self.claims)
            del claims[field]
            with self.subTest(field=field, variation="missing"):
                self.assertIsNone(self.verifier(self.token(claims=claims)))
            with self.subTest(field=field, variation="null"):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: None})))

    def test_wrong_issuer_and_audience_are_denied(self) -> None:
        for field in ("iss", "aud"):
            for value in ("wrong-value", "", 7, True, {}, [self.claims[field]]):
                with self.subTest(field=field, value=value):
                    self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: value})))

    def test_multiple_audiences_are_denied(self) -> None:
        self.assertIsNone(self.verifier(self.token(claims={**self.claims, "aud": [self.audience, "another-api"]})))

    def test_expired_token_and_expiration_now_are_denied(self) -> None:
        for expiration in (int(time.time()) - 1, int(time.time())):
            with self.subTest(expiration=expiration):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, "exp": expiration})))

    def test_future_issued_at_and_not_before_are_denied(self) -> None:
        for field in ("iat", "nbf"):
            with self.subTest(field=field):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: int(time.time()) + 60})))

    def test_numeric_dates_require_integers_not_coercible_values(self) -> None:
        for field in ("iat", "nbf", "exp"):
            for value in (True, False, str(self.claims[field]), float(self.claims[field]), [], {}, float("inf")):
                with self.subTest(field=field, type=type(value).__name__):
                    self.assertIsNone(self.verifier(self.token(claims={**self.claims, field: value})))

    def test_lifetime_cannot_exceed_fifteen_minutes(self) -> None:
        claims = {**self.claims, "exp": self.claims["iat"] + 901}
        self.assertIsNone(self.verifier(self.token(claims=claims)))

    def test_fifteen_minute_lifetime_is_accepted(self) -> None:
        claims = {**self.claims, "exp": self.claims["iat"] + 900}
        self.assertEqual("alice", self.verifier(self.token(claims=claims)))

    def test_not_before_cannot_precede_issued_at(self) -> None:
        self.assertIsNone(self.verifier(self.token(claims={**self.claims, "nbf": self.claims["iat"] - 1})))

    def test_empty_or_inverted_validity_window_is_denied(self) -> None:
        for expiration in (self.claims["iat"], self.claims["iat"] - 1):
            with self.subTest(expiration=expiration):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, "exp": expiration})))

    def test_invalid_subjects_are_denied(self) -> None:
        for subject in ("", "../alice", "alice bob", "álîce", "a" * 129, 7, True, [], {}):
            with self.subTest(subject=subject):
                self.assertIsNone(self.verifier(self.token(claims={**self.claims, "sub": subject})))

    def test_longest_valid_subject_is_accepted(self) -> None:
        subject = "a" * 128
        self.assertEqual(subject, self.verifier(self.token(claims={**self.claims, "sub": subject})))

    def test_malformed_and_nonstring_tokens_are_denied(self) -> None:
        for token in (None, False, 7, [], {}, b"not-a-token", "", "one", "a.b", "a.b.c.d", "a..b", "a.b.c", "a.b.é", "a.b.c\n"):
            with self.subTest(type=type(token).__name__):
                self.assertIsNone(self.verifier(token))

    def test_oversized_signed_token_is_denied_before_parsing(self) -> None:
        token = self.token(claims={**self.claims, "padding": "x" * MAX_TOKEN_LENGTH})
        self.assertGreater(len(token), MAX_TOKEN_LENGTH)
        with mock.patch("jwt_auth.jwt.get_unverified_header") as parse:
            self.assertIsNone(self.verifier(token))
            parse.assert_not_called()

    def test_decoder_errors_fail_closed_without_output(self) -> None:
        token = self.token()
        with mock.patch("jwt_auth.jwt.decode", side_effect=RuntimeError("private diagnostic")):
            with mock.patch("builtins.print") as output:
                self.assertIsNone(self.verifier(token))
                output.assert_not_called()

    def test_private_keys_serializations_and_nonrsa_keys_are_rejected(self) -> None:
        for key in (self.key, "not-a-key", b"not-a-key", None, {}, ec.generate_private_key(ec.SECP256R1()).public_key()):
            with self.subTest(type=type(key).__name__):
                with self.assertRaises(ValueError):
                    JWTVerifier(key, issuer=self.issuer, audience=self.audience)

    def test_undersized_rsa_key_is_rejected(self) -> None:
        key = rsa.generate_private_key(public_exponent=65537, key_size=1024).public_key()
        with self.assertRaises(ValueError):
            JWTVerifier(key, issuer=self.issuer, audience=self.audience)

    def test_nonstandard_rsa_exponent_is_rejected(self) -> None:
        key = rsa.generate_private_key(public_exponent=3, key_size=2048).public_key()
        with self.assertRaises(ValueError):
            JWTVerifier(key, issuer=self.issuer, audience=self.audience)

    def test_invalid_constructor_issuer_and_audience_are_rejected(self) -> None:
        for field in ("issuer", "audience"):
            for value in (None, True, 7, [], {}, "", " ", "a b", "a\n", "á", "a" * 513):
                config = {"issuer": self.issuer, "audience": self.audience, field: value}
                with self.subTest(field=field, type=type(value).__name__):
                    with self.assertRaises(ValueError):
                        JWTVerifier(self.public_key, **config)


if __name__ == "__main__":
    unittest.main()
