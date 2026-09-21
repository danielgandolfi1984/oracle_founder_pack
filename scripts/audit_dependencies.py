#!/usr/bin/env python3
"""Audit active, public dependency pins without installing or executing them.

Only the allowlisted current manifests are read, never historical receipts,
virtual environments, user configuration or credentials. All declared pins,
including platform-marked pins and transitive lock entries, are checked. This
does not resolve missing dependencies or audit the OS, Terraform or Actions.
OSV protocol: https://google.github.io/osv.dev/post-v1-query/
Exit 0: complete/no known advisories; 1: advisories; 2: incomplete/invalid input.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = (
    "requirements-validation.txt",
    "examples/local-backend/requirements-http.txt",
    "tests/fixtures/docker-fastapi/requirements.txt",
)
NPM_DIRECTORY = "scripts/skills-cli-runtime"
OSV_URL = "https://api.osv.dev/v1/query"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_PAGES = 100
NAME = r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}"
VERSION = r"[0-9][A-Za-z0-9.!+_-]{0,127}"
PIN = re.compile(rf"({NAME})(?:\[[A-Za-z0-9._,-]+\])?==({VERSION})(?:\s*;\s*[^\x00-\x1f]+)?\Z")
HASH = re.compile(r"(?:^|\s)--hash=sha256:[a-fA-F0-9]{64}(?=\s|$)")
NPM_NAME = re.compile(r"(?:@[a-z0-9._-]+/)?[a-z0-9][a-z0-9._-]{0,127}\Z")
NPM_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?\Z")


class AuditError(Exception):
    """The message is a fixed diagnostic code, never raw input or HTTP output."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AuditError("duplicate_json_key")
        result[key] = value
    return result


def _constant(_value):
    raise AuditError("invalid_json_constant")


def _json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise AuditError("invalid_json") from None


def _read(root, relative):
    path = root / relative
    if any(part.is_symlink() for part in (path, *path.parents)) or not path.is_file():
        raise AuditError("manifest_not_regular")
    if path.stat().st_size > 1024 * 1024:
        raise AuditError("manifest_too_large")
    return path.read_text(encoding="utf-8")


def requirements_pins(text):
    pins, pending = [], ""
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        continued = line.endswith("\\")
        pending += " " + (line[:-1].rstrip() if continued else line)
        if continued:
            continue
        if not HASH.search(pending):
            raise AuditError("requirement_hash_missing")
        match = PIN.fullmatch(HASH.sub(" ", pending).strip())
        if match is None:
            raise AuditError("requirement_not_exact_supported_pin")
        name, version = match.groups()
        pins.append(("PyPI", re.sub(r"[-_.]+", "-", name).lower(), version))
        pending = ""
    if pending or not pins:
        raise AuditError("requirements_empty_or_unfinished")
    return pins


def npm_pins(lock, manifest):
    if (not isinstance(lock, dict) or lock.get("lockfileVersion") != 3
            or not isinstance(lock.get("packages"), dict) or not isinstance(manifest, dict)):
        raise AuditError("unsupported_npm_lock")
    packages, pins = lock["packages"], []
    if not isinstance(packages.get(""), dict):
        raise AuditError("npm_root_missing")
    for category in ("dependencies", "devDependencies", "optionalDependencies"):
        direct = manifest.get(category, {})
        if not isinstance(direct, dict) or direct != packages[""].get(category, {}):
            raise AuditError("npm_manifest_lock_mismatch")
        for name, version in direct.items():
            entry = packages.get("node_modules/" + name)
            if (not isinstance(version, str) or NPM_VERSION.fullmatch(version) is None
                    or not isinstance(entry, dict) or entry.get("version") != version):
                raise AuditError("npm_direct_pin_missing")
    for location, metadata in packages.items():
        if location == "":
            continue
        if (not isinstance(location, str) or not location.startswith("node_modules/")
                or not isinstance(metadata, dict) or metadata.get("link")):
            raise AuditError("unsupported_npm_entry")
        name = metadata.get("name", location.rsplit("node_modules/", 1)[-1])
        version = metadata.get("version")
        integrity = metadata.get("integrity", "")
        resolved = metadata.get("resolved", "")
        if (not isinstance(name, str) or NPM_NAME.fullmatch(name) is None
                or not isinstance(version, str) or NPM_VERSION.fullmatch(version) is None
                or not isinstance(integrity, str)
                or re.fullmatch(r"sha(?:256|512)-[A-Za-z0-9+/]+={0,2}", integrity) is None
                or not isinstance(resolved, str)
                or not resolved.startswith("https://registry.npmjs.org/" + name + "/-/")):
            raise AuditError("unsupported_npm_pin")
        pins.append(("npm", name, version))
    if not pins:
        raise AuditError("npm_lock_empty")
    return pins


def inventory(root=ROOT):
    sources = {}
    for relative in REQUIREMENTS:
        for pin in requirements_pins(_read(root, relative)):
            sources.setdefault(pin, set()).add(relative)
    relative = NPM_DIRECTORY + "/package-lock.json"
    for pin in npm_pins(_json(_read(root, relative)),
                        _json(_read(root, NPM_DIRECTORY + "/package.json"))):
        sources.setdefault(pin, set()).add(relative)
    return [{"ecosystem": key[0], "name": key[1], "version": key[2], "sources": sorted(value)}
            for key, value in sorted(sources.items())]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AuditError("osv_redirect_rejected")


def fetch(payload):
    request = urllib.request.Request(OSV_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "oci-founder-dependency-audit/1.0"}, method="POST")
    # No environment proxy, credentials, redirects or caller-selected endpoint.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=25) as response:
            if response.status != 200:
                raise AuditError("osv_http_error")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError):
        raise AuditError("osv_unavailable") from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise AuditError("osv_response_too_large")
    return _json(raw)


def query(dependency, requester=fetch):
    base = {"package": {key: dependency[key] for key in ("name", "ecosystem")},
            "version": dependency["version"]}
    payload, seen, advisory_ids = base.copy(), set(), set()
    for _ in range(MAX_PAGES):
        response = requester(payload.copy())
        if (not isinstance(response, dict) or set(response) - {"vulns", "next_page_token"}
                or not isinstance(response.get("vulns", []), list)):
            raise AuditError("osv_invalid_response")
        for vuln in response.get("vulns", []):
            if (not isinstance(vuln, dict) or not isinstance(vuln.get("id"), str)
                    or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}", vuln["id"]) is None):
                raise AuditError("osv_invalid_advisory")
            if "withdrawn" in vuln:
                try:
                    withdrawn = datetime.fromisoformat(vuln["withdrawn"].replace("Z", "+00:00"))
                    if withdrawn.tzinfo is None:
                        raise ValueError
                except (ValueError, AttributeError, TypeError):
                    raise AuditError("osv_invalid_withdrawal") from None
                continue
            advisory_ids.add(vuln["id"])
        if "next_page_token" not in response:
            return sorted(advisory_ids)
        token = response["next_page_token"]
        if not isinstance(token, str) or not token or len(token) > 8192 or token in seen:
            raise AuditError("osv_invalid_pagination")
        seen.add(token)
        payload = {**base, "page_token": token}
    raise AuditError("osv_page_limit_exceeded")


def audit(dependencies, requester=fetch):
    def check(dependency):
        try:
            return {**dependency, "advisory_ids": query(dependency, requester), "complete": True}
        except Exception as error:
            code = str(error) if isinstance(error, AuditError) else "audit_internal_error"
            return {**dependency, "complete": False, "error": code}

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(check, dependencies))
    complete = bool(results) and all(result["complete"] for result in results)
    count = sum(len(result.get("advisory_ids", [])) for result in results)
    code = 2 if not complete else (1 if count else 0)
    return code, {"status": ("incomplete" if not complete else
                              "known_vulnerabilities" if count else "no_known_vulnerabilities"),
                  "scope": "allowlisted-active-manifest-pins", "dependency_count": len(results),
                  "advisory_matches": count, "results": results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-only", action="store_true", help="validate and list pins without network")
    args = parser.parse_args(argv)
    try:
        dependencies = inventory()
    except (AuditError, OSError, UnicodeError) as error:
        print(json.dumps({"status": "incomplete", "error": str(error) if isinstance(error, AuditError)
                          else "manifest_unreadable"}))
        return 2
    if args.inventory_only:
        print(json.dumps({"status": "inventory_only", "vulnerabilities_checked": False,
                          "dependency_count": len(dependencies), "dependencies": dependencies}, indent=2))
        return 0
    code, report = audit(dependencies)
    report["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
