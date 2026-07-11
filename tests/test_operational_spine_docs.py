from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[1]

HUMAN_DOCS = (
    Path("docs/architecture/AI_PROJECT_OS_OVERVIEW.md"),
    Path("docs/workflows/PROJECT_DELIVERY_WORKFLOW.md"),
    Path("docs/workflows/STAGE_EXIT_GATES.md"),
    Path("docs/governance/TERMINOLOGY.md"),
    Path("docs/workflows/L2_ONBOARDING.md"),
    Path("docs/governance/DIAGRAM_CONVENTIONS.md"),
)

LINK_CHECK_DOCS = HUMAN_DOCS + (
    Path("README.zh-CN.md"),
    Path("docs/workflows/L2_PROGRESSION.md"),
    Path("docs/superpowers/plans/2026-07-10-minimum-implementation-draft.superseded.md"),
)

AUTHORITY_PATHS = {
    "overview": "docs/architecture/AI_PROJECT_OS_OVERVIEW.md",
    "project_delivery_workflow": "docs/workflows/PROJECT_DELIVERY_WORKFLOW.md",
    "stage_exit_gates": "docs/workflows/STAGE_EXIT_GATES.md",
    "terminology": "docs/governance/TERMINOLOGY.md",
}

TERM_IDS = {
    "source",
    "business-truth",
    "research",
    "framework-edition",
    "base-governance-profile",
    "overlay-capability",
    "governance-configuration",
    "lifecycle-stage",
    "work-status",
    "approval-status",
    "implementation-status",
    "proof-level",
    "invalidation-status",
    "business-chain",
    "engineering-chain",
    "capability-tree",
    "function-tree",
    "task-tree",
    "workflow",
    "skill",
    "tool",
    "spec",
    "run",
    "evidence",
    "verdict",
    "claim",
}

EXPECTED_HISTORICAL_PAYLOAD = {
    "checker": "check_controlled_objects",
    "version": "0.1.0",
    "scored_at": "2026-07-10",
    "executor": "ai-agent",
    "repo": "ai-project-os",
    "files_scanned": 55,
    "p0_count": 0,
    "p1_count": 0,
    "pass": True,
    "findings": [],
    "claim_limits": [
        "本 Evidence 证明 Phase 0 检查器在 L1 自身仓库上 EXIT=0",
        "不证明 L2 业务项目已接入（需 Phase 2 完成后补 phase2-l2-onboarding-evidence.yaml）",
        "不证明端到端业务链路运行（production_proof 仍不存在）",
        '设计态评分从 84 推进到预计 89（解除"无 Run/Evidence"封顶，"无跨项目隔离"89 封顶接着咬）',
    ],
    "reproducible_command": "python3 linters/check_controlled_objects.py . --report",
}

INVALIDATION_METADATA_KEYS = {
    "evidence_status",
    "stale_status",
    "current_scoring_authority",
    "invalidation_reason",
}


def read_text(relative_path: Path | str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def markdown_relative_links(markdown: str) -> list[str]:
    inline_targets = re.findall(
        r"!?\[[^\]]*\]\(\s*(<[^>\n]+>|(?:\\.|[^)\n])*)\s*\)",
        markdown,
    )
    reference_targets = re.findall(
        r"(?m)^\s{0,3}\[[^\]]+\]:\s*(<[^>\n]+>|\S+)",
        markdown,
    )
    links = []
    for raw_target in inline_targets + reference_targets:
        target_spec = raw_target.strip()
        if target_spec.startswith("<") and target_spec.endswith(">"):
            target = target_spec[1:-1]
        else:
            target = re.split(r"\s+(?=[\"'(])", target_spec, maxsplit=1)[0]
            target = target.replace(r"\ ", " ")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        if "{{" in target or "}}" in target:
            continue
        links.append(unquote(target.split("#", 1)[0].split("?", 1)[0]))
    return links


class OperationalSpineDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_os = yaml.safe_load(read_text("project-os.yaml"))

    def test_human_operational_docs_exist_and_start_with_reading_contract(self) -> None:
        for relative_path in HUMAN_DOCS:
            with self.subTest(path=str(relative_path)):
                text = read_text(relative_path)
                opening = "\n".join(text.splitlines()[:24])
                for label in ("解决的问题", "何时阅读", "输入", "输出", "下一步"):
                    self.assertIn(label, opening)

    def test_overview_keeps_four_non_collapsible_lines(self) -> None:
        text = read_text("docs/architecture/AI_PROJECT_OS_OVERVIEW.md")
        for heading in (
            "项目推进控制流",
            "产物追溯依赖链",
            "状态坐标",
            "框架和项目配置",
        ):
            self.assertRegex(text, rf"(?m)^### .*{heading}")
        self.assertIn("四条线不得合并", text)
        self.assertNotIn("edition_catalog:", text)
        self.assertNotIn("proof_level:", text)

    def test_delivery_workflow_preserves_causal_order_and_boundaries(self) -> None:
        text = read_text("docs/workflows/PROJECT_DELIVERY_WORKFLOW.md")
        expected_chain = (
            "批准需求/存量恢复 → 项目类型 → 治理路由 → 生命周期阶段 → 研究 → 业务链路 → ADR → "
            "工程链路 → Spec/Task → Workflow → Skill/Tool → Run → Evidence → Verdict → Claim → 复盘/升格"
        )
        self.assertIn(expected_chain, text)
        self.assertIn("能力树从业务链路推导", text)
        self.assertIn("任务树从已批准的 Spec 与验收判据推导", text)
        self.assertIn("Workflow 编排 Task", text)
        self.assertIn("Skill 是局部、可复用的能力", text)

    def test_stage_exit_gates_cover_all_nine_stages(self) -> None:
        text = read_text("docs/workflows/STAGE_EXIT_GATES.md")
        stages = ("R0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7")
        headings = re.findall(r"(?m)^## (R0|S[0-7])\b", text)
        self.assertEqual(headings, list(stages))
        for index, stage in enumerate(stages):
            start = text.index(f"## {stage}")
            end = text.find("\n## ", start + 1)
            section = text[start:] if end == -1 else text[start:end]
            with self.subTest(stage=stage):
                for field in ("输入", "产物", "退出门禁", "Evidence", "失效条件", "重开目标"):
                    self.assertIn(field, section)

    def test_terminology_has_unique_stable_term_ids_and_orthogonal_axes(self) -> None:
        text = read_text("docs/governance/TERMINOLOGY.md")
        term_ids = re.findall(r"(?m)^term-id:\s*`?([a-z0-9-]+)`?\s*$", text)
        self.assertEqual(len(term_ids), len(set(term_ids)))
        self.assertTrue(TERM_IDS.issubset(set(term_ids)))
        self.assertIn("生命周期阶段、工作状态、审批状态、实现状态、证据等级、失效状态互相正交", text)

    def test_l2_is_default_fact_and_run_scope_while_l3_is_optional(self) -> None:
        catalog = self.project_os["project_governance_catalog"]
        self.assertEqual(catalog["selection_scope"], "l2_system_or_optional_l3_instance")
        self.assertEqual(catalog["default_project_fact_scope"], "l2_system")
        self.assertEqual(catalog["optional_instance_scope"]["scope"], "l3_project_instance")
        self.assertEqual(
            catalog["optional_instance_scope"]["activation_requires"],
            "multi_instance_isolation_evidence",
        )

        readme = read_text("README.zh-CN.md")
        self.assertIn("项目事实、Run、Evidence 和交付物默认保存在 L2", readme)
        self.assertIn("`projects/{project_id}/` 仅在多实例隔离有证据时启用", readme)

    def test_project_os_registers_resolvable_operational_authorities(self) -> None:
        authority = self.project_os["authority"]
        for key, expected_path in AUTHORITY_PATHS.items():
            with self.subTest(key=key):
                self.assertEqual(authority[key], expected_path)
                self.assertTrue((ROOT / authority[key]).is_file())

    def test_current_score_and_proof_layers_do_not_overclaim(self) -> None:
        score = self.project_os["score_summary"]
        self.assertEqual(score["current_overall_score"], "not_evaluated")
        self.assertEqual(score["design_target_score"], 95.93)
        self.assertEqual(score["static_implementation_evidence"], "present_unscored")
        self.assertEqual(score["fixture_proof"], "not_evaluated")
        self.assertEqual(score["local_runtime_proof"], "not_evaluated")
        self.assertEqual(score["readonly_real_proof"], "not_evaluated")
        self.assertEqual(score["production_proof"], "not_evaluated")
        self.assertEqual(score["hard_gates"]["cross_project_isolation"], "unmet")
        self.assertEqual(score["hard_gates"]["second_heterogeneous_l2"], "unmet")
        self.assertNotIn("phase2_l2_onboarding", self.project_os["scoring_evidence"])

        readme = read_text("README.zh-CN.md")
        for forbidden in ("Phase 0 已完成", "当前评分 84", "当前评分 96", "预测 89", "预测 92"):
            self.assertNotIn(forbidden, readme)
        self.assertIn("当前总体评分：`not_evaluated`", readme)
        self.assertIn("设计目标分：`95.93`", readme)
        self.assertIn("成熟度字段不能证明运行能力", readme)

    def test_phase0_checker_evidence_is_historical_and_invalidated(self) -> None:
        evidence = yaml.safe_load(read_text("reviews/phase0-checker-evidence.yaml"))
        historical_payload = {
            key: value for key, value in evidence.items() if key not in INVALIDATION_METADATA_KEYS
        }
        self.assertEqual(historical_payload, EXPECTED_HISTORICAL_PAYLOAD)
        self.assertEqual(
            set(evidence) - set(EXPECTED_HISTORICAL_PAYLOAD),
            INVALIDATION_METADATA_KEYS,
        )
        self.assertEqual(evidence["evidence_status"], "historical_invalidated")
        self.assertFalse(evidence["current_scoring_authority"])
        self.assertIn("invalidation_reason", evidence)
        scoring_paths = set(self.project_os.get("scoring_evidence", {}).values())
        self.assertNotIn("reviews/phase0-checker-evidence.yaml", scoring_paths)

    def test_l2_onboarding_references_existing_standard_lock_template(self) -> None:
        onboarding = read_text("docs/workflows/L2_ONBOARDING.md")
        template_path = Path("templates/standard-project/project-os.lock.yaml")
        self.assertIn(str(template_path), onboarding)
        self.assertTrue((ROOT / template_path).is_file())

    def test_superseded_implementation_plan_is_preserved_outside_workflow_authority(self) -> None:
        stale_path = Path("docs/superpowers/plans/2026-07-10-minimum-implementation-draft.superseded.md")
        self.assertFalse((ROOT / "docs/workflows/IMPLEMENTATION_PLAN.md").exists())
        text = read_text(stale_path)
        self.assertIn("SUPERSEDED", text)
        self.assertIn("评分已过期", text)
        self.assertIn("# 最小实现计划", text)

    def test_human_entry_docs_have_no_broken_or_escaping_relative_links(self) -> None:
        root = ROOT.resolve()
        for relative_path in LINK_CHECK_DOCS:
            text = read_text(relative_path)
            for target in markdown_relative_links(text):
                resolved = (ROOT / relative_path.parent / target).resolve()
                with self.subTest(path=str(relative_path), target=target):
                    self.assertTrue(
                        resolved.is_relative_to(root),
                        f"relative link escapes repository: {relative_path} -> {target}",
                    )
                    self.assertTrue(resolved.exists(), f"broken relative link: {relative_path} -> {target}")


if __name__ == "__main__":
    unittest.main()
