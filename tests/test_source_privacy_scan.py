"""Synthetic privacy detectors; complete token/URL fixtures exist only at runtime."""

from __future__ import annotations

import base64
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import scan_release_sources as scanner
finally:
    sys.path.pop(0)


def jwt_fixture(*, header=None, claims=None, signature=b"\x01" * 32):
    def encoded(value):
        return base64.urlsafe_b64encode(json.dumps(value).encode("utf-8")).rstrip(b"=")

    return b".".join((
        encoded({"alg": "HS256", "typ": "JWT"} if header is None else header),
        encoded({"sub": "synthetic-subject", "exp": 2000000000} if claims is None else claims),
        base64.urlsafe_b64encode(signature).rstrip(b"="),
    ))


def internal_url(host):
    return b"https" + b"://" + host + b"/synthetic-page"


class SourcePrivacyScanTests(unittest.TestCase):
    def assert_detected_without_values(self, payload, detector):
        findings = scanner.scan_payload("test", "public-source.txt", b"safe\n" + payload)
        self.assertEqual([(detector, 2)], [(finding.detector, finding.line) for finding in findings])
        rendered = scanner.render(findings)
        self.assertNotIn(payload.decode("ascii"), rendered)
        self.assertEqual("test:public-source.txt:2: " + detector, rendered)

    def test_fine_grained_github_token_is_detected_without_echoing_it(self):
        token = b"github" + b"_pat_" + (b"Ab19" * 20) + b"Xy"
        self.assert_detected_without_values(token, "github-fine-grained-token")

    def test_fine_grained_documentation_placeholders_are_not_tokens(self):
        for suffix in (b"", b"REPLACE_ME", b"<your-token>", b"short-example"):
            with self.subTest(length=len(suffix)):
                payload = b"github" + b"_pat_" + suffix
                self.assertEqual([], scanner.scan_payload("test", "guide.md", payload))

    def test_jwt_requires_structured_header_claims_and_signature_shape(self):
        self.assert_detected_without_values(jwt_fixture(), "jwt-token")
        self.assert_detected_without_values(jwt_fixture(header={"alg": "RS256", "typ": "at+jwt"}), "jwt-token")

    def test_jwt_placeholders_and_negative_fixtures_are_not_tokens(self):
        for payload in (
            b"a.b.c", b"eyJ...payload...signature", b"x" * 32 + b"." + b"x" * 32 + b"." + b"x" * 32,
            jwt_fixture(header={"alg": "none"}), jwt_fixture(header={"alg": "not-an-algorithm"}),
            jwt_fixture(header={"alg": ["HS256"]}), jwt_fixture(header=[]),
            jwt_fixture(claims=[]), jwt_fixture(claims={}), jwt_fixture(signature=b"short"),
        ):
            with self.subTest(length=len(payload)):
                self.assertEqual([], scanner.scan_payload("test", "fixture.txt", payload))

    def test_long_resource_identifiers_are_detected_with_global_and_regional_forms(self):
        unique = (b"abcdef234567" * 5)
        for middle in (b"tenancy.oc1..", b"instance.oc1.us-ashburn-1.", b"volume.oc2.region.future."):
            with self.subTest(kind=middle.split(b".")[0].decode()):
                resource = b"ocid" + b"1." + middle + unique
                self.assert_detected_without_values(resource, "oci-resource-identifier")

    def test_existing_ocid_placeholders_and_short_negative_fixtures_are_allowed(self):
        for suffix in (b"replace_me", b"fake", b"foreign", b"<unique_ID>", b"EXAMPLE_ONLY"):
            payload = b"ocid" + b"1.tenancy.oc1.." + suffix
            with self.subTest(length=len(suffix)):
                self.assertEqual([], scanner.scan_payload("test", "fixture.txt", payload))

    def test_internal_confluence_and_sharepoint_urls_are_detected(self):
        for host in (
            b"confluence." + b"oraclecorp.com",
            b"confluence.oci." + b"oraclecorp.com",
            b"oracle." + b"sharepoint.com",
            b"oracle-my." + b"sharepoint.com",
            b"confluence.us." + b"oracle.com",
        ):
            with self.subTest(host_kind=host.split(b".")[0].decode()):
                self.assert_detected_without_values(internal_url(host), "internal-oracle-url")

    def test_public_sources_and_hostname_lookalikes_are_not_internal_urls(self):
        for host in (
            b"docs.oracle.com", b"github.com", b"learn.microsoft.com", b"other.sharepoint.com",
            b"oracle." + b"sharepoint.com.evil.invalid",
            b"confluence." + b"oraclecorp.com.evil.invalid",
            b"notoraclecorp.com", b"notoracle.sharepoint.com",
        ):
            with self.subTest(host_kind=host.split(b".")[0].decode()):
                self.assertEqual([], scanner.scan_payload("test", "guide.md", internal_url(host)))

    def test_repository_scan_applies_privacy_detectors_to_regular_sources(self):
        payload = internal_url(b"confluence." + b"oraclecorp.com") + b"\n" + jwt_fixture()
        with tempfile.TemporaryDirectory(prefix="founder-privacy-scan-") as temporary:
            root = Path(temporary)
            (root / "synthetic.md").write_bytes(payload)
            findings = scanner.scan_repository_tree(root)
            self.assertEqual({"internal-oracle-url", "jwt-token"}, {item.detector for item in findings})
            self.assertTrue(all(item.path == "synthetic.md" for item in findings))
            self.assertNotIn(jwt_fixture().decode(), scanner.render(findings))

    def test_cli_status_and_sanitized_finding_format_remain_compatible(self):
        payload = jwt_fixture()
        findings = scanner.scan_payload("test", "synthetic.md", payload)
        for result, expected in (([], 0), (findings, 1)):
            stdout, stderr = io.StringIO(), io.StringIO()
            with self.subTest(expected=expected), mock.patch.object(scanner, "scan_default_scopes", return_value=result):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(expected, scanner.main())
                self.assertNotIn(payload.decode(), stdout.getvalue() + stderr.getvalue())
        with mock.patch.object(scanner, "scan_default_scopes", side_effect=ValueError("safe scope error")):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(2, scanner.main())


if __name__ == "__main__":
    unittest.main()
