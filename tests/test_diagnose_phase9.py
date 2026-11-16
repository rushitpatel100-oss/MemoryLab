"""Unit tests for Phase 9 saved-evidence root-cause diagnostics."""
import copy
import unittest

from scripts.diagnose_phase9 import diagnose, markdown
from scripts.review_holdout_v2 import load_local_cases


class Phase9DiagnosisTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.entry = {
            "provisional_label": "uncertain",
            "axes": {
                "same_entity": "unknown",
                "same_attribute": "unknown",
                "same_assertion": "unknown",
                "old_fact_known_obsolete": "unknown",
                "new_value_known": "unknown",
            },
            "old_evidence": "",
            "new_evidence": "",
            "flags": ["Old evidence quote is missing or not in old fact.",
                      "New evidence quote is missing or not in new fact."],
        }
        self.report = {
            "dataset_sha256": self.digest,
            "judge_model": "qwen2.5:1.5b",
            "reviewer_type": "automated_llm_not_human",
            "independent_ground_truth": False,
            "policy_version": "evidence_first_v3",
            "answers": {
                c["id"]: copy.deepcopy(self.entry) for c in self.cases
            },
        }

    def test_identifies_all_abstentions_and_missing_quotes(self):
        stats = diagnose(self.cases, self.digest, self.report)
        self.assertEqual(stats["case_count"], 24)
        self.assertEqual(stats["distribution"]["uncertain"], 24)
        self.assertEqual(len(stats["missing_old_quotes"]), 24)
        self.assertEqual(stats["axes"]["same_assertion"]["unknown"], 24)
        self.assertEqual(stats["flags"]["Old evidence quote is missing or not in old fact."], 24)

    def test_report_is_diagnostic_not_ground_truth(self):
        stats = diagnose(self.cases, self.digest, self.report)
        report = markdown(stats)
        self.assertIn("Diagnostic only", report)
        self.assertIn("raw Ollama message was not retained", report)
        self.assertIn("| uncertain | 24 |", report)

    def test_refuses_different_dataset(self):
        self.report["dataset_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "matching Phase 9"):
            diagnose(self.cases, self.digest, self.report)

    def test_refuses_incomplete_file(self):
        del self.report["answers"]["H01"]
        with self.assertRaisesRegex(ValueError, "completed"):
            diagnose(self.cases, self.digest, self.report)

    def test_refuses_falsely_human_labelled_file(self):
        self.report["reviewer_type"] = "human"
        with self.assertRaisesRegex(ValueError, "matching Phase 9"):
            diagnose(self.cases, self.digest, self.report)

    def test_mixed_output_is_not_forced_into_all_abstentions(self):
        self.report["answers"]["H01"]["provisional_label"] = "duplicate"
        stats = diagnose(self.cases, self.digest, self.report)
        self.assertEqual(stats["distribution"]["duplicate"], 1)
        self.assertEqual(stats["distribution"]["uncertain"], 23)
        self.assertIn("Mixed labels", stats["status"])


if __name__ == "__main__":
    unittest.main()
