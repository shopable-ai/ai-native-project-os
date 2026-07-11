import importlib.util
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
