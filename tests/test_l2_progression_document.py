import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


class L2ProgressionDocumentTests(unittest.TestCase):
    def test_l2_progression_connects_onboarding_to_every_lifecycle_stage(self):
        progression_path = ROOT / "docs/workflows/L2_PROGRESSION.md"

        self.assertTrue(progression_path.is_file())
        text = progression_path.read_text(encoding="utf-8")
        for stage in ["R0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
            self.assertIn(f"| `{stage}` |", text)
        for authority in [
            "L2_ONBOARDING.md",
            "PROJECT_LIFECYCLE.md",
            "PROJECT_TYPE_AND_GOVERNANCE_ROUTING.md",
            "STATE_TRANSITIONS_AND_INVALIDATION.md",
            "GATES_PROOF_SCORING.md",
            "RUN_EVIDENCE_ACCEPTANCE.md",
        ]:
            self.assertIn(authority, text)
        self.assertIn("失败后重开", text)
        self.assertIn("Evidence 保存在 L2", text)

    def test_l2_progression_is_registered_as_an_authority_entry(self):
        project_os = yaml.safe_load((ROOT / "project-os.yaml").read_text(encoding="utf-8"))
        readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

        self.assertEqual(
            project_os["authority"]["l2_progression"],
            "docs/workflows/L2_PROGRESSION.md",
        )
        self.assertIn("docs/workflows/L2_PROGRESSION.md", readme)

    def test_progression_places_behavior_specification_and_test_space_without_new_stages(self):
        text = (ROOT / "docs/workflows/L2_PROGRESSION.md").read_text(encoding="utf-8")

        self.assertIn("Behavior Specification", text)
        self.assertIn("Behavior Case", text)
        self.assertIn("Test Space Modeling", text)
        self.assertIn("S3 只在存在架构选择时", text)
        self.assertIn("稳定 Behavior Case ID", text)
        self.assertIn("actual_result", text)
        self.assertIn("Run/Evidence/Verdict/Claim", text)
        self.assertIn("As-Is/To-Be", text)
        self.assertNotIn("S2.5", text)
        self.assertNotIn("S4.5", text)


if __name__ == "__main__":
    unittest.main()
