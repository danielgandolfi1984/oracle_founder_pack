from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT = ROOT / "tests/results/2026-09-18-v0.1.1-assessment.json"


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def retained_answer_and_paths(case_id: str, artifact: Path) -> tuple[str, set[str]]:
    answer, separator, appendix = artifact.read_text(encoding="utf-8").partition("\n---\n")
    if not separator:
        raise AssertionError(f"missing retained-answer separator: {artifact}")
    if case_id == "full-plan-preserved" and answer.startswith("Evidence note "):
        note, paragraph_separator, answer = answer.partition("\n\n")
        if not paragraph_separator or not note.startswith("Evidence note (outside the evaluated answer):"):
            raise AssertionError(f"invalid full-plan evidence-note prefix: {artifact}")

    if case_id == "focused-progressive-disclosure":
        paths = set(re.findall(r"^- `([^`]+)`$", appendix, flags=re.MULTILINE))
    elif case_id == "full-plan-preserved":
        fenced = re.search(
            r"Relative read paths:\s*```text\n(?P<paths>.*?)\n```",
            appendix,
            flags=re.DOTALL,
        )
        if fenced is None:
            raise AssertionError(f"missing full-plan read-path fence: {artifact}")
        paths = {line for line in fenced.group("paths").splitlines() if line}
    else:
        raise AssertionError(f"unexpected progressive-disclosure case: {case_id}")
    return answer, paths


class ProgressiveDisclosureEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assessment = json.loads(ASSESSMENT.read_text(encoding="utf-8"))

    def test_content_forward_cases_bind_real_prompts_and_output_artifacts(self) -> None:
        prompts_path = ROOT / self.assessment["prompt_cases"]["path"]
        self.assertEqual(
            hashlib.sha256(prompts_path.read_bytes()).hexdigest(),
            self.assessment["prompt_cases"]["sha256"],
        )
        prompts = {item["id"]: item for item in (
            json.loads(line) for line in prompts_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )}
        cases = self.assessment["cases"]
        self.assertEqual(set(prompts), {case["id"] for case in cases})
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(prompts[case["id"]]["prompt"], case["prompt"])
                self.assertEqual("read-only", prompts[case["id"]]["mutation_ceiling"])
                artifact = ROOT / case["output"]["path"]
                self.assertEqual(
                    hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    case["output"]["sha256"],
                )
                answer, read_paths = retained_answer_and_paths(case["id"], artifact)
                self.assertEqual(
                    len(answer.split()),
                    case["output"]["answer_word_count"],
                )
                self.assertEqual(set(case["read_paths"]), read_paths)
                self.assertEqual("pass", case["status"])

    def test_native_comparison_counts_are_bound_to_exact_receipts(self) -> None:
        comparison = self.assessment["native_comparison"]
        records = {}
        for key in ("baseline", "candidate"):
            binding = comparison[key]
            path = ROOT / binding["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), binding["sha256"])
            receipt = read(binding["path"])
            records[key] = receipt
            self.assertEqual(
                len(receipt["codex"]["structured_output"]["recommendation"].split()),
                binding["recommendation_word_count"],
            )
            refs = [p for p in receipt["selection_evidence"]["read_paths"]
                    if p.startswith(".agents/skills/oci-founder/references/")]
            self.assertEqual(refs, binding["reference_reads"])
            self.assertFalse(any(receipt["effects"].values()))
        for key in ("prompt_sha256", "response_schema_sha256", "binary_sha256"):
            self.assertEqual(records["baseline"]["codex"][key], records["candidate"]["codex"][key])
        self.assertEqual(
            records["baseline"]["fixture"]["manifest_sha256"],
            records["candidate"]["fixture"]["manifest_sha256"],
        )
        self.assertLess(
            comparison["candidate"]["recommendation_word_count"],
            comparison["baseline"]["recommendation_word_count"],
        )

    def test_focused_reference_scope_does_not_disable_full_plan_detail(self) -> None:
        cases = {case["id"]: case for case in self.assessment["cases"]}
        focused = cases["focused-progressive-disclosure"]
        full = cases["full-plan-preserved"]
        journey_reference = "skills/oci-founder/references/use-cases.md"
        self.assertNotIn(journey_reference, focused["read_paths"])
        self.assertIn(journey_reference, full["read_paths"])
        self.assertLess(focused["output"]["answer_word_count"], full["output"]["answer_word_count"])
        self.assertEqual(1, self.assessment["native_comparison"]["observations_per_revision"])
        self.assertFalse(self.assessment["native_comparison"]["general_performance_claim"])
        self.assertEqual("pass_with_reservations", self.assessment["status"])
        self.assertEqual("development-candidate", self.assessment["release_stage"])
        self.assertEqual(
            "The 0.1.1 source and archives are development candidates. Published v0.1.0 "
            "tag and assets are unchanged; no v0.1.1 release is claimed.",
            self.assessment["publication_boundary"],
        )
        self.assertEqual("BLOCKED", self.assessment["formal_q2"])
        self.assertEqual("BLOCKED", self.assessment["formal_q3"])
        self.assertFalse(self.assessment["release_qualified"])


if __name__ == "__main__":
    unittest.main()
