"""Offline tests for the frozen-result adjudication scorer."""
import copy
import unittest

from scripts.rescore_adjudicated import compare_reports


class AdjudicatedScoreTests(unittest.TestCase):
    def setUp(self):
        self.original = {
            "dataset_sha256": "f" * 64,
            "rows": [
                {"id": "B01", "human_label": "coexists",
                 "raw": "replaces", "guarded": "uncertain"},
                {"id": "B02", "human_label": "replaces",
                 "raw": "replaces", "guarded": "replaces"},
            ],
        }
        self.adjudicated = {
            "dataset_sha256": "f" * 64,
            "rows": [
                {"id": "B01", "first_label": "coexists",
                 "second_label": "duplicate", "status": "adjudicated",
                 "final_label": "duplicate"},
                {"id": "B02", "first_label": "replaces",
                 "second_label": "replaces",
                 "status": "agreed_not_adjudicated",
                 "final_label": "replaces"},
            ],
        }

    def test_rescore_keeps_original_prediction_unchanged(self):
        before = copy.deepcopy(self.original)
        output = compare_reports(self.original, self.adjudicated)
        self.assertEqual(self.original, before)
        self.assertEqual(output["first_second_agreement"], 1)
        self.assertEqual(output["metrics"]["initial"]["raw"]["matches"], 1)
        self.assertEqual(output["metrics"]["adjudicated"]["raw"]["matches"], 1)
        self.assertEqual(output["metrics"]["adjudicated"]["raw"]["false_replacements"], 1)
        self.assertEqual(output["metrics"]["adjudicated"]["guarded"]["false_replacements"], 0)
        self.assertEqual(output["label_changes"][0]["id"], "B01")

    def test_reject_wrong_dataset(self):
        self.adjudicated["dataset_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "fingerprints"):
            compare_reports(self.original, self.adjudicated)

    def test_reject_changed_initial_label(self):
        self.adjudicated["rows"][0]["first_label"] = "duplicate"
        with self.assertRaisesRegex(ValueError, "Original human label"):
            compare_reports(self.original, self.adjudicated)

    def test_reject_duplicate_case_ids(self):
        self.adjudicated["rows"].append(copy.deepcopy(self.adjudicated["rows"][0]))
        with self.assertRaisesRegex(ValueError, "repeated"):
            compare_reports(self.original, self.adjudicated)

    def test_unadjudicated_agreement_must_be_consistent(self):
        self.adjudicated["rows"][1]["final_label"] = "duplicate"
        with self.assertRaisesRegex(ValueError, "Unadjudicated agreement"):
            compare_reports(self.original, self.adjudicated)

    def test_deferred_is_excluded_from_final_denominator(self):
        self.adjudicated["rows"][0]["status"] = "deferred"
        self.adjudicated["rows"][0]["final_label"] = None
        out = compare_reports(self.original, self.adjudicated)
        self.assertEqual(out["metrics"]["adjudicated"]["raw"]["cases"], 1)
        self.assertEqual(out["metrics"]["initial"]["raw"]["cases"], 2)
        self.assertEqual(out["deferred_cases"], 1)


if __name__ == "__main__":
    unittest.main()
