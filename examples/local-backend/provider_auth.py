"""Offline access-token contract, not provider discovery, login or deployment.

Trusted callers supply one issuer, public keys and explicit subject bindings.
No token can select a URL, algorithm, membership, role or unconfigured key.
PyJWT/cryptography perform signature verification. Contract references:
https://www.rfc-editor.org/rfc/rfc9068.html#section-4
https://www.rfc-editor.org/rfc/rfc8725.html#section-3
https://www.rfc-editor.org/rfc/rfc7517.html#section-4
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
import re
from threading import RLock
import time
import unicodedata
from urllib.parse import urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from api import SEGMENT


_CONFIG_FIELDS = {"issuer", "audience", "allowed_client_ids", "required_scope",
                  "max_token_lifetime_seconds", "jwks_fetched_at", "jwks_expires_at"}
_JWK_FIELDS = {"kty", "kid", "n", "e", "alg", "use", "key_ops"}
_SCOPE_TOKEN = re.compile(r"[\x21\x23-\x5b\x5d-\x7e]{1,128}")
_COMPACT_TOKEN = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
_REQUIRED_CLAIMS = ["iss", "aud", "sub", "iat", "exp", "client_id", "jti", "scope"]


def _ascii(value, limit):
    return (isinstance(value, str) and 1 <= len(value) <= limit
            and all(33 <= ord(character) <= 126 for character in value))


def _opaque(value):
    return (isinstance(value, str) and 1 <= len(value) <= 256
            and not any(unicodedata.category(character) in {"Cc", "Cf", "Cs"}
                        for character in value))


@dataclass(frozen=True)
class _Snapshot:
    config: dict
    keys: dict
    bindings: dict
    deadline: float


class ProviderVerifier:
    """Verify a bounded, explicitly configured subset of RFC 9068 offline.

    There is no automatic key refresh, replay prevention or claim-to-role
    mapping. A fresh trusted snapshot and explicit external-subject binding
    are mandatory. Invalid reloads disable verification, with no old-key
    fallback. Current application membership remains a separate check.
    """

    def __init__(self, config: dict, jwks: dict, bindings: dict):
        self._lock = RLock()
        self._snapshot = None
        self._effective_time = time.time()
        self._monotonic_time = time.monotonic()
        self.reload(config, jwks, bindings)

    def _clock(self):
        wall, monotonic = time.time(), time.monotonic()
        if (not math.isfinite(wall) or not math.isfinite(monotonic)
                or monotonic < self._monotonic_time):
            raise ValueError("invalid clock")
        # Keep this high-water clock across reloads, including failed reloads.
        # Reusing an absolute expiry cannot restart an elapsed snapshot TTL.
        self._effective_time = max(wall, self._effective_time + monotonic - self._monotonic_time)
        self._monotonic_time = monotonic
        return wall, monotonic, self._effective_time

    @staticmethod
    def _config(config, wall, effective):
        if not isinstance(config, dict) or set(config) != _CONFIG_FIELDS:
            raise ValueError
        issuer = config["issuer"]
        if not _ascii(issuer, 2048) or any(character in issuer for character in "\\?#"):
            raise ValueError
        parsed = urlsplit(issuer)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or "%" in parsed.netloc
                or (parsed.port is not None and not 1 <= parsed.port <= 65535)):
            raise ValueError
        if not _ascii(config["audience"], 512):
            raise ValueError
        clients = config["allowed_client_ids"]
        if (not isinstance(clients, list) or not 1 <= len(clients) <= 16
                or not all(_ascii(client, 256) for client in clients)
                or len(set(clients)) != len(clients)):
            raise ValueError
        scope = config["required_scope"]
        if not isinstance(scope, str) or _SCOPE_TOKEN.fullmatch(scope) is None:
            raise ValueError
        lifetime, fetched, expires = (config[name] for name in (
            "max_token_lifetime_seconds", "jwks_fetched_at", "jwks_expires_at"))
        if (any(type(value) is not int for value in (lifetime, fetched, expires))
                or not 1 <= lifetime <= 3600 or not 0 < expires - fetched <= 3600
                or not fetched <= wall < expires or effective >= expires):
            raise ValueError

    @staticmethod
    def _keys(jwks):
        if (not isinstance(jwks, dict) or set(jwks) != {"keys"}
                or not isinstance(jwks["keys"], list) or not 1 <= len(jwks["keys"]) <= 8):
            raise ValueError
        result = {}
        for key in jwks["keys"]:
            if (not isinstance(key, dict) or not {"kty", "kid", "n", "e"} <= set(key)
                    or not set(key) <= _JWK_FIELDS or key["kty"] != "RSA"
                    or not _ascii(key["kid"], 128) or key["kid"] in result
                    or ("alg" in key and key["alg"] != "RS256")
                    or ("use" in key and key["use"] != "sig")
                    or ("key_ops" in key and key["key_ops"] != ["verify"])):
                raise ValueError
            for name, limit in (("n", 1366), ("e", 8)):
                value = key[name]
                if (not isinstance(value, str) or not 1 <= len(value) <= limit
                        or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None):
                    raise ValueError
            public = jwt.PyJWK.from_dict(key, algorithm="RS256").key
            if (not isinstance(public, RSAPublicKey) or not 2048 <= public.key_size <= 8192
                    or public.public_numbers().e != 65537):
                raise ValueError
            result[key["kid"]] = public
        return result

    @staticmethod
    def _bindings(bindings):
        if not isinstance(bindings, dict) or len(bindings) > 1000:
            raise ValueError
        for external, local in bindings.items():
            if (not _opaque(external) or not isinstance(local, str)
                    or re.fullmatch(SEGMENT, local) is None):
                raise ValueError
        if len(set(bindings.values())) != len(bindings):
            raise ValueError

    def reload(self, config: dict, jwks: dict, bindings: dict) -> None:
        """Atomically replace trusted inputs; invalid input disables all calls."""
        with self._lock:
            self._snapshot = None
            try:
                config, jwks, bindings = deepcopy((config, jwks, bindings))
                wall, monotonic, effective = self._clock()
                self._config(config, wall, effective)
                keys = self._keys(jwks)
                self._bindings(bindings)
                self._snapshot = _Snapshot(config, keys, bindings,
                                           monotonic + config["jwks_expires_at"] - effective)
            except Exception:
                raise ValueError("invalid trusted provider snapshot") from None

    @staticmethod
    def _fresh(snapshot, wall, monotonic, effective):
        return (snapshot is not None and monotonic < snapshot.deadline
                and snapshot.config["jwks_fetched_at"] <= wall < snapshot.config["jwks_expires_at"]
                and effective < snapshot.config["jwks_expires_at"])

    def ready(self) -> bool:
        with self._lock:
            try:
                return self._fresh(self._snapshot, *self._clock())
            except Exception:
                return False

    def __call__(self, token: str) -> str | None:
        if (not isinstance(token, str) or len(token) > 4096
                or _COMPACT_TOKEN.fullmatch(token) is None):
            return None
        with self._lock:
            try:
                snapshot = self._snapshot
                if not self._fresh(snapshot, *self._clock()):
                    return None
                header = jwt.get_unverified_header(token)
                if (set(header) != {"alg", "typ", "kid"} or header["alg"] != "RS256"
                        or not isinstance(header["typ"], str)
                        or header["typ"].lower() not in {"at+jwt", "application/at+jwt"}
                        or not _ascii(header["kid"], 128) or header["kid"] not in snapshot.keys):
                    return None
                config = snapshot.config
                claims = jwt.decode(
                    token, snapshot.keys[header["kid"]], algorithms=["RS256"],
                    issuer=config["issuer"], audience=config["audience"], leeway=0,
                    options={"require": _REQUIRED_CLAIMS, "strict_aud": True,
                             "verify_signature": True, "verify_iss": True, "verify_aud": True,
                             "verify_sub": True, "verify_iat": True, "verify_exp": True,
                             "verify_nbf": True, "verify_jti": True,
                             "enforce_minimum_key_length": True},
                )
                wall, monotonic, effective = self._clock()
                if not self._fresh(snapshot, wall, monotonic, effective):
                    return None
                dates = [claims["iat"], claims["exp"]]
                if "nbf" in claims:
                    dates.append(claims["nbf"])
                if (any(type(value) is not int for value in dates)
                        or not claims["iat"] <= wall < claims["exp"]
                        or effective >= claims["exp"]
                        or not 0 < claims["exp"] - claims["iat"] <= config["max_token_lifetime_seconds"]
                        or ("nbf" in claims and not claims["iat"] <= claims["nbf"] <= wall < claims["exp"])):
                    return None
                if (claims["iss"] != config["issuer"] or claims["aud"] != config["audience"]
                        or not _ascii(claims["client_id"], 256)
                        or claims["client_id"] not in config["allowed_client_ids"]
                        or not _opaque(claims["sub"]) or not _opaque(claims["jti"])):
                    return None
                scope = claims["scope"]
                if (not isinstance(scope, str) or not 1 <= len(scope) <= 2048
                        or any(_SCOPE_TOKEN.fullmatch(item) is None for item in scope.split(" "))
                        or config["required_scope"] not in scope.split(" ")):
                    return None
                return snapshot.bindings.get(claims["sub"])
            except Exception:
                # No token contents, identifiers or library diagnostics escape.
                return None
