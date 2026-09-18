from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests/results"
sys.path.insert(0, str(ROOT / "scripts"))

import probe_codex_native as probe  # noqa: E402
import qualify_skill_install as lifecycle  # noqa: E402


PUBLISHED_SKILL_TREE_SHA256 = "c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37"
CANDIDATE_NATIVE_NAME = "2026-09-18-v0.1.1-codex-native.json"
CANDIDATE_ASSESSMENT_NAME = "2026-09-18-v0.1.1-assessment.json"


def read(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


class PostreleaseEvidenceTests(unittest.TestCase):
    def test_real_upstream_receipts_match_the_current_lock_and_verifier(self) -> None:
        receipt = read("2026-09-18-oracle-skills-verified.json")
        installed = read("2026-09-18-oracle-skills-verified-codex-lifecycle.json")
        lock = json.loads((ROOT / "upstream/oracle-skills.lock.json").read_text(encoding="utf-8"))
        self.assertTrue(receipt["summary"]["passed"])
        self.assertTrue(receipt["repository"]["worktree_clean"])
        self.assertEqual(lock["commit"], receipt["repository"]["head"])
        for key, relative in (
            ("lock_sha256", "upstream/oracle-skills.lock.json"),
            ("verifier_script_sha256", "scripts/verify_oracle_skills_lock.py"),
            ("reused_script_sha256", "scripts/qualify_skill_install.py"),
        ):
            self.assertEqual(
                hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                installed["runner"][key],
            )
        self.assertEqual(receipt, installed["verification"]["before_install"])
        self.assertEqual(receipt, installed["verification"]["after_final_removal"])

    def test_real_upstream_install_is_exact_project_scoped_and_reversible(self) -> None:
        receipt = read("2026-09-18-oracle-skills-verified-codex-lifecycle.json")
        self.assertEqual("1.7.0", receipt["skills_cli"]["observed_version"])
        self.assertTrue(receipt["skills_cli"]["integrity"]["verified_before_execution"])
        self.assertTrue(receipt["skills_cli"]["dependency_lock"]["verified"])
        source_hash = receipt["source"]["source_tree_sha256_before"]
        self.assertEqual(source_hash, receipt["source"]["source_tree_sha256_after"])
        for phase in ("first_install", "second_install"):
            installed = receipt["case"][phase]
            self.assertTrue(installed["all_copies_match_source"])
            self.assertEqual([".agents/skills/oci"], installed["locations"])
            self.assertEqual({".agents/skills/oci": source_hash}, installed["tree_sha256"])
        for phase in ("first_remove_residuals", "final_remove_residuals"):
            self.assertTrue(receipt["case"][phase]["clean"])
            self.assertEqual([], receipt["case"][phase]["remaining_skill_copies"])
        self.assertEqual(receipt["profile_safety"]["before"], receipt["profile_safety"]["after"])
        self.assertFalse(receipt["profile_safety"]["global_install_attempted"])
        self.assertFalse(receipt["effects"]["cloud_mutation_attempted"])
        self.assertFalse(receipt["release_qualified"])

    def test_published_native_rerun_remains_bound_to_v0_1_0_lineage(self) -> None:
        receipt = read("2026-09-18-codex-native-postrelease.json")
        initial = read("2026-09-18-codex-native-postrelease-initial.json")
        assessment = read("2026-09-18-codex-native-postrelease-assessment.json")
        self.assertEqual(
            assessment["current_runner"]["sha256"],
            receipt["runner"]["script_sha256"],
        )
        self.assertEqual(
            initial["installation"]["source_tree_sha256"],
            receipt["installation"]["source_tree_sha256"],
        )
        self.assertEqual(PUBLISHED_SKILL_TREE_SHA256, receipt["installation"]["source_tree_sha256"])
        self.assertEqual(
            {".agents/skills/oci-founder": PUBLISHED_SKILL_TREE_SHA256},
            receipt["installation"]["tree_sha256"],
        )
        self.assertTrue(receipt["codex"]["structured_output_valid"])
        self.assertTrue(all(receipt["codex"]["semantic_assertions"].values()))
        self.assertTrue(receipt["selection_evidence"]["installed_skill_read"])
        self.assertTrue(receipt["selection_evidence"]["installed_reference_read"])

    def test_v0_1_1_native_rerun_binds_current_code_skill_and_focused_contract(self) -> None:
        receipt = read(CANDIDATE_NATIVE_NAME)
        assessment = read(CANDIDATE_ASSESSMENT_NAME)
        self.assertEqual(
            hashlib.sha256((ROOT / "scripts/probe_codex_native.py").read_bytes()).hexdigest(),
            receipt["runner"]["script_sha256"],
        )
        skill_hash = lifecycle.tree_fingerprint(ROOT / "skills/oci-founder")
        self.assertEqual(skill_hash, receipt["installation"]["source_tree_sha256"])
        self.assertEqual(
            {".agents/skills/oci-founder": skill_hash},
            receipt["installation"]["tree_sha256"],
        )
        schema_bytes = (json.dumps(probe.response_schema(), indent=2, sort_keys=True) + "\n").encode()
        self.assertEqual(
            hashlib.sha256(schema_bytes).hexdigest(),
            receipt["codex"]["response_schema_sha256"],
        )
        manifest = probe.fixture_manifest(ROOT / "tests/fixtures/docker-fastapi")
        self.assertEqual(
            probe.manifest_fingerprint(manifest),
            receipt["fixture"]["manifest_sha256"],
        )
        self.assertEqual([], probe.validate_response(receipt["codex"]["structured_output"]))
        self.assertTrue(
            all(
                probe.semantic_assertions(
                    receipt["codex"]["structured_output"],
                    set(manifest),
                    expected_skill_version=receipt["expected_skill_version"],
                ).values()
            )
        )
        self.assertTrue(receipt["selection_evidence"]["installed_skill_read"])
        self.assertTrue(receipt["selection_evidence"]["installed_reference_read"])
        self.assertNotIn(
            ".agents/skills/oci-founder/references/use-cases.md",
            receipt["selection_evidence"]["read_paths"],
        )
        native_binding = assessment["native_receipt"]
        self.assertEqual(f"tests/results/{CANDIDATE_NATIVE_NAME}", native_binding["path"])
        self.assertEqual(
            hashlib.sha256((RESULTS / CANDIDATE_NATIVE_NAME).read_bytes()).hexdigest(),
            native_binding["sha256"],
        )
        self.assertEqual("pass_with_reservations", receipt["status"])
        self.assertEqual("PASS", receipt["probe_q2"])
        self.assertEqual("PARTIAL", receipt["probe_q3"])
        self.assertEqual("BLOCKED", receipt["formal_q2"])
        self.assertEqual("BLOCKED", receipt["formal_q3"])
        self.assertFalse(receipt["release_qualified"])

    def test_failed_attempt_is_preserved_and_native_success_keeps_formal_limits(self) -> None:
        initial_name = "2026-09-18-codex-native-postrelease-initial.json"
        current_name = "2026-09-18-codex-native-postrelease.json"
        initial = read(initial_name)
        current = read(current_name)
        assessment = read("2026-09-18-codex-native-postrelease-assessment.json")
        self.assertEqual("fail", initial["status"])
        self.assertEqual("pass_with_reservations", current["status"])
        for key, name in (("initial_receipt_sha256", initial_name), ("current_receipt_sha256", current_name)):
            self.assertEqual(hashlib.sha256((RESULTS / name).read_bytes()).hexdigest(), assessment[key])
        self.assertEqual(0, current["codex"]["exit_code"])
        self.assertFalse(current["codex"]["timed_out"])
        self.assertFalse(any(current["effects"].values()))
        self.assertTrue(current["removal"]["clean"])
        self.assertEqual("PASS", current["probe_q2"])
        self.assertEqual("PARTIAL", current["probe_q3"])
        for item in (current, assessment):
            self.assertEqual("BLOCKED", item["formal_q2"])
            self.assertEqual("BLOCKED", item["formal_q3"])
            self.assertFalse(item["release_qualified"])


if __name__ == "__main__":
    unittest.main()
