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
    def test_checker_version_marks_ai_review_rules(self):
        self.assertEqual(checker.CHECKER_VERSION, "0.2.0")

    def test_p1_finding_fails_gate(self):
        findings = [checker.Finding("C4", "P1", "project-os.yaml", 1, "drift")]
        self.assertEqual(checker.exit_code_for_findings(findings), 1)

    def test_empty_findings_pass_gate(self):
        self.assertEqual(checker.exit_code_for_findings([]), 0)

    def test_p1_finding_does_not_report_machine_pass(self):
        findings = [checker.Finding("C4", "P1", "project-os.yaml", 1, "drift")]
        self.assertFalse(checker.gate_pass_for_findings(findings))


class CheckerGovernanceTests(unittest.TestCase):
    def make_repo(self, files: dict[str, str]) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        repo = Path(temp.name)
        for relative_path, content in files.items():
            path = repo / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return repo

    def test_ai_review_workflow_cannot_wait_for_human_approval(self):
        repo = self.make_repo(
            {
                "workflows/review.yaml": (
                    "review_mode: ai_automated\n"
                    "work_status: waiting_approval\n"
                )
            }
        )
        findings = checker.check_c6_ai_review_no_routine_human_wait(
            repo, checker.iter_repo_files(repo)
        )
        self.assertEqual([finding.rule for finding in findings], ["C6"])

    def test_review_verdict_requires_rule_set_and_bounded_rewrite(self):
        repo = self.make_repo(
            {
                "runs/verdict.yaml": (
                    "object_type: ai_review_verdict\n"
                    "decision: rewrite_required\n"
                    "max_rewrite_attempts: 0\n"
                )
            }
        )
        findings = checker.check_c7_ai_review_manifest(
            repo, checker.iter_repo_files(repo)
        )
        self.assertEqual({finding.rule for finding in findings}, {"C7"})

    def test_repository_scan_skips_project_local_worktrees(self):
        repo = self.make_repo(
            {
                "authority.yaml": "schema_version: 1\n",
                ".worktrees/feature/duplicate.yaml": "schema_version: 1\n",
            }
        )
        scanned = {path.relative_to(repo).as_posix() for path in checker.iter_repo_files(repo)}
        self.assertEqual(scanned, {"authority.yaml"})


if __name__ == "__main__":
    unittest.main()
