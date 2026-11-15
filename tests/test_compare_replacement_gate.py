"""Mock-only tests of the replacement gate benchmark."""
import unittest

from scripts.compare_replacement_gate import compare_cases, summarize


class GuardBenchmarkTests(unittest.TestCase):
    CASES = [
        {"id": "C", "topic": "location",
         "old_fact": "I live in York.", "new_fact": "I work in London.",
         "expected": "coexists"},
        {"id": "R", "topic": "location",
         "old_fact": "I live in Bristol.",
         "new_fact": "I moved from Bristol to York.",
         "expected": "replaces"},
    ]

    def test_shared_single_model_call_and_gate_scoring(self):
        calls = []
        def fake(old, topic, new):
            calls.append((old, topic, new))
            return {"relation": "replaces", "reason": "Update"}
        rows = compare_cases(self.CASES, classifier=fake)
        self.assertEqual(len(calls), 2)
        self.assertEqual([r["raw"] for r in rows],
                         ["replaces", "replaces"])
        self.assertEqual([r["guarded"] for r in rows],
                         ["uncertain", "replaces"])
        self.assertEqual(summarize(rows, "raw")["false_replacements"], 1)
        self.assertEqual(summarize(rows, "guarded")["false_replacements"], 0)

    def test_summary_counts_missed_real_updates(self):
        rows = [
            {"expected": "replaces", "raw": "replaces",
             "guarded": "uncertain"},
            {"expected": "coexists", "raw": "replaces",
             "guarded": "uncertain"},
        ]
        self.assertEqual(summarize(rows, "raw")["matches"], 1)
        self.assertEqual(summarize(rows, "guarded")["matches"], 0)
        self.assertEqual(
            summarize(rows, "guarded")["true_replacements_retained"], 0
        )


if __name__ == "__main__":
    unittest.main()
