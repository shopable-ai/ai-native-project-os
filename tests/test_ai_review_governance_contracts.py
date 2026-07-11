import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def load_policy(name: str) -> dict:
    return yaml.safe_load((ROOT / "policies" / name).read_text(encoding="utf-8"))


class GovernanceContractsTests(unittest.TestCase):
    def test_rule_set_contract_requires_human_approved_markdown_members(self):
        contract = load_policy("governance-rule-set-contract.yaml")

        self.assertEqual(contract["object_type"], "governance_rule_set")
        self.assertIn("approved_by", contract["required_fields"])
        self.assertIn("rule_refs", contract["required_fields"])
        self.assertIn("rule_hashes", contract["required_fields"])
        self.assertIn("active_requires_verified_human_principal", contract["invariants"])
        self.assertIn("canonical_path_and_rule_refs_must_reference_markdown", contract["invariants"])
        self.assertIn("rule_refs_and_hashes_have_same_cardinality", contract["invariants"])

    def test_rule_set_conflicts_fail_closed_by_explicit_priority(self):
        contract = load_policy("governance-rule-set-contract.yaml")

        self.assertIn("conflict_resolution", contract["required_fields"])
        self.assertEqual(
            contract["enums"]["conflict_resolution"],
            ["explicit_priority_then_fail_closed"],
        )
        self.assertIn("priority", contract["rule_required_fields"])
        self.assertIn("rule_priority_must_be_unique_within_scope", contract["invariants"])
        self.assertIn("unresolved_rule_conflict_blocks_activation", contract["invariants"])

    def test_ai_review_contract_has_closed_routes_and_rule_citations(self):
        contract = load_policy("ai-review-verdict-contract.yaml")

        self.assertEqual(
            contract["enums"]["decision"],
            ["pending", "allow", "rewrite_required", "blocked", "rule_gap"],
        )
        self.assertIn("every_finding_requires_resolvable_rule_ref", contract["invariants"])
        self.assertIn("rewrite_limit_exhaustion_requires_blocked", contract["invariants"])
        self.assertIn("human_authorization_cannot_override_blocked_review", contract["invariants"])
        self.assertIn("reviewer_must_be_independent_from_generator", contract["invariants"])

    def test_rule_gap_contract_keeps_human_maintenance_asynchronous(self):
        contract = load_policy("rule-gap-case-contract.yaml")
        project_os = yaml.safe_load((ROOT / "project-os.yaml").read_text(encoding="utf-8"))
        control_set = load_policy("control-set-contract.yaml")

        self.assertEqual(contract["object_type"], "rule_gap_case")
        self.assertIn("current_subject_disposition", contract["required_fields"])
        self.assertIn("rule_owner", contract["required_fields"])
        self.assertIn("current_subject_must_remain_blocked", contract["invariants"])
        self.assertIn("case_must_not_become_per_item_human_review", contract["invariants"])
        self.assertEqual(
            project_os["authority"]["rule_gap_case_contract"],
            "policies/rule-gap-case-contract.yaml",
        )
        self.assertIn(
            "rule-gap-case-contract",
            control_set["manifest_example"]["base_control_refs_by_category"][
                "ai_automated_review"
            ],
        )

    def test_authority_documents_define_three_distinct_responsibilities(self):
        controlled = (ROOT / "docs/governance/CONTROLLED_OBJECT_MODEL.md").read_text(encoding="utf-8")
        native = (ROOT / "docs/architecture/AI_NATIVE_EXECUTION_MODEL.md").read_text(encoding="utf-8")
        authorization = (
            ROOT / "docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md"
        ).read_text(encoding="utf-8")
        run_evidence = (ROOT / "docs/governance/RUN_EVIDENCE_ACCEPTANCE.md").read_text(
            encoding="utf-8"
        )
        states = (
            ROOT / "docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md"
        ).read_text(encoding="utf-8")
        scoring = (ROOT / "docs/governance/GATES_PROOF_SCORING.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("`governance_rule_set`", controlled)
        self.assertIn("`ai_review_verdict`", controlled)
        self.assertIn("`rule_gap_case`", controlled)
        self.assertIn("普通内容审核不得进入 `waiting_approval`", native)
        self.assertIn("内容审核通过不授予动作权限", authorization)
        self.assertIn("ai_review_verdict_ref", run_evidence)
        self.assertIn("普通内容审核不得使用 `waiting_approval`", states)
        self.assertIn("ai_review_gate_pass", scoring)
        self.assertTrue((ROOT / "decisions/ADR-0003-human-governed-ai-review.md").exists())

    def test_machine_authority_policies_and_chinese_rule_templates_align(self):
        project_os = yaml.safe_load((ROOT / "project-os.yaml").read_text(encoding="utf-8"))
        control_set = load_policy("control-set-contract.yaml")
        routing = load_policy("project-governance-routing.yaml")
        authorization = load_policy("authorization-snapshot-contract.yaml")
        acceptance = load_policy("acceptance-verdict-claim-contract.yaml")

        self.assertEqual(
            project_os["authority"]["governance_rule_set_contract"],
            "policies/governance-rule-set-contract.yaml",
        )
        self.assertEqual(
            project_os["authority"]["ai_review_verdict_contract"],
            "policies/ai-review-verdict-contract.yaml",
        )
        required = control_set["base_profile_contracts"]["standard"][
            "required_control_categories"
        ]
        self.assertIn("human_rule_governance", required)
        self.assertIn("ai_automated_review", required)
        self.assertEqual(
            routing["review_routing"]["routine_content_review"], "ai_automated"
        )
        self.assertIn(
            "approval_ticket_authorizes_action_not_content",
            authorization["validity_invariants"],
        )
        self.assertIn(
            "ai_review_verdict_refs", acceptance["acceptance_verdict_required_fields"]
        )
        self.assertIn(
            "accepted_subject_governed_by_ai_review_requires_allow_verdict",
            acceptance["verdict_invariants"],
        )

        rules_dir = ROOT / "templates/standard-project/governance/rules"
        expected_files = {
            "审核规则集说明.md",
            "内容与证据审核规则.md",
            "风险与发布审核规则.md",
            "多语言与项目一致性审核规则.md",
        }
        self.assertEqual({path.name for path in rules_dir.glob("*.md")}, expected_files)
        manifest = (rules_dir / "审核规则集说明.md").read_text(encoding="utf-8")
        self.assertIn("rule_set_id:", manifest)
        self.assertIn("approved_by:", manifest)
        self.assertIn("rule_refs:", manifest)
        for name in expected_files - {"审核规则集说明.md"}:
            rule_text = (rules_dir / name).read_text(encoding="utf-8")
            self.assertIn("rule_id:", rule_text)
            self.assertIn("priority:", rule_text)
            self.assertIn("canonical_path:", rule_text)

    def test_review_and_score_evidence_keep_runtime_claims_unproven(self):
        project_os = yaml.safe_load((ROOT / "project-os.yaml").read_text(encoding="utf-8"))
        review = yaml.safe_load(
            (ROOT / "reviews/human-governed-ai-review-adversarial.yaml").read_text(
                encoding="utf-8"
            )
        )
        score = yaml.safe_load(
            (ROOT / "reviews/human-governed-ai-review-score.yaml").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(review["review_type"], "self_adversarial_static_review")
        self.assertEqual(review["reviewer_independence"], "not_independent")
        self.assertEqual(review["verification"]["unit_tests"], "14_passed")
        self.assertEqual(review["verification"]["checker_files_scanned"], 71)
        self.assertEqual(review["verification"]["checker_findings"], "p0_0_p1_0")
        self.assertEqual(score["design_target_score"], 96)
        self.assertEqual(score["current_design_evidence_score"], "not_evaluated")
        self.assertEqual(score["static_implementation_score"], "not_evaluated")
        self.assertEqual(score["local_runtime_proof_score"], "not_evaluated")
        self.assertEqual(score["production_proof_score"], "not_evaluated")
        self.assertEqual(score["proof_level_ceiling"], "contract_tests_ready")
        self.assertIn(
            "reviews/human-governed-ai-review-adversarial.yaml",
            project_os["review_evidence"]["human_governed_ai_review"],
        )
        self.assertEqual(
            project_os["scoring_evidence"]["human_governed_ai_review"],
            "reviews/human-governed-ai-review-score.yaml",
        )


if __name__ == "__main__":
    unittest.main()
