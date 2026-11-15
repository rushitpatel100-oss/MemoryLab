"""Unit tests for paired classifier scoring, with both models mocked."""
import unittest
from scripts.compare_classifiers import evaluate_pair, score
from scripts.run_conflict_benchmark import load_cases
from scripts.compare_classifiers import EVAL_SET


class ComparisonTests(unittest.TestCase):
    def test_score_tracks_false_supersession_separately(self):
        rows = [
            {"expected": "coexists", "baseline": "replaces",
             "staged": "coexists", "baseline_seconds": 1.0,
             "staged_seconds": 2.0},
            {"expected": "replaces", "baseline": "replaces",
             "staged": "replaces", "baseline_seconds": 1.0,
             "staged_seconds": 3.0},
        ]
        base = score(rows, "baseline")
        staged = score(rows, "staged")
        self.assertEqual(base["matches"], 1)
        self.assertEqual(base["coexists_as_replaces"], 1)
        self.assertEqual(staged["matches"], 2)
        self.assertEqual(staged["false_replacements"], 0)

    def test_both_methods_get_same_case_without_storage(self):
        case = {"id": "E01", "topic": "profile",
                "old_fact": "I own a cat.", "new_fact": "I like tea.",
                "expected": "coexists"}
        inputs = []
        def stub(old, topic, new):
            inputs.append((old, topic, new))
            return {"relation": "coexists", "reason": "Independent",
                    "source": "mock"}
        result = evaluate_pair(case, baseline=stub, staged=stub)
        self.assertEqual(inputs[0], inputs[1])
        self.assertEqual(result["staged"], "coexists")
        self.assertEqual(result["baseline"], "coexists")

    def test_evaluation_cases_are_separate_and_balanced(self):
        cases = load_cases(EVAL_SET)
        self.assertEqual(len(cases), 16)
        self.assertEqual(len({c["id"] for c in cases}), 16)
        self.assertEqual(
            [c["expected"] for c in cases[:4]],
            ["duplicate", "coexists", "replaces", "uncertain"]
        )
        for label in ("duplicate", "coexists", "replaces", "uncertain"):
            self.assertEqual(
                sum(c["expected"] == label for c in cases), 4
            )


if __name__ == "__main__":
    unittest.main()
