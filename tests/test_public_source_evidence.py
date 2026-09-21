"""Check historical evidence consistency; these tests do not reinstall skills."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests" / "results"
ASSESSMENT = RESULTS / "2026-09-21-public-source-assessment.json"
NAMES = {"oci-founder", "oci-founder-start", "oci-founder-migrate"}


class PublicSourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.summary = json.loads(ASSESSMENT.read_text(encoding="utf-8"))
        self.receipts = {}
        for label, entry in self.summary["evidence"].items():
            path = (ROOT / entry["path"]).resolve()
            self.assertEqual(RESULTS.resolve(), path.parent)
            self.receipts[label] = json.loads(path.read_text(encoding="utf-8"))

    def test_summary_binds_both_original_receipts_without_replacing_the_failure(self):
        for label, entry in self.summary["evidence"].items():
            with self.subTest(receipt=label):
                self.assertEqual(entry["sha256"], hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest())
                self.assertEqual(self.summary["source_commit"], self.receipts[label]["source_commit"])
                self.assertEqual(entry["status"], self.receipts[label]["status"])
        initial = self.receipts["initial"]
        self.assertEqual("blocked", initial["status"])
        self.assertEqual("undetermined", initial["blocker"]["cause"])
        self.assertFalse(initial["blocker"]["underlying_npm_or_integrity_details_preserved"])
        self.assertFalse(initial["installation_checks"]["same_project_installation_attempted"])

    def test_joint_layout_and_cleanup_claims_match_the_successful_receipt(self):
        receipt = self.receipts["offline_acquisition_followup"]
        checks = receipt["validations"]
        trees = self.summary["skill_tree_sha256"]
        self.assertEqual(NAMES, set(trees))
        self.assertEqual(trees, checks["commit_and_public_source"]["local_skill_tree_sha256"])
        self.assertEqual(trees, checks["commit_and_public_source"]["public_skill_tree_sha256"])
        self.assertEqual(NAMES, set(checks["all_three_installed"]["listed_names"]))
        self.assertTrue(checks["after_removing_start"]["other_two_preserved"])
        self.assertEqual(NAMES - {"oci-founder-start"}, set(checks["after_removing_start"]["listed_names"]))
        self.assertTrue(checks["final_removal"]["list_empty"])
        residuals = checks["final_removal"]["residuals"]
        self.assertTrue(residuals["clean"])
        self.assertEqual({}, residuals["skills_lock"]["skills"])
        self.assertTrue(receipt["global_targets_unchanged"])
        self.assertEqual(12, len(receipt["global_target_names"]))

    def test_offline_acquisition_is_not_claimed_as_native_or_cloud_qualification(self):
        receipt = self.receipts["offline_acquisition_followup"]
        self.assertFalse(self.summary["release_qualified"])
        self.assertFalse(receipt["release_qualified"])
        self.assertEqual("public-source-and-installation-layout-only", self.summary["qualification"])
        for name in ("native_session_started", "oci_account_accessed", "cloud_mutation_attempted", "global_install_attempted"):
            self.assertFalse(receipt["effects"][name])
        self.assertTrue(receipt["effects"]["public_https_clone_performed"])
        self.assertTrue(receipt["effects"]["offline_cache_used"])
        self.assertFalse(receipt["effects"]["npm_network_download_allowed"])
        self.assertTrue(receipt["skills_cli"]["dependency_lock"]["verified"])
        self.assertTrue(receipt["skills_cli"]["integrity"]["verified_before_execution"])
        self.assertEqual(self.summary["source_commit"], self.summary["source_ci"]["head_sha"])


if __name__ == "__main__":
    unittest.main()
