"""The protocol fixtures are static contracts, not a Polyglot runtime import."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AmbientProtocolContractTests(unittest.TestCase):
    def test_protocol_fixtures_are_the_published_bytes(self) -> None:
        expected = {
            "ambient-companion-v1.schema.json": "f0c944274716ad62758e5965613d5db989f2927f0f309321dd3c4dc1ee4f2fe5",
            "ambient-companion-v1.example.json": "d37e8e7ee7be753cd320145920c8fa7ad3d0dbfe77a0f6e9e516842e46724a25",
        }
        for filename, digest in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256((ROOT / "protocol" / filename).read_bytes()).hexdigest(), digest)

    def test_example_satisfies_the_dependency_free_v1_contract(self) -> None:
        schema = json.loads((ROOT / "protocol/ambient-companion-v1.schema.json").read_text())
        example = json.loads((ROOT / "protocol/ambient-companion-v1.example.json").read_text())
        self.assertEqual(set(example), set(schema["required"]))
        self.assertEqual(example["protocol_version"], schema["properties"]["protocol_version"]["const"])
        self.assertIn(example["host"], schema["properties"]["host"]["enum"])
        self.assertEqual(example["event"], schema["properties"]["event"]["const"])
        self.assertIn(example["mode"], schema["properties"]["mode"]["enum"])
        self.assertLessEqual(len(example["intent_tags"]), schema["properties"]["intent_tags"]["maxItems"])

    def test_runtime_has_no_protocol_import(self) -> None:
        pattern = re.compile(r"^\s*(?:from|import)\s+protocol(?:\s|\.|$)", re.MULTILINE)
        offenders = [path for path in (ROOT / "polyglot").rglob("*.py") if pattern.search(path.read_text())]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
