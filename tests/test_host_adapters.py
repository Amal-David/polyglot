from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HostAdapterManifestTests(unittest.TestCase):
    def test_codex_and_claude_manifests_share_one_plugin_identity(self) -> None:
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(codex["name"], "polyglot")
        self.assertEqual(claude["name"], "polyglot")
        self.assertEqual(codex["version"], "1.0.0")
        self.assertEqual(claude["version"], "1.0.0")
        self.assertEqual(codex["skills"], "./skills/")
        self.assertEqual(codex["hooks"], "./hooks/hooks.json")
        self.assertTrue((ROOT / codex["skills"]).is_dir())
        self.assertTrue((ROOT / codex["hooks"]).is_file())

    def test_shared_stop_hook_uses_bundled_stdlib_script(self) -> None:
        payload = json.loads((ROOT / "hooks/hooks.json").read_text())
        command = payload["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/scripts/ambient.py", command)
        self.assertIn("--hook --host auto", command)
        self.assertNotIn("notify", command)

    def test_codex_stop_hook_runs_with_compatibility_roots(self) -> None:
        payload = json.loads((ROOT / "hooks/hooks.json").read_text())
        command = payload["hooks"]["Stop"][0]["hooks"][0]["command"]
        with tempfile.TemporaryDirectory(prefix="polyglot-codex-hook-") as home:
            env = {
                **os.environ,
                "HOME": home,
                "PLUGIN_ROOT": str(ROOT),
                "CLAUDE_PLUGIN_ROOT": str(ROOT),
            }
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/ambient.py"),
                    "--enable",
                    "--pair",
                    "en-es",
                    "--cadence",
                    "1",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                shell=True,
                env=env,
            )
        self.assertTrue(json.loads(result.stdout)["systemMessage"])

    def test_pi_package_has_native_extension_and_no_runtime_dependencies(self) -> None:
        package = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(package["name"], "ambient-polyglot")
        self.assertEqual(package["version"], "1.0.0")
        self.assertIn("pi-package", package["keywords"])
        self.assertEqual(package["pi"]["extensions"], ["./extensions/polyglot.ts"])
        self.assertNotIn("dependencies", package)
        extension = (ROOT / "extensions/polyglot.ts").read_text()
        self.assertIn('pi.on("agent_end"', extension)
        self.assertIn("ctx.ui.notify", extension)

    def test_canonical_skill_is_present_once(self) -> None:
        skills = list(ROOT.glob("**/SKILL.md"))
        self.assertEqual(skills, [ROOT / "skills/polyglot/SKILL.md"])
        self.assertTrue((ROOT / "skills/polyglot/agents/openai.yaml").is_file())

    def test_python_sources_do_not_import_legacy_package(self) -> None:
        legacy_package = "terminal" + "_arcade"
        offenders = [
            path
            for path in ROOT.rglob("*.py")
            if ".git" not in path.parts and legacy_package in path.read_text()
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
