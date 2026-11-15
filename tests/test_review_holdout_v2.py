"""Offline tests for rubric-first, separately stored Phase 8 reviews."""
import copy
import tempfile
import unittest
from pathlib import Path

from scripts.review_second import load_second
from scripts.review_holdout_v2 import (
    CASES, REVIEW_PATHS, consistency_warnings, load_local_cases,
    lock_rater, review_interactive,
)
from scripts.review_second import new_review
from scripts.review_eval_cases import save_review


class HoldoutReviewTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.review = new_review(self.digest)

    def good(self):
        return {
            "label": "coexists", "reason": "Clearly separate properties",
            "axes": {
                "same_entity": "yes", "same_attribute": "no",
                "old_fact_known_obsolete": "no", "new_value_known": "yes",
            },
            "storage_action": "keep_both",
        }

    def test_24_public_cases_unlabelled(self):
        self.assertEqual(len(self.cases), 24)
        self.assertEqual(len({row["id"] for row in self.cases}), 24)
        self.assertTrue(all("expected" not in row and "label" not in row
                            for row in self.cases))

    def test_raters_have_different_review_paths(self):
        self.assertNotEqual(REVIEW_PATHS["A"], REVIEW_PATHS["B"])
        self.assertTrue(CASES.name.startswith("holdout_v2"))

    def test_contradictory_replace_requires_manual_revision(self):
        proposal = self.good()
        proposal["label"] = "replaces"
        proposal["storage_action"] = "supersede_old"
        self.assertTrue(consistency_warnings(proposal))

    def test_duplicate_cannot_supersede(self):
        proposal = self.good()
        proposal["label"] = "duplicate"
        proposal["storage_action"] = "supersede_old"
        self.assertTrue(consistency_warnings(proposal))

    def test_review_asks_axes_first_and_saves_one_case(self):
        answers = iter(["R", "Y", "N", "N", "Y",
                        "C", "Separate properties", "K"])
        prompts = []
        snapshots = []
        count = review_interactive(
            self.cases, self.review, "A", limit=1,
            input_fn=lambda prompt: (prompts.append(prompt) or next(answers)),
            output_fn=lambda _: None,
            save_fn=lambda data: snapshots.append(copy.deepcopy(data)),
        )
        self.assertEqual(count, 1)
        self.assertEqual(len(snapshots), 1)
        self.assertIn("Same person", prompts[1])
        self.assertIn("Relation", prompts[5])

    def test_bad_decision_is_not_saved(self):
        # Same entity/attribute are both unknown, yet model tries to supersede.
        answers = iter(["R", "U", "U", "U", "U",
                        "R", "Certainly changed", "S"])
        count = review_interactive(
            self.cases[:1], self.review, "A",
            input_fn=lambda _: next(answers),
            output_fn=lambda _: None, save_fn=lambda _: None
        )
        self.assertEqual(count, 0)
        self.assertEqual(self.review["answers"], {})

    def test_lock_requires_every_case(self):
        self.review["answers"]["H01"] = self.good()
        with self.assertRaisesRegex(ValueError, "Complete all cases"):
            lock_rater(self.review, self.cases)

    def test_existing_review_is_resumable(self):
        self.review["answers"]["H01"] = self.good()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raterA.json"
            save_review(self.review, path)
            resumed = load_second(
                path, self.digest, {c["id"] for c in self.cases}
            )
            self.assertEqual(resumed["answers"]["H01"], self.good())

    def test_lock_24_answers_and_detect_post_lock_edit(self):
        for case in self.cases:
            self.review["answers"][case["id"]] = self.good()
        lock_rater(self.review, self.cases)
        self.assertTrue(self.review["locked"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raterA.json"
            save_review(self.review, path)
            self.review["answers"]["H01"]["label"] = "uncertain"
            save_review(self.review, path)
            with self.assertRaisesRegex(ValueError, "modified"):
                load_second(path, self.digest, {c["id"] for c in self.cases})


if __name__ == "__main__":
    unittest.main()
