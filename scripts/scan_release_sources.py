#!/usr/bin/env python3
"""Run high-confidence secret/privacy checks over release and repository sources."""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import build_release


@dataclass(frozen=True)
class Finding:
    package_kind: str
    path: str
    detector: str
    line: int


DETECTORS = {
    "pem-private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key-id": re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "github-token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "github-fine-grained-token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{60,255}\b"),
    "openai-style-secret": re.compile(rb"\bsk-[A-Za-z0-9_-]{32,}\b"),
    "slack-token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    # OCIDs are account/resource metadata, not credentials. Require a long
    # unique component so documented replace_me/fake/foreign fixtures stay safe.
    "oci-resource-identifier": re.compile(
        rb"\bocid1\.[a-z][a-z0-9-]{0,63}\.oc[0-9]{1,3}\."
        rb"[a-z0-9-]{0,63}\.(?:[a-z0-9-]{0,63}\.)?[a-z0-9]{32,128}\b"
    ),
    # Only named corporate domains: public Oracle docs and lookalike domains
    # must not be confused with internal Confluence/SharePoint locations.
    "internal-oracle-url": re.compile(
        rb"\bhttps?://(?:[^/?#\s\"<>@]+@)?(?:"
        rb"(?:[a-z0-9-]+\.)*oraclecorp\.com|"
        rb"oracle(?:-my)?\.sharepoint\.com|"
        rb"confluence\.(?:[a-z0-9-]+\.)*oracle\.com"
        rb")\.?(?=[:/?#\s\"'<>\\)]|$)",
        re.IGNORECASE,
    ),
}

# A dotted string alone is not evidence of a JWT. Parse bounded base64url JSON
# objects and require a recognized signing algorithm plus signature-shaped
# bytes. This detects token material, not signature validity or account access;
# it performs no cryptography, provider lookup or network call.
JWT_CANDIDATE = re.compile(
    rb"(?<![A-Za-z0-9_-])([A-Za-z0-9_-]{8,2048})\."
    rb"([A-Za-z0-9_-]{8,16384})\.([A-Za-z0-9_-]{22,4096})(?![A-Za-z0-9_-])"
)
JWT_SIGNING_ALGORITHMS = frozenset(
    {"HS256", "HS384", "HS512", "RS256", "RS384", "RS512",
     "ES256", "ES384", "ES512", "PS256", "PS384", "PS512", "EdDSA"}
)

# These directories contain local metadata or generated outputs and are not
# intended for version control. Keep this list explicit: adding an exclusion is
# a reviewable change to the repository scan boundary.
REPOSITORY_GENERATED_DIRECTORIES = frozenset(
    {
        ".git",
        ".pptx-build",
        ".terraform",
        "__pycache__",
        "dist",
        "node_modules",
    }
)

# The package builder contains two literal PEM markers as detector canaries.
# Exceptions are bound to path, detector, and line so moving or adding a marker
# fails closed until the source location is reviewed again.
REVIEWED_LITERAL_CANARIES = frozenset(
    {
        ("scripts/build_release.py", "pem-private-key", 27),
        ("scripts/build_release.py", "pem-private-key", 28),
    }
)


def line_number(payload: bytes, offset: int) -> int:
    return payload.count(b"\n", 0, offset) + 1


def is_jwt_material(segments: tuple[bytes, bytes, bytes]) -> bool:
    try:
        decoded = [
            base64.b64decode(segment + b"=" * (-len(segment) % 4), altchars=b"-_", validate=True)
            for segment in segments
        ]
        header, claims = (json.loads(part.decode("utf-8")) for part in decoded[:2])
        return (isinstance(header, dict) and isinstance(header.get("alg"), str)
                and header["alg"] in JWT_SIGNING_ALGORITHMS
                and isinstance(claims, dict) and bool(claims) and len(decoded[2]) >= 16)
    except (ValueError, UnicodeError, binascii.Error, RecursionError):
        return False


def scan_payload(package_kind: str, path: str, payload: bytes) -> list[Finding]:
    findings: list[Finding] = []
    for name, pattern in DETECTORS.items():
        for match in pattern.finditer(payload):
            findings.append(
                Finding(
                    package_kind=package_kind,
                    path=path,
                    detector=name,
                    line=line_number(payload, match.start()),
                )
            )
    for match in JWT_CANDIDATE.finditer(payload):
        if is_jwt_material(match.groups()):
            findings.append(Finding(package_kind, path, "jwt-token", line_number(payload, match.start())))
    return findings


def scan_release_allowlists() -> list[Finding]:
    findings: list[Finding] = []
    for spec in build_release.package_specs(build_release.load_version()):
        for entry in build_release.collect_entries(spec):
            findings.extend(
                scan_payload(spec.kind, entry.archive_path, entry.payload)
            )
    return findings


def is_generated_repository_path(path: Path, root: Path) -> bool:
    return bool(
        REPOSITORY_GENERATED_DIRECTORIES.intersection(path.relative_to(root).parts)
    )


def scan_repository_tree(root: Path = build_release.ROOT) -> list[Finding]:
    """Scan every regular repository file outside explicit generated dirs."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError(
            f"repository root is missing, not a directory, or a symlink: {root}"
        )

    findings: list[Finding] = []
    for current_raw, directory_names, file_names in os.walk(
        root, topdown=True, followlinks=False
    ):
        current = Path(current_raw)
        retained_directories: list[str] = []
        for name in sorted(directory_names):
            path = current / name
            if is_generated_repository_path(path, root):
                continue
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise ValueError(
                    f"repository source must not be a symlink: {relative}"
                )
            retained_directories.append(name)
        directory_names[:] = retained_directories

        for name in sorted(file_names):
            path = current / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise ValueError(
                    f"repository source must not be a symlink: {relative}"
                )
            if not path.is_file():
                continue
            for finding in scan_payload(
                "repository-tree", relative, path.read_bytes()
            ):
                key = (finding.path, finding.detector, finding.line)
                if key not in REVIEWED_LITERAL_CANARIES:
                    findings.append(finding)
    return findings


def scan_default_scopes() -> list[Finding]:
    return [*scan_release_allowlists(), *scan_repository_tree()]


def render(findings: Iterable[Finding]) -> str:
    return "\n".join(
        f"{item.package_kind}:{item.path}:{item.line}: {item.detector}"
        for item in findings
    )


def main() -> int:
    try:
        findings = scan_default_scopes()
    except (OSError, ValueError) as exc:
        print(
            f"release and repository-source scan failed closed: {exc}",
            file=sys.stderr,
        )
        return 2
    if findings:
        print(render(findings), file=sys.stderr)
        print(
            "release and repository-source scan failed: "
            f"{len(findings)} high-confidence finding(s)",
            file=sys.stderr,
        )
        return 1
    print(
        "Release and repository-source scan passed: "
        "0 high-confidence secret findings"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
