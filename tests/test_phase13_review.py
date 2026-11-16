"""Phase 13 blind-review and score tests. No network, Ollama or user data."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.phase13_review import (
    LABELS, load_dataset, load_signoff, lock_signoff,
    new_signoff, record_decision, save_signoff,
)
from scripts.evaluate_answer_challenge import evaluate, markdown


class Phase13ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset, cls.digest = load_dataset()
        cls.case_ids = {c["id"] for c in cls.dataset["cases"]}

    def setUp(self):
        self.signoff = new_signoff(self.digest)

    def test_32_source_cases_without_review_labels_or_probe_predictions(self):
        self.assertEqual(len(self.case_ids), 32)
        for case in self.dataset["cases"]:
            self.assertFalse({"gold_label", "truth", "probe_status"} & set(case))

    def test_review_labels_are_not_independent_ground_truth(self):
        self.assertFalse(self.signoff["independent_source_ground_truth"])
        self.assertTrue(self.signoff["blind_to_probe_output"])
        self.assertIsNone(self.signoff["locked_at"])

    def test_first_review_is_saved(self):
        record_decision(self.signoff, "C01", "supported", "From the fact.", self.case_ids)
        self.assertEqual(self.signoff["decisions"]["C01"]["label"], "supported")
        self.assertEqual(len(self.signoff["audit_events"]), 1)

    def test_edit_preserves_original_in_audit_events(self):
        record_decision(self.signoff, "C01", "supported", "First", self.case_ids)
        record_decision(self.signoff, "C01", "uncertain", "Need a closer look", self.case_ids)
        self.assertEqual(self.signoff["decisions"]["C01"]["label"], "uncertain")
        self.assertEqual([e["label"] for e in self.signoff["audit_events"]],
                         ["supported", "uncertain"])

    def test_uncertain_review_must_explain(self):
        with self.assertRaisesRegex(ValueError, "Explain"):
            record_decision(self.signoff, "C01", "uncertain", " ", self.case_ids)

    def test_unknown_id_and_label_rejected(self):
        with self.assertRaises(ValueError):
            record_decision(self.signoff, "X99", "supported", "", self.case_ids)
        with self.assertRaises(ValueError):
            record_decision(self.signoff, "C01", "wrong_label", "", self.case_ids)

    def test_freezing_incomplete_review_is_rejected(self):
        record_decision(self.signoff, "C01", "supported", "", self.case_ids)
        with self.assertRaisesRegex(ValueError, "Every case"):
            lock_signoff(self.signoff, self.case_ids)

    def test_locked_review_cannot_be_changed(self):
        for cid in self.case_ids:
            record_decision(self.signoff, cid, "supported", "", self.case_ids)
        lock_signoff(self.signoff, self.case_ids)
        self.assertIsInstance(self.signoff["locked_at"], str)
        with self.assertRaisesRegex(ValueError, "locked"):
            record_decision(self.signoff, "C01", "unsupported", "", self.case_ids)

    def test_roundtrip_and_dataset_mismatch_fail_closed(self):
        record_decision(self.signoff, "C01", "supported", "From fact", self.case_ids)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "review.json"
            save_signoff(self.signoff, output)
            reloaded = load_signoff(output, self.digest, self.case_ids)
            self.assertEqual(reloaded["decisions"], self.signoff["decisions"])
            with self.assertRaisesRegex(ValueError, "incompatible"):
                load_signoff(output, "wrong", self.case_ids)

    def test_score_requires_frozen_review(self):
        with self.assertRaisesRegex(ValueError, "Frozen"):
            evaluate(self.dataset, self.digest, self.signoff)

    def test_scoring_does_not_mutate_signoff_or_cases(self):
        cases = [{
            "id": "T01",
            "question": "What day is the new meeting?",
            "candidate_answer": "Monday.",
            "retrieved_memories": [{"id": 1, "fact": "The meeting changed day but its new day was not specified."}],
        }]
        data = {"cases": cases, "provenance": "test-only synthetic"}
        audit = new_signoff("test-digest")
        record_decision(audit, "T01", "unsupported", "No weekday given", {"T01"})
        lock_signoff(audit, {"T01"})
        before1, before2 = copy.deepcopy(data), copy.deepcopy(audit)
        result = evaluate(data, "test-digest", audit)
        self.assertEqual(result["counts"]["true_positive"], 1)
        self.assertEqual(data, before1)
        self.assertEqual(audit, before2)

    def test_curated_detector_metrics_distinguish_tp_fp_tn_fn(self):
        data = {
            "provenance": "test-only synthetic",
            "cases": [
                {"id": "T1", "question": "What is the new weekday?",
                 "candidate_answer": "Monday.",
                 "retrieved_memories": [{"id": 1, "fact": "The weekday changed but the new day wasn't recorded."}]},
                {"id": "T2", "question": "Where is the telescope?",
                 "candidate_answer": "By the western window.",
                 "retrieved_memories": [{"id": 1, "fact": "The telescope is by the west window."}]},
                {"id": "T3", "question": "Which day is the meeting NOW?",
                 "candidate_answer": "Tuesday.",
                 "retrieved_memories": [{"id": 1, "fact": "The meeting moved from Tuesday to Friday."}]},
                {"id": "T4", "question": "What does the archive hold?",
                 "candidate_answer": "Maps.",
                 "retrieved_memories": [{"id": 1, "fact": "The archive holds maps."}]},
            ],
        }
        labels = {
            "T1": "unsupported", "T2": "supported",
            "T3": "unsupported", "T4": "supported"
        }
        review = new_signoff("test-sha")
        for cid, label in labels.items():
            record_decision(review, cid, label, "Test only", set(labels))
        lock_signoff(review, set(labels))
        result = evaluate(data, "test-sha", review)
        self.assertEqual(result["counts"], {
            "true_positive": 1, "false_positive": 1,
            "true_negative": 1, "false_negative": 1,
            "excluded_uncertain": 0,
        })
        self.assertEqual(result["detection_precision_on_curated_cases"], 0.5)
        self.assertEqual(result["detection_recall_on_curated_cases"], 0.5)
        content = markdown(result, "a" * 64, "b" * 64)
        self.assertIn("NOT independently sourced accuracy", content)

    def test_uncertain_is_excluded_from_binary_scores(self):
        data = {"provenance": "test", "cases": [{
            "id": "T1", "question": "What is the new day?",
            "candidate_answer": "Monday.",
            "retrieved_memories": [{"id": 1, "fact": "The new day wasn't specified."}],
        }]}
        review = new_signoff("test")
        record_decision(review, "T1", "uncertain", "Referent ambiguous", {"T1"})
        lock_signoff(review, {"T1"})
        result = evaluate(data, "test", review)
        self.assertEqual(result["counts"]["excluded_uncertain"], 1)
        self.assertIsNone(result["detection_recall_on_curated_cases"])

    def test_scoring_refuses_modified_case_digest(self):
        review = new_signoff("old")
        review["locked_at"] = "2026-01-01T00:00:00+00:00"
        review["decisions"] = {
            c["id"]: {"label": "supported", "rationale": ""}
            for c in self.dataset["cases"]
        }
        with self.assertRaisesRegex(ValueError, "Frozen"):
            evaluate(self.dataset, self.digest, review)


if __name__ == "__main__":
    unittest.main()
