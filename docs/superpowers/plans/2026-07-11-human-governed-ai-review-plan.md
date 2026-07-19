# Human-Governed AI Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a project-neutral L1 mechanism in which humans govern versioned Markdown rules, independent AI performs routine review, and humans authorize only rule changes, exceptions, residual risk, and irreversible actions.

**Architecture:** Add two machine contracts (`governance_rule_set` and `ai_review_verdict`) and thread their semantics through the existing authority documents, control-set policies, project templates, and static checker. Keep stable machine paths in English while using Chinese filenames for human-maintained review-rule Markdown. Keep runtime model execution out of scope; prove the static mechanism with synthetic fixtures, strict nonzero exit behavior for P0/P1 findings, and a versioned adversarial score record.

**Tech Stack:** Markdown, YAML 1.2-compatible policy files, Python 3 standard library, PyYAML 6.x for contract tests, `unittest`.

---

### Task 1: Make P1 findings fail the checker gate

**Files:**
- Create: `tests/test_check_controlled_objects.py`
- Modify: `linters/check_controlled_objects.py`

- [ ] **Step 1: Write the failing exit-code regression test**

```python
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "linters" / "check_controlled_objects.py"
SPEC = importlib.util.spec_from_file_location("check_controlled_objects", MODULE_PATH)
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)


class CheckerExitCodeTests(unittest.TestCase):
    def test_p1_finding_fails_gate(self):
        findings = [checker.Finding("C4", "P1", "project-os.yaml", 1, "drift")]
        self.assertEqual(checker.exit_code_for_findings(findings), 1)

    def test_empty_findings_pass_gate(self):
        self.assertEqual(checker.exit_code_for_findings([]), 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the regression test and verify RED**

Run: `python3 -m unittest tests.test_check_controlled_objects -v`

Expected: ERROR because `exit_code_for_findings` does not exist.

- [ ] **Step 3: Implement the minimal exit-code function**

```python
def exit_code_for_findings(findings: list[Finding]) -> int:
    return 1 if any(f.severity in {"P0", "P1"} for f in findings) else 0
```

Replace the final `return 1 if p0 else 0` with `return exit_code_for_findings(all_findings)`, and change the human-readable P1 summary to `❌ 有 P1 发现（门禁失败）`.

- [ ] **Step 4: Run the regression test and checker**

Run: `python3 -m unittest tests.test_check_controlled_objects -v`

Expected: 2 tests pass.

Run: `python3 linters/check_controlled_objects.py . --report`

Expected: nonzero while the existing L1-to-L2 path finding remains, proving P1 no longer silently passes.

- [ ] **Step 5: Commit the gate correction**

```bash
git add -- tests/test_check_controlled_objects.py linters/check_controlled_objects.py
git commit -m "Make governance warnings fail their declared gate"
```

### Task 2: Add rule-set and AI-review machine contracts

**Files:**
- Create: `tests/test_ai_review_governance_contracts.py`
- Create: `policies/governance-rule-set-contract.yaml`
- Create: `policies/ai-review-verdict-contract.yaml`

- [ ] **Step 1: Write failing contract tests**

```python
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
```

- [ ] **Step 2: Run contract tests and verify RED**

Run: `python3 -m unittest tests.test_ai_review_governance_contracts -v`

Expected: ERROR because both contract files are absent.

- [ ] **Step 3: Create the rule-set contract**

Create `policies/governance-rule-set-contract.yaml` with `schema_version: 1`, `contract_id: governance-rule-set-contract`, `object_type: governance_rule_set`, required identity/version/path/hash/scope/rule/status/approval/effective/expiry/supersedes fields, the state enum `[draft, approved, active, superseded, revoked]`, a complete draft manifest example, and invariants for human approval, Markdown authority, nonempty active rules, exact hash/scope binding, supersession, expiry, and fail-closed unknown fields.

- [ ] **Step 4: Create the AI-review contract**

Create `policies/ai-review-verdict-contract.yaml` with `schema_version: 1`, `contract_id: ai-review-verdict-contract`, `object_type: ai_review_verdict`, the decision enum asserted above, required generator/reviewer/rule-set/finding/evidence/rewrite/claim fields, a pending manifest example, and invariants for reviewer independence, exact subject and rule-set hashes, resolvable rule citations, nonempty allow coverage, bounded rewrites, rule-gap records, blocked override prevention, and fail-closed unknown fields.

- [ ] **Step 5: Run contract tests and YAML parsing**

Run: `python3 -m unittest tests.test_ai_review_governance_contracts -v`

Expected: 2 tests pass.

Run: `python3 -c 'from pathlib import Path; import yaml; [yaml.safe_load(p.read_text()) for p in Path("policies").glob("*.yaml")]; print("policies-ok")'`

Expected: `policies-ok`.

- [ ] **Step 6: Commit the machine contracts**

```bash
git add -- tests/test_ai_review_governance_contracts.py policies/governance-rule-set-contract.yaml policies/ai-review-verdict-contract.yaml
git commit -m "Make routine AI review a rule-bound machine contract"
```

### Task 3: Enforce the review boundary in the checker

**Files:**
- Modify: `tests/test_check_controlled_objects.py`
- Modify: `linters/check_controlled_objects.py`

- [ ] **Step 1: Add failing synthetic-fixture tests**

Add tests that create temporary repositories and assert:

```python
def test_ai_review_workflow_cannot_wait_for_human_approval(self):
    repo = self.make_repo({
        "workflows/review.yaml": "review_mode: ai_automated\nwork_status: waiting_approval\n"
    })
    findings = checker.check_c6_ai_review_no_routine_human_wait(repo, checker.iter_repo_files(repo))
    self.assertEqual([f.rule for f in findings], ["C6"])

def test_review_verdict_requires_rule_set_and_bounded_rewrite(self):
    repo = self.make_repo({
        "runs/verdict.yaml": "object_type: ai_review_verdict\ndecision: rewrite_required\nmax_rewrite_attempts: 0\n"
    })
    findings = checker.check_c7_ai_review_manifest(repo, checker.iter_repo_files(repo))
    self.assertEqual({f.rule for f in findings}, {"C7"})
```

The shared `make_repo` helper uses `tempfile.TemporaryDirectory`, writes only the supplied synthetic files, and registers cleanup with `self.addCleanup`.

- [ ] **Step 2: Run targeted tests and verify RED**

Run: `python3 -m unittest tests.test_check_controlled_objects.CheckerGovernanceTests -v`

Expected: ERROR because C6/C7 functions do not exist.

- [ ] **Step 3: Implement C6 and C7**

Implement `check_c6_ai_review_no_routine_human_wait` to flag files that explicitly declare `review_mode: ai_automated` together with `waiting_approval` as P0. Implement `check_c7_ai_review_manifest` to parse declared `ai_review_verdict` YAML text and require `subject_ref`, generator/review Run refs, reviewer actor/node refs, rule-set ref/hash, decision, evidence refs, and a positive rewrite limit when decision is `rewrite_required`.

Register both checks in `main`. Keep detection structural; do not add business-language keyword lists.

- [ ] **Step 4: Run tests and checker**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

Run: `python3 linters/check_controlled_objects.py . --report`

Expected: no C6/C7 finding in L1 itself.

- [ ] **Step 5: Commit checker enforcement**

```bash
git add -- tests/test_check_controlled_objects.py linters/check_controlled_objects.py
git commit -m "Block routine AI review from falling back to human queues"
```

### Task 4: Align authority documents and state semantics

**Files:**
- Modify: `docs/architecture/AI_PROJECT_OS_CORE.md`
- Modify: `docs/architecture/AI_NATIVE_EXECUTION_MODEL.md`
- Modify: `docs/governance/CONTROLLED_OBJECT_MODEL.md`
- Modify: `docs/governance/ARTIFACTS_AND_TRACEABILITY.md`
- Modify: `docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md`
- Modify: `docs/governance/RUN_EVIDENCE_ACCEPTANCE.md`
- Modify: `docs/governance/GATES_PROOF_SCORING.md`
- Modify: `docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md`
- Modify: `docs/workflows/ARCHITECT_WORKFLOWS.md`
- Create: `decisions/ADR-0003-human-governed-ai-review.md`

- [ ] **Step 1: Add failing authority-alignment assertions**

Extend `tests/test_ai_review_governance_contracts.py` to assert exact authority text markers:

```python
def test_authority_documents_define_three_distinct_responsibilities(self):
    controlled = (ROOT / "docs/governance/CONTROLLED_OBJECT_MODEL.md").read_text()
    native = (ROOT / "docs/architecture/AI_NATIVE_EXECUTION_MODEL.md").read_text()
    authorization = (ROOT / "docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md").read_text()
    self.assertIn("`governance_rule_set`", controlled)
    self.assertIn("`ai_review_verdict`", controlled)
    self.assertIn("普通内容审核不得进入 `waiting_approval`", native)
    self.assertIn("内容审核通过不授予动作权限", authorization)
```

- [ ] **Step 2: Run the assertion and verify RED**

Run: `python3 -m unittest tests.test_ai_review_governance_contracts.GovernanceContractsTests.test_authority_documents_define_three_distinct_responsibilities -v`

Expected: FAIL because the markers are absent.

- [ ] **Step 3: Apply the authority rewrite**

Update the listed authority documents to use one consistent model:

```text
人工规则治理 → AI 自动审核 → 独立动作授权
```

Narrow `human_decision` to rule/fact/requirement approval, exception/residual-risk acceptance, and irreversible-action authorization. Add the three new controlled-object rows, `reviewed_by` and `identifies_gap_in` relations, exact rule citations, bounded rewrite rules, and the invariant that human authorization cannot override a blocked AI review. Reserve `waiting_approval` for governance and authorization; routine content review uses the type-specific AI verdict decision.

Create ADR-0003 with context, decision, consequences, rejected alternatives, migration requirements, and claim ceiling. State explicitly that this changes design contracts only and does not prove runtime review.

- [ ] **Step 4: Run authority assertions and link checks**

Run: `python3 -m unittest tests.test_ai_review_governance_contracts -v`

Expected: all tests pass.

Run:

```bash
python3 - <<'PY'
import re
from pathlib import Path

files = [
    Path("docs/architecture/AI_PROJECT_OS_CORE.md"),
    Path("docs/architecture/AI_NATIVE_EXECUTION_MODEL.md"),
    Path("docs/governance/CONTROLLED_OBJECT_MODEL.md"),
    Path("docs/governance/ARTIFACTS_AND_TRACEABILITY.md"),
    Path("docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md"),
    Path("docs/governance/RUN_EVIDENCE_ACCEPTANCE.md"),
    Path("docs/governance/GATES_PROOF_SCORING.md"),
    Path("docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md"),
    Path("docs/workflows/ARCHITECT_WORKFLOWS.md"),
]
missing = []
for source in files:
    text = source.read_text(encoding="utf-8")
    for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
        if "://" in target:
            continue
        resolved = (source.parent / target).resolve()
        if not resolved.exists():
            missing.append(f"{source}: {target}")
if missing:
    raise SystemExit("\n".join(missing))
print("markdown-links-ok")
PY
```

Expected: `markdown-links-ok`.

- [ ] **Step 5: Commit authority alignment**

```bash
git add -- docs/architecture/AI_PROJECT_OS_CORE.md docs/architecture/AI_NATIVE_EXECUTION_MODEL.md docs/governance/CONTROLLED_OBJECT_MODEL.md docs/governance/ARTIFACTS_AND_TRACEABILITY.md docs/governance/AUTHORIZATION_SIDE_EFFECTS_AND_ISOLATION.md docs/governance/RUN_EVIDENCE_ACCEPTANCE.md docs/governance/GATES_PROOF_SCORING.md docs/governance/STATE_TRANSITIONS_AND_INVALIDATION.md docs/workflows/ARCHITECT_WORKFLOWS.md decisions/ADR-0003-human-governed-ai-review.md tests/test_ai_review_governance_contracts.py
git commit -m "Separate rule governance from automated review and action authorization"
```

### Task 5: Align policies, machine authority, and project templates

**Files:**
- Modify: `policies/control-set-contract.yaml`
- Modify: `policies/project-governance-routing.yaml`
- Modify: `policies/acceptance-verdict-claim-contract.yaml`
- Modify: `policies/authorization-snapshot-contract.yaml`
- Modify: `project-os.yaml`
- Modify: `README.md`
- Modify: `templates/standard-project/README.md`
- Modify: `templates/brownfield-project/README.md`
- Create: `templates/standard-project/governance/rules/审核规则集说明.md`
- Create: `templates/standard-project/governance/rules/内容与证据审核规则.md`
- Create: `templates/standard-project/governance/rules/风险与发布审核规则.md`
- Create: `templates/standard-project/governance/rules/多语言与项目一致性审核规则.md`
- Modify: `tests/test_ai_review_governance_contracts.py`

- [ ] **Step 1: Add failing policy and template assertions**

Assert that `project-os.yaml.authority` points to both new contracts; the standard control set requires `human_rule_governance` and `ai_automated_review`; routing declares `routine_content_review: ai_automated`; the authorization contract states action tickets do not approve content; and the standard template contains the four Chinese-named Markdown files with `rule_set_id`, `rule_id`, `approved_by`, and `canonical_path`.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest tests.test_ai_review_governance_contracts -v`

Expected: FAIL on missing authority pointers, categories, and template.

- [ ] **Step 3: Update policies and machine authority**

Add the new contract authority paths without removing the user’s existing uncommitted `scoring_evidence` entries. Replace ambiguous `human_approval` control categories with `human_rule_governance`, add `ai_automated_review`, define routine content review as AI automated, and state that Approval Tickets authorize actions only. Add conditional Acceptance Verdict bindings for subjects governed by an AI review policy.

- [ ] **Step 4: Add the Markdown rule template**

Create one Chinese-named rule-set manifest and three Chinese-named project-neutral rule files. The manifest contains `rule_set_id`, version, canonical path, scope, status, human approval fields, member refs/hashes, dates, and supersession. Rule files use stable `rule_id`, severity, structured applicability, required Evidence, allowed outcome, and failure action. Do not include any business-language trigger words.

- [ ] **Step 5: Run tests and policy parsing**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

Run: `python3 -c 'from pathlib import Path; import yaml; [yaml.safe_load(p.read_text()) for p in Path("policies").glob("*.yaml")]; yaml.safe_load(Path("project-os.yaml").read_text()); print("yaml-ok")'`

Expected: `yaml-ok`.

- [ ] **Step 6: Commit policy and template alignment**

```bash
git add -- policies/control-set-contract.yaml policies/project-governance-routing.yaml policies/acceptance-verdict-claim-contract.yaml policies/authorization-snapshot-contract.yaml project-os.yaml README.md templates/standard-project/README.md templates/brownfield-project/README.md templates/standard-project/governance/rules tests/test_ai_review_governance_contracts.py
git commit -m "Publish human-governed review rules as reusable project controls"
```

### Task 6: Produce truthful adversarial review and score evidence

**Files:**
- Create: `reviews/human-governed-ai-review-adversarial.yaml`
- Create: `reviews/human-governed-ai-review-score.yaml`
- Modify: `project-os.yaml`

- [ ] **Step 1: Run the full verification set**

Run: `python3 -m unittest discover -s tests -v`

Expected: all tests pass.

Run: `python3 linters/check_controlled_objects.py . --report`

Expected: EXIT=0 with P0=0 and P1=0 after removing the invalid direct L2 scoring-evidence path from L1 machine authority or replacing it with an L1-local evidence pointer.

Run: `git diff --check`

Expected: no output.

- [ ] **Step 2: Record adversarial findings**

Create a YAML review record that challenges reviewer independence, stale rules, conflicting rules, rewrite loops, rule-gap handling, authorization override, empty Evidence, keyword hardcoding, project isolation, and proof overclaiming. Each finding contains severity, status, file evidence, resolution, and residual risk. Do not label same-agent review as independent external review.

- [ ] **Step 3: Calculate the score by proof layer**

Create a score record with separate `design_target_score`, `current_design_evidence_score`, `static_implementation_score`, `local_runtime_proof_score`, and `production_proof_score`. The design target may be 96; current validated score remains capped at 94 unless a genuinely independent review is captured, and general 95+ remains unproven until heterogeneous L2/L3 validation exists.

- [ ] **Step 4: Register current evidence without overwriting history**

Add new review and score pointers under `project-os.yaml` while preserving historical score records. Keep `maturity.verification_status` truthful; static tests do not imply local runtime or production proof.

- [ ] **Step 5: Run final verification and inspect the complete diff**

Run: `python3 -m unittest discover -s tests -v && python3 linters/check_controlled_objects.py . --report && git diff --check`

Expected: all tests pass, checker P0/P1 counts are zero, and diff check is clean.

- [ ] **Step 6: Commit the evidence snapshot**

```bash
git add -- reviews/human-governed-ai-review-adversarial.yaml reviews/human-governed-ai-review-score.yaml project-os.yaml
git commit -m "Keep AI review scoring bounded by reproducible evidence"
```

### Task 7: Final verification and completion report

**Files:**
- Verify only; no planned source modification.

- [ ] **Step 1: Verify commit scope and preserve unrelated changes**

Run: `git status --short && git log --oneline -8`

Expected: all task commits are present; pre-existing `.shopme` and unrelated working-tree changes remain untouched unless a task explicitly required the overlapping file.

- [ ] **Step 2: Re-run all proof commands from a clean index state**

Run: `python3 -m unittest discover -s tests -v`

Run: `python3 linters/check_controlled_objects.py . --report`

Run: `git diff --check`

Expected: tests pass, checker has P0=0/P1=0, and diff check is clean.

- [ ] **Step 3: Report claim ceilings**

Report what is now statically enforced, what remains design-only, and what still requires an AI review runtime, heterogeneous project evidence, independent review, and production proof. State whether the user must act; do not ask the user to inspect internal control files as the primary acceptance method.
