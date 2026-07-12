import importlib.util
import subprocess
import sys
import tempfile
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

    def test_repository_scan_excludes_isolated_worktrees(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "project-os.yaml").write_text("schema_version: 1\n", encoding="utf-8")
            nested = repo / ".worktrees" / "feature"
            nested.mkdir(parents=True)
            (nested / "project-os.yaml").write_text("schema_version: 1\n", encoding="utf-8")

            scanned = {path.relative_to(repo).as_posix() for path in checker.iter_repo_files(repo)}

        self.assertEqual(scanned, {"project-os.yaml"})

    def test_repository_root_inside_worktrees_is_still_scanned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / ".worktrees" / "feature"
            repo.mkdir(parents=True)
            (repo / "project-os.yaml").write_text("schema_version: 1\n", encoding="utf-8")

            scanned = {path.relative_to(repo).as_posix() for path in checker.iter_repo_files(repo)}

        self.assertEqual(scanned, {"project-os.yaml"})

    def test_l2_mode_does_not_require_l1_authority_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "project-os.lock.yaml").write_text(
                "schema_version: 1\n", encoding="utf-8"
            )
            (repo / "functional.md").write_text(
                "---\n"
                "stable_id: REQ-FUNC-001\n"
                "object_type: requirement\n"
                "requirement_kind: functional\n"
                "canonical_path: functional.md\n"
                "priority: p1\n"
                "---\n",
                encoding="utf-8",
            )
            spec = repo / "specs" / "REQ-FUNC-001"
            spec.mkdir(parents=True)
            (spec / "traceability.md").write_text(
                "# traceability\n", encoding="utf-8"
            )

            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(repo), "--l2-mode"],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("阶段门禁契约不存在", result.stdout)
        self.assertNotIn("project-os.yaml", result.stdout)


class CheckerGovernanceTests(unittest.TestCase):
    def make_repo(self, files):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        repo = Path(temp_dir.name)
        for relative_path, content in files.items():
            target = repo / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return repo

    def test_ai_review_workflow_cannot_wait_for_human_approval(self):
        repo = self.make_repo({
            "workflows/review.yaml": (
                "review_mode: ai_automated\n"
                "work_status: waiting_approval\n"
            )
        })

        findings = checker.check_c6_ai_review_no_routine_human_wait(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual([finding.rule for finding in findings], ["C6"])

    def test_c4_scans_templates_for_concrete_l3_paths(self):
        repo = self.make_repo({
            "templates/standard-project/README.md": (
                "复制后写入 projects/" "fixture_project/config.yaml\n"
            )
        })

        findings = checker.check_c4_l1_no_l2_refs(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual(
            [(finding.rule, finding.file) for finding in findings],
            [("C4", "templates/standard-project/README.md")],
        )

    def test_c4_allows_generic_l3_and_l2_placeholders(self):
        repo = self.make_repo({
            "docs/workflows/L2_ONBOARDING.md": (
                "项目目录：projects/{project_id}/\n"
                "L2 仓库：{{l2_repo}}/reviews/{{evidence_file}}\n"
            )
        })

        findings = checker.check_c4_l1_no_l2_refs(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual(findings, [])

    def test_c1_resolves_canonical_paths_inside_project_templates(self):
        repo = self.make_repo({
            "templates/standard-project/domain/glossary.md": (
                "stable_" "id: FACT-001\n"
                "canonical_path: domain/glossary.md#fact-001\n"
            )
        })

        findings = checker.check_c1_stable_id_unique(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual(findings, [])

    def test_c1_nested_stable_id_is_reference_not_second_definition(self):
        repo = self.make_repo({
            "requirements/REQ-001.md": (
                "---\n"
                "stable_id: REQ-001\n"
                "canonical_path: requirements/REQ-001.md\n"
                "---\n"
            ),
            "requirements/baseline.yaml": (
                "stable_id: BASELINE-001\n"
                "canonical_path: requirements/baseline.yaml\n"
                "requirement_refs:\n"
                "  - stable_id: REQ-001\n"
                "    version: 1\n"
            ),
        })

        findings = checker.check_c1_stable_id_unique(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual(findings, [])

    def test_c3_business_requirement_does_not_skip_functional_design_layer(self):
        repo = self.make_repo({
            "business.md": (
                "---\n"
                "stable_id: REQ-BIZ-001\n"
                "object_type: requirement\n"
                "requirement_kind: business\n"
                "priority: p1\n"
                "---\n"
            ),
            "specs/.keep.md": "fixture\n",
        })

        findings = checker.check_c3_p0p1_has_spec_traceability(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual(findings, [])

    def test_c3_functional_requirement_requires_matching_spec_traceability(self):
        repo = self.make_repo({
            "functional.md": (
                "---\n"
                "stable_id: REQ-FUNC-001\n"
                "object_type: requirement\n"
                "requirement_kind: functional\n"
                "priority: p1\n"
                "---\n"
            ),
            "specs/.keep.md": "fixture\n",
        })

        findings = checker.check_c3_p0p1_has_spec_traceability(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual([finding.rule for finding in findings], ["C3"])

    def test_review_verdict_requires_rule_binding_and_bounded_rewrite(self):
        repo = self.make_repo({
            "artifacts/review-verdict.yaml": (
                "object_type: ai_review_verdict\n"
                "decision: rewrite_required\n"
                "max_rewrite_attempts: 0\n"
            )
        })

        findings = checker.check_c7_ai_review_manifest(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual({finding.rule for finding in findings}, {"C7"})

    def test_complete_pending_review_manifest_is_structurally_valid(self):
        repo = self.make_repo({
            "artifacts/review-verdict.yaml": (
                "object_type: ai_review_verdict\n"
                "subject_ref: subject/version\n"
                "subject_hash: sha256\n"
                "generator_run_ref: run-generator\n"
                "review_run_ref: run-reviewer\n"
                "reviewer_actor_id: reviewer\n"
                "reviewer_execution_node_ref: reviewer-node/version\n"
                "rule_set_ref: rules/version\n"
                "rule_set_hash: sha256\n"
                "evidence_refs: []\n"
                "decision: pending\n"
                "max_rewrite_attempts: 2\n"
            )
        })

        findings = checker.check_c7_ai_review_manifest(
            repo, checker.iter_repo_files(repo)
        )

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
