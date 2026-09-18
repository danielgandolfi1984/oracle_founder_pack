from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "oci-founder"
SMOKE_PATH = ROOT / "tests" / "prompts" / "smoke.jsonl"
REVISION_ASSESSMENT_PATH = (
    ROOT / "tests" / "results" / "2026-09-18-v0.1.1-assessment.json"
)


def tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update((path.stat().st_mode & 0o777).to_bytes(4, "big"))
        payload = path.read_bytes()
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = [
            json.loads(line)
            for line in SMOKE_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_behavioral_matrix_has_a_stable_typed_contract(self) -> None:
        required = {
            "id",
            "selection",
            "mode",
            "journey",
            "expected_route",
            "mutation_ceiling",
            "prompt",
            "assertions",
        }
        ids: list[str] = []
        for case in self.cases:
            self.assertEqual(required, set(case), case.get("id"))
            self.assertTrue(
                all(
                    isinstance(case[key], str) and case[key]
                    for key in required - {"assertions"}
                )
            )
            self.assertIsInstance(case["assertions"], list)
            self.assertGreaterEqual(len(case["assertions"]), 3)
            self.assertTrue(
                all(isinstance(item, str) and item for item in case["assertions"])
            )
            self.assertEqual(len(case["assertions"]), len(set(case["assertions"])))
            ids.append(case["id"])
        self.assertEqual(len(ids), len(set(ids)), "behavioral case IDs must be unique")

    def test_behavioral_matrix_covers_every_interaction_mode_and_journey(self) -> None:
        self.assertEqual(
            {"answer", "assess", "generate", "execute", "diagnose", "teardown"},
            {case["mode"] for case in self.cases},
        )
        self.assertEqual(
            {"orient", "bootstrap", "ship", "verify", "operate", "teardown", "graduate"},
            {case["journey"] for case in self.cases},
        )
        self.assertEqual(
            {"implicit", "explicit"}, {case["selection"] for case in self.cases}
        )

    def test_behavioral_replay_is_non_mutating_by_construction(self) -> None:
        allowed = {"read-only", "generate"}
        ceilings = {case["mutation_ceiling"] for case in self.cases}
        self.assertTrue(ceilings <= allowed)
        self.assertIn("read-only", ceilings)
        self.assertIn("generate", ceilings)

    def test_matrix_exercises_founder_and_upstream_routes(self) -> None:
        routes = {case["expected_route"] for case in self.cases}
        self.assertTrue(
            {
                "oci-founder",
                "oci-functions-troubleshoot",
                "oke-cluster-generator",
                "enterprise-ai",
                "db",
            }
            <= routes
        )

    def test_repository_fixture_contains_a_deliberate_healthcheck_mismatch(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "docker-fastapi"
        dockerfile = (fixture / "Dockerfile").read_text(encoding="utf-8")
        application = (fixture / "app.py").read_text(encoding="utf-8")
        self.assertIn("/health'", dockerfile)
        self.assertIn('@app.get("/healthz")', application)
        self.assertIn("EXPOSE 8080", dockerfile)
        self.assertIn("psycopg", (fixture / "requirements.txt").read_text(encoding="utf-8"))

    def test_every_portable_reference_is_discoverable_from_skill_entrypoint(self) -> None:
        entrypoint = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference_names = {
            path.name for path in (SKILL_ROOT / "references").glob("*.md")
        }
        linked_names = {
            path.name
            for path in (SKILL_ROOT / "references").glob("*.md")
            if f"references/{path.name}" in entrypoint
        }
        self.assertEqual(reference_names, linked_names)

    def test_focused_requests_do_not_expand_into_a_full_founder_plan(self) -> None:
        entrypoint = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Do not read `references/use-cases.md` for a focused explanation",
            entrypoint,
        )
        self.assertIn(
            "A focused request stays focused and does not produce a founder",
            entrypoint,
        )
        self.assertIn(
            "When the user explicitly asks for a full assessment or full plan",
            entrypoint,
        )

    def test_upstream_install_examples_are_verified_and_project_scoped(self) -> None:
        reference = (
            SKILL_ROOT / "references" / "upstream-oracle-skills.md"
        ).read_text(encoding="utf-8")
        self.assertIn("fail closed at\nplanning level", reference)
        self.assertIn("summary.passed: false", reference)
        self.assertIn("npx --yes skills@1.7.0", reference)
        self.assertIn("exactly one agent", reference)

        commands = re.findall(
            r"npx --yes skills@1\.7\.0 add .*?(?=\n\n|\Z)",
            reference,
            flags=re.DOTALL,
        )
        self.assertEqual(2, len(commands))
        for command in commands:
            normalized = command.replace("\\\n", " ")
            self.assertEqual(1, len(re.findall(r"(?:^|\s)-a(?:\s|$)", normalized)))
            self.assertNotIn(" -g", normalized)

    def test_targeted_revision_assessment_is_bound_to_current_skill(self) -> None:
        assessment = json.loads(REVISION_ASSESSMENT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            tree_fingerprint(SKILL_ROOT), assessment["current_skill_tree_sha256"]
        )
        self.assertEqual(
            {
                "focused-progressive-disclosure",
                "full-plan-preserved",
            },
            {case["id"] for case in assessment["cases"]},
        )
        self.assertTrue(all(case["status"] == "pass" for case in assessment["cases"]))
        self.assertEqual("0.1.1", assessment["toolkit_version"])
        self.assertEqual(2, assessment["model_sessions"]["count"])
        self.assertFalse(assessment["model_sessions"]["host_native"])
        self.assertEqual("BLOCKED", assessment["formal_native_gate"])
        self.assertEqual("BLOCKED", assessment["formal_q2"])
        self.assertEqual("BLOCKED", assessment["formal_q3"])
        self.assertFalse(assessment["release_qualified"])


if __name__ == "__main__":
    unittest.main()
