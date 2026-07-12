import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / "docs" / "workflows" / "REQUIREMENT_DESIGN_WORKFLOW.md"
FIXTURE_ROOT = ROOT / "fixtures" / "requirement-design"
POSITIVE = FIXTURE_ROOT / "positive"
NEGATIVE = FIXTURE_ROOT / "negative"
STATIC_EVIDENCE = (
    ROOT / "reviews" / "human-ai-requirement-design-static-evidence.yaml"
)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def section(text: str, heading: str, next_heading: str | None = None) -> str:
    start = text.index(heading)
    if next_heading is None:
        return text[start:]
    end = text.index(next_heading, start + len(heading))
    return text[start:end]


def canonical_hash(document: dict) -> str:
    payload = {key: value for key, value in document.items() if key != "content_hash"}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_registry(root: Path) -> dict[str, dict]:
    registry = {}
    for path in sorted(root.glob("*.yaml")):
        document = load_yaml(path)
        registry[document["stable_id"]] = document
    return registry


def fixture_integrity(root: Path) -> tuple[dict[str, str], str]:
    files = {}
    for path in sorted(
        candidate for candidate in root.rglob("*") if candidate.is_file()
    ):
        relative_path = path.relative_to(ROOT).as_posix()
        files[relative_path] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = "\n".join(f"{path}:{digest}" for path, digest in files.items())
    return files, hashlib.sha256(manifest.encode("utf-8")).hexdigest()


def set_dotted(document: dict, dotted_path: str, value) -> None:
    current = document
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    if isinstance(current, list):
        current[int(last)] = value
    else:
        current[last] = value


def validate_requirement_fixture(registry: dict[str, dict]) -> list[str]:
    errors = []
    required_ids = {
        "SRC-REQ-001",
        "FACT-REQ-001",
        "REQ-BIZ-001",
        "SCENARIO-REQ-001",
        "CHAIN-REQ-001",
        "CAP-REQ-001",
        "FUNC-REQ-001",
        "CTX-REQ-001",
        "REQ-FUNC-RD-FIX-001",
        "REQ-BASELINE-RD-FIX-001",
        "ADR-REQ-001",
        "SPEC-REQ-FUNC-001",
    }
    if set(registry) != required_ids:
        return ["registry_ids_do_not_match_expected_chain"]

    business = registry["REQ-BIZ-001"]
    functional = registry["REQ-FUNC-RD-FIX-001"]
    context = registry["CTX-REQ-001"]
    baseline = registry["REQ-BASELINE-RD-FIX-001"]
    adr = registry["ADR-REQ-001"]
    spec = registry["SPEC-REQ-FUNC-001"]

    for subject in (business, functional, context, baseline):
        if subject.get("content_hash") != canonical_hash(subject):
            errors.append(f"content_hash_invalid:{subject['stable_id']}")

    expected_links = {
        "FACT-REQ-001": ("source_refs", "SRC-REQ-001"),
        "REQ-BIZ-001": ("fact_refs", "FACT-REQ-001"),
        "SCENARIO-REQ-001": ("requirement_refs", "REQ-BIZ-001"),
        "CHAIN-REQ-001": ("scenario_refs", "SCENARIO-REQ-001"),
        "CAP-REQ-001": ("chain_refs", "CHAIN-REQ-001"),
        "FUNC-REQ-001": ("capability_refs", "CAP-REQ-001"),
        "REQ-FUNC-RD-FIX-001": ("function_refs", "FUNC-REQ-001"),
        "ADR-REQ-001": ("requirement_refs", "REQ-FUNC-RD-FIX-001"),
        "SPEC-REQ-FUNC-001": ("adr_refs", "ADR-REQ-001"),
    }
    for stable_id, (field, expected_ref) in expected_links.items():
        if expected_ref not in registry[stable_id].get(field, []):
            errors.append(f"causal_link_missing:{stable_id}:{expected_ref}")

    if functional.get("object_type") != "requirement" or functional.get(
        "requirement_kind"
    ) != "functional":
        errors.append("functional_requirement_kind_invalid")
    if functional.get("approval_status") != "approved":
        errors.append("spec_cannot_consume_unapproved_functional_requirement")
    if not str(functional.get("approver", "")).startswith("human-"):
        errors.append("ai_cannot_approve_functional_requirement")
    alignment = functional.get("intent_alignment", {})
    if alignment.get("approved_intent_hash") != alignment.get(
        "implementation_intent_source_hash"
    ):
        errors.append("implementation_intent_not_bound_to_approved_intent")
    if alignment.get("status") != "approved" or not str(
        alignment.get("verified_by", "")
    ).startswith("human-"):
        errors.append("intent_alignment_not_human_approved")
    review = functional.get("generation_review", {})
    if set(review) != {
        "missing_information",
        "assumptions",
        "possible_errors",
        "human_confirmations",
    } or any(not review[key] for key in review):
        errors.append("generation_self_review_incomplete")

    if functional.get("context_snapshot_ref") != context["stable_id"]:
        errors.append("functional_requirement_context_unresolved")
    if any(path.startswith(".prompts/") for path in context.get("included_files", [])):
        errors.append("prompt_or_chat_cannot_be_included_as_authority")
    if ".prompts/" not in context.get("excluded_files", []):
        errors.append("prompt_exclusion_missing")
    if not str(context.get("approved_by", "")).startswith("human-"):
        errors.append("context_snapshot_not_human_approved")

    members = {
        member["stable_id"]: member for member in baseline.get("requirement_refs", [])
    }
    for requirement in (business, functional):
        member = members.get(requirement["stable_id"])
        if member is None or member.get("version") != requirement.get("version") or member.get(
            "content_hash"
        ) != requirement.get("content_hash"):
            errors.append(f"baseline_member_mismatch:{requirement['stable_id']}")
    if baseline.get("baseline_state") != "approved" or not str(
        baseline.get("approved_by", "")
    ).startswith("human-"):
        errors.append("baseline_not_human_approved")

    spec_ref = spec.get("functional_requirement_ref", {})
    if spec_ref != {
        "stable_id": functional["stable_id"],
        "version": functional["version"],
        "content_hash": functional["content_hash"],
    }:
        errors.append("spec_functional_requirement_binding_mismatch")
    if spec.get("requirement_baseline_ref") != baseline["stable_id"] or spec.get(
        "requirement_baseline_hash"
    ) != baseline["content_hash"]:
        errors.append("spec_baseline_binding_mismatch")
    if adr.get("decision") != "accepted" or adr.get("baseline_ref") != baseline[
        "stable_id"
    ]:
        errors.append("spec_requires_accepted_adr_on_current_baseline")
    if functional.get("candidate_solution_status") != "candidate":
        errors.append("candidate_solution_was_promoted_inside_requirement")
    return errors


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

    def test_human_ai_reasoning_flow_uses_decision_gate_before_spec_and_execution(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        canonical_flow = (
            "Source → Fact / Unknown → Requirement → Scenario → Business Chain "
            "→ Capability → Function → Functional Requirement → Decision Gate "
            "→ Requirement Baseline → Research / ADR → Engineering Design → Spec"
        )
        self.assertIn(canonical_flow, workflow)

        delivery = (ROOT / "docs/workflows/PROJECT_DELIVERY_WORKFLOW.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "业务链路 → 能力树 → 功能树 → 功能级需求 → 决策门与需求基线 → ADR → 工程设计 → Spec",
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
        self.assertIn("AI 不能给自己的审核策略签发独立认证", model)
        self.assertIn("policy_certified", model)
        self.assertIn("human_signoff", model)

    def test_stage_gates_put_intent_decision_before_spec(self):
        gates = (ROOT / "docs/workflows/STAGE_EXIT_GATES.md").read_text(
            encoding="utf-8"
        )
        s0 = section(gates, "## S0", "## S1")
        s2 = section(gates, "## S2", "## S3")
        s5 = section(gates, "## S5", "## S6")
        for token in ("original_intent", "approved_intent", "需求基线"):
            self.assertIn(token, s0)
        for token in ("功能需求卡", "AI 自检", "Decision Gate"):
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


class RequirementDesignMachineGateTests(unittest.TestCase):
    def test_stage_gate_machine_contract_enforces_intent_baseline_and_spec_binding(self):
        contract = load_yaml(
            ROOT / "contracts/governance/stage-exit-gates-contract.yaml"
        )
        s0 = " ".join(sum(contract["stages"]["S0"].values(), []))
        s2 = " ".join(sum(contract["stages"]["S2"].values(), []))
        s5 = " ".join(sum(contract["stages"]["S5"].values(), []))
        for token in ("original_intent", "approved_intent", "requirement_baseline"):
            self.assertIn(token, s0)
        for token in (
            "functional_requirement",
            "context_snapshot",
            "AI_self_review",
            "decision_gate",
            "policy_certified",
            "human_signoff",
        ):
            self.assertIn(token, s2)
        for token in (
            "functional_requirement_version_and_hash",
            "requirement_baseline",
            "invalid_decision_gate",
            "stale_certification",
            "fail_closed",
        ):
            self.assertIn(token, s5)

    def test_positive_fixture_closes_human_reasoning_to_spec_chain(self):
        registry = load_registry(POSITIVE)
        self.assertEqual(validate_requirement_fixture(registry), [])

    def test_negative_mutations_fail_closed_with_expected_reason(self):
        source_registry = load_registry(POSITIVE)
        mutation_paths = sorted(NEGATIVE.glob("*.yaml"))
        self.assertGreaterEqual(len(mutation_paths), 5)
        for mutation_path in mutation_paths:
            mutation = load_yaml(mutation_path)
            registry = copy.deepcopy(source_registry)
            target = registry[mutation["target_ref"]]
            set_dotted(target, mutation["path"], mutation["value"])
            errors = validate_requirement_fixture(registry)
            with self.subTest(mutation=mutation_path.name):
                self.assertIn(mutation["expected_error"], errors)

    def test_requirement_fixture_does_not_raise_score_or_runtime_claim(self):
        project_os = load_yaml(ROOT / "project-os.yaml")
        current = load_yaml(ROOT / "reviews/current-score-status.yaml")
        self.assertEqual(project_os["score_summary"]["current_overall_score"], "not_evaluated")
        self.assertEqual(current["current_overall_score"], "not_evaluated")
        self.assertIn("runtime_ready", project_os["claim_limits"]["forbidden"])


class RequirementDesignEvidenceTests(unittest.TestCase):
    def test_static_evidence_is_registered_and_fixture_integrity_is_recomputable(self):
        self.assertTrue(STATIC_EVIDENCE.is_file())
        evidence = load_yaml(STATIC_EVIDENCE)
        project_os = load_yaml(ROOT / "project-os.yaml")
        expected_files, expected_manifest = fixture_integrity(FIXTURE_ROOT)

        self.assertEqual(
            project_os["score_summary"]["requirement_design_static_evidence_ref"],
            "reviews/human-ai-requirement-design-static-evidence.yaml",
        )
        self.assertIn(
            "reviews/human-ai-requirement-design-static-evidence.yaml",
            project_os["proof_evidence"],
        )
        self.assertEqual(
            project_os["score_summary"]["requirement_design_proof_scope"],
            "human_requirement_design_static_fixture_only",
        )
        self.assertEqual(
            evidence["content_integrity"]["files"], expected_files
        )
        self.assertEqual(
            evidence["content_integrity"]["fixture_tree_manifest_sha256"],
            expected_manifest,
        )
        self.assertEqual(evidence["results"]["full"]["tests_run"], 135)
        self.assertEqual(evidence["results"]["checker"]["p0_count"], 0)
        self.assertEqual(evidence["results"]["checker"]["p1_count"], 0)
        self.assertEqual(evidence["current_overall_score"], "not_evaluated")
        self.assertEqual(evidence["proof_level_ceiling"], "control_package")
        self.assertFalse(evidence["claims_allowed"]["general_95_plus"])

    def test_discussion_scores_are_non_official_and_current_score_stays_unknown(self):
        current = load_yaml(ROOT / "reviews/current-score-status.yaml")
        assessment = current["design_assessment_context"]

        self.assertEqual(current["current_overall_score"], "not_evaluated")
        self.assertEqual(assessment["approved_operational_spine_target"], 95.93)
        self.assertEqual(
            assessment["discussion_estimates"],
            {
                "machine_governance_only": 86.4,
                "human_requirement_layer": 96.4,
                "broader_blind_spot_candidate": 97.6,
            },
        )
        self.assertEqual(
            assessment["status"], "non_official_unverified_not_current_score"
        )
        for gate in (
            "real_human_usability_test",
            "real_l2_requirement_migration",
            "automatic_impact_simulation",
        ):
            self.assertEqual(current["hard_gates"][gate], "unmet")

    def test_readme_separates_static_requirement_proof_from_real_capability(self):
        readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for token in ("86.4", "96.4", "97.6", "非官方"):
            self.assertIn(token, readme)
        for token in (
            "human_requirement_design_static_fixture_only",
            "真实人工可用性测试",
            "真实 L2 需求迁移",
            "自动影响模拟",
        ):
            self.assertIn(token, readme)
        self.assertIn("当前总体评分继续是 `not_evaluated`", readme)


if __name__ == "__main__":
    unittest.main()
