import tempfile
import textwrap
import unittest
from pathlib import Path

from linters.check_capability_function_mapping import validate


CAPABILITY = """\
---
stable_{gap}id: CAP-001
object_type: business_capability
parent_capability_ref: null
child_capability_refs: []
function_refs: [FUNC-001]
---
# 能力
""".format(gap="")

FUNCTION = """\
---
stable_{gap}id: REQ-FUNC-001
object_type: requirement
requirement_kind: functional
function_id: FUNC-001
capability_refs: [CAP-001]
approval_status: pending
approval_route: null
decision_authority_ref: null
certification_verdict_ref: null
executor: ai-requirement-author
approver: null
verifier: independent-requirement-reviewer
decision_inputs:
  scope_change: none
  threshold_change: unchanged
  blocking_rule_change: unchanged
  permission_change: none
  objective_or_responsibility_change: false
  residual_risk_acceptance: false
  external_side_effect: none
  unresolved_unknown: false
intent:
  approved_intent: null
candidate_solution_status: candidate
spec_refs: []
---
# 功能
""".format(gap="")


HUMAN_APPROVED_FUNCTION = (
    FUNCTION.replace("approval_status: pending", "approval_status: approved")
    .replace("approval_route: null", "approval_route: human_signoff")
    .replace("decision_authority_ref: null", "decision_authority_ref: human-owner")
    .replace("approver: null", "approver: human-owner")
    .replace("approved_intent: null", "approved_intent: approved-business-intent")
)


POLICY_APPROVED_FUNCTION = (
    FUNCTION.replace("approval_status: pending", "approval_status: approved")
    .replace("approval_route: null", "approval_route: policy_certified")
    .replace(
        "decision_authority_ref: null",
        "decision_authority_ref: review-policy-activation-routing@1",
    )
    .replace(
        "certification_verdict_ref: null",
        "certification_verdict_ref: REVIEW-POLICY-CERT-001",
    )
    .replace("approved_intent: null", "approved_intent: approved-business-intent")
)


class CapabilityFunctionMappingTests(unittest.TestCase):
    def write(self, root: Path, relative: str, content: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content), encoding="utf-8")

    def test_positive_draft_mapping_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            self.write(root, "requirements/functions/FUNC-001.md", FUNCTION)
            self.assertEqual([], validate(root))

    def test_orphan_function_is_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/functions/FUNC-001.md", FUNCTION.replace("[CAP-001]", "[CAP-MISSING]"))
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-UNKNOWN-CAPABILITY", codes)

    def test_capability_cycle_is_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(
                root,
                "requirements/capabilities/CAP-001.md",
                CAPABILITY.replace("child_capability_refs: []", "child_capability_refs: [CAP-002]"),
            )
            self.write(
                root,
                "requirements/capabilities/CAP-002.md",
                CAPABILITY.replace("CAP-001", "CAP-002")
                .replace("parent_capability_ref: null", "parent_capability_ref: CAP-001")
                .replace("child_capability_refs: []", "child_capability_refs: [CAP-001]")
                .replace("function_refs: [FUNC-002]", "function_refs: []"),
            )
            self.write(root, "requirements/functions/FUNC-001.md", FUNCTION)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-CAPABILITY-CYCLE", codes)

    def test_unapproved_requirement_cannot_reference_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            self.write(root, "requirements/functions/FUNC-001.md", FUNCTION.replace("spec_refs: []", "spec_refs: [SPEC-001]"))
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-UNAPPROVED-SPEC", codes)

    def test_approved_requirement_accepts_human_signoff_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            self.write(root, "requirements/functions/FUNC-001.md", HUMAN_APPROVED_FUNCTION)
            self.assertEqual([], validate(root))

    def test_approved_requirement_accepts_policy_certified_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            self.write(root, "requirements/functions/FUNC-001.md", POLICY_APPROVED_FUNCTION)
            self.assertEqual([], validate(root))

    def test_approved_requirement_without_route_is_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            invalid = FUNCTION.replace("approval_status: pending", "approval_status: approved").replace(
                "approved_intent: null", "approved_intent: approved-business-intent"
            )
            self.write(root, "requirements/functions/FUNC-001.md", invalid)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-INVALID-DECISION-GATE", codes)

    def test_policy_certified_route_requires_certification_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            invalid = POLICY_APPROVED_FUNCTION.replace(
                "certification_verdict_ref: REVIEW-POLICY-CERT-001",
                "certification_verdict_ref: null",
            )
            self.write(root, "requirements/functions/FUNC-001.md", invalid)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-MISSING-CERTIFICATION", codes)

    def test_policy_certified_route_rejects_high_risk_route_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            invalid = POLICY_APPROVED_FUNCTION.replace(
                "scope_change: none", "scope_change: expanded"
            )
            self.write(root, "requirements/functions/FUNC-001.md", invalid)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-ROUTE-MISMATCH", codes)

    def test_unresolved_unknown_is_blocking_for_every_approval_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            invalid = HUMAN_APPROVED_FUNCTION.replace(
                "unresolved_unknown: false", "unresolved_unknown: true"
            )
            self.write(root, "requirements/functions/FUNC-001.md", invalid)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-UNRESOLVED-UNKNOWN", codes)

    def test_policy_route_rejects_generator_as_decision_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            invalid = POLICY_APPROVED_FUNCTION.replace(
                "decision_authority_ref: review-policy-activation-routing@1",
                "decision_authority_ref: ai-requirement-author",
            )
            self.write(root, "requirements/functions/FUNC-001.md", invalid)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-AI-SELF-CERTIFICATION", codes)

    def test_human_signoff_route_rejects_non_human_approver(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            invalid = HUMAN_APPROVED_FUNCTION.replace("approver: human-owner", "approver: ai-agent")
            self.write(root, "requirements/functions/FUNC-001.md", invalid)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-INVALID-HUMAN-SIGNOFF", codes)


if __name__ == "__main__":
    unittest.main()
