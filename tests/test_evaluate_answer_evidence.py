"""Offline comparison tests; no local Ollama or SQLite user data."""
import copy
import unittest

from answer_generator import NO_MEMORY_ANSWER
from scripts.evaluate_answer_evidence import MODE, compare, markdown
from scripts.evaluate_downstream_memory import load_dataset


class ExtractiveComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.digest = load_dataset()

    def make_results(self):
        results = {}
        for case in self.data["scenarios"]:
            rows = []
            for q in case["checks"]:
                rows.append({
                    "id": q["id"], "question": q["question"],
                    "answer": "Known answer", "text_proxy_pass": True,
                    "support_retrieved": None if q.get("expect_abstention")
                    else True,
                })
            results[case["id"] + "_reviewed"] = {"checks": rows}
        common = {
            "policy": "reviewed", "embedding": "all-minilm",
            "top_k": 3, "minimum": 0.25,
            "dataset_sha256": self.digest,
            "model": "qwen2.5:1.5b", "results": results,
        }
        before = copy.deepcopy(common)
        after = copy.deepcopy(common)
        after["answer_mode"] = MODE
        return before, after

    def test_same_case_comparison_is_not_accuracy(self):
        old, new = self.make_results()
        new["results"]["P07_reviewed"]["checks"][1]["answer"] = NO_MEMORY_ANSWER
        result = compare(self.data, old, new)
        self.assertEqual(result["questions"], 28)
        self.assertEqual(result["extractive_unsupported_answer_events"], 0)
        self.assertEqual(result["baseline_unsupported_answer_events"], 1)
        self.assertIn("NOT blind accuracy", markdown(result, "a", "b"))

    def test_model_change_is_rejected(self):
        old, new = self.make_results()
        new["model"] = "different"
        with self.assertRaisesRegex(ValueError, "model changed"):
            compare(self.data, old, new)

    def test_mismatched_dataset_is_rejected(self):
        old, new = self.make_results()
        new["dataset_sha256"] = "other"
        with self.assertRaisesRegex(ValueError, "different datasets"):
            compare(self.data, old, new)

    def test_missing_question_is_rejected(self):
        old, new = self.make_results()
        new["results"]["P01_reviewed"]["checks"].pop()
        with self.assertRaisesRegex(ValueError, "Question count mismatch"):
            compare(self.data, old, new)

    def test_wrong_answer_mode_is_rejected(self):
        old, new = self.make_results()
        new["answer_mode"] = "ordinary_chat"
        with self.assertRaisesRegex(ValueError, "Candidate provenance"):
            compare(self.data, old, new)

    def test_comparison_does_not_modify_files_or_inputs(self):
        old, new = self.make_results()
        untouched_old, untouched_new = copy.deepcopy(old), copy.deepcopy(new)
        compare(self.data, old, new)
        self.assertEqual(old, untouched_old)
        self.assertEqual(new, untouched_new)


if __name__ == "__main__":
    unittest.main()
