"""Synthetic, local-only SQLite teaching store; not production infrastructure.

The caller supplies a verified subject. This module demonstrates authorization,
not authentication. No OCI account, network access, or real user data belongs here.
"""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sqlite3
from uuid import uuid4


class DomainError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


_SCHEMA = (
    "CREATE TABLE workspaces (id TEXT PRIMARY KEY, name TEXT NOT NULL)",
    """CREATE TABLE memberships (
        workspace_id TEXT NOT NULL REFERENCES workspaces(id),
        subject TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('owner','member')),
        PRIMARY KEY(workspace_id, subject))""",
    """CREATE TABLE projects (
        id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
        name TEXT NOT NULL, UNIQUE(workspace_id, id))""",
    """CREATE TABLE items (
        id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, project_id TEXT NOT NULL,
        title TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('todo','doing','done')),
        FOREIGN KEY(workspace_id, project_id) REFERENCES projects(workspace_id, id))""",
    """CREATE TABLE idempotency (
        subject TEXT NOT NULL, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
        operation TEXT NOT NULL, key TEXT NOT NULL, payload TEXT NOT NULL,
        response TEXT NOT NULL, PRIMARY KEY(subject, workspace_id, operation, key))""",
)
_SHAPE_QUERIES = (
    "SELECT id, name FROM workspaces LIMIT 0",
    "SELECT workspace_id, subject, role FROM memberships LIMIT 0",
    "SELECT id, workspace_id, name FROM projects LIMIT 0",
    "SELECT id, workspace_id, project_id, title, status FROM items LIMIT 0",
    "SELECT subject, workspace_id, operation, key, payload, response FROM idempotency LIMIT 0",
)
_KEY = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z", re.ASCII)


def _new_file(path):
    path = Path(path).absolute()
    # O_EXCL also refuses an existing symlink; do not resolve away the final name.
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    return path


def _connect(path):
    return sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, isolation_level=None)


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise DomainError(400, "invalid_input")
    return value


class Store:
    """One connection for a local, single-threaded demo; no concurrency SLA."""

    def __init__(self, path, *, create=False):
        self.path = _new_file(path) if create else Path(path).absolute()
        if self.path.is_symlink() or not self.path.is_file():
            raise ValueError("Database must be an existing regular file, not a symlink")
        self.connection = _connect(self.path)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.execute("PRAGMA foreign_keys = ON")
            if create:
                with self._transaction(write=True):
                    for statement in _SCHEMA:
                        self.connection.execute(statement)
                    self.connection.execute("PRAGMA user_version = 1")
            if not self.ready():
                raise RuntimeError("Unsupported or invalid local demo database schema")
        except BaseException:
            self.connection.close()
            raise

    def close(self):
        self.connection.close()

    def ready(self):
        """Check the schema version and required reads, not just a constant flag."""
        try:
            if self.connection.execute("PRAGMA user_version").fetchone()[0] != 1:
                return False
            if self.connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                return False
            for statement in _SHAPE_QUERIES:
                self.connection.execute(statement)
            return True
        except sqlite3.Error:
            return False

    @contextmanager
    def _transaction(self, *, write=False):
        self.connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            yield
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise

    def _membership(self, subject, workspace, *, owner=False):
        if not isinstance(subject, str) or not isinstance(workspace, str):
            raise DomainError(403, "forbidden")
        row = self.connection.execute(
            "SELECT role FROM memberships WHERE workspace_id = ? AND subject = ?",
            (workspace, subject),
        ).fetchone()
        if row is None or (owner and row["role"] != "owner"):
            raise DomainError(403, "forbidden")
        return row["role"]

    def _project(self, workspace, project):
        if not isinstance(project, str):
            raise DomainError(403, "forbidden")
        row = self.connection.execute(
            "SELECT id, workspace_id, name FROM projects WHERE workspace_id = ? AND id = ?",
            (workspace, project),
        ).fetchone()
        if row is None:
            raise DomainError(403, "forbidden")
        return dict(row)

    def _replay(self, subject, workspace, operation, key, payload):
        if not isinstance(key, str) or _KEY.fullmatch(key) is None:
            raise DomainError(400, "invalid_input")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        row = self.connection.execute(
            """SELECT payload, response FROM idempotency
               WHERE subject = ? AND workspace_id = ? AND operation = ? AND key = ?""",
            (subject, workspace, operation, key),
        ).fetchone()
        if row is not None and row["payload"] != encoded:
            raise DomainError(409, "idempotency_conflict")
        return (json.loads(row["response"]) if row else None), encoded

    def _remember(self, subject, workspace, operation, key, payload, response):
        self.connection.execute(
            """INSERT INTO idempotency(subject, workspace_id, operation, key, payload, response)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (subject, workspace, operation, key, payload, json.dumps(response, sort_keys=True)),
        )

    def seed_demo(self):
        """Explicitly seed an empty database only; never replace existing data."""
        with self._transaction(write=True):
            if self.connection.execute("SELECT 1 FROM workspaces LIMIT 1").fetchone():
                raise DomainError(409, "demo_not_empty")
            self.connection.executemany(
                "INSERT INTO workspaces(id, name) VALUES (?, ?)",
                (("w-a", "Workspace A"), ("w-b", "Workspace B")),
            )
            self.connection.executemany(
                "INSERT INTO memberships(workspace_id, subject, role) VALUES (?, ?, ?)",
                (("w-a", "alice", "owner"), ("w-a", "amy", "member"), ("w-b", "bob", "owner")),
            )
        return {"workspaces": 2, "memberships": 3}

    def list_workspaces(self, subject):
        if not isinstance(subject, str):
            raise DomainError(403, "forbidden")
        with self._transaction():
            return [dict(row) for row in self.connection.execute(
                """SELECT w.id, w.name, m.role FROM workspaces w JOIN memberships m
                   ON w.id = m.workspace_id WHERE m.subject = ? ORDER BY w.id""", (subject,)
            )]

    def list_projects(self, subject, workspace):
        with self._transaction():
            self._membership(subject, workspace)
            return [dict(row) for row in self.connection.execute(
                "SELECT id, workspace_id, name FROM projects WHERE workspace_id = ? ORDER BY id",
                (workspace,),
            )]

    def create_project(self, subject, workspace, name, idempotency_key):
        with self._transaction(write=True):
            self._membership(subject, workspace)
            name = _text(name)
            replay, payload = self._replay(
                subject, workspace, "create_project", idempotency_key, {"name": name}
            )
            if replay is not None:
                return replay
            result = {"id": str(uuid4()), "workspace_id": workspace, "name": name}
            self.connection.execute(
                "INSERT INTO projects(id, workspace_id, name) VALUES (?, ?, ?)",
                (result["id"], workspace, name),
            )
            self._remember(subject, workspace, "create_project", idempotency_key, payload, result)
            return result

    def list_items(self, subject, workspace, project):
        with self._transaction():
            self._membership(subject, workspace)
            self._project(workspace, project)
            return [dict(row) for row in self.connection.execute(
                """SELECT id, workspace_id, project_id, title, status FROM items
                   WHERE workspace_id = ? AND project_id = ? ORDER BY id""", (workspace, project)
            )]

    def create_item(self, subject, workspace, project, title, idempotency_key):
        with self._transaction(write=True):
            self._membership(subject, workspace)
            self._project(workspace, project)
            title = _text(title)
            replay, payload = self._replay(
                subject, workspace, "create_item", idempotency_key,
                {"project_id": project, "title": title},
            )
            if replay is not None:
                return replay
            result = {"id": str(uuid4()), "workspace_id": workspace,
                      "project_id": project, "title": title, "status": "todo"}
            self.connection.execute(
                "INSERT INTO items(id, workspace_id, project_id, title, status) VALUES (?, ?, ?, ?, ?)",
                (result["id"], workspace, project, title, "todo"),
            )
            self._remember(subject, workspace, "create_item", idempotency_key, payload, result)
            return result

    def update_item(self, subject, workspace, project, item, status):
        with self._transaction(write=True):
            self._membership(subject, workspace)
            self._project(workspace, project)
            if not isinstance(item, str):
                raise DomainError(403, "forbidden")
            row = self.connection.execute(
                """SELECT id, workspace_id, project_id, title, status FROM items
                   WHERE workspace_id = ? AND project_id = ? AND id = ?""",
                (workspace, project, item),
            ).fetchone()
            if row is None:
                raise DomainError(403, "forbidden")
            if not isinstance(status, str) or status not in ("todo", "doing", "done"):
                raise DomainError(400, "invalid_input")
            self.connection.execute(
                "UPDATE items SET status = ? WHERE workspace_id = ? AND project_id = ? AND id = ?",
                (status, workspace, project, item),
            )
            return {**dict(row), "status": status}

    def _protect_last_owner(self, workspace, target, new_role):
        old_role = self._membership(target, workspace)
        if old_role == "owner" and new_role != "owner":
            owners = self.connection.execute(
                "SELECT COUNT(*) FROM memberships WHERE workspace_id = ? AND role = ?",
                (workspace, "owner"),
            ).fetchone()[0]
            if owners == 1:
                raise DomainError(409, "last_owner")

    def set_member_role(self, subject, workspace, target, role):
        with self._transaction(write=True):
            self._membership(subject, workspace, owner=True)
            if not isinstance(role, str) or role not in ("owner", "member"):
                raise DomainError(400, "invalid_input")
            self._protect_last_owner(workspace, target, role)
            self.connection.execute(
                "UPDATE memberships SET role = ? WHERE workspace_id = ? AND subject = ?",
                (role, workspace, target),
            )
            return {"workspace_id": workspace, "subject": target, "role": role}

    def remove_member(self, subject, workspace, target):
        with self._transaction(write=True):
            self._membership(subject, workspace, owner=True)
            self._protect_last_owner(workspace, target, None)
            self.connection.execute(
                "DELETE FROM memberships WHERE workspace_id = ? AND subject = ?", (workspace, target)
            )
            return {"workspace_id": workspace, "subject": target, "removed": True}

    def backup_to(self, new_path):
        """Create a consistent local snapshot at a new path; never overwrite."""
        if not self.ready():
            raise RuntimeError("Cannot back up an unready demo database")
        destination = _new_file(new_path)
        target = _connect(destination)
        try:
            self.connection.backup(target)
        finally:
            target.close()
        return {"path": str(destination)}
