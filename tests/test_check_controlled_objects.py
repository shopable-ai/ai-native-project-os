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


if __name__ == "__main__":
    unittest.main()
