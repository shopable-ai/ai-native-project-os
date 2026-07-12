import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / "docs" / "workflows" / "REQUIREMENT_DESIGN_WORKFLOW.md"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def section(text: str, heading: str, next_heading: str | None = None) -> str:
    start = text.index(heading)
    if next_heading is None:
        return text[start:]
    end = text.index(next_heading, start + len(heading))
    return text[start:end]


class RequirementDesignAuthorityTests(unittest.TestCase):
    def test_requirement_design_workflow_is_registered_human_authority(self):
        self.assertTrue(WORKFLOW.is_file())
        text = WORKFLOW.read_text(encoding="utf-8")
        for label in ("解决的问题", "何时阅读", "输入", "输出", "下一步"):
            self.assertIn(label, text)
        project_os = load_yaml(ROOT / "project-os.yaml")
        self.assertEqual(
            project_os["authority"]["requirement_design_workflow"],
            "docs/workflows/REQUIREMENT_DESIGN_WORKFLOW.md",
        )
        self.assertIn("REQUIREMENT_DESIGN_WORKFLOW.md", (ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("需求设计工作流", (ROOT / "README.zh-CN.md").read_text(encoding="utf-8"))

    def test_human_reasoning_flow_precedes_adr_spec_and_execution(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        canonical_flow = (
            "Source → Fact / Unknown → Requirement → Scenario → Business Chain "
            "→ Capability → Function → Functional Requirement → Human Approval "
            "→ Requirement Baseline → Research / ADR → Engineering Design → Spec"
        )
        self.assertIn(canonical_flow, workflow)

        delivery = (ROOT / "docs/workflows/PROJECT_DELIVERY_WORKFLOW.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "业务链路 → 能力树 → 功能树 → 功能级需求 → 人工批准与需求基线 → ADR → 工程设计 → Spec",
            delivery,
        )
        self.assertIn("AI 生成的 draft 不能自行升格", delivery)

    def test_requirement_remains_one_object_type_with_kinds(self):
        model = (ROOT / "docs/governance/CONTROLLED_OBJECT_MODEL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("requirement_kind", model)
        for kind in ("objective", "business", "functional", "quality_attribute", "constraint"):
            self.assertIn(f"`{kind}`", model)
        self.assertIn("functional_requirement", model)
        self.assertIn("context_snapshot", model)
        self.assertIn("AI 不能批准或冻结需求基线", model)

    def test_stage_gates_put_intent_approval_before_spec(self):
        gates = (ROOT / "docs/workflows/STAGE_EXIT_GATES.md").read_text(
            encoding="utf-8"
        )
        s0 = section(gates, "## S0", "## S1")
        s2 = section(gates, "## S2", "## S3")
        s5 = section(gates, "## S5", "## S6")
        for token in ("original_intent", "approved_intent", "需求基线"):
            self.assertIn(token, s0)
        for token in ("功能需求卡", "AI 自检", "人工批准"):
            self.assertIn(token, s2)
        for token in ("功能需求", "version", "content_hash", "需求基线"):
            self.assertIn(token, s5)
        self.assertIn("未批准", s5)
        self.assertIn("fail closed", s5)

    def test_terminology_adds_human_reasoning_terms_without_new_state_axis(self):
        terminology = (ROOT / "docs/governance/TERMINOLOGY.md").read_text(
            encoding="utf-8"
        )
        project_os = load_yaml(ROOT / "project-os.yaml")
        expected_terms = {
            "intent-verification",
            "functional-requirement",
            "requirement-baseline",
            "context-snapshot",
            "project-map",
        }
        for term_id in expected_terms:
            self.assertEqual(len(re.findall(rf"term-id: `{re.escape(term_id)}`", terminology)), 1)
        self.assertTrue(expected_terms <= set(project_os["terminology_manifest"]["required_term_ids"]))
        self.assertEqual(project_os["project_governance_catalog"]["base_profiles"], ["lite", "standard"])
        self.assertNotIn("critical", project_os["project_governance_catalog"]["base_profiles"])

    def test_artifact_model_separates_requirement_card_from_spec_package(self):
        artifact_model = (ROOT / "docs/governance/ARTIFACTS_AND_TRACEABILITY.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("功能需求卡", artifact_model)
        self.assertIn("人类第一次理解功能", artifact_model)
        self.assertIn("不复制 Spec 五件套", artifact_model)
        self.assertIn("已批准实现约束", artifact_model)
        self.assertIn("候选实现要点", artifact_model)

    def test_overview_and_l2_progression_route_humans_through_requirement_design(self):
        overview = (ROOT / "docs/architecture/AI_PROJECT_OS_OVERVIEW.md").read_text(
            encoding="utf-8"
        )
        progression = (ROOT / "docs/workflows/L2_PROGRESSION.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("需求设计工作流", overview)
        self.assertIn("功能需求", overview)
        self.assertIn("需求设计工作流", progression)
        self.assertIn("功能需求卡", progression)
        self.assertIn("批准需求基线", progression)


if __name__ == "__main__":
    unittest.main()
