from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_oracle_skills_lock  # noqa: E402


class VerifyOracleSkillsLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "oracle-skills"
        self.checkout.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Toolkit Test")
        self.git("config", "user.email", "toolkit@example.invalid")

        files = {
            "oci/SKILL.md": "# OCI\n",
            "db/SKILL.md": "# Database\n",
            ".claude-plugin/plugin.json": '{"name":"oracle-skills"}\n',
            "LICENSE.txt": "Universal Permissive License test fixture\n",
        }
        for relative, content in files.items():
            target = self.checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")

        self.commit = self.git_text("rev-parse", "HEAD")
        paths = ["oci", "db", ".claude-plugin"]
        trees = {path: self.git_text("rev-parse", f"{self.commit}:{path}") for path in paths}
        license_sha256 = hashlib.sha256((self.checkout / "LICENSE.txt").read_bytes()).hexdigest()
        self.lock = {
            "schema_version": 1,
            "source": "https://github.com/oracle/skills",
            "commit": self.commit,
            "license": "UPL-1.0",
            "license_sha256": license_sha256,
            "paths": paths,
            "trees": trees,
        }
        self.lock_path = self.root / "oracle-skills.lock.json"
        self.write_lock()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.checkout), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

    def git_text(self, *arguments: str) -> str:
        return self.git(*arguments).stdout.strip()

    def write_lock(self) -> None:
        self.lock_path.write_text(
            json.dumps(self.lock, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def run_verifier(self, checkout: Path | None = None) -> tuple[int, str, dict[str, object]]:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = verify_oracle_skills_lock.main(
                [
                    "--checkout",
                    str(checkout or self.checkout),
                    "--lock",
                    str(self.lock_path),
                ]
            )
        rendered = stdout.getvalue()
        return exit_code, rendered, json.loads(rendered)

    def test_matching_checkout_passes_with_deterministic_json(self) -> None:
        first_code, first_json, first = self.run_verifier()
        second_code, second_json, second = self.run_verifier()

        self.assertEqual(0, first_code)
        self.assertEqual(0, second_code)
        self.assertEqual(first_json, second_json)
        self.assertEqual("pass", first["status"])
        self.assertTrue(first["summary"]["passed"])
        self.assertTrue(first["repository"]["commit_exists"])
        self.assertTrue(first["repository"]["head_matches"])
        self.assertTrue(first["repository"]["worktree_clean"])
        self.assertTrue(first["license"]["matches"])
        self.assertTrue(all(item["matches"] for item in first["trees"]))

    def test_git_environment_forbids_lazy_fetch_and_optional_writes(self) -> None:
        environment = verify_oracle_skills_lock.git_environment()

        self.assertEqual("1", environment["GIT_NO_LAZY_FETCH"])
        self.assertEqual("1", environment["GIT_NO_REPLACE_OBJECTS"])
        self.assertEqual("0", environment["GIT_OPTIONAL_LOCKS"])
        self.assertEqual("0", environment["GIT_TERMINAL_PROMPT"])
        self.assertEqual("", environment["GIT_ALLOW_PROTOCOL"])

    def test_existing_locked_commit_that_is_not_head_fails(self) -> None:
        (self.checkout / "later.txt").write_text("later\n", encoding="utf-8")
        self.git("add", "later.txt")
        self.git("commit", "-q", "-m", "later")

        exit_code, _, receipt = self.run_verifier()

        self.assertEqual(1, exit_code)
        self.assertFalse(receipt["repository"]["head_matches"])
        self.assertIn("head_commit_mismatch", receipt["summary"]["errors"])

    def test_missing_locked_commit_fails(self) -> None:
        self.lock["commit"] = "0" * 40
        self.write_lock()

        exit_code, _, receipt = self.run_verifier()

        self.assertEqual(1, exit_code)
        self.assertFalse(receipt["repository"]["commit_exists"])
        self.assertIn("locked_commit_missing", receipt["summary"]["errors"])

    def test_mismatched_tree_object_fails(self) -> None:
        self.lock["trees"]["oci"] = "0" * 40
        self.write_lock()

        exit_code, _, receipt = self.run_verifier()

        self.assertEqual(1, exit_code)
        oci = next(item for item in receipt["trees"] if item["path"] == "oci")
        self.assertFalse(oci["matches"])
        self.assertIn("locked_tree_mismatch:oci", receipt["summary"]["errors"])

    def test_mismatched_license_hash_fails(self) -> None:
        self.lock["license_sha256"] = "0" * 64
        self.write_lock()

        exit_code, _, receipt = self.run_verifier()

        self.assertEqual(1, exit_code)
        self.assertFalse(receipt["license"]["matches"])
        self.assertIn("locked_license_sha256_mismatch", receipt["summary"]["errors"])

    def test_dirty_checkout_fails(self) -> None:
        (self.checkout / "oci/SKILL.md").write_text("modified\n", encoding="utf-8")

        exit_code, _, receipt = self.run_verifier()

        self.assertEqual(1, exit_code)
        self.assertFalse(receipt["repository"]["worktree_clean"])
        self.assertIn("checkout_dirty", receipt["summary"]["errors"])

    def test_license_hash_comes_from_commit_not_dirty_worktree(self) -> None:
        (self.checkout / "LICENSE.txt").write_text("working tree replacement\n", encoding="utf-8")

        exit_code, _, receipt = self.run_verifier()

        self.assertEqual(1, exit_code)
        self.assertFalse(receipt["repository"]["worktree_clean"])
        self.assertTrue(receipt["license"]["matches"])
        self.assertEqual(
            self.lock["license_sha256"],
            receipt["license"]["observed_sha256"],
        )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_symlink_checkout_is_refused(self) -> None:
        linked_checkout = self.root / "linked-checkout"
        linked_checkout.symlink_to(self.checkout, target_is_directory=True)

        exit_code, _, receipt = self.run_verifier(linked_checkout)

        self.assertEqual(2, exit_code)
        self.assertEqual("error", receipt["status"])
        self.assertEqual(["checkout_symlink"], receipt["summary"]["errors"])

    def test_checkout_subdirectory_is_refused(self) -> None:
        exit_code, _, receipt = self.run_verifier(self.checkout / "oci")

        self.assertEqual(2, exit_code)
        self.assertEqual(["checkout_not_repository_root"], receipt["summary"]["errors"])


if __name__ == "__main__":
    unittest.main()
