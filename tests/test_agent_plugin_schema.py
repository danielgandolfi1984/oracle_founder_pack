from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_agent_plugin_schema as validator  # noqa: E402


class AgentPluginSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(validator.DEFAULT_SCHEMA.read_text(encoding="utf-8"))
        cls.manifest = json.loads(validator.DEFAULT_MANIFEST.read_text(encoding="utf-8"))

    def test_repository_manifest_matches_vendored_schema(self) -> None:
        self.assertEqual([], validator.validate_instance(self.manifest, self.schema))

    def test_unknown_root_field_is_rejected(self) -> None:
        value = copy.deepcopy(self.manifest)
        value["skills"] = "./skills"
        self.assertTrue(any("additional property" in item for item in validator.validate_instance(value, self.schema)))

    def test_nested_author_contract_is_closed(self) -> None:
        value = copy.deepcopy(self.manifest)
        value["author"] = {"name": "Example", "unexpected": True}
        errors = validator.validate_instance(value, self.schema)
        self.assertTrue(any("$.author.unexpected" in item for item in errors))

    def test_schema_keyword_expansion_fails_closed(self) -> None:
        schema = copy.deepcopy(self.schema)
        schema["enum"] = [self.manifest]
        errors = validator.validate_instance(self.manifest, schema)
        self.assertTrue(any("unsupported keywords" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
