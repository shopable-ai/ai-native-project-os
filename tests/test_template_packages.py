import re
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]

PACKAGE_CONTRACTS = {
    "chain-package-contract": (
        "contracts/artifacts/chain-package-contract.yaml",
        "templates/chain-package",
    ),
    "spec-package-contract": (
        "contracts/artifacts/spec-package-contract.yaml",
        "templates/spec-package",
    ),
    "io-contract": (
        "contracts/io/io-contract.yaml",
        "templates/io-contract",
    ),
    "workflow-contract": (
        "contracts/execution/workflow-contract.yaml",
        "templates/workflow",
    ),
    "skill-contract": (
        "contracts/execution/skill-contract.yaml",
        "templates/skill",
    ),
    "project-instance-contract": (
        "contracts/governance/project-instance-contract.yaml",
        "templates/project-instance",
    ),
}

PACKAGE_AUTHORITY = {
    "chain-package-contract": "chain_package_contract",
    "spec-package-contract": "spec_package_contract",
    "io-contract": "io_contract",
    "workflow-contract": "workflow_contract",
    "skill-contract": "skill_contract",
    "project-instance-contract": "project_instance_contract",
}

PLACEHOLDER_RE = re.compile(r"\{\{([^{}]+)\}\}")
SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
RUNTIME_DIRS = {"Run", "Evidence", "Verdict", "Claim", "artifacts"}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def nested_value(document, dotted_path: str):
    current = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_path)
        current = current[part]
    return current


def validate_package(contract: dict, package_root: Path) -> list[str]:
    errors = []
    for directory_name in sorted(RUNTIME_DIRS):
        if (package_root / directory_name).is_dir():
            errors.append(
                "runtime generated directory must not be precreated: "
                f"{directory_name}"
            )

    for relative_path in contract["required_files"]:
        if not (package_root / relative_path).is_file():
            errors.append(f"missing required file: {relative_path}")

    for relative_path, fields in contract.get("required_fields", {}).items():
        path = package_root / relative_path
        if not path.is_file():
            continue
        try:
            document = load_yaml(path)
        except yaml.YAMLError as exc:
            errors.append(f"invalid yaml: {relative_path}: {exc}")
            continue
        for field in fields:
            try:
                nested_value(document, field)
            except KeyError:
                errors.append(f"missing required field: {relative_path}:{field}")

    for relative_path, required_values in contract.get("required_values", {}).items():
        path = package_root / relative_path
        if not path.is_file():
            continue
        try:
            document = load_yaml(path)
        except yaml.YAMLError as exc:
            errors.append(f"invalid yaml: {relative_path}: {exc}")
            continue
        for field, expected_value in required_values.items():
            try:
                actual_value = nested_value(document, field)
            except KeyError:
                errors.append(f"missing required field: {relative_path}:{field}")
                continue
            if actual_value != expected_value:
                errors.append(
                    "unexpected required value: "
                    f"{relative_path}:{field}={actual_value}"
                )

    for relative_path, sections in contract.get("required_sections", {}).items():
        path = package_root / relative_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for section in sections:
            if not re.search(rf"^#+\s+{re.escape(section)}\s*$", text, re.MULTILINE):
                errors.append(f"missing required section: {relative_path}:{section}")

    task_authority = contract.get("task_authority")
    if task_authority:
        marker_rules = (
            (
                task_authority["declaration_marker"],
                task_authority["declarations_allowed_only_in"],
                "task declaration marker is only allowed in",
            ),
            (
                task_authority["reference_marker"],
                task_authority["references_allowed_in"],
                "task reference marker is only allowed in",
            ),
        )
        for marker, allowed_file, error_prefix in marker_rules:
            marker_token = f"{marker}:"
            allowed_path = package_root / allowed_file
            if allowed_path.is_file() and marker_token not in allowed_path.read_text(
                encoding="utf-8"
            ):
                errors.append(f"missing task authority marker: {allowed_file}:{marker}")
            for path in package_root.rglob("*.md"):
                relative_path = path.relative_to(package_root).as_posix()
                if relative_path == allowed_file:
                    continue
                if marker_token in path.read_text(encoding="utf-8"):
                    errors.append(f"{error_prefix} {allowed_file}: {relative_path}")
    return errors


class TemplatePackageTests(unittest.TestCase):
    def existing_contracts(self):
        paths = [ROOT / contract_path for contract_path, _ in PACKAGE_CONTRACTS.values()]
        self.assertTrue(all(path.is_file() for path in paths))
        return paths

    def test_all_machine_contracts_exist_and_register_the_template_roots(self):
        missing = []
        for contract_id, (contract_path, template_root) in PACKAGE_CONTRACTS.items():
            path = ROOT / contract_path
            if not path.is_file():
                missing.append(contract_path)
                continue
            contract = load_yaml(path)
            self.assertEqual(contract["schema_version"], 1)
            self.assertEqual(contract["contract_id"], contract_id)
            self.assertEqual(contract["version"], 1)
            self.assertEqual(contract["template_root"], template_root)
            self.assertTrue(contract["required_files"])
            self.assertTrue(
                contract.get("required_fields") or contract.get("required_sections")
            )
            self.assertTrue(contract["failure_semantics"])
            self.assertTrue(contract["compatibility"])
        self.assertEqual(missing, [])

    def test_contracts_drive_valid_positive_template_examples(self):
        for contract_path in self.existing_contracts():
            contract = load_yaml(contract_path)
            package_root = ROOT / contract["template_root"]
            with self.subTest(contract=contract["contract_id"]):
                self.assertEqual(validate_package(contract, package_root), [])

    def test_every_template_yaml_parses_and_quotes_snake_case_placeholders(self):
        for contract_path in self.existing_contracts():
            contract = load_yaml(contract_path)
            package_root = ROOT / contract["template_root"]
            for path in package_root.rglob("*"):
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8")
                for placeholder in PLACEHOLDER_RE.findall(text):
                    self.assertRegex(placeholder, SNAKE_CASE_RE, str(path))
                if path.suffix not in {".yaml", ".yml"}:
                    continue
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertIsNotNone(yaml.safe_load(text))
                    for line in text.splitlines():
                        if "{{" not in line or line.lstrip().startswith("#"):
                            continue
                        for match in PLACEHOLDER_RE.finditer(line):
                            placeholder = match.group(0)
                            scalar = line.strip()
                            if scalar.startswith("- "):
                                scalar = scalar[2:].strip()
                            if ":" in scalar:
                                scalar = scalar.split(":", 1)[1].strip()
                            self.assertTrue(
                                (
                                    scalar.startswith('"') and scalar.endswith('"')
                                )
                                or (
                                    scalar.startswith("'") and scalar.endswith("'")
                                ),
                                f"YAML placeholder must be quoted: {path}:{line}",
                            )

    def test_package_readmes_start_with_problem_navigation_and_classified_tree(self):
        readmes = [ROOT / "templates" / "README.md"]
        for contract_path in self.existing_contracts():
            contract = load_yaml(contract_path)
            readmes.extend((ROOT / contract["template_root"]).rglob("README.md"))

        for readme in readmes:
            text = readme.read_text(encoding="utf-8")
            opening = "\n".join(text.splitlines()[:30])
            with self.subTest(readme=readme.relative_to(ROOT)):
                for label in ("问题", "时机", "输入", "输出", "下一步"):
                    self.assertIn(label, opening)
                for classification in ("必需", "条件启用", "运行时生成"):
                    self.assertIn(classification, text)
                self.assertIn("```text", text)

    def test_chain_package_covers_complete_paths_and_p0_p1_diagrams(self):
        self.existing_contracts()
        chain = load_yaml(ROOT / "templates/chain-package/chain.yaml")
        self.assertEqual(
            chain["path_types"],
            ["normal", "exception", "recovery"],
        )
        self.assertEqual(chain["diagram_policy"]["required_priorities"], ["p0", "p1"])
        self.assertEqual(chain["diagram_policy"]["requirement"], "required")
        required_files = set(
            load_yaml(ROOT / PACKAGE_CONTRACTS["chain-package-contract"][0])[
                "required_files"
            ]
        )
        self.assertTrue(
            {
                "responsibility-map.md",
                "io-map.yaml",
                "traceability.md",
                "acceptance.md",
                "diagrams/README.md",
            }
            <= required_files
        )

    def test_spec_tasks_are_authority_and_plans_only_order_task_refs(self):
        self.existing_contracts()
        tasks = (ROOT / "templates/spec-package/tasks.md").read_text(encoding="utf-8")
        plan = (ROOT / "templates/spec-package/plan.md").read_text(encoding="utf-8")
        readme = (ROOT / "templates/spec-package/README.md").read_text(encoding="utf-8")
        self.assertIn("单个 Spec 任务的唯一权威", tasks)
        self.assertIn("task_refs", plan)
        self.assertIn("只排序", plan)
        self.assertIn("跨 Spec task-tree", readme)
        self.assertIn("只生成视图", readme)

    def test_io_contract_covers_operational_protocol_boundaries(self):
        self.existing_contracts()
        io_contract = load_yaml(ROOT / "templates/io-contract/io-contract.yaml")
        required = {
            "producer",
            "consumer",
            "schemas",
            "envelopes",
            "error_taxonomy",
            "retry",
            "idempotency",
            "timeout",
            "ordering",
            "partial_results",
            "data_classification",
            "compatibility",
            "contract_tests",
            "migration",
        }
        self.assertTrue(required <= set(io_contract))
        self.assertEqual(set(io_contract["schemas"]), {"request", "event", "result"})
        self.assertEqual(set(io_contract["envelopes"]), {"success", "failure"})

    def test_workflow_has_task_refs_and_bounded_execution_semantics(self):
        self.existing_contracts()
        workflow = load_yaml(ROOT / "templates/workflow/workflow.yaml")
        required = {
            "task_refs",
            "step_graph",
            "io_contract_refs",
            "permissions",
            "budget",
            "timeout",
            "retry",
            "checkpoint",
            "cancel",
            "compensation",
            "failure_routes",
            "terminal_states",
            "evidence_output",
            "claim_ceiling",
        }
        self.assertTrue(required <= set(workflow))
        self.assertTrue(workflow["task_refs"])
        self.assertTrue(workflow["step_graph"]["nodes"])

    def test_skill_is_local_and_cannot_be_a_cross_stage_workflow(self):
        self.existing_contracts()
        skill = load_yaml(ROOT / "templates/skill/skill.yaml")
        self.assertEqual(skill["workflow_scope"], "single_stage_only")
        self.assertEqual(skill["cross_stage_workflow"], "forbidden")
        self.assertTrue(skill["consumers"])
        self.assertTrue(skill["local_responsibility"])
        for field in (
            "io_contract_refs",
            "model_code_boundary",
            "permissions",
            "failure_semantics",
            "evaluation",
            "version",
            "compatibility",
        ):
            self.assertIn(field, skill)

    def test_l3_instance_documents_runtime_outputs_without_precreating_them(self):
        self.existing_contracts()
        package_root = ROOT / "templates/project-instance"
        actual_dirs = {
            path.name for path in package_root.iterdir() if path.is_dir()
        }
        self.assertEqual(actual_dirs & RUNTIME_DIRS, set())
        readme = (package_root / "README.md").read_text(encoding="utf-8")
        for name in ("Run", "Evidence", "Verdict", "Claim", "artifacts/"):
            self.assertIn(name, readme)
        self.assertIn("运行时生成", readme)
        route_lock = load_yaml(package_root / "governance-route.yaml")
        self.assertIn("namespace", route_lock)
        self.assertIn("route_lock", route_lock)
        self.assertIn("data_boundaries", route_lock)

        contract = load_yaml(
            ROOT / PACKAGE_CONTRACTS["project-instance-contract"][0]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            copied_root = Path(temp_dir) / "project-instance"
            shutil.copytree(package_root, copied_root)
            (copied_root / "Run").mkdir()
            self.assertIn(
                "runtime generated directory must not be precreated: Run",
                validate_package(contract, copied_root),
            )

    def test_standard_and_brownfield_templates_remain_l2_entrypoints(self):
        standard = (ROOT / "templates/standard-project/README.md").read_text(
            encoding="utf-8"
        )
        brownfield = (ROOT / "templates/brownfield-project/README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("L2", standard)
        self.assertIn("Greenfield", standard)
        self.assertIn("L2", brownfield)
        self.assertIn("Brownfield", brownfield)
        self.assertIn("L2 根目录", standard)
        self.assertIn("L2 根目录", brownfield)
        self.assertIn("条件启用", standard)
        self.assertIn("projects/{project_id}/", standard)

    def test_validator_rejects_every_declared_missing_file_field_section_and_bad_yaml(self):
        for contract_path in self.existing_contracts():
            contract = load_yaml(contract_path)
            source_root = ROOT / contract["template_root"]
            declared_yaml_files = {
                relative_path
                for relative_path in contract["required_files"]
                if Path(relative_path).suffix in {".yaml", ".yml"}
            }
            self.assertEqual(
                declared_yaml_files,
                set(contract.get("required_fields", {})),
                contract["contract_id"],
            )
            with tempfile.TemporaryDirectory() as temp_dir:
                mutation_root = Path(temp_dir)

                for index, relative_path in enumerate(contract["required_files"]):
                    copied_root = mutation_root / f"missing-file-{index}"
                    shutil.copytree(source_root, copied_root)
                    (copied_root / relative_path).unlink()
                    with self.subTest(
                        contract=contract["contract_id"],
                        mutation="missing-file",
                        target=relative_path,
                    ):
                        self.assertIn(
                            f"missing required file: {relative_path}",
                            validate_package(contract, copied_root),
                        )

                for relative_path, fields in contract.get(
                    "required_fields", {}
                ).items():
                    for index, field in enumerate(fields):
                        copied_root = mutation_root / f"missing-field-{relative_path.replace('/', '-')}-{index}"
                        shutil.copytree(source_root, copied_root)
                        yaml_path = copied_root / relative_path
                        document = load_yaml(yaml_path)
                        parent = document
                        parts = field.split(".")
                        for part in parts[:-1]:
                            parent = parent[part]
                        del parent[parts[-1]]
                        yaml_path.write_text(
                            yaml.safe_dump(
                                document, allow_unicode=True, sort_keys=False
                            ),
                            encoding="utf-8",
                        )
                        with self.subTest(
                            contract=contract["contract_id"],
                            mutation="missing-field",
                            target=f"{relative_path}:{field}",
                        ):
                            self.assertIn(
                                f"missing required field: {relative_path}:{field}",
                                validate_package(contract, copied_root),
                            )

                    copied_root = mutation_root / f"invalid-yaml-{relative_path.replace('/', '-')}"
                    shutil.copytree(source_root, copied_root)
                    (copied_root / relative_path).write_text(
                        "invalid: [yaml\n", encoding="utf-8"
                    )
                    with self.subTest(
                        contract=contract["contract_id"],
                        mutation="invalid-yaml",
                        target=relative_path,
                    ):
                        self.assertTrue(
                            any(
                                error.startswith(f"invalid yaml: {relative_path}:")
                                for error in validate_package(contract, copied_root)
                            )
                        )

                for relative_path, sections in contract.get(
                    "required_sections", {}
                ).items():
                    for index, section in enumerate(sections):
                        copied_root = mutation_root / f"missing-section-{relative_path.replace('/', '-')}-{index}"
                        shutil.copytree(source_root, copied_root)
                        markdown_path = copied_root / relative_path
                        text = markdown_path.read_text(encoding="utf-8")
                        text = re.sub(
                            rf"^(#+\s+){re.escape(section)}\s*$",
                            rf"\1removed-{index}",
                            text,
                            count=1,
                            flags=re.MULTILINE,
                        )
                        markdown_path.write_text(text, encoding="utf-8")
                        with self.subTest(
                            contract=contract["contract_id"],
                            mutation="missing-section",
                            target=f"{relative_path}:{section}",
                        ):
                            self.assertIn(
                                f"missing required section: {relative_path}:{section}",
                                validate_package(contract, copied_root),
                            )

    def test_required_values_reject_cross_stage_skill_mutations(self):
        contract = load_yaml(ROOT / PACKAGE_CONTRACTS["skill-contract"][0])
        expected_values = {
            "skill.yaml": {
                "workflow_scope": "single_stage_only",
                "cross_stage_workflow": "forbidden",
            }
        }
        self.assertEqual(contract.get("required_values"), expected_values)

        source_root = ROOT / contract["template_root"]
        for field, invalid_value in (
            ("workflow_scope", "cross_stage"),
            ("cross_stage_workflow", "allowed"),
        ):
            with tempfile.TemporaryDirectory() as temp_dir:
                copied_root = Path(temp_dir) / "skill"
                shutil.copytree(source_root, copied_root)
                skill_path = copied_root / "skill.yaml"
                skill = load_yaml(skill_path)
                skill[field] = invalid_value
                skill_path.write_text(
                    yaml.safe_dump(skill, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                self.assertIn(
                    f"unexpected required value: skill.yaml:{field}={invalid_value}",
                    validate_package(contract, copied_root),
                )

    def test_spec_task_authority_markers_are_machine_enforced(self):
        contract = load_yaml(ROOT / PACKAGE_CONTRACTS["spec-package-contract"][0])
        expected_boundary = {
            "declaration_marker": "task_declarations",
            "declarations_allowed_only_in": "tasks.md",
            "reference_marker": "task_refs",
            "references_allowed_in": "plan.md",
        }
        self.assertEqual(contract.get("task_authority"), expected_boundary)
        tasks = (ROOT / "templates/spec-package/tasks.md").read_text(encoding="utf-8")
        plan = (ROOT / "templates/spec-package/plan.md").read_text(encoding="utf-8")
        self.assertIn("task_declarations:", tasks)
        self.assertNotIn("task_declarations:", plan)
        self.assertIn("task_refs:", plan)

        source_root = ROOT / contract["template_root"]
        with tempfile.TemporaryDirectory() as temp_dir:
            copied_root = Path(temp_dir) / "spec-package"
            shutil.copytree(source_root, copied_root)
            plan_path = copied_root / "plan.md"
            plan_path.write_text(
                plan_path.read_text(encoding="utf-8")
                + "\n```yaml\ntask_declarations:\n  - task_ref: TASK-BAD\n```\n",
                encoding="utf-8",
            )
            self.assertIn(
                "task declaration marker is only allowed in tasks.md: plan.md",
                validate_package(contract, copied_root),
            )

    def test_project_os_registers_all_six_template_contracts(self):
        self.existing_contracts()
        project_os = load_yaml(ROOT / "project-os.yaml")
        authority = project_os["authority"]
        expected = {
            PACKAGE_AUTHORITY[contract_id]: contract_path
            for contract_id, (contract_path, _) in PACKAGE_CONTRACTS.items()
        }
        self.assertEqual(
            {key: authority.get(key) for key in expected},
            expected,
        )
        for contract_id, authority_key in PACKAGE_AUTHORITY.items():
            target = PACKAGE_CONTRACTS[contract_id][0]
            self.assertEqual(
                [key for key, value in authority.items() if value == target],
                [authority_key],
            )

    def test_six_template_contract_ids_are_unique_at_authority_targets(self):
        target_contract_ids = set(PACKAGE_CONTRACTS)
        excluded_roots = {
            ROOT / ".git",
            ROOT / ".worktrees",
            ROOT / "tests" / "fixtures",
            ROOT / "tests" / "checker-negative",
            ROOT / "tests" / "checker_negative",
        }
        occurrences = {contract_id: [] for contract_id in target_contract_ids}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in {".yaml", ".yml"}:
                continue
            if any(root == path or root in path.parents for root in excluded_roots):
                continue
            document = load_yaml(path)
            if isinstance(document, dict) and document.get("contract_id") in occurrences:
                occurrences[document["contract_id"]].append(
                    path.relative_to(ROOT).as_posix()
                )
        expected = {
            contract_id: [contract_path]
            for contract_id, (contract_path, _) in PACKAGE_CONTRACTS.items()
        }
        self.assertEqual(occurrences, expected)

    def test_package_readme_tree_records_every_declared_and_actual_file(self):
        for contract_path in self.existing_contracts():
            contract = load_yaml(contract_path)
            package_root = ROOT / contract["template_root"]
            readme = (package_root / "README.md").read_text(encoding="utf-8")
            actual_files = {
                path.relative_to(package_root).as_posix()
                for path in package_root.rglob("*")
                if path.is_file()
            }
            declared_files = set(contract["required_files"])
            with self.subTest(contract=contract["contract_id"], kind="coverage"):
                self.assertEqual(actual_files, declared_files)
            for relative_path in sorted(actual_files | declared_files):
                with self.subTest(
                    contract=contract["contract_id"],
                    kind="readme-tree",
                    target=relative_path,
                ):
                    self.assertIn(relative_path, readme)


if __name__ == "__main__":
    unittest.main()
