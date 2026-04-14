import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from scripts import memory_manager as mm  # noqa: E402


class MemoryLockTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.assets_dir = self.root / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.root / "candidate_memory.json"
        self.state_template_path = self.assets_dir / "memory_schema.json"
        self.template_file = self.assets_dir / "memory_template.md"
        self.contract_file = self.assets_dir / "memory_contract.json"
        self.lock_file = self.root / "candidate_memory.json.lock"

        contract = {
            "type": "object",
            "additionalProperties": False,
            "required": ["version", "candidate_id", "static_profile"],
            "properties": {
                "version": {"type": "string", "enum": ["v2_agentic"]},
                "candidate_id": {"type": "string", "minLength": 1},
                "static_profile": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["metrics"],
                    "properties": {
                        "metrics": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["gpa", "stage1_cv_built"],
                            "properties": {
                                "gpa": {"type": ["number", "null"]},
                                "stage1_cv_built": {"type": "boolean"},
                            },
                        },
                    },
                },
            },
        }
        template = {
            "version": "v2_agentic",
            "candidate_id": "auto_generated",
            "static_profile": {
                "metrics": {
                    "gpa": None,
                    "stage1_cv_built": False,
                }
            },
        }

        self.state_template_path.write_text(
            json.dumps(template, indent=2),
            encoding="utf-8",
        )
        self.contract_file.write_text(
            json.dumps(contract, indent=2),
            encoding="utf-8",
        )
        self.template_file.write_text("# Human view only\n", encoding="utf-8")

        self.patches = [
            patch.object(mm, "ROOT_DIR", self.root),
            patch.object(mm, "REPO_ROOT", self.root),
            patch.object(mm, "ASSETS_DIR", self.assets_dir),
            patch.object(mm, "MEMORY_FILE", self.memory_file),
            patch.object(mm, "BACKUP_DIR", self.root / ".memory_backups"),
            patch.object(mm, "DEFAULT_TEMPLATE", self.state_template_path),
            patch.object(mm, "DEFAULT_CONTRACT", self.contract_file),
            patch.object(mm, "TEMPLATE_FILE", self.template_file),
            patch.object(mm, "CONTRACT_FILE", self.contract_file),
            patch.object(mm, "LEGACY_SCHEMA_FILE", self.state_template_path),
        ]
        for patcher in self.patches:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.tmpdir.cleanup()

    def test_memory_lock_creates_and_releases_lock_file(self):
        self.assertFalse(self.lock_file.exists())
        with mm.memory_lock():
            self.assertTrue(self.lock_file.exists())
        self.assertFalse(self.lock_file.exists())

    def test_bootstrap_memory_initializes_and_validates(self):
        issues = mm.bootstrap_memory()
        self.assertTrue(issues)
        self.assertEqual(issues, [])
        self.assertTrue(self.memory_file.exists())
        self.assertEqual(mm.validate_state(), [])

    def test_initialize_memory_refuses_to_overwrite_existing_file(self):
        mm.initialize_memory()
        original = json.loads(self.memory_file.read_text(encoding="utf-8"))
        original["candidate_id"] = "kept-by-test"
        self.memory_file.write_text(json.dumps(original, indent=2), encoding="utf-8")

        mm.initialize_memory()

        reloaded = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertEqual(reloaded["candidate_id"], "kept-by-test")


if __name__ == "__main__":
    unittest.main()
