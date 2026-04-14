import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "memory_manager.py"
SPEC = importlib.util.spec_from_file_location("memory_manager", MODULE_PATH)
memory_manager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(memory_manager)


class MemoryManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.assets_dir = self.root / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.root / "candidate_memory.json"
        self.state_template_path = self.assets_dir / "memory_schema.json"
        self.template_file = self.assets_dir / "memory_template.md"
        self.contract_path = self.assets_dir / "memory_contract.json"
        self.backup_dir = self.root / ".memory_backups"

        self.schema = {
            "version": "v2_agentic",
            "candidate_id": "auto_generated",
            "static_profile": {
                "intent": None,
                "metrics": {
                    "gpa": None,
                    "ranking": None,
                    "scale": None,
                },
                "funding_constraints": {
                    "requires_full_funding": True,
                    "accepts_csc": False,
                    "self_funded_budget_usd": 0,
                },
                "current_institution": {
                    "name": None,
                    "tier": None,
                    "location": None,
                },
            },
            "academic_arsenal": {
                "language_scores": {
                    "ielts_toefl": None,
                    "gre": None,
                },
                "publications": [],
                "core_skills": [],
            },
            "risk_thresholds": {
                "dealbreakers": [],
                "preferred_regions": [],
            },
            "pipeline_status": {
                "stage0_language_cleared": False,
                "stage1_cv_built": False,
                "stage2_target_pool": [],
                "stage3_pitch_sent": 0,
                "stage4_materials_locked": False,
                "stage5_6_offers_pending": 0,
                "final_offer_accepted": None,
            },
        }
        self.contract = {
            "type": "object",
            "additionalProperties": False,
            "required": list(self.schema.keys()),
            "properties": {
                "version": {"type": "string", "enum": ["v2_agentic"]},
                "candidate_id": {"type": "string", "minLength": 1},
                "static_profile": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["intent", "metrics", "funding_constraints", "current_institution"],
                    "properties": {
                        "intent": {"type": ["string", "null"]},
                        "metrics": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["gpa", "ranking", "scale"],
                            "properties": {
                                "gpa": {"type": ["number", "null"]},
                                "ranking": {"type": ["string", "number", "null"]},
                                "scale": {"type": ["string", "number", "null"]},
                            },
                        },
                        "funding_constraints": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "requires_full_funding",
                                "accepts_csc",
                                "self_funded_budget_usd",
                            ],
                            "properties": {
                                "requires_full_funding": {"type": "boolean"},
                                "accepts_csc": {"type": "boolean"},
                                "self_funded_budget_usd": {"type": "number", "minimum": 0},
                            },
                        },
                        "current_institution": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "tier", "location"],
                            "properties": {
                                "name": {"type": ["string", "null"]},
                                "tier": {"type": ["string", "null"]},
                                "location": {"type": ["string", "null"]},
                            },
                        },
                    },
                },
                "academic_arsenal": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["language_scores", "publications", "core_skills"],
                    "properties": {
                        "language_scores": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["ielts_toefl", "gre"],
                            "properties": {
                                "ielts_toefl": {"type": ["string", "object", "null"]},
                                "gre": {"type": ["string", "object", "null"]},
                            },
                        },
                        "publications": {
                            "type": "array",
                            "items": {"type": ["string", "object"]},
                        },
                        "core_skills": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "risk_thresholds": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["dealbreakers", "preferred_regions"],
                    "properties": {
                        "dealbreakers": {"type": "array", "items": {"type": "string"}},
                        "preferred_regions": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "pipeline_status": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "stage0_language_cleared",
                        "stage1_cv_built",
                        "stage2_target_pool",
                        "stage3_pitch_sent",
                        "stage4_materials_locked",
                        "stage5_6_offers_pending",
                        "final_offer_accepted",
                    ],
                    "properties": {
                        "stage0_language_cleared": {"type": "boolean"},
                        "stage1_cv_built": {"type": "boolean"},
                        "stage2_target_pool": {
                            "type": "array",
                            "items": {"type": ["string", "object"]},
                        },
                        "stage3_pitch_sent": {"type": "integer", "minimum": 0},
                        "stage4_materials_locked": {"type": "boolean"},
                        "stage5_6_offers_pending": {"type": "integer", "minimum": 0},
                        "final_offer_accepted": {"type": ["string", "null"]},
                    },
                },
            },
        }

        self.state_template_path.write_text(
            json.dumps(self.schema, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.contract_path.write_text(
            json.dumps(self.contract, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.template_file.write_text(
            "# Human view only\n",
            encoding="utf-8",
        )

        self.patches = [
            patch.object(memory_manager, "ROOT_DIR", self.root),
            patch.object(memory_manager, "REPO_ROOT", self.root),
            patch.object(memory_manager, "ASSETS_DIR", self.assets_dir),
            patch.object(memory_manager, "MEMORY_FILE", self.memory_file),
            patch.object(memory_manager, "BACKUP_DIR", self.backup_dir),
            patch.object(memory_manager, "DEFAULT_TEMPLATE", self.state_template_path),
            patch.object(memory_manager, "DEFAULT_CONTRACT", self.contract_path),
            patch.object(memory_manager, "TEMPLATE_FILE", self.template_file),
            patch.object(memory_manager, "CONTRACT_FILE", self.contract_path),
            patch.object(memory_manager, "LEGACY_SCHEMA_FILE", self.state_template_path),
        ]
        for patcher in self.patches:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp_dir.cleanup()

    def test_initialize_memory_creates_file_from_state_template(self):
        created = memory_manager.initialize_memory()

        self.assertEqual(created, self.memory_file)
        self.assertEqual(
            json.loads(self.memory_file.read_text(encoding="utf-8")),
            self.schema,
        )

    def test_bootstrap_memory_initializes_and_validates(self):
        bootstrapped = memory_manager.bootstrap_memory()

        self.assertTrue(bootstrapped)
        self.assertEqual(bootstrapped, [])
        self.assertTrue(self.memory_file.exists())
        self.assertEqual(memory_manager.validate_state(), [])

    def test_update_field_updates_existing_path_and_creates_backup(self):
        memory_manager.initialize_memory()

        updated = memory_manager.update_field("static_profile -> metrics -> gpa", 3.9)

        self.assertTrue(updated)
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertEqual(state["static_profile"]["metrics"]["gpa"], 3.9)
        backups = list(self.backup_dir.glob("memory_backup_*.json"))
        self.assertEqual(len(backups), 1)

    def test_update_field_accepts_iterable_path_segments(self):
        memory_manager.initialize_memory()

        updated = memory_manager.update_field(["pipeline_status", "stage3_pitch_sent"], 2)

        self.assertTrue(updated)
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertEqual(state["pipeline_status"]["stage3_pitch_sent"], 2)

    def test_update_field_rejects_unknown_path(self):
        memory_manager.initialize_memory()

        updated = memory_manager.update_field("static_profile -> metrics -> missing_key", "bad")

        self.assertFalse(updated)
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertNotIn("missing_key", state["static_profile"]["metrics"])

    def test_update_field_rejects_wrong_type_when_schema_is_typed(self):
        memory_manager.initialize_memory()

        updated = memory_manager.update_field("pipeline_status -> stage1_cv_built", "yes")

        self.assertFalse(updated)
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertFalse(state["pipeline_status"]["stage1_cv_built"])

    def test_update_field_rejects_wrong_type_for_nullable_contract_field(self):
        memory_manager.initialize_memory()

        updated = memory_manager.update_field("static_profile -> metrics -> gpa", "excellent")

        self.assertFalse(updated)
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertIsNone(state["static_profile"]["metrics"]["gpa"])

    def test_validate_state_reports_missing_key(self):
        memory_manager.initialize_memory()
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        del state["pipeline_status"]["stage1_cv_built"]
        self.memory_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        issues = memory_manager.validate_state()

        self.assertTrue(
            any("missing required key 'stage1_cv_built'" in issue for issue in issues)
        )

    def test_validate_state_reports_unexpected_key(self):
        memory_manager.initialize_memory()
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        state["pipeline_status"]["rogue_flag"] = True
        self.memory_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        issues = memory_manager.validate_state()

        self.assertTrue(any("unexpected key 'rogue_flag'" in issue for issue in issues))

    def test_validate_state_reports_min_length_violation(self):
        memory_manager.initialize_memory()
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        state["candidate_id"] = ""
        self.memory_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        issues = memory_manager.validate_state()

        self.assertTrue(any("length must be >= 1" in issue for issue in issues))


    def test_initialize_memory_handles_malformed_template(self):
        self.state_template_path.write_text("NOT JSON", encoding="utf-8")
        created = memory_manager.initialize_memory()
        self.assertEqual(created, self.memory_file)
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertIn("version", state)

    def test_update_field_returns_false_when_memory_file_missing(self):
        updated = memory_manager.update_field("static_profile -> metrics -> gpa", 3.9)
        self.assertFalse(updated)

    def test_update_field_returns_false_when_memory_file_corrupted(self):
        self.memory_file.write_text("NOT JSON", encoding="utf-8")
        updated = memory_manager.update_field("static_profile -> metrics -> gpa", 3.9)
        self.assertFalse(updated)

    def test_create_backup_raises_when_no_memory_file(self):
        with self.assertRaises(FileNotFoundError):
            memory_manager.create_backup()

    def test_validate_state_reports_type_mismatch_via_contract(self):
        memory_manager.initialize_memory()
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        state["version"] = 42
        self.memory_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        issues = memory_manager.validate_state()
        self.assertTrue(any("version" in issue and "invalid type" in issue for issue in issues))

    def test_main_returns_error_on_no_args(self):
        exit_code = memory_manager.main([])
        self.assertEqual(exit_code, 1)

    def test_main_update_succeeds(self):
        memory_manager.initialize_memory()
        exit_code = memory_manager.main(["update", "static_profile -> metrics -> gpa", "3.9"])
        self.assertEqual(exit_code, 0)
        state = json.loads(self.memory_file.read_text(encoding="utf-8"))
        self.assertEqual(state["static_profile"]["metrics"]["gpa"], 3.9)


if __name__ == "__main__":
    unittest.main()
