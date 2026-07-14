import importlib.util
import re
import shutil
import tempfile
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

    def mutated_chain_package_findings(self, mutate):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract_dir = root / "contracts" / "artifacts"
            contract_dir.mkdir(parents=True)
            shutil.copy2(
                REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml",
                contract_dir / "chain-package-contract.yaml",
            )
            shutil.copytree(
                REPO_ROOT / "templates/chain-package",
                root / "templates/chain-package",
            )
            mutate(root)
            return self.findings("check_c9_template_packages", root)

    def mutated_spec_package_findings(self, mutate):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract_dir = root / "contracts" / "artifacts"
            contract_dir.mkdir(parents=True)
            for filename in (
                "chain-package-contract.yaml",
                "spec-package-contract.yaml",
            ):
                shutil.copy2(
                    REPO_ROOT / "contracts/artifacts" / filename,
                    contract_dir / filename,
                )
            shutil.copytree(
                REPO_ROOT / "templates/chain-package",
                root / "templates/chain-package",
            )
            shutil.copytree(
                REPO_ROOT / "templates/spec-package",
                root / "templates/spec-package",
            )
            mutate(root)
            return self.findings("check_c9_template_packages", root)

    def render_chain_package(self, package, *, case_type="main_path", include_oracle=False):
        shutil.copytree(REPO_ROOT / "templates/chain-package", package)
        values = {
            "behavior_spec_id": "BS-1",
            "behavior_spec_version": "1",
            "behavior_case_id": "BC-1",
            "behavior_case_type": case_type,
            "behavior_case_ref": "BC-1",
            "test_space_id": "TS-1",
            "coverage_id": "COV-1",
            "coverage_ref": "COV-1",
            "combination_id": "COMB-1",
            "dimension_id": "dimension",
            "dimension_value": "member",
            "generator_kind": "covering_array",
            "interaction_strength": "2",
            "generation_budget": "16",
            "coverage_status": "planned",
            "derivation_status": "derived",
            "case_relation": "positive",
            "inventory_partition_ref": "PART-1",
            "inventory_member_ref": "MEMBER-1",
            "coverage_obligation_id": "OBL-1",
            "case_type": case_type,
            "requirement_ref": "REQ-1",
            "semantic_inventory_ref": "INV-1@hash",
            "behavior_spec_ref": "BS-1",
            "acceptance_coverage_ref": "COV-1",
            "pre_failure_state": "PRE",
            "failure_terminal": "FAILED",
            "recovery_action": "RECOVER",
            "post_recovery_invariants": "STABLE",
            "idempotency_or_side_effect_oracle": "IDEMPOTENT",
            "compensation_ref": "NONE",
        }
        pattern = re.compile(r"{{([a-zA-Z0-9_]+)}}")
        for path in package.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            text = pattern.sub(lambda match: values.get(match.group(1), "value"), text)
            path.write_text(text, encoding="utf-8")

        acceptance = package / "acceptance.md"
        text = acceptance.read_text(encoding="utf-8")
        text = text.replace(
            '{"dimension":["member"]}',
            '{"locale":["a","b"],"surface":["api","ui"]}',
            1,
        )
        source_row = (
            '| `COMB-1` | `TS-1` | `{"dimension":"member"}` | `value` | `derived` |'
        )
        combination_rows = "\n".join(
            f'| `COMB-{index}` | `TS-1` | `{{"locale":"{locale}","surface":"{surface}"}}` | `INV-1@hash` | `derived` |'
            for index, (locale, surface) in enumerate(
                (("a", "api"), ("a", "ui"), ("b", "api"), ("b", "ui")),
                1,
            )
        )
        text = text.replace(source_row, combination_rows, 1)
        oracle_row = (
            "| `COV-1` | `PRE` | `FAILED` | `RECOVER` | `STABLE` | `IDEMPOTENT` | `NONE` |"
        )
        if not include_oracle:
            text = text.replace(oracle_row + "\n", "", 1)
        acceptance.write_text(text, encoding="utf-8")

    def render_spec_package(self, package):
        shutil.copytree(REPO_ROOT / "templates/spec-package", package)
        values = {
            "spec_id": "SPEC-1",
            "behavior_specification_ref": "BS-1",
            "behavior_case_registry_ref": "scenarios.md#behavior-case-registry:*",
            "behavior_case_ref": "BC-1",
            "acceptance_coverage_ref": "COV-1",
            "criterion_ref": "CRIT-1",
            "requirement_ref": "REQ-1",
            "task_ref": "TASK-1",
        }
        pattern = re.compile(r"{{([a-zA-Z0-9_]+)}}")
        for path in package.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            text = pattern.sub(lambda match: values.get(match.group(1), "value"), text)
            path.write_text(text, encoding="utf-8")

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

    def test_c9_rejects_markdown_table_column_drift(self):
        def mutate(root):
            path = root / "templates/chain-package/scenarios.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace(" | `coverage_target` |", " |", 1), encoding="utf-8")

        findings = self.mutated_chain_package_findings(mutate)
        self.assertTrue(
            any(
                "Behavior Case Registry" in item.message
                and ("columns" in item.message or "separator" in item.message)
                for item in findings
            )
        )

    def test_c9_rejects_duplicate_markdown_primary_key(self):
        def mutate(root):
            path = root / "templates/chain-package/scenarios.md"
            text = path.read_text(encoding="utf-8")
            row = "| `{{behavior_case_id}}` | `{{requirement_ref}}` | `{{behavior_case_type}}` | `{{representative_scenario_or_trigger}}` | `{{expected_user_observable_behavior}}` | `{{coverage_target}}` |"
            path.write_text(text.replace(row, f"{row}\n{row}", 1), encoding="utf-8")

        findings = self.mutated_chain_package_findings(mutate)
        self.assertTrue(any("duplicate primary key" in item.message for item in findings))

    def test_c9_rejects_duplicate_declared_markdown_section(self):
        def mutate(root):
            path = root / "templates/chain-package/scenarios.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n## Behavior Case Registry\n",
                encoding="utf-8",
            )

        findings = self.mutated_chain_package_findings(mutate)
        self.assertTrue(any("duplicate section" in item.message for item in findings))

    def test_c9_rejects_invalid_markdown_enum_value(self):
        def mutate(root):
            path = root / "templates/chain-package/scenarios.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("`{{behavior_case_type}}`", "`unsupported_type`", 1), encoding="utf-8")

        findings = self.mutated_chain_package_findings(mutate)
        self.assertTrue(any("case_type" in item.message and "allowed enum" in item.message for item in findings))

    def test_c9_rejects_unresolved_canonical_root_reference(self):
        def mutate(root):
            path = root / "templates/chain-package/chain.yaml"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("scenarios.md#behavior-specification", "scenarios.md#missing-section", 1), encoding="utf-8")

        findings = self.mutated_chain_package_findings(mutate)
        self.assertTrue(any("unresolved canonical reference" in item.message for item in findings))

    def test_c9_profile_dispatch_is_explicit_and_contract_versioned(self):
        contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            checker.validate_profile_dispatch(contract, "chain-package-contract@2", "s4_exit"),
            [],
        )
        mismatch = checker.validate_profile_dispatch(
            contract, "chain-package-contract@2", "historical_read_v1"
        )
        unknown = checker.validate_profile_dispatch(
            contract, "chain-package-contract@2", "implicit_default"
        )
        self.assertTrue(any("profile_contract_mismatch" in message for message in mismatch))
        self.assertTrue(any("unknown_profile" in message for message in unknown))

    def test_c9_profile_schema_rejects_removed_stage_required_tables(self):
        def mutate(root):
            path = root / "contracts/artifacts/chain-package-contract.yaml"
            contract = yaml.safe_load(path.read_text(encoding="utf-8"))
            del contract["validation_profiles"]["s4_exit"]["required_tables"]
            path.write_text(
                yaml.safe_dump(contract, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

        findings = self.mutated_chain_package_findings(mutate)
        self.assertTrue(
            any("s4_exit" in item.message and "required_tables" in item.message for item in findings)
        )

    def test_c9_spec_rejects_task_without_behavior_case_refs(self):
        def mutate(root):
            path = root / "templates/spec-package/tasks.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    '    behavior_case_refs:\n      - "{{behavior_case_ref}}"\n',
                    "",
                    1,
                ),
                encoding="utf-8",
            )

        findings = self.mutated_spec_package_findings(mutate)
        self.assertTrue(any("behavior_case_refs" in item.message for item in findings))

    def test_c9_spec_rejects_orphan_cross_package_coverage_ref(self):
        def mutate(root):
            path = root / "templates/spec-package/acceptance.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("`{{acceptance_coverage_ref}}`", "`COV-ORPHAN`", 1),
                encoding="utf-8",
            )

        findings = self.mutated_spec_package_findings(mutate)
        self.assertTrue(
            any("COV-ORPHAN" in item.message and "unresolved" in item.message for item in findings)
        )

    def test_package_profile_reads_real_v1_shape_but_blocks_stage_exit(self):
        contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir)
            shape = contract["historical_package_shapes"][1]
            for filename in shape["required_files"]:
                path = package / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            (package / "chain.yaml").write_text(
                "schema_version: 1\nchain_id: CHAIN-V1\npriority: p1\nowners: {}\n"
                "path_types: [normal, exception, recovery]\nscenario_refs: [SC-1]\n"
                "trigger_refs: [TR-1]\ndiagram_policy:\n  required_priorities: [p0, p1]\n"
                "  requirement: required\n",
                encoding="utf-8",
            )
            (package / "triggers.yaml").write_text(
                "schema_version: 1\nchain_ref: CHAIN-V1\ntrigger_profiles: []\n",
                encoding="utf-8",
            )
            (package / "io-map.yaml").write_text(
                "schema_version: 1\nchain_ref: CHAIN-V1\nproducer: P\nconsumer: C\ninputs: []\noutputs: []\n",
                encoding="utf-8",
            )
            for filename, sections in shape["required_sections"].items():
                (package / filename).write_text(
                    "\n".join(f"## {section}" for section in sections) + "\n",
                    encoding="utf-8",
                )

            self.assertEqual(
                checker.validate_package_profile(
                    contract,
                    package,
                    "chain-package-contract@1",
                    "historical_read_v1",
                ),
                [],
            )
            errors = checker.validate_package_profile(
                contract, package, "chain-package-contract@1", "s2_exit"
            )
            self.assertTrue(any("profile_contract_mismatch" in message for message in errors))

    def test_spec_profile_reads_real_v1_shape_but_blocks_stage_exit(self):
        contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/spec-package-contract.yaml").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir)
            shape = contract["historical_package_shapes"][1]
            for filename in shape["required_files"]:
                path = package / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("", encoding="utf-8")
            for filename, sections in shape["required_sections"].items():
                (package / filename).write_text(
                    "\n".join(f"## {section}" for section in sections) + "\n",
                    encoding="utf-8",
                )
            self.assertEqual(
                checker.validate_package_profile(
                    contract,
                    package,
                    "spec-package-contract@1",
                    "historical_read_v1",
                ),
                [],
            )
            errors = checker.validate_package_profile(
                contract, package, "spec-package-contract@1", "s5_exit"
            )
            self.assertTrue(any("profile_contract_mismatch" in message for message in errors))

    def test_real_package_profile_rejects_unresolved_template_placeholders(self):
        contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "chain"
            shutil.copytree(REPO_ROOT / "templates/chain-package", package)
            errors = checker.validate_package_profile(
                contract, package, "chain-package-contract@2", "s2_exit"
            )
            self.assertTrue(any("unresolved template placeholder" in message for message in errors))

    def test_s4_profile_recomputes_pair_obligations_when_dimension_domain_changes(self):
        contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "chain"
            self.render_chain_package(package)
            self.assertEqual(
                checker.validate_package_profile(
                    contract, package, "chain-package-contract@2", "s4_exit"
                ),
                [],
            )
            acceptance = package / "acceptance.md"
            text = acceptance.read_text(encoding="utf-8").replace(
                '"locale":["a","b"]',
                '"locale":["a","b","c"]',
                1,
            )
            acceptance.write_text(text, encoding="utf-8")
            errors = checker.validate_package_profile(
                contract, package, "chain-package-contract@2", "s4_exit"
            )
            self.assertTrue(any("locale=\"c\"" in message for message in errors))

    def test_s4_profile_recomputes_per_member_obligations_when_inventory_changes(self):
        contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "chain"
            self.render_chain_package(package)
            acceptance = package / "acceptance.md"
            text = acceptance.read_text(encoding="utf-8").replace(
                '{"PART-1":["MEMBER-1"]}',
                '{"PART-1":["MEMBER-1","MEMBER-2"]}',
                1,
            )
            acceptance.write_text(text, encoding="utf-8")
            errors = checker.validate_package_profile(
                contract, package, "chain-package-contract@2", "s4_exit"
            )
            self.assertTrue(
                any("OBL-1/MEMBER-2/positive" in message for message in errors)
            )

    def test_s5_spec_profile_executes_chain_prerequisite_and_cross_package_refs(self):
        chain_contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml").read_text(encoding="utf-8")
        )
        spec_contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/spec-package-contract.yaml").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            chain_package = root / "chain"
            spec_package = root / "spec"
            self.render_chain_package(chain_package)
            self.render_spec_package(spec_package)
            related = {"chain-package-contract@2": (chain_contract, chain_package)}
            self.assertEqual(
                checker.validate_package_profile(
                    spec_contract,
                    spec_package,
                    "spec-package-contract@2",
                    "s5_exit",
                    related,
                ),
                [],
            )

            tasks = spec_package / "tasks.md"
            tasks.write_text(
                tasks.read_text(encoding="utf-8").replace("BC-1", "BC-ORPHAN", 1),
                encoding="utf-8",
            )
            errors = checker.validate_package_profile(
                spec_contract,
                spec_package,
                "spec-package-contract@2",
                "s5_exit",
                related,
            )
            self.assertTrue(
                any("unresolved Behavior Case reference: BC-ORPHAN" in message for message in errors)
            )

    def test_failure_recovery_oracle_is_conditional_and_cross_table_checked(self):
        contract = yaml.safe_load(
            (REPO_ROOT / "contracts/artifacts/chain-package-contract.yaml").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            main_path_package = root / "main"
            self.render_chain_package(main_path_package, case_type="main_path", include_oracle=False)
            self.assertEqual(
                checker.validate_package_profile(
                    contract, main_path_package, "chain-package-contract@2", "s4_exit"
                ),
                [],
            )

            recovery_package = root / "recovery"
            self.render_chain_package(
                recovery_package,
                case_type="failure_recovery",
                include_oracle=False,
            )
            errors = checker.validate_package_profile(
                contract, recovery_package, "chain-package-contract@2", "s4_exit"
            )
            self.assertTrue(any("failure_recovery coverage has no oracle" in message for message in errors))

            complete_package = root / "complete"
            self.render_chain_package(
                complete_package,
                case_type="failure_recovery",
                include_oracle=True,
            )
            self.assertEqual(
                checker.validate_package_profile(
                    contract, complete_package, "chain-package-contract@2", "s4_exit"
                ),
                [],
            )

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

    def test_c11_accepts_versions_explicitly_declared_historical_read_only(self):
        findings = self.findings("check_c11_authority_and_contract_references", REPO_ROOT)
        messages = [finding.message for finding in findings]
        self.assertFalse(any("chain-package-contract@1" in message for message in messages))
        self.assertFalse(any("spec-package-contract@1" in message for message in messages))

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
