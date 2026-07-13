import importlib.util
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).parents[1]
MODULE_PATH = REPO_ROOT / "linters" / "check_controlled_objects.py"
SPEC = importlib.util.spec_from_file_location("check_controlled_objects", MODULE_PATH)
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)

FIXTURES = REPO_ROOT / "fixtures"
VALID = FIXTURES / "checker-positive" / "valid"
REVIEW_FIXTURES = REPO_ROOT / "fixtures" / "review-policy-certification"


class OperationalSpineCheckerTests(unittest.TestCase):
    def findings(self, function_name, root):
        return getattr(checker, function_name)(root, checker.iter_repo_files(root))

    def assert_rule(self, findings, rule):
        self.assertIn(rule, {finding.rule for finding in findings})

    def test_c8_accepts_complete_stage_gate_contract(self):
        self.assertEqual(self.findings("check_c8_stage_gate_contract", VALID), [])

    def test_c8_rejects_stage_without_evidence_requirements(self):
        root = FIXTURES / "checker-negative" / "stage-gate-missing-evidence"
        self.assert_rule(self.findings("check_c8_stage_gate_contract", root), "C8")

    def test_c8_invalid_yaml_fails_closed_without_exception(self):
        root = FIXTURES / "checker-negative" / "stage-gate-invalid-yaml"
        findings = self.findings("check_c8_stage_gate_contract", root)
        self.assertEqual({finding.rule for finding in findings}, {"C8"})
        self.assertTrue(any("YAML" in finding.message for finding in findings))

    def test_c8_malformed_string_lists_fail_closed_without_type_error(self):
        root = FIXTURES / "checker-negative" / "stage-gate-malformed-types"
        findings = self.findings("check_c8_stage_gate_contract", root)
        messages = [finding.message for finding in findings]
        self.assertTrue(any("independent_axes" in message and "list[str]" in message for message in messages))
        self.assertTrue(any("stage_gate_record.required_fields" in message and "list[str]" in message for message in messages))
        self.assertTrue(any("exit_criterion_result.required_fields" in message and "list[str]" in message for message in messages))

    def test_c9_accepts_complete_template_package(self):
        self.assertEqual(self.findings("check_c9_template_packages", VALID), [])

    def test_c9_rejects_missing_required_template_file(self):
        root = FIXTURES / "checker-negative" / "template-package-missing-file"
        self.assert_rule(self.findings("check_c9_template_packages", root), "C9")

    def test_c9_rejects_missing_required_frontmatter_field(self):
        root = FIXTURES / "checker-negative" / "template-frontmatter-missing-field"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(
            any(
                finding.rule == "C9"
                and "required_frontmatter_field: object_type" in finding.message
                for finding in findings
            )
        )

    def test_c9_required_fields_must_be_mapping(self):
        root = FIXTURES / "checker-negative" / "template-contract-malformed-required-fields"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(any("required_fields" in finding.message for finding in findings))

    def test_c9_required_values_must_be_mapping(self):
        root = FIXTURES / "checker-negative" / "template-contract-malformed-required-values"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(any("required_values" in finding.message for finding in findings))

    def test_c9_required_sections_must_be_mapping(self):
        root = FIXTURES / "checker-negative" / "template-contract-malformed-required-sections"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(any("required_sections" in finding.message for finding in findings))

    def test_c9_task_authority_must_be_mapping(self):
        root = FIXTURES / "checker-negative" / "template-contract-malformed-task-authority"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(any("task_authority" in finding.message for finding in findings))

    def test_c9_nested_required_fields_must_be_list_of_strings(self):
        root = FIXTURES / "checker-negative" / "template-contract-nested-malformed-required-fields"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(any("required_fields[sample.yaml]" in finding.message for finding in findings))

    def test_c9_nested_required_values_must_be_mapping_with_string_keys(self):
        root = FIXTURES / "checker-negative" / "template-contract-nested-malformed-required-values"
        findings = self.findings("check_c9_template_packages", root)
        messages = [finding.message for finding in findings]
        self.assertTrue(any("required_values[sample.yaml]" in message and "mapping" in message for message in messages))
        self.assertTrue(any("required_values[other.yaml]" in message and "string" in message for message in messages))

    def test_c9_nested_required_sections_must_be_list_of_strings(self):
        root = FIXTURES / "checker-negative" / "template-contract-nested-malformed-required-sections"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(any("required_sections[README.md]" in finding.message for finding in findings))

    def test_c9_rejects_absolute_template_root_before_external_read(self):
        root = FIXTURES / "checker-negative" / "template-root-escape"
        findings = self.findings("check_c9_template_packages", root)
        self.assertTrue(any("template_root" in finding.message and "相对路径" in finding.message for finding in findings))

    def test_c9_accepts_all_registered_repository_template_contracts(self):
        project = yaml.safe_load((REPO_ROOT / "project-os.yaml").read_text(encoding="utf-8"))
        authority_keys = (
            "chain_package_contract",
            "spec_package_contract",
            "requirement_design_package_contract",
            "io_contract",
            "workflow_contract",
            "skill_contract",
            "project_instance_contract",
        )
        contract_files = [REPO_ROOT / project["authority"][key] for key in authority_keys]
        self.assertEqual(len({path.resolve() for path in contract_files}), 7)
        files = contract_files + [path for path in (REPO_ROOT / "templates").rglob("*") if path.is_file()]
        self.assertEqual(checker.check_c9_template_packages(REPO_ROOT, files), [])

    def test_c10_accepts_exact_terminology_manifest(self):
        self.assertEqual(self.findings("check_c10_terminology_authority", VALID), [])

    def test_c10_rejects_manifest_term_missing_from_authority(self):
        root = FIXTURES / "checker-negative" / "terminology-missing-term"
        self.assert_rule(self.findings("check_c10_terminology_authority", root), "C10")

    def test_c10_rejects_legacy_profile_enabled_axis(self):
        root = FIXTURES / "checker-negative" / "terminology-missing-term"
        findings = self.findings("check_c10_terminology_authority", root)
        self.assertTrue(any("profiles.*.enabled" in finding.message for finding in findings))

    def test_c11_accepts_valid_authority_and_contract_references(self):
        self.assertEqual(
            self.findings("check_c11_authority_and_contract_references", VALID), []
        )

    def test_c11_rejects_broken_authority_path(self):
        root = FIXTURES / "checker-negative" / "authority-broken-reference"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assert_rule(findings, "C11")
        self.assertTrue(any("missing.md" in finding.message for finding in findings))

    def test_c11_rejects_unresolved_contract_reference(self):
        root = FIXTURES / "checker-negative" / "authority-broken-reference"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertTrue(any("unknown-contract@9" in finding.message for finding in findings))

    def test_c11_accepts_inline_reference_angle_and_spaced_relative_links(self):
        self.assertEqual(
            self.findings("check_c11_authority_and_contract_references", VALID), []
        )

    def test_c11_rejects_broken_markdown_relative_link(self):
        root = FIXTURES / "checker-negative" / "markdown-broken-link"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertTrue(any("docs/missing target.md" in finding.message for finding in findings))

    def test_c11_rejects_markdown_link_escaping_repository(self):
        root = FIXTURES / "checker-negative" / "markdown-escaping-link"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertTrue(any("仓库边界" in finding.message for finding in findings))

    def test_c11_invalid_project_yaml_fails_closed_without_exception(self):
        root = FIXTURES / "checker-negative" / "authority-invalid-yaml"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertEqual({finding.rule for finding in findings}, {"C11"})
        self.assertTrue(any("YAML" in finding.message for finding in findings))

    def test_c11_rejects_registered_contract_reference_version_mismatch(self):
        root = FIXTURES / "checker-negative" / "contract-version-mismatch"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertTrue(any("sample-contract@1" in finding.message for finding in findings))

    def test_c11_rejects_duplicate_contract_id(self):
        root = FIXTURES / "checker-negative" / "contract-id-duplicate"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertTrue(any("contract_id 重复" in finding.message for finding in findings))

    def test_c11_rejects_boolean_contract_version(self):
        root = FIXTURES / "checker-negative" / "contract-version-boolean"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertTrue(any("正整数" in finding.message for finding in findings))

    def test_c11_rejects_authority_parent_escape_before_external_read(self):
        root = FIXTURES / "checker-negative" / "authority-path-escape"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertTrue(any("authority.escape" in finding.message and "相对路径" in finding.message for finding in findings))

    def test_c11_tilde_fence_hides_markdown_links(self):
        self.assertEqual(
            self.findings("check_c11_authority_and_contract_references", VALID), []
        )

    def test_c11_unclosed_markdown_fence_fails_closed(self):
        root = FIXTURES / "checker-negative" / "markdown-unclosed-fence"
        findings = self.findings("check_c11_authority_and_contract_references", root)
        self.assertEqual(len(findings), 1)
        self.assertIn("未闭合", findings[0].message)

    def test_c12_accepts_complete_flowchart_diagram_coverage(self):
        self.assertEqual(self.findings("check_c12_diagram_coverage", VALID), [])

    def test_c12_p0_p1_engineering_chain_requires_flowchart(self):
        root = FIXTURES / "checker-negative" / "diagram-coverage-missing-flowchart"
        findings = self.findings("check_c12_diagram_coverage", root)
        self.assertTrue(any("flowchart" in finding.message for finding in findings))

    def test_c12_flow_alias_does_not_satisfy_flowchart_gate(self):
        root = FIXTURES / "checker-negative" / "diagram-coverage-flow-alias"
        findings = self.findings("check_c12_diagram_coverage", root)
        self.assertTrue(any("flowchart" in finding.message for finding in findings))

    def test_c12_cross_node_chain_requires_sequence(self):
        root = FIXTURES / "checker-negative" / "diagram-coverage-missing-sequence"
        findings = self.findings("check_c12_diagram_coverage", root)
        self.assertEqual([finding.rule for finding in findings], ["C12"])
        self.assertIn("sequence", findings[0].message)

    def test_c12_multi_state_chain_requires_state(self):
        root = FIXTURES / "checker-negative" / "diagram-coverage-missing-state"
        findings = self.findings("check_c12_diagram_coverage", root)
        self.assertEqual([finding.rule for finding in findings], ["C12"])
        self.assertIn("state", findings[0].message)

    def test_c12_boundary_chain_requires_boundary(self):
        root = FIXTURES / "checker-negative" / "diagram-coverage-missing-boundary"
        findings = self.findings("check_c12_diagram_coverage", root)
        self.assertEqual([finding.rule for finding in findings], ["C12"])
        self.assertIn("boundary", findings[0].message)

    def test_c12_rejects_orphan_diagram(self):
        root = FIXTURES / "checker-negative" / "diagram-coverage-missing"
        findings = self.findings("check_c12_diagram_coverage", root)
        self.assertEqual(len(findings), 1)
        self.assertTrue(any("orphan" in finding.message.lower() for finding in findings))

    def test_c12_ignores_non_chain_yaml_and_diagrams_outside_chain_package(self):
        root = FIXTURES / "checker-negative" / "diagram-scope-unrelated"
        self.assertEqual(self.findings("check_c12_diagram_coverage", root), [])

    def test_c14_accepts_policy_human_and_rule_gap_recovery_scenarios(self):
        for scenario in (
            "policy-certified",
            "human-signoff",
            "rule-gap-recovery",
        ):
            with self.subTest(scenario=scenario):
                root = REVIEW_FIXTURES / "positive" / scenario
                self.assertEqual(
                    self.findings("check_c14_review_policy_certification", root),
                    [],
                )

    def test_c14_rejects_missing_core_categories(self):
        root = REVIEW_FIXTURES / "negative" / "missing-core-categories"
        findings = self.findings("check_c14_review_policy_certification", root)
        self.assertTrue(any("类别" in finding.message for finding in findings))

    def test_c14_rejects_insufficient_nondeterministic_repeats(self):
        root = REVIEW_FIXTURES / "negative" / "insufficient-repeats"
        findings = self.findings("check_c14_review_policy_certification", root)
        self.assertTrue(any("重复" in finding.message for finding in findings))

    def test_c14_rejects_self_certification(self):
        root = REVIEW_FIXTURES / "negative" / "self-certification"
        findings = self.findings("check_c14_review_policy_certification", root)
        self.assertTrue(any("独立" in finding.message for finding in findings))

    def test_c14_rejects_bundle_hash_drift(self):
        root = REVIEW_FIXTURES / "negative" / "bundle-hash-drift"
        findings = self.findings("check_c14_review_policy_certification", root)
        self.assertTrue(any("hash" in finding.message for finding in findings))

    def test_c14_rejects_scope_expansion_auto_activation(self):
        root = REVIEW_FIXTURES / "negative" / "scope-expansion-auto"
        findings = self.findings("check_c14_review_policy_certification", root)
        self.assertTrue(any("路由" in finding.message for finding in findings))

    def test_c14_rejects_failed_threshold_active_policy(self):
        root = REVIEW_FIXTURES / "negative" / "failed-threshold-active"
        findings = self.findings("check_c14_review_policy_certification", root)
        self.assertTrue(any("阈值" in finding.message for finding in findings))

    def test_c14_rejects_certification_as_external_authorization(self):
        root = REVIEW_FIXTURES / "negative" / "authorization-escalation"
        findings = self.findings("check_c14_review_policy_certification", root)
        self.assertTrue(any("外部动作授权" in finding.message for finding in findings))

    def test_main_repository_scan_skips_checker_fixtures(self):
        scanned = {path.relative_to(REPO_ROOT).as_posix() for path in checker.iter_repo_files(REPO_ROOT)}
        self.assertFalse(any(path.startswith("fixtures/checker-positive/") for path in scanned))
        self.assertFalse(any(path.startswith("fixtures/checker-negative/") for path in scanned))


if __name__ == "__main__":
    unittest.main()
