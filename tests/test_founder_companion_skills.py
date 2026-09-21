"""Standalone packaging contracts, not model-behavior or cloud validation."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
COMPANIONS = ("oci-founder-start", "oci-founder-migrate")


class FounderCompanionSkillsTests(unittest.TestCase):
    def test_each_standalone_copy_retains_every_local_dependency(self) -> None:
        for name in COMPANIONS:
            with self.subTest(skill=name), tempfile.TemporaryDirectory(prefix="founder-skill-copy-") as temporary:
                installed = Path(temporary) / name
                shutil.copytree(ROOT / "skills" / name, installed)
                self.assertTrue((installed / "SKILL.md").is_file())
                self.assertEqual([installed / "SKILL.md"], list(installed.rglob("SKILL.md")))
                for path in installed.rglob("*"):
                    self.assertFalse(path.is_symlink())
                for markdown in installed.rglob("*.md"):
                    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown.read_text(encoding="utf-8"))
                    for raw in links:
                        target = raw.strip().split(maxsplit=1)[0].strip("<>")
                        with self.subTest(skill=name, link=target):
                            if urlsplit(target).scheme:
                                self.assertEqual("https", urlsplit(target).scheme)
                                self.assertTrue(urlsplit(target).hostname)
                                continue
                            linked_path = (markdown.parent / target.split("#", 1)[0]).resolve()
                            linked_path.relative_to(installed.resolve())
                            self.assertTrue(linked_path.exists())

    def test_each_standalone_copy_carries_the_complete_project_license(self) -> None:
        approved_license = (ROOT / "LICENSE").read_bytes()
        for name in COMPANIONS:
            with self.subTest(skill=name):
                self.assertEqual(approved_license, (ROOT / "skills" / name / "LICENSE").read_bytes())


if __name__ == "__main__":
    unittest.main()
