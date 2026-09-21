"""Offline contracts for active dependency inventory and OSV failure handling."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_dependencies as audit


SHA = "0" * 64
DEPENDENCY = {"ecosystem": "PyPI", "name": "example", "version": "1.0", "sources": ["requirements.txt"]}


def requirement(name="example", version="1.0"):
    return f"{name}=={version} --hash=sha256:{SHA}\n"


def npm_fixture():
    manifest = {"dependencies": {"example": "1.0.0"}}
    entry = {"version": "1.0.0", "resolved": "https://registry.npmjs.org/example/-/example-1.0.0.tgz",
             "integrity": "sha512-AAAA"}
    return {"lockfileVersion": 3, "packages": {"": manifest.copy(), "node_modules/example": entry}}, manifest


class InventoryTests(unittest.TestCase):
    def test_python_continuations_hashes_comments_and_extras(self):
        text = f"# comment\nExample_Name[binary]==1.0 \\\n  --hash=sha256:{SHA} \\\n  --hash=sha256:{'1' * 64} # reviewed\n"
        self.assertEqual([("PyPI", "example-name", "1.0")], audit.requirements_pins(text))

    def test_all_platform_marked_pins_are_audited_without_evaluating_markers(self):
        text = f"example==1.0; sys_platform == 'win32' --hash=sha256:{SHA}\n"
        text += f"example==2.0; sys_platform != 'win32' --hash=sha256:{SHA}\n"
        self.assertEqual([("PyPI", "example", "1.0"), ("PyPI", "example", "2.0")],
                         audit.requirements_pins(text))

    def test_unsupported_requirements_fail_instead_of_silently_skipping(self):
        for value in ("example>=1.0", "example==1.*", "-r other.txt", "-e .",
                      "example @ https://example.invalid/archive.whl", "--index-url https://example.invalid",
                      "example===1.0", "", "# comments only", "example==1.0 \\"):
            with self.subTest(kind=value.split(" ")[0]):
                text = value if value in ("", "# comments only", "example==1.0 \\") else value + " --hash=sha256:" + SHA
                with self.assertRaises(audit.AuditError):
                    audit.requirements_pins(text)

    def test_missing_or_malformed_hash_is_not_accepted(self):
        for value in ("example==1.0", "example==1.0 --hash=md5:" + SHA,
                      "example==1.0 --hash=sha256:123"):
            with self.assertRaises(audit.AuditError):
                audit.requirements_pins(value)

    def test_npm_includes_nested_and_scoped_transitive_entries(self):
        lock, manifest = npm_fixture()
        lock["packages"]["node_modules/example/node_modules/@scope/transitive"] = {
            "version": "2.1.0", "integrity": "sha512-AAAA",
            "resolved": "https://registry.npmjs.org/@scope/transitive/-/transitive-2.1.0.tgz"}
        self.assertEqual({("npm", "example", "1.0.0"), ("npm", "@scope/transitive", "2.1.0")},
                         set(audit.npm_pins(lock, manifest)))

    def test_npm_missing_integrity_link_range_or_non_registry_source_fails(self):
        for key, value in (("integrity", None), ("link", True), ("version", "^1.0.0"),
                           ("resolved", "https://example.invalid/archive.tgz")):
            with self.subTest(key=key):
                lock, manifest = npm_fixture()
                lock["packages"]["node_modules/example"][key] = value
                with self.assertRaises(audit.AuditError):
                    audit.npm_pins(lock, manifest)

    def test_npm_root_manifest_mismatch_or_omitted_direct_dependency_fails(self):
        lock, manifest = npm_fixture()
        for replacement in ({"dependencies": {"different": "1.0.0"}},
                            {"dependencies": {"example": "^1.0.0"}}):
            with self.assertRaises(audit.AuditError):
                audit.npm_pins(lock, replacement)
        lock["packages"].pop("node_modules/example")
        with self.assertRaises(audit.AuditError):
            audit.npm_pins(lock, manifest)

    def test_empty_malformed_or_old_npm_lock_fails(self):
        for lock in ({}, [], {"lockfileVersion": 2}, {"lockfileVersion": 3, "packages": {"": {}}}):
            with self.assertRaises(audit.AuditError):
                audit.npm_pins(lock, {})

    def test_inventory_reads_only_the_four_active_manifests_and_deduplicates(self):
        reads = []
        lock, manifest = npm_fixture()

        def reader(_root, relative):
            reads.append(relative)
            if relative in audit.REQUIREMENTS:
                return requirement()
            return json.dumps(lock if relative.endswith("package-lock.json") else manifest)

        with mock.patch.object(audit, "_read", side_effect=reader):
            result = audit.inventory()
        self.assertEqual(2, len(result))
        self.assertEqual(sorted(audit.REQUIREMENTS), result[0]["sources"])
        self.assertEqual(set(audit.REQUIREMENTS) | {audit.NPM_DIRECTORY + "/package.json",
                         audit.NPM_DIRECTORY + "/package-lock.json"}, set(reads))
        self.assertFalse(any("tests/results" in path for path in reads))

    def test_symlink_or_nonregular_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "actual").write_text(requirement())
            (root / "link").symlink_to(root / "actual")
            (root / "directory").mkdir()
            for relative in ("link", "directory", "absent"):
                with self.assertRaises(audit.AuditError):
                    audit._read(root, relative)

    def test_json_duplicate_keys_nonfinite_and_invalid_input_fail(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{'):
            with self.assertRaises(audit.AuditError):
                audit._json(raw)


class QueryTests(unittest.TestCase):
    def test_query_uses_public_name_ecosystem_and_exact_version_only(self):
        request = mock.Mock(return_value={})
        self.assertEqual([], audit.query(DEPENDENCY, request))
        request.assert_called_once_with({"package": {"name": "example", "ecosystem": "PyPI"}, "version": "1.0"})

    def test_pagination_including_empty_page_preserves_query_and_collects_ids(self):
        request = mock.Mock(side_effect=[{"next_page_token": "one"},
            {"vulns": [{"id": "GHSA-example-1"}], "next_page_token": "two"},
            {"vulns": [{"id": "GHSA-example-1"}, {"id": "CVE-2099-1234"}]}])
        self.assertEqual(["CVE-2099-1234", "GHSA-example-1"], audit.query(DEPENDENCY, request))
        self.assertEqual("one", request.call_args_list[1].args[0]["page_token"])
        self.assertEqual("two", request.call_args_list[2].args[0]["page_token"])
        self.assertEqual("1.0", request.call_args_list[2].args[0]["version"])

    def test_repeated_empty_wrong_type_or_oversized_page_tokens_fail(self):
        for token in (None, "", [], 4, "x" * 8193):
            with self.assertRaises(audit.AuditError):
                audit.query(DEPENDENCY, lambda _query: {"next_page_token": token})
        with self.assertRaisesRegex(audit.AuditError, "pagination"):
            audit.query(DEPENDENCY, lambda _query: {"next_page_token": "same"})

    def test_page_limit_is_incomplete_not_a_clean_partial_result(self):
        counter = iter(range(10))
        with mock.patch.object(audit, "MAX_PAGES", 2), self.assertRaisesRegex(audit.AuditError, "page_limit"):
            audit.query(DEPENDENCY, lambda _query: {"next_page_token": str(next(counter))})

    def test_malformed_response_or_advisory_is_not_a_clean_result(self):
        for response in (None, [], {"error": "unavailable"}, {"vulns": None},
                         {"vulns": [{}]}, {"vulns": [{"id": 3}]}, {"vulns": [{"id": "unsafe\nvalue"}]}):
            with self.subTest(response_type=type(response).__name__), self.assertRaises(audit.AuditError):
                audit.query(DEPENDENCY, lambda _query: response)

    def test_withdrawn_advisories_are_ignored_only_with_a_valid_timestamp(self):
        self.assertEqual([], audit.query(DEPENDENCY, lambda _q: {
            "vulns": [{"id": "CVE-2099-1234", "withdrawn": "2026-09-21T00:00:00Z"}]}))
        for withdrawn in (None, "", "bad", "2026-09-21", 2):
            with self.assertRaises(audit.AuditError):
                audit.query(DEPENDENCY, lambda _q: {"vulns": [{"id": "CVE-2099-1234", "withdrawn": withdrawn}]})

    def test_advisory_causes_exit_one_and_service_error_causes_exit_two(self):
        code, result = audit.audit([DEPENDENCY], lambda _q: {"vulns": [{"id": "CVE-2099-1234"}]})
        self.assertEqual(1, code)
        self.assertEqual("known_vulnerabilities", result["status"])
        code, result = audit.audit([DEPENDENCY], mock.Mock(side_effect=audit.AuditError("osv_unavailable")))
        self.assertEqual(2, code)
        self.assertEqual("incomplete", result["status"])

    def test_unexpected_error_does_not_echo_exception_or_claim_pass(self):
        code, result = audit.audit([DEPENDENCY], mock.Mock(side_effect=RuntimeError("private-input-marker")))
        self.assertEqual(2, code)
        self.assertNotIn("private-input-marker", json.dumps(result))

    def test_no_dependencies_does_not_report_clean(self):
        self.assertEqual(2, audit.audit([], mock.Mock())[0])

    def test_fetch_is_fixed_https_post_without_proxy_or_redirect_and_bounded(self):
        response = mock.MagicMock()
        response.status = 200
        response.read.return_value = b"{}"
        opener = mock.Mock()
        opener.open.return_value.__enter__ = mock.Mock(return_value=response)
        opener.open.return_value.__exit__ = mock.Mock(return_value=False)
        with mock.patch.object(audit.urllib.request, "build_opener", return_value=opener) as build:
            self.assertEqual({}, audit.fetch({"package": {"name": "example", "ecosystem": "PyPI"}, "version": "1.0"}))
        request = opener.open.call_args.args[0]
        self.assertEqual("https://api.osv.dev/v1/query", request.full_url)
        self.assertEqual("POST", request.method)
        self.assertEqual({}, build.call_args.args[0].proxies)
        self.assertIsInstance(build.call_args.args[1], audit._NoRedirect)
        self.assertEqual(25, opener.open.call_args.kwargs["timeout"])
        response.read.assert_called_once_with(audit.MAX_RESPONSE_BYTES + 1)

    def test_network_error_and_redirect_are_fail_closed(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.URLError("private-response-marker")
        with mock.patch.object(audit.urllib.request, "build_opener", return_value=opener), \
                self.assertRaisesRegex(audit.AuditError, "^osv_unavailable$"):
            audit.fetch({})
        with self.assertRaisesRegex(audit.AuditError, "redirect_rejected"):
            audit._NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.invalid")

    def test_oversized_http_response_is_not_a_clean_result(self):
        response = mock.MagicMock()
        response.status = 200
        response.read.return_value = b"x" * 17
        opener = mock.MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with mock.patch.object(audit, "MAX_RESPONSE_BYTES", 16), \
                mock.patch.object(audit.urllib.request, "build_opener", return_value=opener), \
                self.assertRaisesRegex(audit.AuditError, "response_too_large"):
            audit.fetch({})

    def test_one_failed_query_prevents_pass_even_if_other_queries_are_clean(self):
        def request(query):
            if query["package"]["name"] == "unavailable":
                raise audit.AuditError("osv_unavailable")
            return {}
        code, report = audit.audit([DEPENDENCY, {**DEPENDENCY, "name": "unavailable"}], request)
        self.assertEqual(2, code)
        self.assertEqual("incomplete", report["status"])
        self.assertEqual([True, False], [item["complete"] for item in report["results"]])

    def test_inventory_only_never_calls_the_advisory_service(self):
        output = io.StringIO()
        with mock.patch.object(audit, "inventory", return_value=[DEPENDENCY]), \
                mock.patch.object(audit, "audit") as service, redirect_stdout(output):
            self.assertEqual(0, audit.main(["--inventory-only"]))
        service.assert_not_called()
        self.assertFalse(json.loads(output.getvalue())["vulnerabilities_checked"])

    def test_invalid_manifest_stops_before_network(self):
        output = io.StringIO()
        with mock.patch.object(audit, "inventory", side_effect=audit.AuditError("invalid_pin")), \
                mock.patch.object(audit, "audit") as service, redirect_stdout(output):
            self.assertEqual(2, audit.main([]))
        service.assert_not_called()
        self.assertEqual("incomplete", json.loads(output.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
