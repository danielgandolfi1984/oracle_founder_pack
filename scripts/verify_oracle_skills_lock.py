#!/usr/bin/env python3
"""Verify a local oracle/skills checkout against the reviewed lock.

The verifier is intentionally offline and read-only. It never fetches, clones,
checks out, installs, or writes to the supplied repository. All repository
content is read through Git object plumbing at the locked commit, rather than
through potentially modified working-tree files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "upstream/oracle-skills.lock.json"
LICENSE_PATH = "LICENSE.txt"
SCHEMA_VERSION = "1.0"
RESULT_KIND = "oci-founder-oracle-skills-lock-verification"
GIT_TIMEOUT_SECONDS = 20
OBJECT_ID_PATTERN = re.compile(r"[0-9a-f]{40}")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class VerificationInputError(Exception):
    """An invalid or unsafe caller-controlled input."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class GitExecutionError(Exception):
    """A deterministic wrapper for an unavailable or unresponsive Git command."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline, read-only verification of an oracle/skills checkout "
            "against the reviewed toolkit lock."
        )
    )
    parser.add_argument(
        "--checkout",
        type=Path,
        required=True,
        help="Explicit local oracle/skills Git checkout root; symlinks are refused.",
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=DEFAULT_LOCK,
        help="Lock JSON to verify; defaults to upstream/oracle-skills.lock.json.",
    )
    return parser.parse_args(argv)


def error_receipt(code: str) -> dict[str, Any]:
    return {
        "kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "scope": "offline_read_only",
        "status": "error",
        "summary": {
            "checkout_modified": False,
            "errors": [code],
            "network_attempted": False,
            "passed": False,
        },
    }


def safe_checkout(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.is_symlink():
        raise VerificationInputError("checkout_symlink")
    if not candidate.exists():
        raise VerificationInputError("checkout_missing")
    if not candidate.is_dir():
        raise VerificationInputError("checkout_not_directory")
    return candidate.resolve()


def safe_lock_path(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.is_symlink():
        raise VerificationInputError("lock_symlink")
    if not candidate.exists():
        raise VerificationInputError("lock_missing")
    if not candidate.is_file():
        raise VerificationInputError("lock_not_file")
    return candidate.resolve()


def safe_locked_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise VerificationInputError("lock_invalid_path")
    if "\\" in value:
        raise VerificationInputError("lock_invalid_path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or str(parsed) != value:
        raise VerificationInputError("lock_invalid_path")
    if any(part in {"", ".", ".."} for part in parsed.parts):
        raise VerificationInputError("lock_invalid_path")
    return value


def load_lock(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationInputError("lock_unreadable") from exc
    if not isinstance(value, dict):
        raise VerificationInputError("lock_not_object")

    commit = value.get("commit")
    license_sha256 = value.get("license_sha256")
    raw_paths = value.get("paths")
    raw_trees = value.get("trees")
    if not isinstance(commit, str) or not OBJECT_ID_PATTERN.fullmatch(commit):
        raise VerificationInputError("lock_invalid_commit")
    if not isinstance(license_sha256, str) or not SHA256_PATTERN.fullmatch(license_sha256):
        raise VerificationInputError("lock_invalid_license_sha256")
    if not isinstance(raw_paths, list) or not raw_paths:
        raise VerificationInputError("lock_invalid_paths")
    if not isinstance(raw_trees, dict):
        raise VerificationInputError("lock_invalid_trees")

    paths = [safe_locked_path(item) for item in raw_paths]
    if len(paths) != len(set(paths)):
        raise VerificationInputError("lock_duplicate_path")
    if set(raw_trees) != set(paths):
        raise VerificationInputError("lock_tree_path_mismatch")
    for path_name in paths:
        object_id = raw_trees.get(path_name)
        if not isinstance(object_id, str) or not OBJECT_ID_PATTERN.fullmatch(object_id):
            raise VerificationInputError("lock_invalid_tree_object")
    return value


def git_environment() -> dict[str, str]:
    environment: dict[str, str] = {
        "GIT_ALLOW_PROTOCOL": "",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", os.defpath),
    }
    system_root = os.environ.get("SYSTEMROOT")
    if system_root:
        environment["SYSTEMROOT"] = system_root
    return environment


def run_git(git: str, checkout: Path, arguments: Sequence[str]) -> tuple[int, bytes]:
    try:
        completed = subprocess.run(
            [
                git,
                "--no-optional-locks",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "core.untrackedCache=false",
                "-C",
                str(checkout),
                *arguments,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
            env=git_environment(),
        )
    except subprocess.TimeoutExpired as exc:
        raise GitExecutionError("git_timeout") from exc
    except OSError as exc:
        raise GitExecutionError("git_unavailable") from exc
    return completed.returncode, completed.stdout


def required_git() -> str:
    executable = shutil.which("git")
    if executable is None:
        raise GitExecutionError("git_unavailable")
    return executable


def git_text(git: str, checkout: Path, arguments: Sequence[str]) -> str | None:
    return_code, stdout = run_git(git, checkout, arguments)
    if return_code != 0:
        return None
    try:
        return stdout.decode("ascii").strip()
    except UnicodeDecodeError:
        return None


def verify(checkout: Path, lock: dict[str, Any], git: str) -> dict[str, Any]:
    expected_commit = str(lock["commit"])
    expected_license = str(lock["license_sha256"])
    paths = sorted(str(item) for item in lock["paths"])
    trees = lock["trees"]
    errors: list[str] = []

    root_return_code, root_stdout = run_git(git, checkout, ("rev-parse", "--show-toplevel"))
    if root_return_code != 0:
        raise VerificationInputError("checkout_not_git_repository")
    try:
        repository_root = Path(os.fsdecode(root_stdout.strip())).resolve()
    except (OSError, ValueError) as exc:
        raise VerificationInputError("checkout_root_unreadable") from exc
    if repository_root != checkout:
        raise VerificationInputError("checkout_not_repository_root")

    head = git_text(git, checkout, ("rev-parse", "--verify", "HEAD^{commit}"))
    if head is None or not OBJECT_ID_PATTERN.fullmatch(head):
        raise VerificationInputError("checkout_head_unreadable")

    commit_code, _ = run_git(git, checkout, ("cat-file", "-e", f"{expected_commit}^{{commit}}"))
    commit_exists = commit_code == 0
    head_matches = head == expected_commit
    if not commit_exists:
        errors.append("locked_commit_missing")
    if not head_matches:
        errors.append("head_commit_mismatch")

    status_code, status_bytes = run_git(
        git,
        checkout,
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
    )
    if status_code != 0:
        raise VerificationInputError("checkout_status_unreadable")
    worktree_clean = status_bytes == b""
    if not worktree_clean:
        errors.append("checkout_dirty")

    tree_results: list[dict[str, Any]] = []
    for path_name in paths:
        expected_tree = str(trees[path_name])
        observed_object: str | None = None
        object_type: str | None = None
        if commit_exists:
            observed_object = git_text(
                git,
                checkout,
                ("rev-parse", "--verify", f"{expected_commit}:{path_name}"),
            )
            if observed_object and OBJECT_ID_PATTERN.fullmatch(observed_object):
                object_type = git_text(git, checkout, ("cat-file", "-t", observed_object))
            else:
                observed_object = None
        matches = observed_object == expected_tree and object_type == "tree"
        if commit_exists and observed_object is None:
            errors.append(f"locked_path_missing:{path_name}")
        elif commit_exists and object_type != "tree":
            errors.append(f"locked_path_not_tree:{path_name}")
        elif commit_exists and not matches:
            errors.append(f"locked_tree_mismatch:{path_name}")
        tree_results.append(
            {
                "expected_object": expected_tree,
                "matches": matches,
                "object_type": object_type,
                "observed_object": observed_object,
                "path": path_name,
            }
        )

    observed_license: str | None = None
    license_type: str | None = None
    if commit_exists:
        license_spec = f"{expected_commit}:{LICENSE_PATH}"
        license_object = git_text(git, checkout, ("rev-parse", "--verify", license_spec))
        if license_object and OBJECT_ID_PATTERN.fullmatch(license_object):
            license_type = git_text(git, checkout, ("cat-file", "-t", license_object))
            if license_type == "blob":
                blob_code, license_bytes = run_git(git, checkout, ("cat-file", "blob", license_object))
                if blob_code == 0:
                    observed_license = hashlib.sha256(license_bytes).hexdigest()
        if observed_license is None:
            errors.append("locked_license_unreadable")
        elif observed_license != expected_license:
            errors.append("locked_license_sha256_mismatch")

    passed = not errors
    return {
        "kind": RESULT_KIND,
        "license": {
            "expected_sha256": expected_license,
            "matches": observed_license == expected_license and license_type == "blob",
            "object_type": license_type,
            "observed_sha256": observed_license,
            "path": LICENSE_PATH,
        },
        "lock": {
            "commit": expected_commit,
            "license": lock.get("license"),
            "path_count": len(paths),
            "schema_version": lock.get("schema_version"),
            "source": lock.get("source"),
        },
        "repository": {
            "commit_exists": commit_exists,
            "head": head,
            "head_matches": head_matches,
            "is_repository_root": True,
            "worktree_clean": worktree_clean,
        },
        "schema_version": SCHEMA_VERSION,
        "scope": "offline_read_only",
        "status": "pass" if passed else "fail",
        "summary": {
            "checkout_modified": False,
            "errors": errors,
            "network_attempted": False,
            "passed": passed,
        },
        "trees": tree_results,
    }


def render_json(receipt: dict[str, Any]) -> str:
    return json.dumps(receipt, indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        checkout = safe_checkout(args.checkout)
        lock_path = safe_lock_path(args.lock)
        lock = load_lock(lock_path)
        receipt = verify(checkout, lock, required_git())
    except (VerificationInputError, GitExecutionError) as exc:
        receipt = error_receipt(exc.code)
        sys.stdout.write(render_json(receipt))
        return 2

    sys.stdout.write(render_json(receipt))
    return 0 if receipt["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
