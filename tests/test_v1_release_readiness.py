"""Offline tests for a non-destructive MemoryLab V1 release gate."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.v1_release_readiness import (
    build_report, guarded_baseline_ui, isolated_review_smoke,
    next_report_path, privacy_exclusions, project_layout, run_checks,
)


class V1ReadinessTests(unittest.TestCase):
    def test_isolated_sqlite_storage_smoke(self):
        passed, detail = isolated_review_smoke()
        self.assertTrue(passed, detail)
        self.assertIn("Temporary SQLite", detail)

    def test_required_source_paths_exist(self):
        passed, detail = project_layout()
        self.assertTrue(passed, detail)

    def test_gitignore_excludes_local_memory_and_results(self):
        passed, detail = privacy_exclusions()
        self.assertTrue(passed, detail)

    def test_research_baseline_is_guarded_before_release(self):
        passed, detail = guarded_baseline_ui()
        self.assertTrue(passed, detail)

    def test_report_cannot_claim_model_accuracy(self):
        text = build_report([
            {"name": "smoke", "passed": True, "detail": "works"}
        ])
        self.assertIn("production-ready", text)
        self.assertIn("does **not** mean", text)
        self.assertIn("Phase 14", text)

    def test_failed_checks_mark_release_not_ready(self):
        text = build_report([
            {"name": "offline tests", "passed": False, "detail": "failed"}
        ])
        self.assertIn("NOT READY", text)
        self.assertIn("| offline tests | FAIL | failed |", text)

    def test_report_paths_increment_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            first = next_report_path(folder)
            self.assertTrue(str(first).endswith("001.md"))
            first.write_text("first run", encoding="utf-8")
            second = next_report_path(folder)
            self.assertTrue(str(second).endswith("002.md"))
            self.assertEqual(first.read_text(encoding="utf-8"), "first run")

    def test_quick_checks_skip_network_and_full_test_runner(self):
        with (patch("scripts.v1_release_readiness.unit_tests",
                    side_effect=AssertionError("Must not run tests")),
              patch("scripts.v1_release_readiness.local_ollama_model_check",
                    side_effect=AssertionError("Must not call network"))):
            checks = run_checks(skip_tests=True, with_models=False)
        self.assertEqual(len(checks), 5)
        self.assertTrue(all("name" in item for item in checks))


if __name__ == "__main__":
    unittest.main()
