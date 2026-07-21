from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import polyglot.skill.config as hook_config
import polyglot.storage as storage
from polyglot.cli import main


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.tempdir.name)
        self.state_file = self.base_dir / "hook_state.json"
        self.data_patch = patch.object(storage, "data_dir", return_value=self.base_dir)
        self.state_patch = patch.object(hook_config, "HOOK_STATE_FILE", self.state_file)
        self.data_patch.start()
        self.state_patch.start()

    def tearDown(self) -> None:
        self.state_patch.stop()
        self.data_patch.stop()
        self.tempdir.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str]:
        output = StringIO()
        with redirect_stdout(output):
            code = main(list(args))
        return code, output.getvalue()

    def test_lists_all_pairs_as_json(self) -> None:
        code, output = self.run_cli("pairs", "--json")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(len(payload), 70)
        self.assertEqual(sum(item["entries"] for item in payload), 18_235)

    def test_sets_pair_and_samples_json(self) -> None:
        self.assertEqual(self.run_cli("pair", "en-es")[0], 0)
        code, output = self.run_cli("sample", "--json")
        payload = json.loads(output)
        self.assertEqual(code, 0)
        self.assertEqual(payload["pair_id"], "en-es")
        self.assertTrue(payload["source"])
        self.assertTrue(payload["target"])

    def test_ambient_is_opt_in(self) -> None:
        _, output = self.run_cli("ambient", "status", "--json")
        self.assertFalse(json.loads(output)["enabled"])

        _, output = self.run_cli(
            "ambient",
            "enable",
            "--pair",
            "en-ja",
            "--cadence",
            "7",
            "--json",
        )
        payload = json.loads(output)
        self.assertTrue(payload["enabled"])
        self.assertEqual(payload["active_pair"], "en-ja")
        self.assertEqual(payload["cadence"], 7)

        _, output = self.run_cli("ambient", "disable", "--json")
        self.assertFalse(json.loads(output)["enabled"])


if __name__ == "__main__":
    unittest.main()
