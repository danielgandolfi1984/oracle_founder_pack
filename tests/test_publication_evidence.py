from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicationEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.publication = json.loads((ROOT / "tests/results/2026-09-18-v0.1.1-publication.json").read_text())

    def test_public_coordinate_receipt_matches_release_and_preserves_limits(self) -> None:
        publication = self.publication
        binding = publication["public_tag_lifecycle"]
        path = ROOT / binding["path"]
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), binding["sha256"])
        receipt = json.loads(path.read_text())
        self.assertEqual(publication["release"]["commit"], publication["source_ci"]["head_sha"])
        self.assertEqual(publication["release"]["commit"], receipt["source"]["commit"])
        self.assertEqual("success", publication["source_ci"]["conclusion"])
        self.assertEqual(publication["release"]["tag"], receipt["source"]["tag"])
        self.assertEqual(binding["skill_tree_sha256"], receipt["source"]["skill_tree_sha256"])
        self.assertTrue(receipt["case"]["passed"])
        self.assertTrue(receipt["case"]["final_remove_residuals"]["clean"])
        self.assertTrue(receipt["profile_safety"]["observed_global_skill_targets_unchanged"])
        self.assertTrue(publication["release"]["is_prerelease"])
        self.assertFalse(publication["release"]["is_draft"])
        self.assertTrue(publication["previous_release"]["tag_unchanged"])
        self.assertFalse(publication["previous_release"]["assets_replaced"])
        self.assertFalse(any(receipt["effects"].values()))
        self.assertFalse(publication["release_qualified"])
        self.assertEqual("BLOCKED", publication["formal_q2"])
        self.assertEqual("BLOCKED", publication["formal_q3"])

    def test_published_asset_hashes_match_prepublication_package_evidence(self) -> None:
        assets = {item["name"]: item for item in self.publication["asset_verification"]["assets"]}
        self.assertEqual(6, len(assets))
        for kind in ("skill", "full"):
            path = ROOT / f"tests/results/2026-09-18-v0.1.1-{kind}-package-install-lifecycle.json"
            package = json.loads(path.read_text())["package"]
            archive_name = package["archive_file"]
            self.assertEqual(package["archive_sha256"], assets[archive_name]["sha256"])
            self.assertEqual(package["archive_size"], assets[archive_name]["size"])
            self.assertEqual(package["manifest_sha256"], assets[archive_name + ".manifest.json"]["sha256"])
            sidecar = f"{package['archive_sha256']}  {archive_name}\n".encode()
            self.assertEqual(hashlib.sha256(sidecar).hexdigest(), assets[archive_name + ".sha256"]["sha256"])
        self.assertTrue(self.publication["asset_verification"]["downloaded_from_published_release"])
        self.assertEqual(0, self.publication["asset_verification"]["package_verifier_exit_code"])


if __name__ == "__main__":
    unittest.main()
