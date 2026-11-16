"""Tests for V4 high-risk duplicate safety audit: no model or SQLite."""
import copy
import unittest

from scripts.audit_review_v4 import audit, audit_case, render
from scripts.review_holdout_v2 import load_local_cases


class V4SafetyAuditTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.responses = {
            case["id"]: {
                "provisional_label": "uncertain",
                "safe_storage_action": "review_needed",
                "axes": {},
            }
            for case in self.cases
        }
        self.source = {
            "dataset_sha256": self.digest,
            "reviewer_type": "automated_llm_not_human",
            "independent_ground_truth": False,
            "policy_version": "contrastive_evidence_v4",
            "answers": self.responses,
        }

    def duplicate(self, case):
        return {
            "provisional_label": "duplicate",
            "safe_storage_action": "skip_duplicate",
            "axes": {
                "same_entity": "yes", "same_attribute": "yes",
                "same_assertion": "yes",
            },
            "old_quote": case["old_fact"][:15],
            "new_quote": case["new_fact"][:15],
        }

    def test_changed_plant_is_not_safe_to_skip_as_duplicate(self):
        case = next(c for c in self.cases if c["id"] == "H18")
        row = audit_case(case, self.duplicate(case))
        self.assertEqual(row["status"], "high_priority")
        self.assertEqual(row["audit_action"], "review_needed")
        self.assertTrue(any("change" in s.lower() for s in row["alerts"]))

    def test_home_away_contrast_is_a_high_priority_duplicate(self):
        case = next(c for c in self.cases if c["id"] == "H20")
        row = audit_case(case, self.duplicate(case))
        self.assertEqual(row["status"], "high_priority")
        self.assertTrue(any("home versus away" in s for s in row["alerts"]))

    def test_clear_paraphrase_still_requires_approval(self):
        case = next(c for c in self.cases if c["id"] == "H02")
        row = audit_case(case, self.duplicate(case))
        self.assertEqual(row["status"], "confirm_duplicate")
        self.assertEqual(row["audit_action"], "review_needed")

    def test_uncertain_is_never_made_confident(self):
        case = self.cases[0]
        row = audit_case(case, self.responses[case["id"]])
        self.assertEqual(row["status"], "unresolved")
        self.assertEqual(row["audit_action"], "review_needed")

    def test_all_duplicates_withheld_without_touching_source(self):
        for case in self.cases:
            self.responses[case["id"]] = self.duplicate(case)
        initial = copy.deepcopy(self.source)
        result = audit(self.cases, self.digest, self.source)
        self.assertEqual(result["prevented_duplicate_skips"], 24)
        self.assertEqual(self.source, initial)

    def test_requires_matching_dataset_sha(self):
        self.source["dataset_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance"):
            audit(self.cases, self.digest, self.source)

    def test_requires_all_cases(self):
        del self.responses["H01"]
        with self.assertRaisesRegex(ValueError, "Complete all"):
            audit(self.cases, self.digest, self.source)

    def test_markdown_discloses_no_accuracy_and_preserves_provenance(self):
        self.responses["H18"] = self.duplicate(
            next(c for c in self.cases if c["id"] == "H18")
        )
        result = audit(self.cases, self.digest, self.source)
        report = render(result, "f" * 64)
        self.assertIn("not model accuracy", report)
        self.assertIn("H18", report)
        self.assertIn("f" * 64, report)


if __name__ == "__main__":
    unittest.main()
