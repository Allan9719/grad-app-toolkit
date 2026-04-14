import json
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
README_PATH = ROOT_DIR / "README.md"
SKILL_PATH = ROOT_DIR / "SKILL.md"
TRAE_RULES_PATH = ROOT_DIR / ".traerules"
CLAUDE_PLUGIN_PATH = ROOT_DIR / ".claude-plugin"
REFERENCE_DIR = ROOT_DIR / "references"

EXPECTED_COMMAND_ROUTES = {
    "ielts-toefl-coach": "references/stage0_language_coach.md",
    "grad-profile-analyzer": "references/stage1_profile_analyzer.md",
    "global-lab-detective": "references/stage2_lab_detective.md",
    "cold-pitch-tactician": "references/stage3_cold_pitch.md",
    "sop-proposal-architect": "references/stage4_sop_architect.md",
    "defense-simulator": "references/stage5_6_defense_and_offer.md",
    "offer-negotiation-desk": "references/stage5_6_defense_and_offer.md",
}


class ProtocolConsistencyTests(unittest.TestCase):
    def test_claude_plugin_commands_match_expected_routes(self):
        plugin = json.loads(CLAUDE_PLUGIN_PATH.read_text(encoding="utf-8"))
        commands = plugin["commands"]

        self.assertEqual(set(commands), set(EXPECTED_COMMAND_ROUTES))
        for command_name, reference_path in EXPECTED_COMMAND_ROUTES.items():
            self.assertIn(reference_path, commands[command_name])
            self.assertTrue((ROOT_DIR / reference_path).exists(), reference_path)

    def test_readme_and_skill_mention_all_slash_commands(self):
        readme = README_PATH.read_text(encoding="utf-8")
        skill = SKILL_PATH.read_text(encoding="utf-8")

        for command_name in EXPECTED_COMMAND_ROUTES:
            slash_command = f"/{command_name}"
            self.assertIn(slash_command, readme)
            self.assertIn(slash_command, skill)

    def test_shared_state_protocol_uses_candidate_memory_json(self):
        paths_to_scan = [
            README_PATH,
            SKILL_PATH,
            TRAE_RULES_PATH,
            *sorted(REFERENCE_DIR.glob("*.md")),
        ]

        for path in paths_to_scan:
            contents = path.read_text(encoding="utf-8")
            self.assertNotRegex(contents, r'\bmemory\.md\b', path.name)

        self.assertIn("candidate_memory.json", README_PATH.read_text(encoding="utf-8"))
        self.assertIn("candidate_memory.json", SKILL_PATH.read_text(encoding="utf-8"))
        self.assertIn("candidate_memory.json", TRAE_RULES_PATH.read_text(encoding="utf-8"))

    def test_memory_manager_commands_are_documented_consistently(self):
        readme = README_PATH.read_text(encoding="utf-8")
        skill = SKILL_PATH.read_text(encoding="utf-8")

        expected_commands = [
            "python scripts/memory_manager.py init",
            "python scripts/memory_manager.py read",
            "python scripts/memory_manager.py validate",
            "python scripts/memory_manager.py bootstrap",
            "python scripts/memory_manager.py update",
        ]

        for command in expected_commands:
            self.assertIn(command, skill)

        for command in [
            "python scripts/memory_manager.py init",
            "python scripts/memory_manager.py validate",
        ]:
            self.assertIn(command, readme)

    def test_traerules_mentions_all_reference_paths(self):
        trae_rules = TRAE_RULES_PATH.read_text(encoding="utf-8")
        unique_paths = set(EXPECTED_COMMAND_ROUTES.values())
        for reference_path in unique_paths:
            self.assertIn(reference_path, trae_rules, f".traerules missing reference to {reference_path}")


if __name__ == "__main__":
    unittest.main()
