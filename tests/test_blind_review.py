"""No-network tests of the blind, label-first evaluation workflow."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.review_eval_cases import (
    empty_review, load_cases, load_review, lock_review,
    record_label, save_review,
)
from scripts.evaluate_review_v1 import (
    paired_predict, require_locked_labels, run_evaluation, score,
)


class BlindReviewTests(unittest.TestCase):
    def test_all_public_cases_are_unlabeled_and_unique(self):
        cases, digest = load_cases()
        self.assertEqual(len(cases), 20)
        self.assertEqual(len({case["id"] for case in cases}), 20)
        self.assertEqual(len(digest), 64)
        for case in cases:
            self.assertNotIn("expected", case)
            self.assertNotIn("label", case)

    def test_recording_and_resuming_local_review(self):
        cases, digest = load_cases()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "votes.json"
            review = empty_review(digest)
            record_label(review, cases[0]["id"], "C", "Both can be true")
            save_review(review, path)
            resume = load_review(path, digest, {c["id"] for c in cases})
            self.assertEqual(
                resume["answers"][cases[0]["id"]]["label"], "coexists"
            )
            self.assertFalse(resume["locked"])

    def test_cannot_lock_incomplete_labels(self):
        cases, digest = load_cases()
        review = empty_review(digest)
        record_label(review, cases[0]["id"], "D", "Repeat")
        with self.assertRaisesRegex(ValueError, "Finish all"):
            lock_review(review, cases)

    def test_lock_complete_review_and_prevent_edits(self):
        cases, digest = load_cases()
        review = empty_review(digest)
        for case in cases:
            record_label(review, case["id"], "U", "Referent unclear")
        lock_review(review, cases)
        self.assertTrue(review["locked"])
        with self.assertRaisesRegex(ValueError, "locked"):
            record_label(review, cases[0]["id"], "R", "Revised")

    def test_locked_review_detects_accidental_changes(self):
        cases, digest = load_cases()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "votes.json"
            review = empty_review(digest)
            for case in cases:
                record_label(review, case["id"], "U", "Need context")
            lock_review(review, cases)
            save_review(review, path)
            tampered = json.loads(path.read_text(encoding="utf-8"))
            tampered["answers"][cases[0]["id"]]["label"] = "coexists"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Locked label content changed"):
                load_review(path, digest, {c["id"] for c in cases})

    def test_refuse_unlocked_labels_before_model_call(self):
        cases, digest = load_cases()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "votes.json"
            review = empty_review(digest)
            save_review(review, path)
            with self.assertRaisesRegex(ValueError, "locked"):
                require_locked_labels(cases, digest, path)

    def test_refuse_changed_case_file(self):
        cases, digest = load_cases()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "votes.json"
            save_review(empty_review(digest), path)
            with self.assertRaisesRegex(ValueError, "case file changed"):
                load_review(path, "0" * 64, {c["id"] for c in cases})

    def test_no_model_reinference_for_gate(self):
        examples = [
            {"id": "T1", "topic": "location",
             "old_fact": "I live in York.", "new_fact": "I work in London."},
            {"id": "T2", "topic": "location",
             "old_fact": "I live in Bristol.",
             "new_fact": "I moved from Bristol to York."},
        ]
        votes = {"T1": "coexists", "T2": "replaces"}
        count = []
        def fake_classifier(old, topic, fact):
            count.append((old, topic, fact))
            return {"relation": "replaces", "reason": "Potential update"}
        rows, summaries = run_evaluation(examples, votes, fake_classifier)
        self.assertEqual(len(count), 2)
        self.assertEqual([r["guarded"] for r in rows],
                         ["uncertain", "replaces"])
        self.assertEqual(summaries["raw"]["false_replacements"], 1)
        self.assertEqual(summaries["guarded"]["false_replacements"], 0)
        self.assertEqual(
            summaries["guarded"]["genuine_replacements_missed"], 0
        )

    def test_metrics_show_safety_utility_tradeoff(self):
        rows = [
            {"human_label": "replaces", "raw": "replaces",
             "guarded": "uncertain"},
            {"human_label": "coexists", "raw": "replaces",
             "guarded": "uncertain"},
        ]
        raw = score(rows, "raw")
        gated = score(rows, "guarded")
        self.assertEqual(raw["false_replacements"], 1)
        self.assertEqual(raw["genuine_replacements_missed"], 0)
        self.assertEqual(gated["false_replacements"], 0)
        self.assertEqual(gated["genuine_replacements_missed"], 1)


if __name__ == "__main__":
    unittest.main()
