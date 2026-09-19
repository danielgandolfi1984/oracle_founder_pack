"""Offline RS256 verification for the optional loopback-only teaching server.

This is not a login flow or an identity provider integration. A trusted public
key, issuer and audience must be supplied by the local harness, never selected
from token claims, HTTP headers, URLs or discovery. Cryptographic verification
is delegated to PyJWT and cryptography; no keys or tokens are logged or stored.
"""

from __future__ import annotations

import re

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from api import SEGMENT


MAX_TOKEN_LENGTH = 4096
MAX_TOKEN_LIFETIME_SECONDS = 900
_COMPACT_TOKEN = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
_FORBIDDEN_HEADERS = frozenset({"crit", "jku", "jwk", "x5u"})


class JWTVerifier:
    """Return a verified subject or None; never grant workspace membership.

Only one preconfigured RSA public key and the literal RS256 algorithm are
accepted. A ``kid`` may be present but is never used to select or fetch a key.
Tokens have a maximum lifetime of 15 minutes, with no clock-skew allowance.
The caller must still check current workspace membership on every operation.
"""

    def __init__(self, public_key: RSAPublicKey, *, issuer: str, audience: str):
        if not isinstance(public_key, RSAPublicKey):
            raise ValueError("a trusted RSA public key object is required")
        if public_key.key_size < 2048 or public_key.public_numbers().e != 65537:
            raise ValueError("RSA public keys require at least 2048 bits and exponent 65537")
        for value in (issuer, audience):
            if not isinstance(value, str) or re.fullmatch(r"[\x21-\x7e]{1,512}", value) is None:
                raise ValueError("issuer and audience must be nonempty printable ASCII strings")
        self._public_key = public_key
        self._issuer = issuer
        self._audience = audience

    def __call__(self, token: str) -> str | None:
        if (not isinstance(token, str) or len(token) > MAX_TOKEN_LENGTH
                or _COMPACT_TOKEN.fullmatch(token) is None):
            return None
        try:
            # This unverified header is used only to reject input, never to
            # choose an algorithm, key, URL or trusted identity.
            header = jwt.get_unverified_header(token)
            if (header.get("alg") != "RS256" or header.get("typ") != "JWT"
                    or _FORBIDDEN_HEADERS.intersection(header)):
                return None
            claims = jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
                issuer=self._issuer,
                audience=self._audience,
                leeway=0,
                options={
                    "require": ["iss", "aud", "sub", "iat", "nbf", "exp"],
                    "strict_aud": True,
                    "verify_signature": True,
                    "verify_iss": True,
                    "verify_aud": True,
                    "verify_sub": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                    "verify_exp": True,
                    "enforce_minimum_key_length": True,
                },
            )
            # PyJWT's NumericDate checks may coerce values; this lab deliberately
            # requires JSON integers and rejects booleans, floats and strings.
            if any(type(claims[name]) is not int for name in ("iat", "nbf", "exp")):
                return None
            if not (claims["iat"] <= claims["nbf"] < claims["exp"]
                    and 0 < claims["exp"] - claims["iat"] <= MAX_TOKEN_LIFETIME_SECONDS):
                return None
            if claims["iss"] != self._issuer or claims["aud"] != self._audience:
                return None
            subject = claims["sub"]
            if not isinstance(subject, str) or re.fullmatch(SEGMENT, subject) is None:
                return None
            return subject
        except Exception:
            # Fail closed for malformed claims, signatures and decoder failures.
            # Never expose exception text, token content, key details or claims.
            return None
