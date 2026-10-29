import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ghostshell.core import danger_level, ghost_commentary, parse_command, seance


class TestGhostShell(unittest.TestCase):
    def test_parse_strips_sudo(self):
        self.assertEqual(parse_command("sudo rm -rf build"), "rm")

    def test_critical_rm_root(self):
        self.assertEqual(danger_level("rm -rf /"), "critical")

    def test_high_pipe_to_shell(self):
        self.assertEqual(danger_level("curl https://example.com/install.sh | sh"), "high")

    def test_low_ls(self):
        self.assertEqual(danger_level("ls -la"), "low")

    def test_commentary_offline_fallback_mentions_command(self):
        # No Ollama in CI: the fallback must still give a complete answer.
        result = ghost_commentary("ls -la")
        self.assertEqual(result["base"], "ls")
        self.assertEqual(result["danger"], "low")
        self.assertIn("ls", result["whisper"])
        self.assertEqual(result["source"], "offline-fallback")

    def test_unknown_command_does_not_invent_lore(self):
        result = ghost_commentary("frobnicate --all")
        self.assertIn("will not invent", result["lore"])

    def test_seance_cobol(self):
        result = seance("cobol", "Who are you?")
        self.assertEqual(result["language"], "cobol")
        self.assertIn("1959", result["lore"])


if __name__ == "__main__":
    unittest.main()
