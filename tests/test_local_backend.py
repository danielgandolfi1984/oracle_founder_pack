"""Adversarial, in-process tests for the deliberately local-only backend lab.

All identities and bearer strings below are synthetic fixtures. The injected
verifier is not an authentication implementation and no network is opened.
"""

from __future__ import annotations

import json
import os
import sqlite3
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "local-backend"
sys.path.insert(0, str(EXAMPLE))
try:
    from api import API
    from store import DomainError, Store
finally:
    sys.path.pop(0)


SESSIONS = {
    "alice-session": "alice",
    "amy-session": "amy",
    "bob-session": "bob",
}


class LocalBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="oci-founder-lab-test-")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "lab.sqlite3"
        self.store = Store(self.path, create=True)
        self.addCleanup(self.store.close)
        self.store.seed_demo()
        self.api = API(self.store, verify_token=SESSIONS.get)

    def request(
        self,
        method: str,
        path: str,
        *,
        subject: str = "alice",
        body: object = None,
        key: str | None = None,
        headers: dict | None = None,
    ) -> tuple[int, dict]:
        request_headers = {"Authorization": f"Bearer {subject}-session"}
        if key is not None:
            request_headers["Idempotency-Key"] = key
        if headers is not None:
            request_headers.update(headers)
        return self.api.handle(method, path, request_headers, body)

    def project(
        self, *, workspace: str = "w-a", subject: str = "alice", key: str = "project-1"
    ) -> dict:
        status, payload = self.request(
            "POST",
            f"/workspaces/{workspace}/projects",
            subject=subject,
            body={"name": "Customer project"},
            key=key,
        )
        self.assertEqual(201, status, payload)
        self.assertIsInstance(payload.get("id"), str)
        return payload

    def item(self, project: dict, *, key: str = "item-1") -> dict:
        status, payload = self.request(
            "POST",
            f"/workspaces/w-a/projects/{project['id']}/items",
            body={"title": "Ship one safe increment"},
            key=key,
        )
        self.assertEqual(201, status, payload)
        self.assertIsInstance(payload.get("id"), str)
        return payload

    def test_health_and_readiness_are_public(self) -> None:
        locked_api = API(self.store)
        self.assertEqual(200, locked_api.handle("GET", "/healthz")[0])
        self.assertEqual(200, locked_api.handle("GET", "/readyz")[0])

    def test_default_verifier_denies_business_routes(self) -> None:
        status, _ = API(self.store).handle(
            "GET", "/workspaces", {"Authorization": "Bearer alice-session"}
        )
        self.assertEqual(401, status)

    def test_missing_invalid_and_wrong_scheme_credentials_fail_closed(self) -> None:
        for headers in (
            None,
            {},
            {"Authorization": ""},
            {"Authorization": "Bearer"},
            {"Authorization": "Bearer unknown-session"},
            {"Authorization": "Basic alice-session"},
        ):
            with self.subTest(headers=headers):
                self.assertEqual(401, self.api.handle("GET", "/workspaces", headers)[0])

    def test_verifier_receives_only_raw_bearer_value(self) -> None:
        received = []

        def verify(value: str) -> str | None:
            received.append(value)
            return SESSIONS.get(value)

        api = API(self.store, verify_token=verify)
        status, payload = api.handle(
            "GET", "/workspaces", {"Authorization": "Bearer alice-session"}
        )
        self.assertEqual(200, status, payload)
        self.assertEqual(["alice-session"], received)

    def test_verifier_exceptions_are_sanitized(self) -> None:
        sentinel = "PRIVATE_VERIFIER_DIAGNOSTIC_DO_NOT_RETURN"

        def broken_verifier(_value: str) -> str:
            raise RuntimeError(sentinel)

        status, payload = API(self.store, verify_token=broken_verifier).handle(
            "GET", "/workspaces", {"Authorization": "Bearer alice-session"}
        )
        self.assertEqual(401, status)
        self.assertNotIn(sentinel, json.dumps(payload))
        self.assertNotIn("Traceback", json.dumps(payload))

    def test_invalid_verifier_results_cannot_become_subjects(self) -> None:
        for result in (None, False, 7, {}, [], "", "alice bob", "../alice", "a" * 129):
            with self.subTest(result=result):
                api = API(self.store, verify_token=lambda _token: result)
                self.assertEqual(
                    401,
                    api.handle("GET", "/workspaces", {"Authorization": "Bearer fixture"})[0],
                )

    def test_malformed_duplicate_and_control_character_headers_are_rejected(self) -> None:
        for headers in (
            [], "Authorization: Bearer alice-session", {1: "value"},
            {"Authorization": None}, {"Authorization": "Bearer alice-session\n"},
            {"Authorization": "Bearer alice-session", "authorization": "Bearer bob-session"},
            {"Authorization": "Bearer alice-session", "Idempotency-Key": 3},
            {"Bad Header Name": "value"}, {"X-Large": "x" * 8193},
        ):
            with self.subTest(headers=headers):
                self.assertEqual(400, self.api.handle("GET", "/workspaces", headers)[0])

    def test_header_names_and_bearer_scheme_are_case_insensitive(self) -> None:
        status, payload = self.api.handle(
            "GET", "/workspaces", {"aUtHoRiZaTiOn": "bEaReR alice-session"}
        )
        self.assertEqual(200, status, payload)
        self.assertEqual(["w-a"], [row["id"] for row in payload["workspaces"]])

    def test_caller_cannot_select_identity_with_headers_or_body(self) -> None:
        self.assertEqual(
            401,
            self.api.handle("GET", "/workspaces", {"X-User-ID": "alice"})[0],
        )
        self.assertEqual(
            403,
            self.request(
                "GET", "/workspaces/w-a/projects", subject="bob",
                headers={"X-User-ID": "alice", "X-Subject": "alice"},
            )[0],
        )
        self.assertEqual(
            400,
            self.request(
                "POST", "/workspaces/w-a/projects",
                body={"name": "Injected identity", "subject": "bob"}, key="spoof-1",
            )[0],
        )

    def test_workspace_list_contains_only_current_memberships(self) -> None:
        for subject, expected in (("alice", "w-a"), ("amy", "w-a"), ("bob", "w-b")):
            with self.subTest(subject=subject):
                status, payload = self.request("GET", "/workspaces", subject=subject)
                self.assertEqual(200, status, payload)
                self.assertEqual([expected], [row["id"] for row in payload["workspaces"]])

    def test_lifecycle_persists_after_close_and_reopen(self) -> None:
        project = self.project()
        item = self.item(project)
        path = f"/workspaces/w-a/projects/{project['id']}/items"
        status, updated = self.request(
            "PATCH", f"{path}/{item['id']}", body={"status": "done"}
        )
        self.assertEqual(200, status, updated)
        self.assertEqual("done", updated["status"])
        self.store.close()
        reopened = Store(self.path)
        self.addCleanup(reopened.close)
        status, payload = API(reopened, verify_token=SESSIONS.get).handle(
            "GET", path, {"Authorization": "Bearer alice-session"}
        )
        self.assertEqual(200, status, payload)
        self.assertEqual([item["id"]], [row["id"] for row in payload["items"]])
        self.assertEqual("done", payload["items"][0]["status"])

    def test_backup_can_be_opened_as_an_independent_restore(self) -> None:
        project = self.project()
        self.item(project)
        backup = Path(self.temporary.name) / "backup.sqlite3"
        self.store.backup_to(backup)
        restored = Store(backup)
        self.addCleanup(restored.close)
        self.assertTrue(restored.ready())
        self.assertEqual(
            self.store.list_projects("alice", "w-a"),
            restored.list_projects("alice", "w-a"),
        )
        self.assertEqual(
            self.store.list_items("alice", "w-a", project["id"]),
            restored.list_items("alice", "w-a", project["id"]),
        )
        restored.create_project("alice", "w-a", "Restore-only change", "restore-only")
        self.assertEqual(1, len(self.store.list_projects("alice", "w-a")))
        self.assertEqual(2, len(restored.list_projects("alice", "w-a")))

    def test_creation_cannot_overwrite_an_existing_database(self) -> None:
        project = self.project()
        with self.assertRaises((DomainError, OSError, ValueError)):
            Store(self.path, create=True)
        self.assertEqual([project], self.store.list_projects("alice", "w-a"))

    def test_open_does_not_silently_create_a_missing_database(self) -> None:
        missing = Path(self.temporary.name) / "absent.sqlite3"
        with self.assertRaises((DomainError, OSError, ValueError)):
            Store(missing)
        self.assertFalse(missing.exists())

    def test_unsupported_schema_is_not_ready_and_cannot_be_reopened(self) -> None:
        self.store.connection.execute("PRAGMA user_version = 999")
        self.assertFalse(self.store.ready())
        self.assertEqual(503, self.api.handle("GET", "/readyz")[0])
        self.store.close()
        with self.assertRaises(RuntimeError):
            Store(self.path)

    def test_readiness_detects_missing_table_and_disabled_foreign_keys(self) -> None:
        self.store.connection.execute("PRAGMA foreign_keys = OFF")
        self.assertFalse(self.store.ready())
        self.store.connection.execute("PRAGMA foreign_keys = ON")
        self.assertTrue(self.store.ready())
        self.store.connection.execute("DROP TABLE items")
        self.assertFalse(self.store.ready())
        self.assertEqual(503, self.api.handle("GET", "/readyz")[0])

    def test_database_symlink_is_not_followed_on_open_or_creation(self) -> None:
        link = Path(self.temporary.name) / "linked.sqlite3"
        link.symlink_to(self.path)
        for create in (False, True):
            with self.subTest(create=create):
                with self.assertRaises((DomainError, OSError, ValueError)):
                    Store(link, create=create)
        self.assertTrue(self.store.ready())

    def test_demo_seed_cannot_reset_existing_data(self) -> None:
        project = self.project()
        with self.assertRaises((DomainError, ValueError)):
            self.store.seed_demo()
        self.assertEqual([project], self.store.list_projects("alice", "w-a"))

    def test_backup_cannot_overwrite_existing_file(self) -> None:
        backup = Path(self.temporary.name) / "backup.sqlite3"
        self.store.backup_to(backup)
        before = backup.read_bytes()
        with self.assertRaises((DomainError, OSError, ValueError)):
            self.store.backup_to(backup)
        self.assertEqual(before, backup.read_bytes())

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits are required")
    def test_created_database_and_backup_are_owner_read_write_only(self) -> None:
        backup = Path(self.temporary.name) / "private-backup.sqlite3"
        self.store.backup_to(backup)
        self.assertEqual(0o600, stat.S_IMODE(self.path.stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE(backup.stat().st_mode))

    def test_unknown_and_foreign_workspace_reads_and_writes_are_denied(self) -> None:
        for workspace in ("w-b", "unknown-workspace"):
            with self.subTest(workspace=workspace):
                path = f"/workspaces/{workspace}/projects"
                self.assertEqual(403, self.request("GET", path)[0])
                self.assertEqual(
                    403,
                    self.request("POST", path, body={"name": "Denied"}, key="denied")[0],
                )

    def test_cross_workspace_project_ids_cannot_be_mixed_into_routes(self) -> None:
        foreign = self.project(workspace="w-b", subject="bob")
        path = f"/workspaces/w-a/projects/{foreign['id']}/items"
        self.assertEqual(403, self.request("GET", path)[0])
        self.assertEqual(
            403,
            self.request("POST", path, body={"title": "Denied"}, key="denied")[0],
        )
        self.assertEqual(
            403,
            self.request("PATCH", f"{path}/unknown-item", body={"status": "done"})[0],
        )

    def test_item_ids_cannot_be_mixed_across_projects_or_workspaces(self) -> None:
        project = self.project()
        item = self.item(project)
        other = self.project(key="project-2")
        for workspace, project_id, subject in (
            ("w-a", other["id"], "alice"),
            ("w-b", project["id"], "bob"),
            ("w-a", "unknown-project", "alice"),
        ):
            with self.subTest(workspace=workspace, project=project_id):
                self.assertEqual(
                    403,
                    self.request(
                        "PATCH", f"/workspaces/{workspace}/projects/{project_id}/items/{item['id']}",
                        subject=subject, body={"status": "done"},
                    )[0],
                )
        status, payload = self.request("GET", f"/workspaces/w-a/projects/{project['id']}/items")
        self.assertEqual(200, status, payload)
        self.assertEqual("todo", payload["items"][0]["status"])

    def test_member_cannot_escalate_or_remove_the_owner(self) -> None:
        self.assertEqual(
            403,
            self.request("PATCH", "/workspaces/w-a/members/amy", subject="amy", body={"role": "owner"})[0],
        )
        self.assertEqual(
            403,
            self.request("DELETE", "/workspaces/w-a/members/alice", subject="amy")[0],
        )

    def test_last_owner_cannot_be_removed_or_demoted(self) -> None:
        self.assertEqual(409, self.request("DELETE", "/workspaces/w-a/members/alice")[0])
        self.assertEqual(
            409,
            self.request("PATCH", "/workspaces/w-a/members/alice", body={"role": "member"})[0],
        )
        self.assertEqual(
            200,
            self.request("PATCH", "/workspaces/w-a/members/amy", body={"role": "owner"})[0],
        )

    def test_revocation_applies_to_still_valid_token_and_idempotent_replay(self) -> None:
        project = self.project(subject="amy", key="amy-project")
        item_path = f"/workspaces/w-a/projects/{project['id']}/items"
        item_body = {"title": "Created before revocation"}
        self.assertEqual(
            201, self.request("POST", item_path, subject="amy", body=item_body, key="amy-item")[0]
        )
        self.assertEqual(200, self.request("DELETE", "/workspaces/w-a/members/amy")[0])
        self.assertEqual("amy", SESSIONS["amy-session"])
        self.assertEqual(403, self.request("GET", "/workspaces/w-a/projects", subject="amy")[0])
        self.assertEqual(
            403,
            self.request(
                "POST", "/workspaces/w-a/projects", subject="amy",
                body={"name": "Customer project"}, key="amy-project",
            )[0],
        )
        self.assertEqual(
            403,
            self.request(
                "POST", f"/workspaces/w-a/projects/{project['id']}/items", subject="amy",
                body={"title": "Denied"}, key="revoked-create",
            )[0],
        )
        self.assertEqual([], self.request("GET", "/workspaces", subject="amy")[1]["workspaces"])
        self.assertEqual(
            403, self.request("POST", item_path, subject="amy", body=item_body, key="amy-item")[0]
        )

    def test_role_downgrade_applies_to_still_valid_token(self) -> None:
        self.assertEqual(
            200,
            self.request("PATCH", "/workspaces/w-a/members/amy", body={"role": "owner"})[0],
        )
        self.assertEqual(
            200,
            self.request(
                "PATCH", "/workspaces/w-a/members/alice", subject="amy", body={"role": "member"}
            )[0],
        )
        self.assertEqual("alice", SESSIONS["alice-session"])
        self.assertEqual(
            403,
            self.request("PATCH", "/workspaces/w-a/members/alice", body={"role": "owner"})[0],
        )
        self.assertEqual(403, self.request("DELETE", "/workspaces/w-a/members/amy")[0])
        self.assertEqual(200, self.request("GET", "/workspaces/w-a/projects")[0])

    def test_project_replay_is_identical_without_duplicate_row(self) -> None:
        first = self.project()
        replay = self.project()
        self.assertEqual(first, replay)
        self.assertEqual([first], self.store.list_projects("alice", "w-a"))

    def test_failed_idempotency_record_rolls_back_creation_and_connection_recovers(self) -> None:
        with mock.patch.object(
            self.store, "_remember", side_effect=sqlite3.OperationalError("synthetic write failure")
        ) as remember:
            status, payload = self.request(
                "POST", "/workspaces/w-a/projects",
                body={"name": "Customer project"}, key="rollback-key",
            )
            remember.assert_called_once()
        self.assertEqual(503, status)
        self.assertEqual({"error": "unavailable"}, payload)
        self.assertEqual([], self.store.list_projects("alice", "w-a"))
        self.assertEqual(
            0, self.store.connection.execute("SELECT COUNT(*) FROM idempotency").fetchone()[0]
        )
        project = self.project(key="rollback-key")
        self.assertEqual([project], self.store.list_projects("alice", "w-a"))
        self.assertEqual(
            1, self.store.connection.execute("SELECT COUNT(*) FROM idempotency").fetchone()[0]
        )

    def test_same_key_and_different_project_payload_conflicts(self) -> None:
        self.project()
        self.assertEqual(
            409,
            self.request("POST", "/workspaces/w-a/projects", body={"name": "Different"}, key="project-1")[0],
        )
        self.assertEqual(1, len(self.store.list_projects("alice", "w-a")))

    def test_idempotency_is_scoped_to_subject_and_workspace(self) -> None:
        alice = self.project(key="same-key")
        amy = self.project(subject="amy", key="same-key")
        bob = self.project(workspace="w-b", subject="bob", key="same-key")
        self.assertEqual(3, len({alice["id"], amy["id"], bob["id"]}))
        self.assertEqual(2, len(self.store.list_projects("alice", "w-a")))
        self.assertEqual(1, len(self.store.list_projects("bob", "w-b")))

    def test_item_replay_detects_changed_title_or_parent(self) -> None:
        project = self.project()
        first = self.item(project, key="same-key")
        self.assertEqual(first, self.item(project, key="same-key"))
        self.assertEqual(
            409,
            self.request(
                "POST", f"/workspaces/w-a/projects/{project['id']}/items",
                body={"title": "Different"}, key="same-key",
            )[0],
        )
        second_project = self.project(key="second-project")
        self.assertEqual(
            409,
            self.request(
                "POST", f"/workspaces/w-a/projects/{second_project['id']}/items",
                body={"title": "Ship one safe increment"}, key="same-key",
            )[0],
        )
        self.assertEqual([], self.store.list_items("alice", "w-a", second_project["id"]))
        second_item = self.item(second_project, key="new-key")
        self.assertNotEqual(first["id"], second_item["id"])
        self.assertEqual(1, len(self.store.list_items("alice", "w-a", project["id"])))

    def test_item_replay_returns_original_snapshot_without_reverting_current_state(self) -> None:
        project = self.project()
        original = self.item(project)
        self.assertEqual("todo", original["status"])
        path = f"/workspaces/w-a/projects/{project['id']}/items"
        status, updated = self.request(
            "PATCH", f"{path}/{original['id']}", body={"status": "done"}
        )
        self.assertEqual(200, status, updated)
        self.assertEqual("done", updated["status"])
        self.assertEqual(original, self.item(project))
        persisted = self.store.list_items("alice", "w-a", project["id"])
        self.assertEqual(1, len(persisted))
        self.assertEqual(original["id"], persisted[0]["id"])
        self.assertEqual("done", persisted[0]["status"])

    def test_idempotency_is_scoped_to_operation(self) -> None:
        project = self.project(key="same-key")
        item = self.item(project, key="same-key")
        self.assertNotEqual(project["id"], item["id"])

    def test_store_enforces_tenant_and_owner_rules_without_api_wrapper(self) -> None:
        project = self.project()
        item = self.item(project)
        denied_calls = (
            lambda: self.store.list_projects("bob", "w-a"),
            lambda: self.store.create_project("bob", "w-a", "Denied", "direct-denial"),
            lambda: self.store.list_items("bob", "w-a", project["id"]),
            lambda: self.store.create_item("bob", "w-a", project["id"], "Denied", "direct-denial"),
            lambda: self.store.update_item("bob", "w-a", project["id"], item["id"], "done"),
            lambda: self.store.set_member_role("amy", "w-a", "amy", "owner"),
            lambda: self.store.remove_member("amy", "w-a", "alice"),
        )
        for index, denied_call in enumerate(denied_calls):
            with self.subTest(case=index):
                with self.assertRaises(DomainError) as error:
                    denied_call()
                self.assertEqual(403, error.exception.status)

    def test_get_and_delete_reject_request_bodies(self) -> None:
        self.assertEqual(400, self.request("GET", "/workspaces", body={"subject": "bob"})[0])
        self.assertEqual(
            400, self.request("DELETE", "/workspaces/w-a/members/amy", body={"confirm": True})[0]
        )
        self.assertEqual(200, self.request("GET", "/workspaces/w-a/projects", subject="amy")[0])

    def test_idempotent_replay_survives_process_store_reopen(self) -> None:
        first = self.project()
        self.store.close()
        reopened = Store(self.path)
        self.addCleanup(reopened.close)
        self.assertEqual(
            first, reopened.create_project("alice", "w-a", "Customer project", "project-1")
        )
        self.assertEqual(1, len(reopened.list_projects("alice", "w-a")))

    def test_invalid_or_missing_idempotency_key_is_rejected(self) -> None:
        for key in (None, "", "contains space", "contains/slash", "line\nbreak", "x" * 129):
            with self.subTest(key=key):
                self.assertEqual(
                    400,
                    self.request("POST", "/workspaces/w-a/projects", body={"name": "Valid"}, key=key)[0],
                )
        self.assertEqual([], self.store.list_projects("alice", "w-a"))

    def test_project_input_requires_only_one_bounded_nonempty_text_field(self) -> None:
        for body in (None, [], "text", 7, {}, {"name": None}, {"name": 4}, {"name": ""},
                     {"name": "   "}, {"name": "x" * 201}, {"name": "Valid", "extra": True}):
            with self.subTest(body=body):
                self.assertEqual(
                    400,
                    self.request("POST", "/workspaces/w-a/projects", body=body, key="invalid-body")[0],
                )
        self.assertEqual([], self.store.list_projects("alice", "w-a"))

    def test_item_and_patch_inputs_reject_unknown_fields_and_values(self) -> None:
        project = self.project()
        item = self.item(project)
        path = f"/workspaces/w-a/projects/{project['id']}/items"
        for body in ({}, {"title": ""}, {"title": "x" * 201}, {"title": "OK", "workspace": "w-b"}):
            with self.subTest(body=body):
                self.assertEqual(400, self.request("POST", path, body=body, key="invalid-item")[0])
        for body in (None, [], {}, {"status": "deleted"}, {"status": None}, {"status": "done", "title": "Injected"}):
            with self.subTest(body=body):
                self.assertEqual(400, self.request("PATCH", f"{path}/{item['id']}", body=body)[0])
        for body in ({"role": "admin"}, {"role": None}, {"role": "owner", "subject": "bob"}):
            with self.subTest(body=body):
                self.assertEqual(400, self.request("PATCH", "/workspaces/w-a/members/amy", body=body)[0])

    def test_closed_database_readiness_and_business_errors_are_sanitized(self) -> None:
        self.store.close()
        self.assertEqual(200, self.api.handle("GET", "/healthz")[0])
        self.assertEqual(503, self.api.handle("GET", "/readyz")[0])
        status, payload = self.request("GET", "/workspaces")
        self.assertEqual(503, status)
        serialized = json.dumps(payload)
        for forbidden in (str(self.path), "sqlite3", "Traceback", "closed database"):
            self.assertNotIn(forbidden, serialized)

    def test_sql_looking_strings_are_stored_as_data(self) -> None:
        name = "Robert'); DROP TABLE projects; --"
        status, project = self.request(
            "POST", "/workspaces/w-a/projects", body={"name": name}, key="sql-name"
        )
        self.assertEqual(201, status, project)
        self.assertEqual(name, project["name"])
        title = "x' OR '1'='1"
        status, item = self.request(
            "POST", f"/workspaces/w-a/projects/{project['id']}/items",
            body={"title": title}, key="sql-title",
        )
        self.assertEqual(201, status, item)
        self.assertEqual(title, item["title"])
        self.assertEqual([project], self.store.list_projects("alice", "w-a"))
        self.assertTrue(self.store.ready())


if __name__ == "__main__":
    unittest.main()
