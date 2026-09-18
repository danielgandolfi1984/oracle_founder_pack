from __future__ import annotations

import json
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import qualify_skill_install  # noqa: E402


class QualifySkillInstallTests(unittest.TestCase):
    def test_parse_json_suffix_ignores_human_preamble(self) -> None:
        value = "agent detected\ninstallation complete\n[{\"name\": \"oci-founder\"}]\n"
        self.assertEqual(
            [{"name": "oci-founder"}], qualify_skill_install.parse_json_suffix(value)
        )

    def test_redaction_covers_raw_and_resolved_temp_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = f"raw={root} resolved={root.resolve()}"
            redacted = qualify_skill_install.redact_text(
                value, [(root, "$QUALIFICATION_ROOT")]
            )
        self.assertEqual(
            "raw=$QUALIFICATION_ROOT resolved=$QUALIFICATION_ROOT", redacted
        )

    def test_installed_copies_find_universal_and_claude_locations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            for relative in (
                ".agents/skills/oci-founder/SKILL.md",
                ".claude/skills/oci-founder/SKILL.md",
            ):
                path = project / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("---\nname: oci-founder\ndescription: test\n---\n", encoding="utf-8")
            locations = {
                path.relative_to(project).as_posix()
                for path in qualify_skill_install.installed_copies(project)
            }
        self.assertEqual(
            {".agents/skills/oci-founder", ".claude/skills/oci-founder"}, locations
        )

    def test_exact_version_parser_rejects_decorated_or_multiline_output(self) -> None:
        self.assertEqual("1.7.0", qualify_skill_install.parse_exact_version("1.7.0\n"))
        for value in ("v1.7.0", "skills 1.7.0", "1.7.0-beta", "1.7.0\nextra"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    qualify_skill_install.parse_exact_version(value)

    def test_verify_install_requires_exact_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("content", encoding="utf-8")
            source_hash = qualify_skill_install.tree_fingerprint(source)
            project = root / "project"
            for relative in (
                ".agents/skills/oci-founder",
                ".claude/skills/oci-founder",
            ):
                target = project / relative
                target.mkdir(parents=True)
                (target / "SKILL.md").write_text("content", encoding="utf-8")
            result = qualify_skill_install.verify_install(
                project,
                source_hash,
                [".agents/skills/oci-founder", ".claude/skills/oci-founder"],
            )
        self.assertTrue(result["all_copies_match_source"])
        self.assertEqual(2, result["copy_count"])
        self.assertEqual(
            [".agents/skills/oci-founder", ".claude/skills/oci-founder"],
            result["locations"],
        )
        self.assertTrue(result["exact_location_set"])
        self.assertTrue(result["regular_copy"])
        self.assertEqual({}, result["copy_errors"])

    def test_verify_install_rejects_symlink_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("content", encoding="utf-8")
            source_hash = qualify_skill_install.tree_fingerprint(source)
            project = root / "project"
            target_parent = project / ".agents/skills"
            target_parent.mkdir(parents=True)
            target = target_parent / "oci-founder"
            target.symlink_to(source, target_is_directory=True)
            result = qualify_skill_install.verify_install(
                project,
                source_hash,
                [".agents/skills/oci-founder"],
            )
        self.assertTrue(result["exact_location_set"])
        self.assertFalse(result["regular_copy"])
        self.assertFalse(result["all_copies_match_source"])
        self.assertIn(".agents/skills/oci-founder", result["copy_errors"])

    def test_residual_audit_allows_only_empty_lock_and_empty_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".git").mkdir()
            (project / ".git/config").write_text("ignored", encoding="utf-8")
            (project / ".agents/skills").mkdir(parents=True)
            (project / "skills-lock.json").write_text(
                json.dumps({"version": 1, "skills": {}}), encoding="utf-8"
            )
            clean = qualify_skill_install.audit_residuals(
                project, [".agents", ".agents/skills"]
            )
            stale = project / ".agents/skills/oci-founder/orphan.txt"
            stale.parent.mkdir()
            stale.write_text("stale", encoding="utf-8")
            dirty = qualify_skill_install.audit_residuals(
                project, [".agents", ".agents/skills"]
            )
        self.assertTrue(clean["clean"])
        self.assertEqual(["skills-lock.json"], clean["allowed_residual_files"])
        self.assertFalse(dirty["clean"])
        self.assertEqual(
            [".agents/skills/oci-founder/orphan.txt"], dirty["unexpected_files"]
        )

    def test_residual_audit_rejects_nonempty_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "skills-lock.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "skills": {"oci-founder": {"source": "local"}},
                    }
                ),
                encoding="utf-8",
            )
            result = qualify_skill_install.audit_residuals(project)
        self.assertFalse(result["clean"])
        self.assertFalse(result["skills_lock_empty_or_absent"])

    def test_universal_agent_detection_fixture_is_isolated_and_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = qualify_skill_install.prepare_universal_agent_detection_fixture(
                root
            )
            fixture = root / "xdg-config" / "opencode"
            self.assertTrue(fixture.is_dir())
            self.assertFalse(fixture.is_symlink())
            self.assertEqual([], list(fixture.iterdir()))
            self.assertEqual("opencode", result["agent"])
            self.assertEqual("disposable-qualification-root", result["scope"])
            self.assertFalse(result["model_session_started"])

    def test_sanitized_environment_drops_cloud_and_token_variables(self) -> None:
        source = {
            "PATH": "/usr/bin",
            "HOME": "/tmp/example-home",
            "HTTPS_PROXY": "http://proxy.example",
            "AWS_SECRET_ACCESS_KEY": "secret",
            "OCI_CLI_KEY_FILE": "/secret/key.pem",
            "NPM_TOKEN": "token",
        }
        with tempfile.TemporaryDirectory() as temporary:
            env, policy = qualify_skill_install.sanitized_environment(
                Path(temporary), source
            )
        self.assertEqual("/usr/bin", env["PATH"])
        self.assertEqual("/tmp/example-home", env["HOME"])
        self.assertNotIn("HTTPS_PROXY", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertNotIn("OCI_CLI_KEY_FILE", env)
        self.assertNotIn("NPM_TOKEN", env)
        self.assertFalse(policy["cloud_token_or_password_named_variables_inherited"])
        self.assertFalse(policy["proxy_variables_inherited"])

    def test_npm_integrity_requires_manifest_and_every_reviewed_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary)
            (package / "bin").mkdir()
            (package / "dist").mkdir()
            (package / "package.json").write_text(
                json.dumps(
                    {
                        "name": "skills",
                        "version": "1.7.0",
                        "bin": {"skills": "./bin/cli.mjs"},
                    },
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
            (package / "bin/cli.mjs").write_text("wrapper", encoding="utf-8")
            (package / "dist/cli.mjs").write_text("bundle", encoding="utf-8")
            expected = {
                relative: qualify_skill_install.sha256_file(package / relative)
                for relative in qualify_skill_install.EXPECTED_NPM_FILE_HASHES
            }
            with patch.object(
                qualify_skill_install, "EXPECTED_NPM_FILE_HASHES", expected
            ):
                valid = qualify_skill_install.npm_package_integrity(package)
                (package / "dist/cli.mjs").write_text("changed", encoding="utf-8")
                changed = qualify_skill_install.npm_package_integrity(package)
        self.assertTrue(valid["verified_before_execution"])
        self.assertFalse(changed["verified_before_execution"])

    def test_reviewed_dependency_lock_is_complete_and_pinned(self) -> None:
        result = qualify_skill_install.reviewed_dependency_lock()
        self.assertTrue(result["verified"])
        self.assertTrue(result["dependency_integrities_complete"])
        self.assertEqual(
            qualify_skill_install.EXPECTED_SKILLS_DIST_INTEGRITY,
            result["observed_skills_dist_integrity"],
        )

    def test_offline_npm_cache_seed_is_an_exact_regular_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source-cache"
            source.mkdir()
            (source / "entry").write_text("cached bytes", encoding="utf-8")
            target = root / "isolated-cache"
            result = qualify_skill_install.seed_offline_npm_cache(source, target)
        self.assertTrue(result["provided"])
        self.assertTrue(result["copied_before_npm_execution"])
        self.assertEqual(result["source_tree_sha256"], result["copied_tree_sha256"])
        self.assertFalse(result["source_path_recorded"])

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlinks are unavailable")
    def test_offline_npm_cache_seed_rejects_symlink_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source-cache"
            source.mkdir()
            link = root / "linked-cache"
            link.symlink_to(source, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                qualify_skill_install.seed_offline_npm_cache(
                    link, root / "isolated-cache"
                )

    def test_emit_evidence_writes_the_exact_printed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                qualify_skill_install.emit_evidence({"status": "pass"}, output)
            self.assertEqual(stdout.getvalue(), output.read_text(encoding="utf-8"))
            self.assertEqual({"status": "pass"}, json.loads(stdout.getvalue()))
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(FileExistsError):
                    qualify_skill_install.emit_evidence({"status": "new"}, output)
            with redirect_stdout(io.StringIO()):
                qualify_skill_install.emit_evidence(
                    {"status": "new"}, output, overwrite=True
                )
            self.assertEqual(
                {"status": "new"}, json.loads(output.read_text(encoding="utf-8"))
            )

    def test_global_snapshot_is_stable_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            user_home = Path(temporary)
            before = qualify_skill_install.global_snapshot(user_home)
            skill = user_home / ".codex/skills/oci-founder"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("one", encoding="utf-8")
            after = qualify_skill_install.global_snapshot(user_home)
        self.assertNotEqual(json.dumps(before, sort_keys=True), json.dumps(after, sort_keys=True))

    def test_global_snapshot_symlink_target_blocks_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_home = root / "home"
            target = root / "target"
            target.mkdir()
            (target / "SKILL.md").write_text("one", encoding="utf-8")
            link = user_home / ".agents/skills/oci-founder"
            link.parent.mkdir(parents=True)
            link.symlink_to(target, target_is_directory=True)
            before = qualify_skill_install.global_snapshot(user_home)
            (target / "SKILL.md").write_text("two", encoding="utf-8")
            after = qualify_skill_install.global_snapshot(user_home)
        self.assertEqual(before, after)
        self.assertTrue(before["~/.agents/skills/oci-founder"]["is_symlink"])
        self.assertFalse(
            qualify_skill_install.global_snapshots_acceptable(before, after)
        )


if __name__ == "__main__":
    unittest.main()
