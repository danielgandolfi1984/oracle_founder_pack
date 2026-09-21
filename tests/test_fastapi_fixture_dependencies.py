"""Offline lock/fixture regressions; does not install or execute dependencies."""

from pathlib import Path
import re
import unittest


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "docker-fastapi"
EXPECTED_RUNTIME = {
    "annotated-doc", "annotated-types", "anyio", "click", "fastapi", "h11",
    "idna", "psycopg", "psycopg-binary", "pydantic", "pydantic-core",
    "starlette", "typing-extensions", "typing-inspection", "uvicorn",
}


class FastAPIFixtureDependencyTests(unittest.TestCase):
    def locked_requirements(self):
        contents = (FIXTURE / "requirements.txt").read_text(encoding="utf-8")
        entries = []
        current = ""
        for line in contents.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            current += " " + line.removesuffix("\\").strip()
            if not line.endswith("\\"):
                entries.append(current.strip())
                current = ""
        self.assertEqual("", current, "dangling requirement continuation")
        return entries

    def test_complete_runtime_closure_has_exact_pins_and_sha256_hashes(self):
        names = []
        for entry in self.locked_requirements():
            with self.subTest(requirement=entry.split()[0]):
                match = re.fullmatch(
                    r"([a-z][a-z0-9-]*)(?:\[binary\])?==([0-9]+(?:\.[0-9]+)+)"
                    r"(?: --hash=sha256:[a-f0-9]{64})+", entry,
                )
                self.assertIsNotNone(match, "only exact, hashed runtime pins are allowed")
                names.append(match.group(1))
        self.assertEqual(len(names), len(set(names)), "duplicate runtime pin")
        self.assertEqual(EXPECTED_RUNTIME, set(names))

    def test_starlette_security_floor_and_binary_driver_pair_are_preserved(self):
        pins = {entry.split("==", 1)[0]: entry.split("==", 1)[1].split()[0]
                for entry in self.locked_requirements()}
        self.assertGreaterEqual(tuple(map(int, pins["starlette"].split("."))), (1, 3, 1))
        self.assertEqual(pins["psycopg[binary]"], pins["psycopg-binary"])

    def test_container_enforces_hashes_and_never_builds_dependency_sources(self):
        dockerfile = (FIXTURE / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("--require-hashes --only-binary=:all: -r requirements.txt", dockerfile)

    def test_intentional_healthcheck_mismatch_is_unchanged(self):
        dockerfile = (FIXTURE / "Dockerfile").read_text(encoding="utf-8")
        application = (FIXTURE / "app.py").read_text(encoding="utf-8")
        self.assertIn("/health'", dockerfile)
        self.assertIn('@app.get("/healthz")', application)
        self.assertNotIn('@app.get("/health")', application)
        self.assertIn("EXPOSE 8080", dockerfile)


if __name__ == "__main__":
    unittest.main()
