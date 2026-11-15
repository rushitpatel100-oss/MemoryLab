"""Mock-only tests: no Qwen or SQLite required for Phase 8 evaluation."""
import copy
import unittest

from scripts.review_holdout_v2 import (
    consistency_warnings, load_local_cases,
)
from scripts.review_second import new_review
from scripts.evaluate_holdout_v2 import (
    consensus_labels, evaluate_cases, require_frozen_reviews,
)


class HoldoutEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.first = new_review(self.digest)
        self.second = new_review(self.digest)
        for review in (self.first, self.second):
            review["answers"] = {
                case["id"]: {
                    "label": "coexists", "reason": "Separate attributes",
                    "axes": {
                        "same_entity": "yes", "same_attribute": "no",
                        "old_fact_known_obsolete": "no",
                        "new_value_known": "yes",
                    },
                    "storage_action": "keep_both",
                } for case in self.cases
            }
            review["answers_sha256"] = "f" * 64
            review["locked"] = True

    def loader(self, rater, cases, digest):
        self.assertEqual(digest, self.digest)
        return self.first if rater == "A" else self.second

    def test_reject_unlocked_rater(self):
        self.first["locked"] = False
        with self.assertRaisesRegex(ValueError, "Reviewer A"):
            require_frozen_reviews(self.cases, self.digest, loader=self.loader)

    def test_reject_incomplete_rater(self):
        del self.second["answers"]["H01"]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            require_frozen_reviews(self.cases, self.digest, loader=self.loader)

    def test_reject_contradictory_action(self):
        self.first["answers"]["H01"]["storage_action"] = "supersede_old"
        with self.assertRaisesRegex(ValueError, "Reviewer A"):
            require_frozen_reviews(self.cases, self.digest, loader=self.loader)

    def test_consensus_excludes_disagreements(self):
        self.second["answers"]["H01"]["label"] = "uncertain"
        self.second["answers"]["H01"]["storage_action"] = "review_needed"
        labels, disagreements = consensus_labels(
            self.cases, self.first, self.second
        )
        self.assertIsNone(labels["H01"])
        self.assertEqual(len(disagreements), 1)

    def test_one_classifier_call_for_both_methods(self):
        # Assert no extra Qwen inference for the guarded policy.
        calls = []
        def pretend_model(old, topic, fact):
            calls.append((old, topic, fact))
            return {"relation": "replaces", "reason": "Possible update"}
        rows, scores, disagreements = evaluate_cases(
            self.cases[:2], self.first, self.second,
            classifier=pretend_model
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(disagreements), 0)
        self.assertEqual(scores["raw"]["false_replacements"], 2)
        self.assertEqual(scores["guarded"]["false_replacements"], 0)
        self.assertEqual(scores["guarded"]["cases"], 2)

    def test_zero_consensus_is_an_unscored_result(self):
        for case in self.cases:
            self.second["answers"][case["id"]]["label"] = "uncertain"
            self.second["answers"][case["id"]]["storage_action"] = "review_needed"
        def pretend_model(old, topic, fact):
            return {"relation": "coexists", "reason": "Compatible"}
        rows, stats, disagreements = evaluate_cases(
            self.cases[:2], self.first, self.second,
            classifier=pretend_model
        )
        self.assertEqual(stats["raw"]["cases"], 0)
        self.assertEqual(stats["guarded"]["cases"], 0)
        self.assertEqual(len(disagreements), 2)

    def test_evidence_axes_can_be_unknown_without_auto_supersession(self):
        item = copy.deepcopy(self.first["answers"]["H01"])
        item["label"] = "uncertain"
        item["storage_action"] = "review_needed"
        item["axes"]["same_entity"] = "unknown"
        self.assertEqual(consistency_warnings(item), [])


if __name__ == "__main__":
    unittest.main()
