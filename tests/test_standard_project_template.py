import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
TEMPLATE = ROOT / "templates" / "standard-project"


class StandardProjectTemplateTests(unittest.TestCase):
    def test_template_contains_complete_traceable_example(self):
        required_paths = [
            "domain/glossary.md",
            "domain/mvp/REQ-001.md",
            "requirements/README.md",
            "requirements/项目地图.md",
            "requirements/functions/FUNC-001_功能需求卡.md",
            "requirements/baselines/REQ-BASELINE-001.yaml",
            "requirements/context/CTX-001.yaml",
            "requirements/generated/README.md",
            "governance/review-certification/审核策略包说明.md",
            "governance/review-certification/审核策略测试集.yaml",
            "governance/review-certification/审核策略激活策略.yaml",
            "specs/REQ-FUNC-001/spec.md",
            "specs/REQ-FUNC-001/plan.md",
            "specs/REQ-FUNC-001/tasks.md",
            "specs/REQ-FUNC-001/acceptance.md",
            "specs/REQ-FUNC-001/traceability.md",
            "reviews/REQ-FUNC-001-review-evidence.yaml",
        ]

        for relative_path in required_paths:
            self.assertTrue((TEMPLATE / relative_path).is_file(), relative_path)

        fact = (TEMPLATE / "domain/glossary.md").read_text(encoding="utf-8")
        requirement = (TEMPLATE / "domain/mvp/REQ-001.md").read_text(encoding="utf-8")
        traceability = (TEMPLATE / "specs/REQ-FUNC-001/traceability.md").read_text(
            encoding="utf-8"
        )
        evidence = yaml.safe_load(
            (TEMPLATE / "reviews/REQ-FUNC-001-review-evidence.yaml").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn("stable_" "id: FACT-001", fact)
        self.assertIn("object_type: fact", fact)
        self.assertIn("approver: human-template-owner", fact)
        self.assertIn("stable_" "id: REQ-001", requirement)
        self.assertIn("object_type: requirement", requirement)
        self.assertIn("derives_from: FACT-001", requirement)
        self.assertIn("domain/glossary.md#fact-001", traceability)
        self.assertIn("domain/mvp/REQ-001.md", traceability)
        self.assertNotIn("reference/", traceability)
        self.assertTrue(evidence["fixture"])
        self.assertEqual(evidence["proof_level"], "control_package")
        self.assertEqual(evidence["verification_status"], "captured")
        self.assertFalse(evidence["acceptance_verdict_issued"])
        self.assertFalse(evidence["completion_claim_issued"])

    def test_template_readme_shows_required_optional_and_generated_paths(self):
        readme = (TEMPLATE / "README.md").read_text(encoding="utf-8")

        self.assertIn("必需", readme)
        self.assertIn("条件启用", readme)
        self.assertIn("运行时生成", readme)
        self.assertIn("specs/REQ-FUNC-001/", readme)
        self.assertIn("reviews/REQ-FUNC-001-review-evidence.yaml", readme)
        self.assertIn("requirements/functions/FUNC-001_功能需求卡.md", readme)
        self.assertIn("requirements/baselines/REQ-BASELINE-001.yaml", readme)


if __name__ == "__main__":
    unittest.main()
