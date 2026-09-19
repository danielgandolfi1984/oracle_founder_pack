"""In-process teaching API. No HTTP listener or production authentication.

Only an explicitly supplied, trusted verifier may produce a subject. Its
production implementation must validate the identity provider's token, not
decode claims without verifying them. The default denies every business call.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Callable

from store import DomainError, Store


SEGMENT = r"[A-Za-z0-9_-]{1,128}"
PROJECTS = re.compile(rf"/workspaces/({SEGMENT})/projects")
ITEMS = re.compile(rf"/workspaces/({SEGMENT})/projects/({SEGMENT})/items")
ITEM = re.compile(rf"/workspaces/({SEGMENT})/projects/({SEGMENT})/items/({SEGMENT})")
MEMBER = re.compile(rf"/workspaces/({SEGMENT})/members/({SEGMENT})")


class API:
    """Framework-neutral contract; calls are serialized by the local demo.

    HTTP parsing, TLS, body limits, rate limits and trusted proxy handling are
    intentionally not implemented. Do not expose this class through a server
    without a separate transport and authentication review.
    """

    def __init__(self, store: Store, verify_token: Callable[[str], str | None] | None = None):
        self.store = store
        self.verify_token = verify_token

    @staticmethod
    def _headers(headers: Any) -> dict[str, str]:
        if headers is None:
            return {}
        if not isinstance(headers, dict) or len(headers) > 32:
            raise DomainError(400, "invalid_input")
        normalized: dict[str, str] = {}
        for key, value in headers.items():
            if (not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,64}", key)
                    or not isinstance(value, str) or len(value) > 8192
                    or any(ord(char) < 32 or ord(char) == 127 for char in value)
                    or key.lower() in normalized):
                raise DomainError(400, "invalid_input")
            normalized[key.lower()] = value
        return normalized

    def _subject(self, headers: dict[str, str]) -> str:
        auth = headers.get("authorization", "")
        match = re.fullmatch(r"(?i:Bearer) ([\x21-\x7e]{1,4096})", auth)
        if match is None or self.verify_token is None:
            raise DomainError(401, "unauthorized")
        try:
            subject = self.verify_token(match.group(1))
        except Exception:
            # Never return a verifier error, token or decoded claim to callers.
            raise DomainError(401, "unauthorized") from None
        if not isinstance(subject, str) or re.fullmatch(SEGMENT, subject) is None:
            raise DomainError(401, "unauthorized")
        return subject

    @staticmethod
    def _body(body: Any, field: str) -> str:
        if not isinstance(body, dict) or set(body) != {field} or not isinstance(body[field], str):
            raise DomainError(400, "invalid_input")
        return body[field]

    def handle(self, method: str, path: str, headers: Any = None, body: Any = None) -> tuple[int, Any]:
        """Return status and JSON-compatible data without logging request data."""
        try:
            if (not isinstance(method, str) or method not in {"GET", "POST", "PATCH", "DELETE"}
                    or not isinstance(path, str) or len(path) > 1024):
                raise DomainError(400, "invalid_input")
            normalized = self._headers(headers)
            if method == "GET" and path == "/healthz":
                return 200, {"status": "ok", "scope": "in-process-local-lab"}
            if method == "GET" and path == "/readyz":
                return (200, {"status": "ready"}) if self.store.ready() else (503, {"error": "unavailable"})
            subject = self._subject(normalized)
            if method in {"GET", "DELETE"} and body is not None:
                raise DomainError(400, "invalid_input")
            if method == "GET" and path == "/workspaces":
                return 200, {"workspaces": self.store.list_workspaces(subject)}
            match = PROJECTS.fullmatch(path)
            if match:
                workspace = match.group(1)
                if method == "GET":
                    return 200, {"projects": self.store.list_projects(subject, workspace)}
                if method == "POST":
                    return 201, self.store.create_project(
                        subject, workspace, self._body(body, "name"), normalized.get("idempotency-key", ""))
            match = ITEMS.fullmatch(path)
            if match:
                workspace, project = match.groups()
                if method == "GET":
                    return 200, {"items": self.store.list_items(subject, workspace, project)}
                if method == "POST":
                    return 201, self.store.create_item(
                        subject, workspace, project, self._body(body, "title"), normalized.get("idempotency-key", ""))
            match = ITEM.fullmatch(path)
            if match and method == "PATCH":
                return 200, self.store.update_item(subject, *match.groups(), self._body(body, "status"))
            match = MEMBER.fullmatch(path)
            if match:
                if method == "PATCH":
                    return 200, self.store.set_member_role(subject, *match.groups(), self._body(body, "role"))
                if method == "DELETE":
                    return 200, self.store.remove_member(subject, *match.groups())
            return 404, {"error": "not_found"}
        except DomainError as exc:
            return exc.status, {"error": exc.code}
        except sqlite3.Error:
            # Database paths, SQL, values and operational details stay private.
            return 503, {"error": "unavailable"}
