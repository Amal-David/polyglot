"""Real executable discovery; missing hosts are skips, never synthetic passes."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RealHostDiscoveryTests(unittest.TestCase):
    def _help(self, executable: str, *arguments: str) -> None:
        binary = os.environ.get(
            f"POLYGLOT_{executable.upper()}_BIN",
        ) or shutil.which(executable)
        if binary is None:
            self.skipTest(f"{executable} CLI is not installed; real-host smoke unavailable")
        with tempfile.TemporaryDirectory(prefix=f"polyglot-{executable}-host-") as home:
            environment = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": home,
                "CODEX_HOME": home,
                "CLAUDE_CONFIG_DIR": home,
            }
            result = subprocess.run([binary, *arguments], capture_output=True, text=True, env=environment, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_codex_discovery(self) -> None:
        self._help("codex", "exec", "--help")

    def test_claude_discovery(self) -> None:
        self._help("claude", "--help")

    def test_hermes_discovery(self) -> None:
        self._help("hermes", "--ignore-user-config", "--help")

    def test_real_hermes_loader_registers_namespaced_plugin_from_clean_cwd(self) -> None:
        python = os.environ.get("POLYGLOT_HERMES_PYTHON")
        if not python or not os.path.isfile(python):
            self.skipTest("set POLYGLOT_HERMES_PYTHON to the Hermes 0.16 Python")
        program = """
import os
from hermes_cli.plugins import PluginManager, PluginManifest

root = os.environ["PLUGIN_UNDER_TEST"]
manager = PluginManager()
manifest = PluginManifest(
    name="polyglot",
    source="user",
    path=root,
    key="polyglot",
)
manager._load_plugin(manifest)
loaded = manager._plugins["polyglot"]
assert loaded.enabled, loaded.error
assert "transform_llm_output" in manager._hooks
assert "polyglot:polyglot" in manager._plugin_skills
assert "polyglot" in manager._plugin_commands
"""
        with tempfile.TemporaryDirectory(prefix="polyglot-hermes-loader-") as home:
            environment = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": home,
                "XDG_DATA_HOME": os.path.join(home, "data"),
                "PLUGIN_UNDER_TEST": str(ROOT),
            }
            result = subprocess.run(
                [python, "-c", program],
                cwd=home,
                env=environment,
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pi_isolated_package_install(self) -> None:
        binary = shutil.which("pi")
        if binary is None:
            self.skipTest("pi CLI is not installed; isolated extension smoke unavailable")
        with tempfile.TemporaryDirectory(prefix="polyglot-pi-host-") as home:
            environment = {"PATH": os.environ.get("PATH", ""), "HOME": home}
            installed = subprocess.run([binary, "install", str(ROOT)], capture_output=True, text=True, env=environment, timeout=30)
            listed = subprocess.run([binary, "list"], capture_output=True, text=True, env=environment, timeout=15)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertIn("polyglot", listed.stdout)


if __name__ == "__main__":
    unittest.main()
