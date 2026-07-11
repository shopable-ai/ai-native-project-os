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

    def test_ai_review_contract_has_four_terminal_routes_and_rule_citations(self):
        contract = load_policy("ai-review-verdict-contract.yaml")
        self.assertEqual(
            contract["enums"]["decision"],
            ["pending", "allow", "rewrite_required", "blocked", "rule_gap"],
        )
        self.assertIn("every_finding_requires_resolvable_rule_ref", contract["invariants"])
        self.assertIn("rewrite_limit_exhaustion_requires_blocked", contract["invariants"])
        self.assertIn("human_authorization_cannot_override_blocked_review", contract["invariants"])


if __name__ == "__main__":
    unittest.main()
