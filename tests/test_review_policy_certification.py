import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
AUTHORITY = ROOT / "docs" / "governance" / "REVIEW_POLICY_CERTIFICATION.md"
ADR = ROOT / "decisions" / "ADR-0005-certify-review-policy-before-activation.md"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class ReviewPolicyCertificationAuthorityTests(unittest.TestCase):
    def test_human_authority_is_registered_and_starts_with_reading_contract(self):
        self.assertTrue(AUTHORITY.is_file())
        text = AUTHORITY.read_text(encoding="utf-8")
        for label in ("解决的问题", "何时阅读", "输入", "输出", "下一步"):
            self.assertIn(label, text)

        project = load_yaml(ROOT / "project-os.yaml")
        self.assertEqual(
            project["authority"]["review_policy_certification"],
            "docs/governance/REVIEW_POLICY_CERTIFICATION.md",
        )
        self.assertIn(
            "REVIEW_POLICY_CERTIFICATION.md",
            (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "审核策略认证",
            (ROOT / "README.zh-CN.md").read_text(encoding="utf-8"),
        )

    def test_terms_are_unique_and_registered_without_new_state_axis(self):
        terminology = (ROOT / "docs" / "governance" / "TERMINOLOGY.md").read_text(
            encoding="utf-8"
        )
        project = load_yaml(ROOT / "project-os.yaml")
        expected = {
            "approval-route",
            "review-policy-bundle",
            "review-policy-certification",
        }
        for term_id in expected:
            self.assertEqual(
                len(re.findall(rf"term-id: `{re.escape(term_id)}`", terminology)),
                1,
            )
        self.assertTrue(expected <= set(project["terminology_manifest"]["required_term_ids"]))
        self.assertEqual(project["project_governance_catalog"]["base_profiles"], ["lite", "standard"])
        self.assertNotIn("critical", project["project_governance_catalog"]["base_profiles"])

    def test_execution_model_certifies_the_bundle_and_keeps_prompt_non_authoritative(self):
        text = (ROOT / "docs" / "architecture" / "AI_NATIVE_EXECUTION_MODEL.md").read_text(
            encoding="utf-8"
        )
        for token in (
            "审核策略包",
            "规则集",
            "Prompt",
            "Schema",
            "Context",
            "模型 fingerprint",
            "不是规则权威源",
            "policy_certified",
            "human_signoff",
        ):
            self.assertIn(token, text)

    def test_stage_gates_use_a_decision_gate_and_keep_human_signoff_for_high_risk(self):
        text = (ROOT / "docs" / "workflows" / "STAGE_EXIT_GATES.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Decision Gate", text)
        self.assertIn("policy_certified", text)
        self.assertIn("human_signoff", text)
        self.assertIn("不可逆外部动作", text)

    def test_architecture_decision_records_why_blanket_human_approval_is_rejected(self):
        self.assertTrue(ADR.is_file())
        text = ADR.read_text(encoding="utf-8")
        self.assertIn("状态：已接受", text)
        self.assertIn("固定人工批准", text)
        self.assertIn("policy_certified", text)
        self.assertIn("human_signoff", text)
        self.assertIn("AI 不能给自己的策略签发独立认证", text)


if __name__ == "__main__":
    unittest.main()
