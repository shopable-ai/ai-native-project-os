import unittest
from collections import defaultdict
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]

MOVED_CONTRACTS = {
    "acceptance-verdict-claim-contract.yaml",
    "ai-review-verdict-contract.yaml",
    "authorization-snapshot-contract.yaml",
    "control-set-contract.yaml",
    "governance-rule-set-contract.yaml",
    "overlay-activation-verdict-contract.yaml",
    "route-decision-contract.yaml",
    "rule-gap-case-contract.yaml",
}
GOVERNANCE_CONTRACTS = MOVED_CONTRACTS | {
    "project-instance-contract.yaml",
    "run-evidence-contract.yaml",
    "stage-exit-gates-contract.yaml",
}
STAGES = ["R0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]
STAGE_SECTIONS = {
    "required_inputs",
    "required_artifacts",
    "exit_criteria",
    "evidence_requirements",
    "invalidation_triggers",
    "reopen_targets",
}
STAGE_GATE_RECORD_FIELDS = {
    "stage",
    "scope",
    "work_status",
    "approval_status",
    "implementation_status",
    "proof_level",
    "framework_edition",
    "governance_profile",
    "stage_definition_ref",
    "stage_definition_hash",
    "exit_criterion_results",
    "required_object_refs",
    "required_proof_level",
    "verification_commands",
    "result",
    "uncovered_items",
    "waivers",
    "approved_by",
    "verified_by",
    "checked_at",
    "valid_until",
    "invalidation_conditions",
    "reopen_target",
    "evidence_refs",
    "evidence_hashes",
}
EXIT_CRITERION_RESULT_FIELDS = {
    "criterion_ref",
    "criterion_hash",
    "status",
    "evidence_refs",
    "waiver_ref",
}
HISTORICAL_STALE_REFERENCE_ALLOWLIST = {
    ROOT / "reviews" / "human-governed-ai-review-adversarial.yaml",
    ROOT / "reviews" / "profile-taxonomy-alignment-resolution.yaml",
    ROOT / "reviews" / "profile-taxonomy-file-audit.yaml",
}
YAML_CONTRACT_ID_EXCLUDED_ROOTS = {
    ROOT / ".git",
    ROOT / ".worktrees",
    ROOT / "fixtures",
    ROOT / "tests" / "fixtures",
    ROOT / "tests" / "checker-negative",
    ROOT / "tests" / "checker_negative",
}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class ContractPolicyBoundaryTests(unittest.TestCase):
    def test_policies_contains_only_policy_authority_and_navigation(self):
        policy_files = {path.name for path in (ROOT / "policies").iterdir() if path.is_file()}

        self.assertEqual(policy_files, {"README.md", "project-governance-routing.yaml"})
        self.assertEqual(list((ROOT / "policies").glob("*-contract.yaml")), [])
        for name in MOVED_CONTRACTS:
            self.assertFalse((ROOT / "policies" / name).exists())

    def test_governance_contracts_have_one_exact_authority_location(self):
        contract_dir = ROOT / "contracts" / "governance"
        contract_files = {path.name for path in contract_dir.glob("*.yaml")}

        self.assertEqual(contract_files, GOVERNANCE_CONTRACTS)
        for name in MOVED_CONTRACTS:
            contract = load_yaml(contract_dir / name)
            self.assertEqual(contract["contract_id"], Path(name).stem)

    def test_project_os_authority_resolves_every_governance_contract(self):
        project_os = load_yaml(ROOT / "project-os.yaml")
        authority = project_os["authority"]

        for name in MOVED_CONTRACTS:
            key = Path(name).stem.replace("-", "_")
            expected = f"contracts/governance/{name}"
            self.assertEqual(authority[key], expected)
            self.assertTrue((ROOT / authority[key]).is_file())
        self.assertEqual(
            authority["stage_exit_gates_contract"],
            "contracts/governance/stage-exit-gates-contract.yaml",
        )
        self.assertTrue((ROOT / authority["stage_exit_gates_contract"]).is_file())
        self.assertEqual(
            authority["run_evidence_contract"],
            "contracts/governance/run-evidence-contract.yaml",
        )
        self.assertTrue((ROOT / authority["run_evidence_contract"]).is_file())

    def test_governance_contract_ids_are_unique_and_only_declared_by_authority_targets(self):
        project_os = load_yaml(ROOT / "project-os.yaml")
        authority_targets = list(project_os["authority"].values())
        contract_occurrences = defaultdict(list)

        yaml_paths = sorted([*ROOT.rglob("*.yaml"), *ROOT.rglob("*.yml")])
        for path in yaml_paths:
            if any(root == path or root in path.parents for root in YAML_CONTRACT_ID_EXCLUDED_ROOTS):
                continue
            document = load_yaml(path)
            if isinstance(document, dict) and "contract_id" in document:
                contract_occurrences[document["contract_id"]].append(
                    path.relative_to(ROOT).as_posix()
                )

        for name in GOVERNANCE_CONTRACTS:
            expected_path = f"contracts/governance/{name}"
            contract_id = Path(name).stem
            self.assertEqual(authority_targets.count(expected_path), 1)
            self.assertEqual(contract_occurrences[contract_id], [expected_path])

    def test_active_references_do_not_use_retired_policy_contract_paths(self):
        excluded_roots = {
            ROOT / "docs" / "superpowers" / "plans",
            ROOT / "docs" / "superpowers" / "specs",
            ROOT / ".shopme",
            ROOT / ".worktrees",
            ROOT / ".git",
        }
        excluded_file = ROOT / "decisions" / "ADR-0004-separate-contracts-from-policies.md"
        stale_references = []

        for path in ROOT.rglob("*"):
            if not path.is_file() or path == excluded_file:
                continue
            if any(root == path or root in path.parents for root in excluded_roots):
                continue
            if path.suffix not in {".md", ".py", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for name in MOVED_CONTRACTS:
                stale = f"policies/{name}"
                if stale in text and path not in HISTORICAL_STALE_REFERENCE_ALLOWLIST:
                    stale_references.append(f"{path.relative_to(ROOT)}: {stale}")

        self.assertEqual(stale_references, [])

    def test_stage_exit_gate_contract_covers_exactly_nine_fail_closed_stages(self):
        contract_path = ROOT / "contracts" / "governance" / "stage-exit-gates-contract.yaml"
        self.assertTrue(contract_path.is_file())
        contract = load_yaml(contract_path)

        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(contract["contract_id"], "stage-exit-gates-contract")
        self.assertEqual(contract["version"], 1)
        self.assertEqual(list(contract["stages"]), STAGES)
        for stage, definition in contract["stages"].items():
            self.assertEqual(set(definition), STAGE_SECTIONS, stage)
            for section in STAGE_SECTIONS:
                self.assertIsInstance(definition[section], list, f"{stage}.{section}")
                self.assertTrue(definition[section], f"{stage}.{section}")

        record = contract["stage_gate_record"]
        self.assertTrue(STAGE_GATE_RECORD_FIELDS <= set(record["required_fields"]))
        self.assertEqual(record["enums"]["result"], ["passed", "failed", "unknown"])
        self.assertEqual(record["fail_closed_results"], ["failed", "unknown"])
        self.assertIn("failed_or_unknown_result_blocks_stage_exit", record["invariants"])
        self.assertIn("required_proof_level_is_gate_target", record["invariants"])
        self.assertIn("proof_level_is_actual_evidence_coordinate", record["invariants"])
        criterion_result = record["exit_criterion_result"]
        self.assertEqual(set(criterion_result["required_fields"]), EXIT_CRITERION_RESULT_FIELDS)
        self.assertEqual(
            criterion_result["enums"]["status"],
            ["passed", "waived", "failed", "unknown"],
        )
        self.assertIn(
            "exit_criterion_results_exactly_cover_stage_exit_criteria_once",
            record["invariants"],
        )
        self.assertIn(
            "passed_criterion_requires_non_empty_evidence_refs",
            record["invariants"],
        )
        self.assertIn(
            "waived_criterion_requires_valid_unexpired_scope_matched_waiver",
            record["invariants"],
        )
        self.assertIn(
            "failed_unknown_or_missing_criterion_blocks_stage_exit",
            record["invariants"],
        )
        self.assertIn(
            "stage_definition_ref_and_hash_must_exactly_match_evaluated_stage_definition",
            record["invariants"],
        )
        self.assertEqual(
            contract["independent_axes"],
            [
                "stage",
                "work_status",
                "approval_status",
                "implementation_status",
                "proof_level",
                "framework_edition",
                "governance_profile",
            ],
        )
        self.assertIn(
            "independent_axes_must_not_be_collapsed_or_inferred_from_each_other",
            contract["invariants"],
        )

        manifest = contract["manifest_example"]
        self.assertTrue(set(record["required_fields"]) <= set(manifest))
        record_axes = contract["independent_axes"][1:]
        for axis in record_axes:
            self.assertIn(axis, manifest)
            self.assertNotIn(manifest[axis], (None, ""))
        self.assertNotIn("status", manifest)
        self.assertNotIn("profile", manifest)
        self.assertTrue(manifest["stage_definition_ref"])
        self.assertTrue(manifest["stage_definition_hash"])
        self.assertEqual(
            len(manifest["exit_criterion_results"]),
            len(contract["stages"][manifest["stage"]]["exit_criteria"]),
        )
        for result in manifest["exit_criterion_results"]:
            self.assertEqual(set(result), EXIT_CRITERION_RESULT_FIELDS)
            self.assertEqual(result["status"], "passed")
            self.assertTrue(result["evidence_refs"])
        self.assertNotEqual(
            contract["field_semantics"]["required_proof_level"],
            contract["field_semantics"]["proof_level"],
        )

        negative_examples = contract["negative_examples"]
        expected_negative_examples = {
            "missing_axis",
            "mixed_axis",
            "unknown_axis",
            "missing_criterion",
            "failed_criterion",
            "missing_evidence",
            "stale_waiver",
        }
        self.assertTrue(expected_negative_examples <= set(negative_examples))
        for name in expected_negative_examples:
            self.assertEqual(negative_examples[name]["result"], "blocked")
            self.assertEqual(negative_examples[name]["handling"], "fail_closed")
        self.assertIn("missing_fields", negative_examples["missing_axis"])
        self.assertIn("status", negative_examples["mixed_axis"]["invalid_fields"])
        self.assertIn("profile", negative_examples["mixed_axis"]["invalid_fields"])
        self.assertIn("axis", negative_examples["unknown_axis"])

    def test_contract_and_policy_readmes_are_problem_navigation_not_field_copies(self):
        contracts_readme_path = ROOT / "contracts" / "README.md"
        self.assertTrue(contracts_readme_path.is_file())
        contracts_readme = contracts_readme_path.read_text(encoding="utf-8")
        policies_readme = (ROOT / "policies" / "README.md").read_text(encoding="utf-8")
        navigation_columns = ["问题", "时机", "输入", "输出", "文件", "示例", "下一步"]

        for readme in (contracts_readme, policies_readme):
            for column in navigation_columns:
                self.assertIn(column, readme)
            self.assertNotIn("required_fields", readme)
            self.assertNotIn("枚举清单", readme)

        self.assertIn("contracts/governance/", contracts_readme)
        self.assertIn("project-governance-routing.yaml", policies_readme)
        self.assertIn("契约 ID", policies_readme)
        self.assertIn("contracts/governance/", policies_readme)


if __name__ == "__main__":
    unittest.main()
