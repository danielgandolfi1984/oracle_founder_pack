from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT_PATH = ROOT / "tests/results/2026-09-18-codex-native-probe.json"
OUTPUT_PATH = ROOT / "tests/results/2026-09-18-codex-native-output.json"
RUNNER_RECEIPT_PATH = ROOT / "tests/results/2026-09-18-codex-native-runner-probe.json"
ASSESSMENT_PATH = ROOT / "tests/results/2026-09-18-codex-native-runner-assessment.json"


class CodexNativeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        cls.output = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        cls.runner_receipt = json.loads(RUNNER_RECEIPT_PATH.read_text(encoding="utf-8"))
        cls.assessment = json.loads(ASSESSMENT_PATH.read_text(encoding="utf-8"))

    def test_probe_preserves_historical_skill_lineage(self) -> None:
        historical = self.assessment["historical_receipt"]["skill_tree_sha256"]
        installation = self.receipt["installation"]
        self.assertEqual(historical, installation["source_tree_sha256"])
        self.assertEqual(historical, installation["installed_tree_sha256"])
        self.assertEqual(
            historical,
            self.runner_receipt["installation"]["source_tree_sha256"],
        )
        self.assertTrue(installation["regular_copy"])
        self.assertFalse(installation["symlinks_found"])

    def test_native_codex_used_the_skill_without_mutation(self) -> None:
        replay = self.receipt["native_replay"]
        self.assertEqual("0.153.4", self.receipt["environment"]["codex_cli_version"])
        self.assertTrue(replay["skill_discovered"])
        self.assertTrue(replay["structured_output_valid"])
        self.assertTrue(replay["explicit_invocation"])
        self.assertEqual("read-only", replay["sandbox"])
        self.assertEqual(0, replay["file_change_events"])
        self.assertEqual(0, replay["mcp_tool_calls"])
        self.assertEqual(0, replay["web_searches"])
        self.assertFalse(replay["cloud_commands_executed"])
        self.assertFalse(replay["files_changed"])

    def test_structured_output_hash_and_safety_flags_match(self) -> None:
        payload = OUTPUT_PATH.read_bytes().rstrip(b"\n")
        self.assertEqual(
            self.receipt["native_replay"]["final_output_sha256"],
            hashlib.sha256(payload).hexdigest(),
        )
        self.assertEqual("oci-founder", self.output["skill_name"])
        self.assertEqual("0.1.0", self.output["skill_version"])
        self.assertTrue(self.output["skill_discovered"])
        self.assertFalse(self.output["cloud_commands_executed"])
        self.assertFalse(self.output["files_changed"])

    def test_probe_passes_without_overstating_formal_gates(self) -> None:
        qualification = self.receipt["qualification"]
        self.assertEqual("PASS", qualification["q2_probe"]["status"])
        self.assertEqual("BLOCKED", qualification["q2_formal_gate"]["status"])
        self.assertEqual("PASS", qualification["q3_probe"]["status"])
        self.assertEqual("BLOCKED", qualification["q3_formal_gate"]["status"])
        self.assertRegex(
            self.receipt["native_replay"]["redacted_transcript_sha256"],
            r"^[0-9a-f]{64}$",
        )

    def test_codex_invocation_was_ephemeral_and_ignored_user_rules(self) -> None:
        invocations = self.receipt["sanitized_argv"]
        codex = next(arguments for arguments in invocations if "exec" in arguments)
        self.assertIn("--ephemeral", codex)
        self.assertIn("--ignore-user-config", codex)
        self.assertIn("--ignore-rules", codex)
        self.assertIn("--sandbox", codex)
        self.assertEqual("read-only", codex[codex.index("--sandbox") + 1])

    def test_hardened_runner_assessment_preserves_historical_lineage(self) -> None:
        initial_postrelease = json.loads(
            (ROOT / "tests/results/2026-09-18-codex-native-postrelease-initial.json").read_text(encoding="utf-8")
        )
        historical = self.assessment["historical_receipt"]
        self.assertEqual(
            initial_postrelease["runner"]["script_sha256"],
            self.assessment["current_runner"]["sha256"],
        )
        self.assertEqual(
            hashlib.sha256(RUNNER_RECEIPT_PATH.read_bytes()).hexdigest(),
            historical["sha256"],
        )
        self.assertEqual(
            self.runner_receipt["runner"]["script_sha256"],
            historical["runner_sha256"],
        )
        self.assertEqual(
            initial_postrelease["installation"]["source_tree_sha256"],
            self.assessment["current_runner"]["skill_tree_sha256"],
        )

    def test_assessment_does_not_promote_historical_q3_to_a_formal_pass(self) -> None:
        historical = self.assessment["historical_receipt"]
        renewal = self.assessment["renewal"]
        self.assertEqual("PASS", historical["recorded_probe_q3"])
        self.assertEqual("PARTIAL", historical["normalized_q3"])
        self.assertEqual("BLOCKED", self.assessment["formal_q2"])
        self.assertEqual("BLOCKED", self.assessment["formal_q3"])
        self.assertEqual("BLOCKED", renewal["status"])
        self.assertFalse(renewal["model_session_started"])
        self.assertFalse(renewal["cloud_mutation_attempted"])
        self.assertFalse(self.assessment["release_qualified"])


if __name__ == "__main__":
    unittest.main()
