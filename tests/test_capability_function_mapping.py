import tempfile
import textwrap
import unittest
from pathlib import Path

from linters.check_capability_function_mapping import validate


CAPABILITY = """\
---
stable_id: CAP-001
object_type: business_capability
parent_capability_ref: null
child_capability_refs: []
function_refs: [FUNC-001]
---
# 能力
"""

FUNCTION = """\
---
stable_id: REQ-FUNC-001
object_type: requirement
requirement_kind: functional
function_id: FUNC-001
capability_refs: [CAP-001]
approval_status: pending
approver: human-owner
intent:
  approved_intent: null
candidate_solution_status: candidate
spec_refs: []
---
# 功能
"""


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

    def test_approved_requirement_requires_human_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "requirements/capabilities/CAP-001.md", CAPABILITY)
            invalid = FUNCTION.replace("approval_status: pending", "approval_status: approved").replace("approver: human-owner", "approver: ai-agent")
            self.write(root, "requirements/functions/FUNC-001.md", invalid)
            codes = {finding.code for finding in validate(root)}
            self.assertIn("C13-INVALID-APPROVAL", codes)


if __name__ == "__main__":
    unittest.main()
