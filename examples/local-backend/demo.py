#!/usr/bin/env python3
"""Run a synthetic, in-process founder journey without credentials or network."""

from __future__ import annotations

from contextlib import ExitStack, closing
from pathlib import Path
from tempfile import TemporaryDirectory

from api import API
from store import Store


def synthetic_verifier(token: str) -> str | None:
    """TEST FIXTURE ONLY. These strings are not credentials or real tokens."""
    return {"demo-alice": "alice", "demo-amy": "amy", "demo-bob": "bob"}.get(token)


def request(api: API, actor: str, method: str, path: str, expected: int,
            label: str, body: dict | None = None, key: str | None = None) -> dict:
    headers = {"Authorization": "Bearer demo-" + actor}
    if key is not None:
        headers["Idempotency-Key"] = key
    status, payload = api.handle(method, path, headers, body)
    if status != expected:
        raise RuntimeError(f"{label}: expected {expected}, received {status}")
    print(f"PASS {label} ({status})")
    return payload


def require(condition: bool, label: str) -> None:
    if not condition:
        raise RuntimeError(f"{label}: contract failed")
    print(f"PASS {label}")


def main() -> int:
    print("Synthetic in-process lab: no HTTP listener, real login or OCI deployment.")
    # All writes are inside a newly created private temporary directory. No
    # caller-supplied database or cleanup path can target an existing project.
    with TemporaryDirectory(prefix="oci-founder-local-lab-") as directory, ExitStack() as stack:
        path = Path(directory) / "synthetic.sqlite3"
        store = stack.enter_context(closing(Store(path, create=True)))
        store.seed_demo()
        request(API(store), "alice", "GET", "/workspaces", 401, "default authentication denies access")
        api = API(store, synthetic_verifier)
        request(api, "alice", "GET", "/readyz", 200, "database readiness")
        projects = "/workspaces/w-a/projects"
        project = request(api, "alice", "POST", projects, 201, "create project",
                          {"name": "Synthetic founder project"}, "create-project")
        replay = request(api, "alice", "POST", projects, 201, "retry project creation",
                         {"name": "Synthetic founder project"}, "create-project")
        require(project == replay, "retry returns the same creation result")
        request(api, "bob", "GET", projects, 403, "another workspace cannot list projects")
        items = projects + "/" + project["id"] + "/items"
        item = request(api, "amy", "POST", items, 201, "member creates a work item",
                       {"title": "Verify the local journey"}, "create-item")
        request(api, "amy", "PATCH", items + "/" + item["id"], 200,
                "member completes work item", {"status": "done"})
        request(api, "bob", "PATCH", items + "/" + item["id"], 403,
                "cross-workspace update denied", {"status": "todo"})
        request(api, "amy", "PATCH", "/workspaces/w-a/members/alice", 403,
                "member cannot change roles", {"role": "member"})
        request(api, "alice", "PATCH", "/workspaces/w-a/members/amy", 200,
                "owner promotes colleague", {"role": "owner"})
        request(api, "amy", "PATCH", "/workspaces/w-a/members/alice", 200,
                "second owner downgrades previous owner", {"role": "member"})
        request(api, "alice", "DELETE", "/workspaces/w-a/members/amy", 403,
                "downgrade takes effect with the same synthetic token")
        request(api, "amy", "DELETE", "/workspaces/w-a/members/alice", 200,
                "owner revokes membership")
        request(api, "alice", "POST", projects, 403, "revoked user cannot replay creation",
                {"name": "Synthetic founder project"}, "create-project")
        request(api, "amy", "DELETE", "/workspaces/w-a/members/amy", 409,
                "last owner is protected")
        store.close()
        reopened = stack.enter_context(closing(Store(path)))
        result = request(API(reopened, synthetic_verifier), "amy", "GET", items, 200,
                         "reopen persistent database")
        require(len(result["items"]) == 1 and result["items"][0]["status"] == "done",
                "saved work survives reopening")
        backup_path = Path(directory) / "recovery.sqlite3"
        reopened.backup_to(backup_path)
        recovered = stack.enter_context(closing(Store(backup_path)))
        recovery_api = API(recovered, synthetic_verifier)
        recovery = request(recovery_api, "amy", "GET", items, 200, "read independent backup copy")
        require(recovery == result, "local recovery preserves the saved work")
        request(recovery_api, "alice", "GET", projects, 403, "recovery preserves revoked membership")
    print("Local lab complete; synthetic temporary data removed. No network or OCI calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
