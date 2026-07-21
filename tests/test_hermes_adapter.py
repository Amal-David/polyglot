from __future__ import annotations

import unittest
from unittest.mock import patch

from polyglot.hermes import handle_command, register, transform_llm_output


class _Context:
    def __init__(self) -> None:
        self.hooks = {}
        self.skills = {}
        self.commands = {}

    def register_hook(self, name, callback) -> None:
        self.hooks[name] = callback

    def register_skill(self, name, path) -> None:
        self.skills[name] = path

    def register_command(self, name, handler, **metadata) -> None:
        self.commands[name] = (handler, metadata)


class HermesAdapterTests(unittest.TestCase):
    def test_registers_transform_and_canonical_skill(self) -> None:
        context = _Context()
        register(context)
        self.assertIn("transform_llm_output", context.hooks)
        self.assertEqual(context.skills["polyglot"].name, "SKILL.md")
        self.assertTrue(context.skills["polyglot"].is_file())
        self.assertIn("polyglot", context.commands)

    def test_transform_preserves_response_and_appends_phrase(self) -> None:
        with patch("polyglot.hermes.next_ambient_message", return_value="🌍 hola"):
            self.assertEqual(transform_llm_output("Done."), "Done.\n\n🌍 hola")

    def test_transform_failure_does_not_break_turn(self) -> None:
        with patch("polyglot.hermes.next_ambient_message", side_effect=OSError):
            self.assertIsNone(transform_llm_output("Done."))

    def test_command_reports_usage_for_bad_input(self) -> None:
        self.assertIn("Usage:", handle_command("enable not-a-pair"))


if __name__ == "__main__":
    unittest.main()
