"""No-network tests for the separate blinded reviewer."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.review_eval_cases import load_cases, save_review
from scripts.review_second import (
    FIELDS, add_assessment, load_second, lock_second, new_review,
    review_cases,
)


class SecondReviewTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_cases()
        self.valid_ids = {c["id"] for c in self.cases}

    def add(self, review, case):
        axes = {field: "U" for field, _ in FIELDS}
        add_assessment(review, case["id"], "U", "Insufficient context",
                       axes, "R")

    def test_first_review_is_not_imported_or_reused(self):
        review = new_review(self.digest)
        self.assertEqual(review["answers"], {})
        self.assertNotIn("label_source", review)

    def test_structured_axes_and_label_validate(self):
        review = new_review(self.digest)
        axes = {field: "Y" for field, _ in FIELDS}
        add_assessment(review, "B01", "C", "Independent languages",
                       axes, "K")
        self.assertEqual(review["answers"]["B01"]["label"], "coexists")
        self.assertEqual(
            review["answers"]["B01"]["axes"]["same_entity"], "yes"
        )

    def test_reject_missing_structured_evidence(self):
        review = new_review(self.digest)
        with self.assertRaises(ValueError):
            add_assessment(review, "B01", "R", "Change", {}, "S")

    def test_resume_and_lock_preserves_labels(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "second.json"
            review = new_review(self.digest)
            self.add(review, self.cases[0])
            save_review(review, path)
            resumed = load_second(path, self.digest, self.valid_ids)
            self.assertEqual(len(resumed["answers"]), 1)
            for case in self.cases[1:]:
                self.add(resumed, case)
            lock_second(resumed, self.cases)
            save_review(resumed, path)
            reread = load_second(path, self.digest, self.valid_ids)
            self.assertTrue(reread["locked"])
            with self.assertRaisesRegex(ValueError, "locked"):
                self.add(reread, self.cases[0])

    def test_cannot_lock_partial_review(self):
        review = new_review(self.digest)
        self.add(review, self.cases[0])
        with self.assertRaisesRegex(ValueError, "Complete all"):
            lock_second(review, self.cases)

    def test_invalid_locked_file_detected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "second.json"
            review = new_review(self.digest)
            for case in self.cases:
                self.add(review, case)
            lock_second(review, self.cases)
            save_review(review, path)
            tampered = json.loads(path.read_text(encoding="utf-8"))
            tampered["answers"]["B01"]["label"] = "coexists"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "modified"):
                load_second(path, self.digest, self.valid_ids)

    def test_interactive_saves_one_and_skips_completed(self):
        responses = iter(["C", "Both can be true", "Y", "N", "N", "Y", "K"])
        saves = []
        review = new_review(self.digest)
        completed = review_cases(
            self.cases, review, limit=1,
            input_fn=lambda prompt: next(responses),
            output_fn=lambda text: None,
            save_fn=lambda result: saves.append(copy.deepcopy(result)),
        )
        self.assertEqual(completed, 1)
        self.assertEqual(len(saves), 1)
        self.assertEqual(list(review["answers"]), ["B01"])
        self.assertEqual(
            review_cases(self.cases, review, limit=0,
                         output_fn=lambda text: None,
                         save_fn=lambda result: None), 0
        )


if __name__ == "__main__":
    unittest.main()
