from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from polyglot.ambient import detect_hook_host


ROOT = Path(__file__).resolve().parents[1]


class HostAdapterManifestTests(unittest.TestCase):
    def test_codex_and_claude_manifests_share_one_plugin_identity(self) -> None:
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(codex["name"], "polyglot")
        self.assertEqual(claude["name"], "polyglot")
        for manifest in (codex, claude):
            self.assertEqual(manifest["version"], "1.2.0")
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertEqual(manifest["hooks"], "./hooks/hooks.json")
            self.assertTrue((ROOT / manifest["skills"]).is_dir())
            self.assertTrue((ROOT / manifest["hooks"]).is_file())

    def test_shared_stop_hook_uses_bundled_stdlib_script(self) -> None:
        payload = json.loads((ROOT / "hooks/hooks.json").read_text())
        command = payload["hooks"]["Stop"][0]["hooks"][0]["command"]
        self.assertIn("scripts/ambient.py", command)
        self.assertIn("PLUGIN_ROOT", command)
        self.assertIn("CLAUDE_PLUGIN_ROOT", command)
        self.assertIn("CODEX_PLUGIN_ROOT", command)
        self.assertIn("--hook --host", command)
        self.assertIn("env -i", command)
        self.assertNotIn("polyglot ", command)
        self.assertNotIn("notify", command)

    def test_stop_hook_runs_from_each_host_root_without_global_cli(self) -> None:
        payload = json.loads((ROOT / "hooks/hooks.json").read_text())
        command = payload["hooks"]["Stop"][0]["hooks"][0]["command"]
        for root_variable in ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
            with self.subTest(root_variable=root_variable), tempfile.TemporaryDirectory(prefix="polyglot-hook-") as home:
                env = {"PATH": os.environ["PATH"], "HOME": home, root_variable: str(ROOT)}
                result = subprocess.run(command, check=True, capture_output=True, text=True, shell=True, env=env)
                # Disabled or unavailable state is a successful empty hook result.
                self.assertEqual(json.loads(result.stdout), {})

    def test_pi_package_has_native_extension_and_no_runtime_dependencies(self) -> None:
        package = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(package["name"], "ambient-polyglot")
        self.assertEqual(package["version"], "1.2.0")
        self.assertIn("pi-package", package["keywords"])
        self.assertEqual(package["pi"]["extensions"], ["./extensions/polyglot.ts"])
        self.assertNotIn("dependencies", package)
        extension = (ROOT / "extensions/polyglot.ts").read_text()
        self.assertIn('pi.on("agent_end"', extension)
        self.assertIn("ctx.ui.notify", extension)
        self.assertIn("childEnvironment", extension)
        self.assertNotIn("env: { ...process.env", extension)
        self.assertNotIn('startsWith("POLYGLOT_")', extension)
        self.assertNotIn("POLYGLOT_API_KEY", extension)

    def test_codex_fallback_root_is_attributed_to_codex(self) -> None:
        with patch.dict(os.environ, {"CODEX_PLUGIN_ROOT": str(ROOT)}, clear=True):
            self.assertEqual(detect_hook_host(), "codex")

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
