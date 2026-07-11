import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def load_policy(name: str) -> dict:
    return yaml.safe_load((ROOT / "policies" / name).read_text(encoding="utf-8"))


class GovernanceContractsTests(unittest.TestCase):
    def test_rule_set_contract_requires_human_approved_active_markdown(self):
        contract = load_policy("governance-rule-set-contract.yaml")
        self.assertEqual(contract["object_type"], "governance_rule_set")
        self.assertIn("approved_by", contract["required_fields"])
        self.assertIn("rule_ids", contract["required_fields"])
        self.assertIn("active_requires_verified_human_principal", contract["invariants"])
        self.assertIn("canonical_path_must_reference_markdown", contract["invariants"])

    def test_rule_set_contract_fails_closed_on_rule_conflict(self):
        contract = load_policy("governance-rule-set-contract.yaml")
        self.assertIn("conflict_resolution", contract["required_fields"])
        self.assertEqual(
            contract["enums"]["conflict_resolution"],
            ["explicit_priority_then_fail_closed"],
        )
        self.assertIn("rule_priority_must_be_unique_within_scope", contract["invariants"])
        self.assertIn("unresolved_rule_conflict_blocks_activation", contract["invariants"])

    def test_ai_review_contract_has_four_terminal_routes_and_rule_citations(self):
        contract = load_policy("ai-review-verdict-contract.yaml")
        self.assertEqual(
            contract["enums"]["decision"],
            ["pending", "allow", "rewrite_required", "blocked", "rule_gap"],
        )
        self.assertIn("every_finding_requires_resolvable_rule_ref", contract["invariants"])
        self.assertIn("rewrite_limit_exhaustion_requires_blocked", contract["invariants"])
        self.assertIn("human_authorization_cannot_override_blocked_review", contract["invariants"])

    def test_rule_gap_contract_keeps_human_maintenance_asynchronous(self):
        contract = load_policy("rule-gap-case-contract.yaml")
        self.assertEqual(contract["object_type"], "rule_gap_case")
        self.assertIn("current_subject_disposition", contract["required_fields"])
        self.assertIn("rule_owner", contract["required_fields"])
        self.assertIn("current_subject_must_remain_blocked", contract["invariants"])
        self.assertIn("case_must_not_become_per_item_human_review", contract["invariants"])

    def test_authority_documents_define_three_distinct_responsibilities(self):
        controlled = (ROOT / "docs/governance/CONTROLLED_OBJECT_MODEL.md").read_text(
            encoding="utf-8"
        )
        native = (ROOT / "docs/architecture/AI_NATIVE_EXECUTION_MODEL.md").read_text(
            encoding="utf-8"
        )
        authorization = (
            ROOT / "docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`governance_rule_set`", controlled)
        self.assertIn("`ai_review_verdict`", controlled)
        self.assertIn("普通内容审核不得进入 `waiting_approval`", native)
        self.assertIn("内容审核通过不授予动作权限", authorization)

    def test_machine_authority_policies_and_template_are_aligned(self):
        project_os = yaml.safe_load((ROOT / "project-os.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            project_os["authority"]["governance_rule_set_contract"],
            "policies/governance-rule-set-contract.yaml",
        )
        self.assertEqual(
            project_os["authority"]["ai_review_verdict_contract"],
            "policies/ai-review-verdict-contract.yaml",
        )
        self.assertEqual(
            project_os["authority"]["rule_gap_case_contract"],
            "policies/rule-gap-case-contract.yaml",
        )

        control_set = load_policy("control-set-contract.yaml")
        standard_categories = control_set["base_profile_contracts"]["standard"][
            "required_control_categories"
        ]
        self.assertIn("human_rule_governance", standard_categories)
        self.assertIn("ai_automated_review", standard_categories)
        self.assertIn(
            "rule-gap-case-contract@1",
            control_set["manifest_example"]["base_control_refs_by_category"][
                "ai_automated_review"
            ],
        )

        routing = load_policy("project-governance-routing.yaml")
        self.assertEqual(routing["review_governance"]["routine_content_review"], "ai_automated")

        authorization = load_policy("authorization-snapshot-contract.yaml")
        self.assertIn(
            "approval_ticket_authorizes_action_not_content_quality",
            authorization["validity_invariants"],
        )

        acceptance = load_policy("acceptance-verdict-claim-contract.yaml")
        self.assertIn("ai_review_verdict_refs", acceptance["acceptance_verdict_required_fields"])
        self.assertIn(
            "review_governed_subject_requires_allow_ai_review_verdict",
            acceptance["verdict_invariants"],
        )

        template = (
            ROOT / "templates/standard-project/governance/rules/README.md"
        ).read_text(encoding="utf-8")
        for marker in (
            "rule_set_id",
            "rule_id",
            "priority",
            "approved_by",
            "canonical_path",
        ):
            self.assertIn(marker, template)


if __name__ == "__main__":
    unittest.main()
