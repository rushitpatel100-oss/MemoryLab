"""Unit checks for the human-attested V1.0 manual QA report generator."""
import tempfile
import unittest
from pathlib import Path

from scripts.record_v1_manual_qa import (
    CHECKS, collect, next_output, report_text, valid_entry,
)


class ManualAcceptanceReportTests(unittest.TestCase):
    def test_has_seven_functional_and_one_observation_case(self):
        self.assertEqual(len(CHECKS), 8)
        self.assertEqual(CHECKS[-1][0], "UI08")

    def test_manual_check_will_not_assume_a_pass(self):
        e = valid_entry("UI01", "not_tested", "")
        self.assertEqual(e["status"], "not_tested")
        with self.assertRaises(ValueError):
            valid_entry("UI01", "observed", "not applicable")

    def test_unsupported_question_is_observation_not_truth_claim(self):
        entry = valid_entry("UI08", "observed", "Model guessed an old day.")
        self.assertEqual(entry["status"], "observed")
        with self.assertRaises(ValueError):
            valid_entry("UI08", "pass", "I checked.")

    def test_fail_and_observed_require_explanation(self):
        with self.assertRaises(ValueError):
            valid_entry("UI04", "fail", "")
        with self.assertRaises(ValueError):
            valid_entry("UI08", "observed", "")

    def test_complete_report_preserves_failed_and_untested(self):
        entries = [
            valid_entry(cid, "fail" if cid == "UI03" else
                        ("observed" if cid == "UI08" else "not_tested"),
                        "Unexpected result" if cid in ("UI03", "UI08") else "")
            for cid, _, _ in CHECKS
        ]
        md = report_text(entries)
        self.assertIn("Manual UI acceptance incomplete or failed", md)
        self.assertIn("Functional checks passed: 0/7", md)
        self.assertIn("Functional checks failed: 1/7", md)
        self.assertIn("does not execute the app", md)

    def test_collect_can_capture_all_manual_answers(self):
        iterator = iter(
            value for cid, _, _ in CHECKS
            for value in (
                "observed" if cid == "UI08" else "pass",
                "It ran as expected."
            )
        )
        got = collect(prompt=lambda _: next(iterator), say=lambda _: None)
        self.assertEqual(len(got), 8)
        self.assertIn("7/7", report_text(got))

    def test_new_report_path_never_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            one = next_output(folder)
            one.write_text("original", encoding="utf-8")
            two = next_output(folder)
            self.assertNotEqual(one, two)
            self.assertEqual(one.read_text(encoding="utf-8"), "original")


if __name__ == "__main__":
    unittest.main()
