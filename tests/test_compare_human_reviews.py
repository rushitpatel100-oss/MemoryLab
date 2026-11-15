"""Tests: second human comparison requires both labels locked."""
import tempfile
import unittest
from pathlib import Path

from scripts.review_eval_cases import (
    load_cases, empty_review, lock_review, record_label, save_review,
)
from scripts.review_second import (
    FIELDS, add_assessment, lock_second, new_review,
)
from scripts.compare_human_reviews import (
    build_comparison, locked_reviews,
)


class HumanAgreementTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_cases()
        self.first = empty_review(self.digest)
        self.second = new_review(self.digest)
        for case in self.cases:
            record_label(self.first, case["id"], "C", "Compatible")
            add_assessment(self.second, case["id"], "C", "Compatible",
                           {f: "U" for f, _ in FIELDS}, "K")

    def test_all_agreement_but_flagged_cases_still_reviewed(self):
        rows, score = build_comparison(
            self.cases, self.first, self.second
        )
        self.assertEqual(score["same_label"], 20)
        self.assertEqual(score["disagreements"], 0)
        self.assertEqual(score["needs_adjudication"], 7)
        self.assertEqual(score["cohens_kappa"], None)
        self.assertTrue(next(r for r in rows if r["id"] == "B04")
                        ["adjudicate"])

    def test_disagreement_lists_new_case(self):
        self.second["answers"]["B01"]["label"] = "duplicate"
        rows, summary = build_comparison(
            self.cases, self.first, self.second
        )
        self.assertEqual(summary["disagreements"], 1)
        self.assertIn("B01", summary["adjudication_ids"])
        self.assertIn("B04", summary["adjudication_ids"])
        self.assertEqual(summary["same_label"], 19)
        self.assertTrue(isinstance(summary["cohens_kappa"], float))

    def test_conflicting_review_evidence_is_flagged(self):
        # Same label from both humans is not enough when the second
        # reviewer also says the subject identity is unproven.
        self.first["answers"]["B01"]["label"] = "replaces"
        self.second["answers"]["B01"]["label"] = "replaces"
        self.second["answers"]["B01"]["storage_action"] = "supersede_old"
        rows, result = build_comparison(self.cases, self.first, self.second)
        first = next(row for row in rows if row["id"] == "B01")
        self.assertFalse(first["disagreement"])
        self.assertTrue(first["second_evidence_conflict"])
        self.assertTrue(first["adjudicate"])
        self.assertGreaterEqual(result["second_evidence_conflicts"], 1)

    def test_both_label_files_must_be_complete_and_locked(self):
        with tempfile.TemporaryDirectory() as dirname:
            p1 = Path(dirname) / "first.json"
            p2 = Path(dirname) / "second.json"
            save_review(self.first, p1)
            save_review(self.second, p2)
            with self.assertRaisesRegex(ValueError, "not locked"):
                locked_reviews(self.cases, self.digest, p1, p2)
            lock_review(self.first, self.cases)
            save_review(self.first, p1)
            with self.assertRaisesRegex(ValueError, "Second review"):
                locked_reviews(self.cases, self.digest, p1, p2)
            lock_second(self.second, self.cases)
            save_review(self.second, p2)
            first, second = locked_reviews(self.cases, self.digest, p1, p2)
            self.assertEqual(len(first["answers"]), 20)
            self.assertEqual(len(second["answers"]), 20)


if __name__ == "__main__":
    unittest.main()
