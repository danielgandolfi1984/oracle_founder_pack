from __future__ import annotations

import tempfile
import unittest
import os
import json
from pathlib import Path
from unittest import mock

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import qualify_hosts  # noqa: E402


class QualifyHostsTests(unittest.TestCase):
    def test_tree_fingerprint_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.txt").write_text("one", encoding="utf-8")
            first = qualify_hosts.tree_fingerprint(root)
            (root / "a.txt").write_text("two", encoding="utf-8")
            second = qualify_hosts.tree_fingerprint(root)
        self.assertNotEqual(first, second)

    def test_redaction_hides_toolkit_and_home_paths(self) -> None:
        value = f"{qualify_hosts.ROOT}/skills {Path.home()}/.codex"
        redacted = qualify_hosts.redact_text(value)
        self.assertIn("$TOOLKIT_ROOT/skills", redacted)
        self.assertIn("$HOME/.codex", redacted)
        self.assertNotIn(str(Path.home()), redacted)

    def test_cursor_probe_never_calls_agent_through_editor_wrapper(self) -> None:
        calls: list[tuple[str, ...]] = []

        def fake_locate(name: str, candidates: object) -> Path | None:
            del candidates
            return Path("/fake/cursor") if name == "cursor" else None

        def fake_command(argv: object, **kwargs: object) -> dict[str, object]:
            del kwargs
            calls.append(tuple(str(item) for item in argv))
            return {
                "exit_code": 0,
                "stdout_excerpt": "3.0.12\ncommit\narm64\n",
                "stderr_excerpt": "",
            }

        with (
            mock.patch.object(qualify_hosts, "locate_executable", side_effect=fake_locate),
            mock.patch.object(qualify_hosts, "bundle_info", return_value={"installed": True}),
            mock.patch.object(qualify_hosts, "command_result", side_effect=fake_command),
        ):
            evidence = qualify_hosts.probe_cursor()

        self.assertFalse(evidence["agent_cli_available"])
        self.assertEqual(calls, [("/fake/cursor", "--version")])
        self.assertFalse(any("agent" in call[1:] for call in calls))

    def test_codex_help_without_validate_is_not_native_validation(self) -> None:
        def fake_command(argv: object, **kwargs: object) -> dict[str, object]:
            del kwargs
            arguments = tuple(str(item) for item in argv)
            output = "Commands:\n  add\n  list\n  marketplace\n  remove\n" if "--help" in arguments else "codex-cli 1.2.3\n"
            return {"exit_code": 0, "stdout_excerpt": output, "stderr_excerpt": ""}

        with (
            mock.patch.object(qualify_hosts, "locate_executable", return_value=Path("/fake/codex")),
            mock.patch.object(qualify_hosts, "bundle_info", return_value={"installed": True}),
            mock.patch.object(qualify_hosts, "command_result", side_effect=fake_command),
            mock.patch.object(Path, "is_file", return_value=False),
        ):
            evidence = qualify_hosts.probe_codex(run_validators=False)

        self.assertEqual(evidence["native_manifest_validator"], "not_exposed_by_cli")

    def test_repo_validation_uses_receipt_renewal_mode(self) -> None:
        observed: list[tuple[str, ...]] = []

        def fake_command(argv: object, **kwargs: object) -> dict[str, object]:
            del kwargs
            observed.append(tuple(str(item) for item in argv))
            return {"exit_code": 0}

        with mock.patch.object(qualify_hosts, "command_result", side_effect=fake_command):
            result = qualify_hosts.repo_validation(False)

        self.assertEqual("passed", result["status"])
        self.assertEqual("source-without-host-preflight-evidence", result["mode"])
        self.assertEqual("--skip-host-preflight-evidence", observed[0][-1])

    def test_child_environment_uses_an_allowlist_and_drops_credentials(self) -> None:
        supplied = {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "OCI_CLI_AUTH": "security_token",
            "OCI_CLI_KEY_FILE": "/secret/key.pem",
            "AWS_SECRET_ACCESS_KEY": "secret",
            "GOOGLE_APPLICATION_CREDENTIALS": "/secret/google.json",
            "AZURE_CLIENT_SECRET": "secret",
            "PASSWORD": "secret",
            "TOKEN": "secret",
        }
        with mock.patch.dict(os.environ, supplied, clear=True):
            environment = qualify_hosts.sanitized_environment()

        self.assertEqual("/usr/bin:/bin", environment["PATH"])
        self.assertEqual("C.UTF-8", environment["LANG"])
        self.assertEqual("1", environment["PYTHONDONTWRITEBYTECODE"])
        for name in supplied:
            if name not in {"PATH", "LANG"}:
                self.assertNotIn(name, environment)

    def test_explicit_validator_pythonpath_is_the_only_extra_child_variable(self) -> None:
        captured: dict[str, str] = {}

        def fake_run(*args: object, **kwargs: object) -> object:
            del args
            captured.update(kwargs["env"])
            return __import__("subprocess").CompletedProcess([], 0, stdout="ok\n", stderr="")

        with (
            mock.patch.dict(os.environ, {"PATH": "/usr/bin", "TOKEN": "secret"}, clear=True),
            mock.patch.object(qualify_hosts.subprocess, "run", side_effect=fake_run),
        ):
            qualify_hosts.command_result(
                ("example", "--version"),
                validator_pythonpath=Path("/reviewed/validator-deps"),
            )

        self.assertEqual("/reviewed/validator-deps", captured["PYTHONPATH"])
        self.assertNotIn("TOKEN", captured)

    def test_validator_dependency_evidence_requires_exact_pyyaml_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "yaml").mkdir()
            (root / "yaml/__init__.py").write_text("", encoding="utf-8")
            metadata = root / "PyYAML-6.0.2.dist-info"
            metadata.mkdir()
            (metadata / "METADATA").write_text("Name: PyYAML\nVersion: 6.0.2\n", encoding="utf-8")
            evidence = qualify_hosts.validator_dependency_evidence(root)
        self.assertEqual("passed", evidence["status"])
        self.assertEqual("6.0.2", evidence["pyyaml_version"])
        self.assertRegex(evidence["tree_sha256"], r"^[0-9a-f]{64}$")

    def test_write_report_is_atomic_and_refuses_implicit_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "report.json"
            qualify_hosts.write_report(target, {"status": "first"})
            self.assertEqual({"status": "first"}, json.loads(target.read_text()))
            self.assertFalse(list(target.parent.glob(f".{target.name}.*.tmp")))
            with self.assertRaises(FileExistsError):
                qualify_hosts.write_report(target, {"status": "second"})
            qualify_hosts.write_report(target, {"status": "second"}, overwrite=True)
            self.assertEqual({"status": "second"}, json.loads(target.read_text()))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_write_report_refuses_symlink_target_and_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / "actual"
            actual.mkdir()
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink parent"):
                qualify_hosts.write_report(linked_parent / "report.json", {})

            real_target = actual / "real.json"
            real_target.write_text("{}\n", encoding="utf-8")
            linked_target = actual / "linked.json"
            linked_target.symlink_to(real_target)
            with self.assertRaisesRegex(ValueError, "replace symlink"):
                qualify_hosts.write_report(linked_target, {}, overwrite=True)


if __name__ == "__main__":
    unittest.main()
