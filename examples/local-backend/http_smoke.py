#!/usr/bin/env python3
"""Exercise the actual loopback transport using ephemeral signed test tokens."""

from __future__ import annotations

from http.client import HTTPConnection
import json
import threading

from http_lab import lab_session
from http_transport import build_server


def main() -> int:
    with lab_session() as session:
        with build_server(session.database_path, session.verifier) as server:
            worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
            worker.start()

            def request(method, path, expected, label, *, actor=None, body=None, key=None, token=None):
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                headers = {}
                if actor is not None:
                    headers["Authorization"] = "Bearer " + session.tokens[actor]
                if token is not None:
                    headers["Authorization"] = "Bearer " + token
                if key is not None:
                    headers["Idempotency-Key"] = key
                if body is not None:
                    headers["Content-Type"] = "application/json"
                encoded = None if body is None else json.dumps(body).encode("utf-8")
                try:
                    connection.request(method, path, body=encoded, headers=headers)
                    response = connection.getresponse()
                    data = response.read(16385)
                    if response.status != expected or len(data) > 16384:
                        raise RuntimeError(f"{label}: HTTP contract failed (status {response.status})")
                    payload = json.loads(data)
                finally:
                    connection.close()
                print(f"PASS {label} ({expected})")
                return payload

            try:
                request("GET", "/healthz", 200, "loopback health")
                request("GET", "/workspaces", 401, "missing token denied")
                token_parts = session.tokens["alice"].split(".")
                signature = token_parts[2]
                token_parts[2] = ("A" if signature[0] != "A" else "B") + signature[1:]
                request("GET", "/workspaces", 401, "tampered signature denied", token=".".join(token_parts))
                request("GET", "/workspaces", 200, "signed identity accepted", actor="alice")
                projects = "/workspaces/w-a/projects"
                project = request("POST", projects, 201, "project creation", actor="alice",
                                  body={"name": "Synthetic HTTP project"}, key="http-create")
                replay = request("POST", projects, 201, "creation retry", actor="alice",
                                 body={"name": "Synthetic HTTP project"}, key="http-create")
                if project != replay:
                    raise RuntimeError("HTTP retry produced a different resource")
                request("GET", projects, 403, "foreign workspace denied", actor="bob")
                items = projects + "/" + project["id"] + "/items"
                item = request("POST", items, 201, "member creates item", actor="amy",
                               body={"title": "Try signed HTTP requests"}, key="http-item")
                request("PATCH", items + "/" + item["id"], 200, "member updates item",
                        actor="amy", body={"status": "done"})
                request("DELETE", "/workspaces/w-a/members/alice", 403, "member privilege escalation denied", actor="amy")
                request("DELETE", "/workspaces/w-a/members/amy", 200, "owner revokes member", actor="alice")
                request("GET", projects, 403, "same signed token loses revoked access", actor="amy")
            finally:
                server.shutdown()
                worker.join(timeout=5)
                if worker.is_alive():
                    raise RuntimeError("Local server did not stop")
    print("PASS loopback session stopped and temporary synthetic data removed; no OCI calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
