from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import scan_release_sources as scanner  # noqa: E402


class ScanReleaseSourcesTests(unittest.TestCase):
    def test_current_release_allowlists_have_no_high_confidence_findings(self) -> None:
        self.assertEqual([], scanner.scan_release_allowlists())

    def test_current_repository_tree_has_no_high_confidence_findings(self) -> None:
        self.assertEqual([], scanner.scan_repository_tree())

    def test_private_key_and_cloud_key_patterns_are_detected_without_echoing_values(self) -> None:
        aws_key = b"AKIA" + b"ABCDEFGHIJKLMNOP"
        payload = (
            b"safe\n-----BEGIN " + b"PRIVATE KEY-----\n"
            + aws_key
            + b"\n"
        )
        findings = scanner.scan_payload("test", "fixture.txt", payload)
        self.assertEqual(
            {"pem-private-key", "aws-access-key-id"},
            {item.detector for item in findings},
        )
        rendered = scanner.render(findings)
        self.assertNotIn(aws_key.decode("ascii"), rendered)
        self.assertIn("fixture.txt:2", rendered)

    def test_repository_scan_ignores_only_named_generated_directories(self) -> None:
        aws_key = b"AKIA" + b"ABCDEFGHIJKLMNOP"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "dist").mkdir()
            (root / "dist" / "generated.txt").write_bytes(aws_key)
            (root / "docs").mkdir()
            (root / "docs" / "reviewed.txt").write_text("safe\n", encoding="utf-8")
            self.assertEqual([], scanner.scan_repository_tree(root))

            (root / "docs" / "tracked.txt").write_bytes(aws_key)
            findings = scanner.scan_repository_tree(root)
            self.assertEqual(1, len(findings))
            self.assertEqual("docs/tracked.txt", findings[0].path)
            self.assertNotIn(aws_key.decode("ascii"), scanner.render(findings))

    def test_reviewed_literal_canaries_are_exactly_scoped(self) -> None:
        self.assertEqual(
            {
                ("scripts/build_release.py", "pem-private-key", 27),
                ("scripts/build_release.py", "pem-private-key", 28),
            },
            set(scanner.REVIEWED_LITERAL_CANARIES),
        )

    def test_deliberate_short_secret_canary_is_not_misclassified_as_a_real_token(self) -> None:
        findings = scanner.scan_payload(
            "test",
            "fixture.txt",
            b"OCI_FOUNDER_SECRET_CANARY_9f6c",
        )
        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
