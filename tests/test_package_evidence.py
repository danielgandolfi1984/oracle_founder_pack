from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_release  # noqa: E402
import qualify_skill_install  # noqa: E402


EVIDENCE_PATHS = {
    "skill-only": ROOT / "tests/results/2026-09-18-v0.1.1-skill-package-install-lifecycle.json",
    "full-toolkit": ROOT / "tests/results/2026-09-18-v0.1.1-full-package-install-lifecycle.json",
}
PUBLISHED_EVIDENCE_PATHS = {
    "skill-only": ROOT / "tests/results/2026-09-18-skill-package-install-lifecycle.json",
    "full-toolkit": ROOT / "tests/results/2026-09-18-full-package-install-lifecycle.json",
}
PUBLISHED_SKILL_TREE_SHA256 = "c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37"
PUBLISHED_ARCHIVE_SHA256 = {
    "skill-only": "517c4f6d4d29b35d085d4cf534656608e6c1d7315526563ee632ee5ae9fe7954",
    "full-toolkit": "33037edf2783895c03a5e40bb03a0f18468a26945dc7fce8a9e251ea7e75ca80",
}


class PackageEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence_by_kind = {
            kind: json.loads(path.read_text(encoding="utf-8"))
            for kind, path in EVIDENCE_PATHS.items()
        }
        cls.published_evidence_by_kind = {
            kind: json.loads(path.read_text(encoding="utf-8"))
            for kind, path in PUBLISHED_EVIDENCE_PATHS.items()
        }

    def test_published_v0_1_0_package_evidence_remains_historical(self) -> None:
        for kind, evidence in self.published_evidence_by_kind.items():
            with self.subTest(kind=kind):
                self.assertIn("0.1.0-preview.tar.gz", evidence["package"]["archive_file"])
                self.assertEqual(
                    PUBLISHED_SKILL_TREE_SHA256,
                    evidence["verification"]["skill_tree_sha256"],
                )
                self.assertEqual(
                    PUBLISHED_ARCHIVE_SHA256[kind],
                    evidence["package"]["archive_sha256"],
                )
                self.assertEqual("pass_with_reservations", evidence["status"])
                self.assertFalse(evidence["release_qualified"])

    def test_evidence_is_bound_to_both_fresh_deterministic_packages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manifests = build_release.build_all(Path(temporary))
        manifest_by_kind = {item["package_kind"]: item for item in manifests}
        self.assertEqual(set(EVIDENCE_PATHS), set(manifest_by_kind))
        for kind, evidence in self.evidence_by_kind.items():
            with self.subTest(kind=kind):
                manifest = manifest_by_kind[kind]
                package = evidence["package"]
                self.assertEqual("0.1.1", manifest["version"])
                self.assertIn("0.1.1-preview.tar.gz", package["archive_file"])
                self.assertEqual(manifest["archive"]["sha256"], package["archive_sha256"])
                self.assertEqual(manifest["archive"]["size"], package["archive_size"])
                self.assertEqual(manifest["content_sha256"], package["content_sha256"])
                self.assertEqual(len(manifest["files"]), package["file_count"])
                self.assertEqual(manifest["archive_root"], package["archive_root"])
                self.assertEqual(
                    hashlib.sha256(build_release.canonical_json(manifest)).hexdigest(),
                    package["manifest_sha256"],
                )

    def test_lifecycle_runner_and_skill_fingerprints_are_current(self) -> None:
        runner_hash = hashlib.sha256((ROOT / "scripts/qualify_skill_install.py").read_bytes()).hexdigest()
        skill_hash = qualify_skill_install.tree_fingerprint(ROOT / "skills/oci-founder")
        for kind, evidence in self.evidence_by_kind.items():
            with self.subTest(kind=kind):
                self.assertEqual(runner_hash, evidence["lifecycle"]["runner_sha256"])
                self.assertEqual(skill_hash, evidence["verification"]["skill_tree_sha256"])

    def test_every_agent_package_lifecycle_passed_and_cleanup_was_clean(self) -> None:
        evidence_sets = (
            ("published-v0.1.0", self.published_evidence_by_kind),
            ("candidate-v0.1.1", self.evidence_by_kind),
        )
        for lineage, evidence_by_kind in evidence_sets:
            for kind, evidence in evidence_by_kind.items():
                cases = {item["agent"]: item for item in evidence["lifecycle"]["cases"]}
                with self.subTest(lineage=lineage, kind=kind):
                    self.assertEqual({"codex", "cursor", "claude-code"}, set(cases))
                    for case in cases.values():
                        self.assertTrue(case["passed"])
                        self.assertTrue(case["first_install_exact_and_matching"])
                        self.assertTrue(case["first_list_contains_skill"])
                        self.assertTrue(case["second_install_exact_and_matching"])
                        self.assertTrue(case["second_list_contains_skill"])
                        self.assertTrue(case["final_remove_clean"])

    def test_committed_raw_receipts_are_hash_bound_and_safe(self) -> None:
        evidence_sets = (
            ("published-v0.1.0", self.published_evidence_by_kind),
            ("candidate-v0.1.1", self.evidence_by_kind),
        )
        for lineage, evidence_by_kind in evidence_sets:
            for kind, evidence in evidence_by_kind.items():
                lifecycle = evidence["lifecycle"]
                raw_path = ROOT / lifecycle["raw_receipt_path"]
                raw = json.loads(raw_path.read_text(encoding="utf-8"))
                with self.subTest(lineage=lineage, kind=kind):
                    self.assertEqual(
                        hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                        lifecycle["raw_receipt_sha256"],
                    )
                    self.assertEqual("committed", lifecycle["raw_receipt_retention"])
                    self.assertEqual("pass_with_reservations", raw["status"])
                    self.assertEqual("npm-pinned-reviewed-files-offline-cache", raw["skills_cli"]["source"])
                    self.assertTrue(raw["skills_cli"]["offline_cache"]["provided"])
                    self.assertEqual(
                        raw["skills_cli"]["offline_cache"]["source_tree_sha256"],
                        raw["skills_cli"]["offline_cache"]["copied_tree_sha256"],
                    )
                    self.assertFalse(raw["effects"]["cloud_mutation_attempted"])

    def test_evidence_does_not_overstate_release_status(self) -> None:
        evidence_sets = (
            ("published-v0.1.0", self.published_evidence_by_kind),
            ("candidate-v0.1.1", self.evidence_by_kind),
        )
        for lineage, evidence_by_kind in evidence_sets:
            for kind, evidence in evidence_by_kind.items():
                with self.subTest(lineage=lineage, kind=kind):
                    self.assertEqual("pass_with_reservations", evidence["status"])
                    self.assertFalse(evidence["release_qualified"])
                    self.assertFalse(evidence["effects"]["real_global_profile_changed"])
                    self.assertFalse(evidence["effects"]["cloud_mutation_attempted"])


if __name__ == "__main__":
    unittest.main()
