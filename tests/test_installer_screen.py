"""Regression coverage for the out-of-curses install flow — print_only must
never persist state, matching the CLI equivalent it only prints."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import polyglot.storage as polyglot_storage
from polyglot.data.content_loader import get_pair
from polyglot.screens.installer_screen import run_install_flow


class PrintOnlyInstallFlowTests(unittest.TestCase):
    def test_print_only_does_not_change_active_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(polyglot_storage, "data_dir", return_value=Path(tmp)):
                polyglot_storage.set_active_pair_id("en-de")
                pair = get_pair("en-es")
                with patch("builtins.print"):
                    run_install_flow(pair, print_only=True)
                self.assertEqual(polyglot_storage.get_active_pair_id(), "en-de")

    def test_print_only_does_not_enable_ambient_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(polyglot_storage, "data_dir", return_value=Path(tmp)):
                pair = get_pair("en-es")
                with patch("builtins.print"):
                    run_install_flow(pair, print_only=True)
                self.assertFalse(polyglot_storage.load_config().get("ambient_enabled"))

    def test_print_only_never_prompts_for_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(polyglot_storage, "data_dir", return_value=Path(tmp)):
                pair = get_pair("en-es")
                with patch("builtins.print"), patch("builtins.input") as mock_input:
                    result = run_install_flow(pair, print_only=True)
                mock_input.assert_not_called()
                self.assertEqual(result, [])

    def test_confirmed_install_does_change_active_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(polyglot_storage, "data_dir", return_value=Path(tmp)):
                pair = get_pair("en-es")
                with patch("builtins.print"), patch("builtins.input", side_effect=EOFError):
                    run_install_flow(pair, auto_confirm=True, print_only=False)
                self.assertEqual(polyglot_storage.get_active_pair_id(), "en-es")
                self.assertTrue(polyglot_storage.load_config().get("ambient_enabled"))


if __name__ == "__main__":
    unittest.main()
