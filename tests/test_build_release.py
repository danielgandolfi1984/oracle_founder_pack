from __future__ import annotations

import json
import hashlib
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_release  # noqa: E402


class BuildReleaseTests(unittest.TestCase):
    def test_two_clean_builds_are_byte_for_byte_identical(self) -> None:
        manifests = build_release.deterministic_check()
        self.assertEqual({"skill-only", "full-toolkit"}, {item["package_kind"] for item in manifests})
        for manifest in manifests:
            self.assertEqual("1.1", manifest["schema_version"])
            self.assertEqual("oci-founder-package", manifest["kind"])
            self.assertEqual("public-preview", manifest["status"])
            self.assertEqual("UPL-1.0", manifest["license"])
            self.assertEqual(build_release.PACKAGE_PUBLISHER, manifest["publisher"])

    def test_built_archives_verify_and_have_the_expected_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifests = build_release.build_all(output)
            verified = build_release.verify_all(output)
            self.assertEqual(
                [item["content_sha256"] for item in manifests],
                [item["content_sha256"] for item in verified],
            )

            by_kind = {item["package_kind"]: item for item in manifests}
            skill_paths = {item["path"] for item in by_kind["skill-only"]["files"]}
            full_paths = {item["path"] for item in by_kind["full-toolkit"]["files"]}
            self.assertTrue(any(path.endswith("/skills/oci-founder/SKILL.md") for path in skill_paths))
            self.assertTrue(any(path.endswith("/skills/oci-founder/LICENSE") for path in skill_paths))
            self.assertTrue(any(path.endswith("/skills/oci-founder/LICENSE") for path in full_paths))
            self.assertFalse(any("/blueprints/" in path for path in skill_paths))
            self.assertFalse(any(path.endswith("/plugin.json") for path in skill_paths))
            self.assertFalse(
                any(path.endswith("/scripts/verify_oracle_skills_lock.py") for path in skill_paths)
            )
            self.assertTrue(any(path.endswith("/plugin.json") for path in full_paths))
            self.assertTrue(
                any(path.endswith("/scripts/verify_oracle_skills_lock.py") for path in full_paths)
            )
            self.assertTrue(any("/blueprints/container-api/terraform/" in path for path in full_paths))
            self.assertFalse(any("/blueprints/container-api/tests/" in path for path in full_paths))
            self.assertFalse(any("artifacts" in path or ".pptx-build" in path for path in full_paths))

    def test_full_toolkit_uses_versioned_filename_and_manifest_root(self) -> None:
        version = build_release.load_version()
        expected_archive = f"oci-founder-toolkit-{version}-preview.tar.gz"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifests = build_release.build_all(output)
            full = next(item for item in manifests if item["package_kind"] == "full-toolkit")

            self.assertEqual(expected_archive, full["archive"]["file"])
            self.assertEqual("oci-founder-toolkit", full["archive_root"])
            self.assertEqual(full["name"], full["archive_root"])
            with tarfile.open(output / expected_archive, mode="r:gz") as archive:
                member_names = [member.name for member in archive.getmembers()]

            self.assertIn("oci-founder-toolkit/plugin.json", member_names)
            self.assertTrue(
                all(name.startswith("oci-founder-toolkit/") for name in member_names)
            )
            self.assertFalse(
                any(
                    name.startswith(f"oci-founder-toolkit-{version}-preview/")
                    for name in member_names
                )
            )

    def test_verification_detects_archive_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifests = build_release.build_all(output)
            archive = output / manifests[0]["archive"]["file"]
            archive.write_bytes(archive.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "archive hash mismatch"):
                build_release.verify_all(output)

    def test_verification_rejects_forged_extra_member_and_rewritten_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            build_release.build_all(output)
            spec = build_release.package_specs(build_release.load_version())[0]
            archive_name, manifest_name, checksum_name = build_release.expected_output_names(spec)
            entries = build_release.collect_entries(spec)
            forged = build_release.ContentEntry(
                archive_path=f"{spec.archive_root}/unexpected.txt",
                source_path="unexpected.txt",
                payload=b"forged\n",
                mode=0o644,
            )
            forged_entries = sorted([*entries, forged], key=lambda entry: entry.archive_path)
            archive_payload = build_release.tar_bytes(forged_entries)
            archive_sha256 = hashlib.sha256(archive_payload).hexdigest()
            manifest_path = output / manifest_name
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["archive"]["sha256"] = archive_sha256
            manifest["archive"]["size"] = len(archive_payload)
            manifest["files"] = [entry.manifest_value() for entry in forged_entries]
            manifest["content_sha256"] = build_release.content_fingerprint(manifest["files"])
            (output / archive_name).write_bytes(archive_payload)
            manifest_path.write_bytes(build_release.canonical_json(manifest))
            (output / checksum_name).write_text(
                f"{archive_sha256}  {archive_name}\n",
                encoding="ascii",
            )
            with self.assertRaisesRegex(ValueError, "current source allowlist"):
                build_release.verify_package(spec, output)

    def test_build_refuses_overwrite_without_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            build_release.build_all(output)
            with self.assertRaises(FileExistsError):
                build_release.build_all(output)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_build_refuses_a_symlink_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / "actual"
            actual.mkdir()
            linked = root / "linked"
            linked.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "must not be a symlink"):
                build_release.build_all(linked)

    def test_manifest_is_plain_json_and_archive_contains_only_regular_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifests = build_release.build_all(output)
            for manifest in manifests:
                manifest_path = output / f"{manifest['archive']['file']}.manifest.json"
                self.assertEqual(manifest, json.loads(manifest_path.read_text(encoding="utf-8")))
                self.assertEqual(0o644, manifest_path.stat().st_mode & 0o777)
                self.assertEqual(
                    0o644,
                    (output / manifest["archive"]["file"]).stat().st_mode & 0o777,
                )
                with tarfile.open(output / manifest["archive"]["file"], mode="r:gz") as archive:
                    self.assertTrue(all(member.isfile() for member in archive.getmembers()))

    def test_package_specs_use_explicit_file_allowlists(self) -> None:
        specs = build_release.package_specs(build_release.load_version())
        self.assertTrue(all(not spec.tree_sources for spec in specs))
        full = next(spec for spec in specs if spec.kind == "full-toolkit")
        sources = {path.relative_to(ROOT).as_posix() for path in full.exact_sources}
        self.assertTrue(set(build_release.SKILL_PACKAGE_PATHS) <= sources)
        self.assertTrue(set(build_release.BLUEPRINT_PACKAGE_PATHS) <= sources)
        self.assertTrue(
            {"LICENSE", "SECURITY.md", "SUPPORT.md", "CONTRIBUTING.md", "GOVERNANCE.md"}
            <= sources
        )

    def test_sensitive_local_artifact_patterns_are_forbidden(self) -> None:
        forbidden = (
            "blueprints/container-api/secret.auto.tfvars",
            "blueprints/container-api/secret.tfvars",
            "blueprints/container-api/secret.tfvars.json",
            "blueprints/container-api/terraform.tfstate.backup",
            "blueprints/container-api/terraform-plan.json",
            "blueprints/container-api/crash.log",
            "blueprints/container-api/founder-plan.local.md",
            "blueprints/container-api/.env.production",
        )
        for relative in forbidden:
            with self.subTest(relative=relative):
                self.assertTrue(build_release.is_forbidden_source(ROOT / relative))
        self.assertFalse(
            build_release.is_forbidden_source(
                ROOT / "blueprints/container-api/terraform/runtime/terraform.tfvars.example.json"
            )
        )


if __name__ == "__main__":
    unittest.main()
