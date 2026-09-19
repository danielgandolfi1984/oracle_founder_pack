#!/usr/bin/env python3
"""Synthetic offline provider-contract exercise; no login, listener or network."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from api import API
from provider_auth import ProviderVerifier
from provider_preflight import inspect_configuration
from store import Store


def public_jwk(private_key, kid):
    """Only public material enters the trusted snapshot, never the private key."""
    return {**jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True),
            "kid": kid, "alg": "RS256", "use": "sig"}


def main() -> int:
    print("Synthetic offline provider contract; no live provider, login or OCI connection.")
    first_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    next_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = int(time.time())
    config = {
        "issuer": "https://issuer.example.invalid",
        "audience": "https://founder-api.example.invalid",
        "allowed_client_ids": ["synthetic-client"],
        "required_scope": "founder:api",
        "max_token_lifetime_seconds": 900,
        "jwks_fetched_at": now - 1,
        "jwks_expires_at": now + 300,
    }
    old_jwk = public_jwk(first_key, "first-key")
    next_jwk = public_jwk(next_key, "next-key")
    bindings = {"example|alice": "alice", "example|amy": "amy", "example|bob": "bob"}
    verifier = ProviderVerifier(config, {"keys": [old_jwk]}, bindings)

    def issue(subject, *, new_key=False, typ="at+jwt", overrides=None):
        claims = {"iss": config["issuer"], "aud": config["audience"], "sub": subject,
                  "iat": now, "exp": now + 120, "client_id": "synthetic-client",
                  "jti": str(uuid4()), "scope": "founder:api"}
        claims.update(overrides or {})
        return jwt.encode(claims, next_key if new_key else first_key, algorithm="RS256",
                          headers={"typ": typ, "kid": "next-key" if new_key else "first-key"})

    with TemporaryDirectory(prefix="oci-founder-provider-demo-") as directory:
        root = Path(directory)
        # The preflight input files contain only this run's synthetic metadata.
        for name, value in (("config.json", config), ("jwks.json", {"keys": [old_jwk]}),
                            ("bindings.json", bindings)):
            descriptor = os.open(root / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(value, output)
        inspect_configuration(root / "config.json", root / "jwks.json", root / "bindings.json")
        print("PASS read-only configuration preflight (not a provider connection test)")
        store = Store(root / "synthetic.sqlite3", create=True)
        try:
            store.seed_demo()
            api = API(store, verifier)

            def request(token, path, expected, label, method="GET", body=None, key=None):
                headers = {"Authorization": "Bearer " + token}
                if key is not None:
                    headers["Idempotency-Key"] = key
                status, result = api.handle(method, path, headers, body)
                if status != expected:
                    raise RuntimeError(f"{label}: expected {expected}, received {status}")
                print(f"PASS {label} ({status})")
                return result

            alice = issue("example|alice")
            amy = issue("example|amy")
            request(alice, "/workspaces", 200, "explicit issuer-subject binding")
            request(issue("alice"), "/workspaces", 401, "same-looking local name is not an identity binding")
            request(issue("unknown", overrides={"roles": ["owner"]}), "/workspaces", 401,
                    "unmapped identity cannot grant itself owner permissions")
            request(issue("example|alice", typ="JWT"), "/workspaces", 401,
                    "generic JWT type rejected by strict access-token profile")
            request(issue("example|alice", overrides={"client_id": "other-client"}), "/workspaces", 401,
                    "unapproved client denied")
            request(issue("example|alice", overrides={"scope": "founder:read"}), "/workspaces", 401,
                    "missing application-admission scope denied")
            request(alice, "/workspaces/w-a/projects", 201, "authorized business request",
                    "POST", {"name": "Synthetic provider project"}, "provider-create")
            request(issue("example|bob"), "/workspaces/w-a/projects", 403, "mapped foreign member denied")
            request(alice, "/workspaces/w-a/members/amy", 200, "owner revokes local membership", "DELETE")
            request(amy, "/workspaces/w-a/projects", 403, "same access token respects current membership")
            rotated_alice = issue("example|alice", new_key=True)
            request(rotated_alice, "/workspaces", 401, "unknown signing key denied without fetching")
            verifier.reload(config, {"keys": [old_jwk, next_jwk]}, bindings)
            request(rotated_alice, "/workspaces", 200, "new key accepted during reviewed overlap")
            request(alice, "/workspaces", 200, "previous key accepted during overlap")
            verifier.reload(config, {"keys": [next_jwk]}, bindings)
            request(alice, "/workspaces", 401, "removed key no longer accepted by reloaded verifier")
            try:
                verifier.reload(config, {"keys": []}, bindings)
            except ValueError:
                pass
            else:
                raise RuntimeError("Invalid snapshot was accepted")
            request(rotated_alice, "/workspaces", 401, "invalid reload disables stale fallback")
            verifier.reload(config, {"keys": [next_jwk]}, bindings)
            request(rotated_alice, "/workspaces", 200, "valid replacement restores verification")
        finally:
            store.close()
    print("PASS synthetic files removed; no external issuer, network, real token or OCI calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
