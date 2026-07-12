import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
AUTHORITY = ROOT / "docs" / "governance" / "REVIEW_POLICY_CERTIFICATION.md"
ADR = ROOT / "decisions" / "ADR-0005-certify-review-policy-before-activation.md"
TEST_SUITE_CONTRACT = (
    ROOT / "contracts" / "governance" / "review-policy-test-suite-contract.yaml"
)
CERTIFICATION_CONTRACT = (
    ROOT / "contracts" / "governance" / "review-policy-certification-contract.yaml"
)
ACTIVATION_POLICY = ROOT / "policies" / "review-policy-activation-routing.yaml"


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


class ReviewPolicyCertificationContractTests(unittest.TestCase):
    def test_contracts_and_policy_are_registered_at_their_single_authorities(self):
        for path in (TEST_SUITE_CONTRACT, CERTIFICATION_CONTRACT, ACTIVATION_POLICY):
            self.assertTrue(path.is_file(), path)
        project = load_yaml(ROOT / "project-os.yaml")
        authority = project["authority"]
        self.assertEqual(
            authority["review_policy_test_suite_contract"],
            "contracts/governance/review-policy-test-suite-contract.yaml",
        )
        self.assertEqual(
            authority["review_policy_certification_contract"],
            "contracts/governance/review-policy-certification-contract.yaml",
        )
        self.assertEqual(
            authority["review_policy_activation_policy"],
            "policies/review-policy-activation-routing.yaml",
        )

    def test_test_suite_contract_preregisters_complete_adversarial_coverage(self):
        contract = load_yaml(TEST_SUITE_CONTRACT)
        categories = set(contract["enums"]["case_category"])
        self.assertTrue(
            {
                "positive",
                "negative",
                "boundary",
                "adversarial",
                "unknown",
                "rule_conflict",
                "stale_rule",
                "cross_project",
                "multilingual",
                "rewrite_limit",
                "recovery",
            }
            <= categories
        )
        self.assertTrue(
            {
                "input_ref",
                "input_hash",
                "expected_decision",
                "expected_rule_refs",
                "forbidden_decisions",
                "required_evidence",
                "risk_level",
                "repeat_count",
            }
            <= set(contract["case_required_fields"])
        )
        self.assertIn(
            "expectations_thresholds_and_repeat_counts_are_fixed_before_first_run",
            contract["invariants"],
        )
        self.assertIn(
            "nondeterministic_cases_require_repeat_count_at_least_configured_minimum",
            contract["invariants"],
        )

    def test_certification_contract_requires_all_runs_metrics_and_independent_verifier(self):
        contract = load_yaml(CERTIFICATION_CONTRACT)
        required = set(contract["required_fields"])
        self.assertTrue(
            {
                "subject_bundle_ref",
                "subject_bundle_hash",
                "test_suite_ref",
                "test_suite_hash",
                "run_refs",
                "evidence_refs",
                "metric_results",
                "threshold_results",
                "verifier_ref",
                "certification_decision",
                "eligible_activation_routes",
                "claim_ceiling",
                "invalidation_conditions",
            }
            <= required
        )
        self.assertEqual(
            contract["enums"]["activation_route"],
            ["policy_certified", "human_signoff"],
        )
        for invariant in (
            "certified_requires_every_required_threshold_passed",
            "all_attempts_must_be_included_or_excluded_with_reason",
            "verifier_must_be_independent_from_bundle_generator_and_review_runs",
            "ai_cannot_self_certify_its_own_policy_bundle",
        ):
            self.assertIn(invariant, contract["invariants"])

    def test_activation_policy_routes_low_risk_human_signoff_and_unknown_fail_closed(self):
        policy = load_yaml(ACTIVATION_POLICY)
        routes = policy["routes"]
        self.assertIn("policy_certified", routes)
        self.assertIn("human_signoff", routes)
        self.assertIn("blocked", routes)
        self.assertIn("scope_expansion", routes["human_signoff"]["when_any"])
        self.assertIn("threshold_reduction", routes["human_signoff"]["when_any"])
        self.assertEqual(routes["blocked"]["when_any"]["unknown"], True)
        self.assertEqual(policy["external_action_authorization"], "always_independent")

    def test_rule_set_stage_gate_and_run_evidence_bind_conditional_certification(self):
        rule_set = load_yaml(
            ROOT / "contracts" / "governance" / "governance-rule-set-contract.yaml"
        )
        self.assertEqual(
            rule_set["enums"]["approval_route"],
            ["policy_certified", "human_signoff"],
        )
        for field in (
            "approval_route",
            "decision_authority_ref",
            "certification_verdict_ref",
        ):
            self.assertIn(field, rule_set["required_fields"])
        self.assertIn(
            "policy_certified_requires_current_scope_matched_certification_verdict",
            rule_set["invariants"],
        )
        self.assertIn(
            "human_signoff_requires_verified_human_principal",
            rule_set["invariants"],
        )
        self.assertNotIn("active_requires_verified_human_principal", rule_set["invariants"])

        stage = load_yaml(ROOT / "contracts" / "governance" / "stage-exit-gates-contract.yaml")
        self.assertNotIn("approval_route", stage["independent_axes"])
        for field in (
            "approval_route",
            "decision_authority_ref",
            "certification_verdict_ref",
        ):
            self.assertIn(field, stage["stage_gate_record"]["required_fields"])

        run_evidence = load_yaml(
            ROOT / "contracts" / "governance" / "run-evidence-contract.yaml"
        )
        conditional = run_evidence["run"]["conditional_required_fields"]
        self.assertIn(
            "review_policy_bundle_fingerprints",
            conditional["independent_ai_review"],
        )
        self.assertIn(
            "review_policy_certification_refs",
            conditional["independent_ai_review"],
        )
        self.assertIn(
            "review_policy_test_suite_refs",
            conditional["review_policy_certification_run"],
        )

    def test_requirement_package_uses_conditional_decision_routes(self):
        contract = load_yaml(
            ROOT / "contracts" / "artifacts" / "requirement-design-package-contract.yaml"
        )
        function_fields = contract["required_frontmatter_fields"][
            "functions/FUNC-001_功能需求卡.md"
        ]
        for field in (
            "approval_route",
            "decision_authority_ref",
            "certification_verdict_ref",
            "decision_inputs.scope_change",
            "decision_inputs.unresolved_unknown",
        ):
            self.assertIn(field, function_fields)
        for invariant in (
            "approved_object_requires_exactly_one_valid_decision_route",
            "policy_certified_requires_current_scope_matched_certification_verdict",
            "human_signoff_requires_verified_human_principal",
            "AI_cannot_self_certify_or_promote_without_a_valid_decision_gate",
        ):
            self.assertIn(invariant, contract["state_invariants"])


if __name__ == "__main__":
    unittest.main()
