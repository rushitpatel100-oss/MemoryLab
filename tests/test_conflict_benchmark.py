"""Offline benchmark unit tests; never call Ollama."""
import unittest

from scripts.run_conflict_benchmark import run_cases, summarize


class BenchmarkTests(unittest.TestCase):
    def test_two_correct_mocked_predictions(self):
        cases = [
            {"id": "D", "expected": "duplicate", "topic": "hobby",
             "old_fact": "I paint.", "new_fact": "I paint."},
            {"id": "C", "expected": "coexists", "topic": "hobby",
             "old_fact": "I paint.", "new_fact": "I read."},
        ]
        answers = iter([
            {"relation": "duplicate", "reason": "Same assertion",
             "source": "local_rule"},
            {"relation": "coexists", "reason": "Different hobbies",
             "source": "qwen"},
        ])
        results = run_cases(cases, classifier=lambda *_: next(answers))
        summary = summarize(results)
        self.assertEqual(summary["correct"], 2)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["confusion"]["duplicate"]["duplicate"], 1)
        self.assertEqual(summary["sources"]["local_rule"], 1)

    def test_mismatch_is_counted(self):
        cases = [
            {"id": "C", "expected": "coexists", "topic": "location",
             "old_fact": "I live in York.",
             "new_fact": "I work in London."}
        ]
        results = run_cases(
            cases,
            classifier=lambda *_: {"relation": "uncertain",
                                   "reason": "Ambiguous", "source": "qwen"}
        )
        summary = summarize(results)
        self.assertEqual(summary["correct"], 0)
        self.assertEqual(summary["confusion"]["coexists"]["uncertain"], 1)


if __name__ == "__main__":
    unittest.main()
