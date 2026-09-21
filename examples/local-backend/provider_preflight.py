#!/usr/bin/env python3
"""Read-only offline contract check. Never read a token or contact a provider."""

from __future__ import annotations

import argparse
import errno
import json
import os
from pathlib import Path
import stat

from provider_auth import ProviderConfigurationError, ProviderVerifier


MAX_FILE_BYTES = 65536
_INPUT_CODES = frozenset({"input_file_unavailable", "input_file_type",
                          "input_file_too_large", "input_permissions", "invalid_json"})
_SNAPSHOT_INPUTS = {
    "invalid_config_fields": "config", "invalid_issuer": "config",
    "invalid_audience": "config", "invalid_client_allowlist": "config",
    "invalid_required_scope": "config", "invalid_time_policy": "config",
    "invalid_public_jwks": "jwks", "invalid_subject_bindings": "bindings",
    "invalid_clock": "snapshot", "invalid_snapshot": "snapshot",
}


class PreflightError(ValueError):
    """Allowlisted diagnostic labels only; never include input values or paths."""

    def __init__(self, input_name: str, code: str):
        self.input = (input_name if type(input_name) is str
                      and input_name in {"config", "jwks", "bindings", "snapshot"} else "snapshot")
        self.code = (code if type(code) is str
                     and (code in _INPUT_CODES or code in _SNAPSHOT_INPUTS) else "invalid_snapshot")
        super().__init__("Invalid provider configuration")


class _InputError(ValueError):
    def __init__(self, code: str):
        self.code = code if type(code) is str and code in _INPUT_CODES else "input_file_unavailable"
        super().__init__("Invalid input file")


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
        raise _InputError("input_file_type")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as source:
            metadata = os.fstat(source.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise _InputError("input_file_type")
            if metadata.st_size > MAX_FILE_BYTES:
                raise _InputError("input_file_too_large")
            if private and os.name == "posix" and stat.S_IMODE(metadata.st_mode) & 0o077:
                raise _InputError("input_permissions")
            payload = source.read(MAX_FILE_BYTES + 1)
    except OSError as error:
        code = "input_file_type" if error.errno in {errno.ELOOP, errno.EISDIR} else "input_file_unavailable"
        raise _InputError(code) from None
    if len(payload) > MAX_FILE_BYTES:
        raise _InputError("input_file_too_large")
    try:
        result = json.loads(payload.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
    except (ValueError, RecursionError):
        raise _InputError("invalid_json") from None
    if not isinstance(result, dict):
        raise _InputError("invalid_json")
    return result


def inspect_configuration(config_path: Path, jwks_path: Path, bindings_path: Path) -> None:
    """Validate only server-side configuration and its trusted public snapshot."""
    inputs = {}
    for name, path in (("config", config_path), ("jwks", jwks_path), ("bindings", bindings_path)):
        try:
            inputs[name] = load_object(path, private=name == "bindings")
        except _InputError as error:
            raise PreflightError(name, error.code) from None
        except (OSError, ValueError, TypeError):
            raise PreflightError(name, "input_file_unavailable") from None
    try:
        verifier = ProviderVerifier(inputs["config"], inputs["jwks"], inputs["bindings"])
    except ProviderConfigurationError as error:
        raise PreflightError(_SNAPSHOT_INPUTS.get(error.code, "snapshot"), error.code) from None
    if not verifier.ready():
        raise PreflightError("snapshot", "invalid_snapshot")


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
    parser.add_argument("--diagnostics", action="store_true",
                        help="Add safe input labels and error codes, never configuration values")
    args = parser.parse_args()
    diagnostics = []
    try:
        inspect_configuration(args.config, args.jwks, args.bindings)
        status, exit_code = "configuration_valid", 0
    except PreflightError as error:
        status, exit_code = "invalid_configuration", 2
        diagnostics = [{"input": error.input, "code": error.code}]
    except (OSError, ValueError, TypeError, RecursionError):
        status, exit_code = "invalid_configuration", 2
        diagnostics = [{"input": "snapshot", "code": "invalid_snapshot"}]
    result = {"status": status, "provider_connection_tested": False,
              "token_verified": False, "network_calls": 0}
    if args.diagnostics:
        result["diagnostics"] = diagnostics
    print(json.dumps(result, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
