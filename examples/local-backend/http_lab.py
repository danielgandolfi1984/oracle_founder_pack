#!/usr/bin/env python3
"""Optional loopback lab with ephemeral, signed synthetic identities only."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from pathlib import Path
import shlex
import signal
from tempfile import TemporaryDirectory
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from http_transport import build_server
from jwt_auth import JWTVerifier
from store import Store


ISSUER = "https://local-lab.invalid"
AUDIENCE = "oci-founder-local-backend"


@dataclass(frozen=True)
class LabSession:
    directory: Path
    database_path: Path
    expires_at: int
    verifier: JWTVerifier = field(repr=False)
    tokens: dict[str, str] = field(repr=False)


@contextmanager
def lab_session(*, lifetime: int = 900):
    """Own only new temporary fixtures; never accept a user database/key path."""
    if type(lifetime) is not int or not 1 <= lifetime <= 900:
        raise ValueError("Lab lifetime must be between 1 and 900 seconds")
    with TemporaryDirectory(prefix="oci-founder-http-lab-") as directory:
        root = Path(directory)
        database = root / "synthetic.sqlite3"
        store = Store(database, create=True)
        try:
            store.seed_demo()
        finally:
            store.close()
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        verifier = JWTVerifier(private_key.public_key(), issuer=ISSUER, audience=AUDIENCE)
        now = int(time.time())
        tokens = {}
        for subject in ("alice", "amy", "bob"):
            token = jwt.encode(
                {"iss": ISSUER, "aud": AUDIENCE, "sub": subject,
                 "iat": now, "nbf": now, "exp": now + lifetime},
                private_key, algorithm="RS256", headers={"typ": "JWT"},
            )
            tokens[subject] = token
            descriptor = os.open(root / (subject + ".curl"), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as config:
                config.write('header = "Authorization: Bearer ' + token + '"\n')
                config.write('noproxy = "*"\nconnect-timeout = 2\nmax-time = 5\n')
        # No private key is serialized or retained by the verifier/session.
        del private_key
        yield LabSession(root, database, now + lifetime, verifier, tokens)


def main() -> int:
    parser = argparse.ArgumentParser(description="Temporary synthetic HTTP lab; loopback only, not production")
    parser.add_argument("--port", type=int, default=0, help="Local port; 0 selects an unused port")
    parser.add_argument("--seconds", type=int, default=900, help="Session lifetime, 1-900 seconds")
    args = parser.parse_args()
    if not 1 <= args.seconds <= 900 or not 0 <= args.port <= 65535:
        parser.error("port must be 0-65535 and seconds must be 1-900")

    def stop(_signum, _frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, stop)
    try:
        with lab_session(lifetime=args.seconds) as session:
            # Wall-clock corrections must not extend the listener lifetime.
            deadline = time.monotonic() + args.seconds
            with build_server(session.database_path, session.verifier, port=args.port) as server:
                server.timeout = 0.25
                print("Synthetic lab only; no real login, OCI access, TLS or production support.", flush=True)
                print(f"LAB_URL=http://127.0.0.1:{server.server_port}", flush=True)
                print("LAB_SESSION_DIR=" + shlex.quote(str(session.directory)), flush=True)
                print("Use the private .curl files from HTTP-LAB.md; do not share them.", flush=True)
                print(f"Stops after {args.seconds} seconds or Ctrl+C; all session data is temporary.", flush=True)
                try:
                    while time.monotonic() < deadline:
                        server.handle_request()
                except KeyboardInterrupt:
                    pass
        print("Stopped; this session's synthetic database and curl files were removed.", flush=True)
        return 0
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    raise SystemExit(main())
