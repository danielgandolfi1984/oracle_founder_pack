from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import probe_codex_native as probe  # noqa: E402


class ProbeCodexNativeTests(unittest.TestCase):
    def test_expected_version_reads_only_frontmatter_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skill = Path(temporary) / "SKILL.md"
            for scalar, version in (
                ("0.1.0", "0.1.0"),
                ('"0.1.1"', "0.1.1"),
                ("'0.2.0-preview.3' # reviewed", "0.2.0-preview.3"),
                ('"1.2.3+build.4"', "1.2.3+build.4"),
            ):
                with self.subTest(scalar=scalar):
                    skill.write_text(
                        "---\nname: oci-founder\nmetadata: # provenance\n"
                        f"  author: Example\n  version: {scalar}\n---\n"
                        "metadata:\n  version: 9.9.9\n",
                        encoding="utf-8",
                    )
                    self.assertEqual(version, probe.read_expected_skill_version(skill))

    def test_expected_version_fails_closed_on_missing_invalid_or_ambiguous_metadata(self) -> None:
        frontmatter_cases = (
            "name: oci-founder\n",
            "version: 0.1.1\n",
            "metadata:\n  author: Example\n",
            "metadata: {version: 0.1.1}\n",
            "metadata:\n  version: 0.1.1\nmetadata:\n  version: 0.1.0\n",
            "metadata:\n  version: 0.1.1\n  version: 0.1.0\n",
            "metadata:\n  nested:\n    version: 0.1.1\n",
            "metadata:\n  version: &release 0.1.1\n",
            "metadata:\n  version: *release\n",
            '"metadata":\n  version: 0.1.1\n',
            "metadata:\n\tversion: 0.1.1\n",
            *(f"metadata:\n  version: {value}\n" for value in (
                "", "null", "latest", "0.1", "01.1.1", "0.1.1-01", '"0.1.1', "0.1.1 extra",
            )),
        )
        with tempfile.TemporaryDirectory() as temporary:
            skill = Path(temporary) / "SKILL.md"
            for frontmatter in frontmatter_cases:
                with self.subTest(frontmatter=frontmatter):
                    skill.write_text(f"---\n{frontmatter}---\n", encoding="utf-8")
                    with self.assertRaises(ValueError):
                        probe.read_expected_skill_version(skill)
            for content in ("metadata:\n  version: 0.1.1\n", "---\nmetadata:\n  version: 0.1.1\n"):
                with self.subTest(content=content):
                    skill.write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        probe.read_expected_skill_version(skill)

    def test_expected_version_rejects_symlink_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.md"
            target.write_text('---\nmetadata:\n  version: "0.1.1"\n---\n', encoding="utf-8")
            skill = root / "SKILL.md"
            skill.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink"):
                probe.read_expected_skill_version(skill)

    def test_main_rejects_missing_version_before_any_probe_acquisition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "skills/oci-founder/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: oci-founder\n---\n", encoding="utf-8")
            args = argparse.Namespace(
                allow_download=False,
                offline_npm_cache=Path("/tmp/reviewed-cache"),
                allow_model_session=True,
                timeout_seconds=60,
                source=root,
            )
            with patch.object(probe, "parse_args", return_value=args), \
                    patch.object(probe, "locate_codex") as locate, \
                    patch.object(probe.lifecycle, "acquire_cli") as acquire, \
                    patch.object(probe, "run_codex") as run:
                with self.assertRaisesRegex(SystemExit, "metadata.version is required"):
                    probe.main()
                locate.assert_not_called()
                acquire.assert_not_called()
                run.assert_not_called()

    def test_receipt_records_source_version_even_if_installer_acquisition_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "skills/oci-founder/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text('---\nmetadata:\n  version: "0.1.1"\n---\n', encoding="utf-8")
            args = argparse.Namespace(
                allow_download=False,
                offline_npm_cache=Path("/tmp/reviewed-cache"),
                allow_model_session=True,
                timeout_seconds=60,
                source=root,
                codex=None,
                node=None,
                npm=None,
                output="-",
                overwrite=False,
                keep=False,
            )
            with patch.object(probe, "parse_args", return_value=args), \
                    patch.object(probe, "locate_codex", return_value=Path(sys.executable)), \
                    patch.object(probe.lifecycle, "global_snapshot", return_value={}), \
                    patch.object(probe.lifecycle, "command_result", return_value={}), \
                    patch.object(probe.lifecycle, "acquire_cli", return_value=(None, {}, {})), \
                    patch.object(probe.lifecycle, "emit_evidence") as emit, \
                    patch.object(probe, "run_codex") as run:
                self.assertEqual(2, probe.main())
                self.assertEqual("0.1.1", emit.call_args.args[0]["expected_skill_version"])
                run.assert_not_called()

    def test_parser_accepts_reviewed_offline_npm_cache(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "probe_codex_native.py",
                "--offline-npm-cache",
                "/tmp/reviewed-cache",
                "--allow-model-session",
            ],
        ):
            parsed = probe.parse_args()
        self.assertFalse(parsed.allow_download)
        self.assertEqual(Path("/tmp/reviewed-cache"), parsed.offline_npm_cache)
        self.assertTrue(parsed.allow_model_session)

    def test_response_contract_accepts_exact_safe_output(self) -> None:
        value = {
            "skill_name": "oci-founder",
            "skill_discovered": True,
            "skill_version": "0.1.0",
            "invocation_mode": "explicit",
            "evidence_paths": ["Dockerfile"],
            "recommendation": "Plan only.",
            "guardrails": ["No mutation."],
            "cloud_commands_executed": False,
            "files_changed": False,
        }
        self.assertEqual([], probe.validate_response(value))
        value["unexpected"] = True
        self.assertTrue(probe.validate_response(value))

    def test_response_schema_requires_explicit_skill_selection_category(self) -> None:
        invocation_mode = probe.response_schema()["properties"]["invocation_mode"]
        self.assertEqual(["explicit"], invocation_mode["enum"])
        self.assertIn("selection category", invocation_mode["description"])
        self.assertIn("not the skill's interaction mode", invocation_mode["description"])

    def test_forbidden_command_parser_distinguishes_text_from_execution(self) -> None:
        self.assertEqual([], probe.forbidden_command_names("rg terraform README.md"))
        self.assertEqual(["terraform"], probe.forbidden_command_names("/bin/zsh -lc 'terraform plan'"))
        self.assertEqual(["oci"], probe.forbidden_command_names("echo ok && oci iam region list"))
        self.assertEqual(["docker"], probe.forbidden_command_names("/usr/local/bin/docker build ."))
        self.assertEqual(["docker"], probe.forbidden_command_names("env docker build ."))
        self.assertEqual(["docker"], probe.forbidden_command_names("command docker build ."))
        self.assertEqual(
            ["terraform"],
            probe.forbidden_command_names("sudo /usr/local/bin/terraform plan"),
        )

    def test_command_policy_rejects_interpreters_writes_and_shell_substitution(self) -> None:
        python = probe.command_policy("python3 -c 'print(1)'")
        self.assertEqual(["python3"], python["disallowed_executables"])
        self.assertEqual([], python["forbidden_executables"])
        self.assertIn("sed:in-place", probe.command_policy("sed -i s/a/b/ app.py")["argument_policy_failures"])
        self.assertIn("find:write-or-exec-option", probe.command_policy("find . -delete")["argument_policy_failures"])
        self.assertIn("command-substitution", probe.command_policy("echo $(pwd)")["unsafe_shell_features"])

    def test_command_policy_preserves_quoted_regex_controls_as_one_argument(self) -> None:
        for command in (
            "rg -n 'DATABASE_URL|celery;startup' .",
            'rg -n "DATABASE_URL|celery;startup" .',
            "rg -n 'left>right|low<high;done' README.md",
        ):
            with self.subTest(command=command):
                policy = probe.command_policy(command)
                self.assertEqual(["rg"], policy["executables"])
                self.assertEqual([], policy["disallowed_executables"])
                self.assertEqual([], policy["unsafe_shell_features"])
                self.assertEqual(1, len(policy["segments"]))

    def test_command_policy_splits_real_pipelines_and_injected_commands(self) -> None:
        pipeline = probe.command_policy("rg -n startup . | sed -n '1,20p'")
        self.assertEqual(["rg", "sed"], pipeline["executables"])
        self.assertEqual([], pipeline["disallowed_executables"])

        injected = probe.command_policy(
            "rg -n startup .; terraform plan && oci iam region list"
        )
        self.assertEqual(["oci", "rg", "terraform"], injected["executables"])
        self.assertEqual(["oci", "terraform"], injected["forbidden_executables"])

    def test_command_policy_fails_closed_on_malformed_or_active_shell_syntax(self) -> None:
        unterminated = probe.command_policy("rg -n 'DATABASE_URL|celery .")
        self.assertIn("unparseable-shell", unterminated["unsafe_shell_features"])

        active = probe.command_policy("echo $(pwd) `pwd` > output & terraform plan")
        self.assertEqual(
            ["backticks", "command-substitution", "output-redirection", "unsupported-shell-syntax"],
            active["unsafe_shell_features"],
        )
        self.assertIn("terraform", active["forbidden_executables"])

        literal = probe.command_policy("rg '\$(pwd)|`pwd`|left>right;done' README.md")
        self.assertEqual([], literal["unsafe_shell_features"])
        self.assertEqual(["rg"], literal["executables"])

    def test_command_policy_rejects_reads_outside_the_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertIn(
                "path-outside-project",
                probe.command_policy("cat /etc/passwd", root)["path_policy_failures"],
            )
            self.assertIn(
                "home-path-reference",
                probe.command_policy("cat ~/.ssh/id_rsa", root)["path_policy_failures"],
            )
            self.assertIn(
                "path-outside-project",
                probe.command_policy("find .. -type f", root)["path_policy_failures"],
            )
            self.assertIn(
                "git:alternate-directory",
                probe.command_policy("git -C .. status", root)["argument_policy_failures"],
            )
            self.assertIn(
                "absolute-or-relative-executable:cat",
                probe.command_policy("/bin/cat Dockerfile", root)["path_policy_failures"],
            )

    def test_event_summary_counts_effects_without_retaining_command_text(self) -> None:
        events = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "private"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "command": "/bin/zsh -lc 'sed -n 1,20p SKILL.md'",
                            "aggregated_output": "safe",
                            "exit_code": 0,
                            "status": "completed",
                        },
                    }
                ),
            ]
        )
        summary = probe.summarize_events(events)
        self.assertEqual(1, summary["completed_command_executions"])
        self.assertEqual([], summary["forbidden_executables_observed"])
        self.assertNotIn("command", summary["command_executions"][0])

    def test_event_summary_detects_deny_shim_and_forbidden_execution(self) -> None:
        event = json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "command_execution",
                    "command": "/bin/zsh -lc 'docker build .'",
                    "aggregated_output": "OCI_FOUNDER_DENY_SHIM_CALLED:docker\n",
                    "exit_code": 86,
                    "status": "failed",
                },
            }
        )
        summary = probe.summarize_events(event)
        self.assertEqual(["docker"], summary["forbidden_executables_observed"])
        self.assertEqual(["docker"], summary["disallowed_executables_observed"])
        self.assertEqual(["docker"], summary["deny_shims_triggered"])

    def test_event_summary_binds_installed_skill_read_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / ".agents/skills/oci-founder/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: oci-founder\n---\n", encoding="utf-8")
            command = f"/bin/zsh -lc 'sed -n 1,20p {skill.relative_to(root)}'"
            event = json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": command,
                        "aggregated_output": "safe",
                        "exit_code": 0,
                        "status": "completed",
                    },
                }
            )
            summary = probe.summarize_events(event, root)
        self.assertEqual([".agents/skills/oci-founder/SKILL.md"], summary["read_paths"])

    def test_semantic_assertions_require_relative_fixture_evidence_and_guardrail(self) -> None:
        value = {
            "skill_name": "oci-founder",
            "skill_discovered": True,
            "skill_version": "0.1.0",
            "invocation_mode": "explicit",
            "evidence_paths": ["Dockerfile"],
            "recommendation": "Use Container API for this HTTP process.",
            "guardrails": ["Do not deploy or provision resources."],
        }
        self.assertTrue(all(probe.semantic_assertions(value, {"Dockerfile"}).values()))
        value["evidence_paths"] = ["../secret"]
        self.assertFalse(probe.semantic_assertions(value, {"Dockerfile"})["relative_fixture_evidence"])

    def test_semantic_assertions_bind_explicit_version_and_preserve_historical_default(self) -> None:
        value = {
            "skill_name": "oci-founder",
            "skill_discovered": True,
            "skill_version": "0.1.1",
            "invocation_mode": "explicit",
            "evidence_paths": ["Dockerfile"],
            "recommendation": "Use Container API for this HTTP process.",
            "guardrails": ["Do not deploy or provision resources."],
        }
        self.assertTrue(all(probe.semantic_assertions(
            value, {"Dockerfile"}, expected_skill_version="0.1.1"
        ).values()))
        self.assertFalse(probe.semantic_assertions(value, {"Dockerfile"})["explicit_skill_identity"])
        value["skill_version"] = "0.1.0"
        self.assertTrue(all(probe.semantic_assertions(value, {"Dockerfile"}).values()))
        self.assertFalse(probe.semantic_assertions(
            value, {"Dockerfile"}, expected_skill_version="0.1.1"
        )["explicit_skill_identity"])

    def test_redaction_removes_paths_thread_and_policy_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = (
                f'{root}/file {{"thread_id":"abc-123"}} '
                "enterprise-managed requirements company-policy-9)"
            )
            redacted = probe.redact_transcript(value, [(root, "$QUALIFICATION_ROOT")])
        self.assertNotIn(str(root), redacted)
        self.assertNotIn("abc-123", redacted)
        self.assertNotIn("company-policy-9", redacted)
        self.assertIn("$QUALIFICATION_ROOT/file", redacted)

    def test_deny_shims_are_executable_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "deny"
            probe.write_deny_shims(root)
            docker = root / "docker"
            self.assertTrue(docker.stat().st_mode & 0o111)
            self.assertIn("exit 86", docker.read_text(encoding="utf-8"))

    def test_native_removal_allows_the_original_fixture_and_empty_installer_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            baseline = probe.fixture_manifest(root)
            (root / ".agents/skills").mkdir(parents=True)
            (root / "skills-lock.json").write_text(
                json.dumps({"version": 1, "skills": {}}),
                encoding="utf-8",
            )
            clean = probe.audit_native_removal(root, baseline)
            (root / "Dockerfile").write_text("changed\n", encoding="utf-8")
            changed = probe.audit_native_removal(root, baseline)
        self.assertTrue(clean["clean"])
        self.assertTrue(clean["fixture_unchanged"])
        self.assertFalse(changed["clean"])
        self.assertFalse(changed["fixture_unchanged"])


if __name__ == "__main__":
    unittest.main()
