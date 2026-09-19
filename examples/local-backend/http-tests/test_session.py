"""Ephemeral fixture and launcher tests; never use real identity credentials."""

from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest
from unittest import mock


EXAMPLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLE))
try:
    import http_lab
    from http_lab import lab_session
    from store import Store
finally:
    sys.path.pop(0)


class LabSessionTests(unittest.TestCase):
    def test_owned_temporary_fixture_directory_is_removed_on_normal_exit(self) -> None:
        with lab_session() as session:
            directory = session.directory
            self.assertTrue(directory.is_dir())
            self.assertTrue(session.database_path.is_file())
        self.assertFalse(directory.exists())

    def test_owned_temporary_fixture_directory_is_removed_after_exception(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "synthetic body failure"):
            with lab_session() as session:
                directory = session.directory
                raise RuntimeError("synthetic body failure")
        self.assertFalse(directory.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits are required")
    def test_directory_is_private_and_database_and_configs_are_mode_0600(self) -> None:
        with lab_session() as session:
            self.assertEqual(0o700, stat.S_IMODE(session.directory.stat().st_mode))
            for name in ("synthetic.sqlite3", "alice.curl", "amy.curl", "bob.curl"):
                with self.subTest(file=name):
                    path = session.directory / name
                    self.assertTrue(path.is_file())
                    self.assertFalse(path.is_symlink())
                    self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))

    def test_only_expected_fixture_files_exist_and_no_private_key_is_serialized(self) -> None:
        with lab_session() as session:
            self.assertEqual(
                {"synthetic.sqlite3", "alice.curl", "amy.curl", "bob.curl"},
                {path.name for path in session.directory.iterdir()},
            )
            for path in session.directory.iterdir():
                content = path.read_bytes()
                for marker in (b"PRIVATE KEY", b"BEGIN RSA", b"BEGIN PUBLIC KEY"):
                    self.assertFalse(marker in content, "Key material appeared in a fixture file")

    def test_all_synthetic_tokens_are_accepted_only_as_their_own_subject(self) -> None:
        with lab_session() as session:
            self.assertEqual({"alice", "amy", "bob"}, set(session.tokens))
            for subject, token in session.tokens.items():
                with self.subTest(subject=subject):
                    self.assertEqual(subject, session.verifier(token))
                    config = (session.directory / f"{subject}.curl").read_text(encoding="utf-8")
                    self.assertTrue(
                        f'header = "Authorization: Bearer {token}"\n' in config,
                        "The private configuration must contain its own synthetic credential",
                    )
                    self.assertTrue('noproxy = "*"' in config)

    def test_seeded_memberships_match_the_documented_exercise(self) -> None:
        with lab_session() as session:
            store = Store(session.database_path)
            try:
                for subject, workspace, role in (
                    ("alice", "w-a", "owner"),
                    ("amy", "w-a", "member"),
                    ("bob", "w-b", "owner"),
                ):
                    with self.subTest(subject=subject):
                        memberships = store.list_workspaces(subject)
                        self.assertEqual([(workspace, role)], [(row["id"], row["role"]) for row in memberships])
            finally:
                store.close()

    def test_each_session_has_distinct_fixtures_and_an_independent_signing_key(self) -> None:
        with lab_session() as first, lab_session() as second:
            self.assertNotEqual(first.directory, second.directory)
            for subject in ("alice", "amy", "bob"):
                with self.subTest(subject=subject):
                    self.assertFalse(
                        first.tokens[subject] == second.tokens[subject],
                        "Independent sessions unexpectedly shared a token",
                    )
                    self.assertIsNone(first.verifier(second.tokens[subject]))
                    self.assertIsNone(second.verifier(first.tokens[subject]))

    def test_invalid_lifetime_is_rejected_before_creating_any_temporary_directory(self) -> None:
        for lifetime in (0, -1, 901, 999999, True, False, 1.5, "60", None):
            with self.subTest(lifetime=lifetime):
                with mock.patch.object(http_lab, "TemporaryDirectory") as temporary:
                    with self.assertRaises(ValueError):
                        with lab_session(lifetime=lifetime):
                            self.fail("Invalid lifetime was accepted")
                    temporary.assert_not_called()

    def test_repr_and_session_construction_do_not_print_tokens_or_verifier(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with lab_session() as session:
                representation = repr(session)
                self.assertNotIn("tokens=", representation)
                self.assertNotIn("verifier=", representation)
                for token in session.tokens.values():
                    self.assertFalse(token in representation, "Session repr leaked a token")
                    self.assertFalse(token in stdout.getvalue(), "Session stdout leaked a token")
                    self.assertFalse(token in stderr.getvalue(), "Session stderr leaked a token")
        self.assertEqual("", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())


class LabLauncherTests(unittest.TestCase):
    def test_cli_defaults_to_random_port_and_fifteen_minute_maximum(self) -> None:
        # Exercise argument parsing and output without opening a socket or
        # waiting for the default session lifetime.
        fake_session = SimpleNamespace(
            directory=Path("/synthetic-session-fixture"),
            database_path=Path("/synthetic-session-fixture/synthetic.sqlite3"),
            expires_at=int(time.time()) + 900,
            verifier=lambda _token: None,
        )

        @contextmanager
        def session_context(*, lifetime):
            self.assertEqual(900, lifetime)
            yield fake_session

        server = mock.MagicMock()
        server.server_port = 43123
        server.handle_request.side_effect = KeyboardInterrupt
        server.__enter__.return_value = server
        output = io.StringIO()
        with mock.patch.object(sys, "argv", ["http_lab.py"]), \
                mock.patch.object(http_lab, "lab_session", side_effect=session_context) as session_factory, \
                mock.patch.object(http_lab, "build_server", return_value=server) as server_factory, \
                mock.patch.object(http_lab.time, "monotonic", side_effect=[100.0, 100.1]) as clock, \
                redirect_stdout(output):
            self.assertEqual(0, http_lab.main())
        session_factory.assert_called_once_with(lifetime=900)
        server_factory.assert_called_once_with(fake_session.database_path, fake_session.verifier, port=0)
        self.assertEqual(2, clock.call_count)
        self.assertIn("LAB_URL=http://127.0.0.1:43123", output.getvalue())
        self.assertIn("LAB_SESSION_DIR=/synthetic-session-fixture", output.getvalue())
        self.assertNotIn("Authorization", output.getvalue())

    def test_cli_rejects_unsafe_limits_or_host_override_before_session_creation(self) -> None:
        for arguments in (
            ["--seconds", "0"], ["--seconds", "901"], ["--seconds", "-1"],
            ["--port", "-1"], ["--port", "65536"], ["--host", "0.0.0.0"],
        ):
            with self.subTest(arguments=arguments):
                with mock.patch.object(sys, "argv", ["http_lab.py", *arguments]), \
                        mock.patch.object(http_lab, "lab_session") as session_factory, \
                        redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        http_lab.main()
                    self.assertEqual(2, error.exception.code)
                    session_factory.assert_not_called()

    def test_one_second_cli_run_exits_cleans_up_and_never_prints_bearer_values(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(EXAMPLE / "http_lab.py"), "--seconds", "1"],
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(0, result.returncode, "Short-lived CLI run did not complete successfully")
        self.assertEqual("", result.stderr, "The CLI unexpectedly wrote diagnostics")
        output = result.stdout
        self.assertTrue(re.search(r"(?m)^LAB_URL=http://127\.0\.0\.1:[0-9]+$", output))
        directory_lines = [line for line in output.splitlines() if line.startswith("LAB_SESSION_DIR=")]
        self.assertEqual(1, len(directory_lines))
        directory_values = shlex.split(directory_lines[0].split("=", 1)[1])
        self.assertEqual(1, len(directory_values))
        self.assertFalse(Path(directory_values[0]).exists())
        self.assertIn("removed", output)
        self.assertNotIn("Authorization", output)
        self.assertFalse(
            re.search(r"[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", output),
            "CLI output contained a JWT-shaped value",
        )


if __name__ == "__main__":
    unittest.main()
