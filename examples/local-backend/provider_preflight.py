#!/usr/bin/env python3
"""Read-only offline contract check. Never read a token or contact a provider."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat

from provider_auth import ProviderVerifier


MAX_FILE_BYTES = 65536


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Invalid JSON object")
        result[key] = value
    return result


def _constant(_value):
    raise ValueError("Invalid JSON constant")


def load_object(path: Path, *, private: bool = False) -> dict:
    """Read one bounded regular file; never follow a final symlink or a FIFO."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError("Invalid input file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as source:
        metadata = os.fstat(source.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_FILE_BYTES:
            raise ValueError("Invalid input file")
        if private and os.name == "posix" and stat.S_IMODE(metadata.st_mode) & 0o077:
            raise ValueError("Bindings must be private to their owner")
        payload = source.read(MAX_FILE_BYTES + 1)
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError("Invalid input file")
    result = json.loads(payload.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
    if not isinstance(result, dict):
        raise ValueError("Invalid JSON object")
    return result


def inspect_configuration(config_path: Path, jwks_path: Path, bindings_path: Path) -> None:
    """Validate only server-side configuration and its trusted public snapshot."""
    verifier = ProviderVerifier(
        load_object(config_path), load_object(jwks_path), load_object(bindings_path, private=True)
    )
    if not verifier.ready():
        raise ValueError("Configuration is not ready")


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # Unknown arguments might contain a mistakenly pasted credential.
        # Do not echo them, even though this command accepts no tokens.
        self.exit(2, "Invalid arguments; use --help. Do not pass tokens or secrets.\n")


def main() -> int:
    parser = _Parser(description="Check local identity configuration only; no network or tokens")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--jwks", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    args = parser.parse_args()
    try:
        inspect_configuration(args.config, args.jwks, args.bindings)
        status, exit_code = "configuration_valid", 0
    except (OSError, ValueError, TypeError, RecursionError):
        status, exit_code = "invalid_configuration", 2
    print(json.dumps({"status": status, "provider_connection_tested": False,
                      "token_verified": False, "network_calls": 0}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
