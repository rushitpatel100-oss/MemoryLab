"""Mocked semantic retrieval outcome tests; never contacts Ollama."""
import copy
import tempfile
import unittest
from pathlib import Path

from answer_generator import NO_MEMORY_ANSWER
from scripts.evaluate_downstream_memory import load_dataset
from scripts.evaluate_semantic_outcomes import (
    load_saved, markdown, run_all_semantic, run_semantic_scenario,
    select_retrieved, summarize_semantic,
)


class SemanticOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.sha = load_dataset()
        cls.cases = {x["id"]: x for x in cls.data["scenarios"]}

    def test_threshold_filters_out_weak_matches(self):
        memories = [{"id": 1, "topic": "test", "fact": "Old"},
                    {"id": 2, "topic": "test", "fact": "New"}]
        def ranker(question, records):
            return [
                {"memory": records[1], "similarity": 0.9},
                {"memory": records[0], "similarity": 0.1},
            ]
        result = select_retrieved("What?", memories, ranker=ranker)
        self.assertEqual([x["id"] for x in result], [2])

    def test_missing_retrieval_support_is_not_mistaken_for_storage_loss(self):
        def ranker(question, records):
            return [{"memory": records[-1], "similarity": 0.91}]
        result = run_semantic_scenario(
            self.cases["P01"], "reviewed", ranker=ranker,
            answer_fn=lambda question, selected, model: NO_MEMORY_ANSWER
        )
        self.assertTrue(result["checks"][0]["support_available"])
        self.assertFalse(result["checks"][0]["support_retrieved"])
        self.assertEqual(result["checks"][0]["retrieved_memory_ids"], [2])

    def test_all_memories_are_selected_on_high_scores(self):
        def ranker(question, records):
            return [{"memory": r, "similarity": 0.91} for r in records]
        seen = []
        def answer(question, selected, model):
            seen.append([x["fact"] for x in selected])
            return "printing press and drying rack"
        output = run_semantic_scenario(
            self.cases["P01"], "reviewed",
            ranker=ranker, answer_fn=answer
        )
        self.assertEqual(len(seen), 2)
        self.assertTrue(all(c["support_retrieved"] for c in output["checks"]))

    def test_resume_does_not_rerun_saved_scenario(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "semantic.json"
            calls = []
            def ranker(question, records):
                return [{"memory": r, "similarity": 0.7} for r in records]
            def answer(question, selected, model):
                calls.append(question)
                return "Not provided"
            first = run_all_semantic(
                self.data, self.sha, "reviewed", output=output,
                model="fake", ranker=ranker, answer_fn=answer,
                limit=1, log=lambda _: None
            )
            self.assertEqual(len(first["results"]), 1)
            self.assertEqual(len(calls), 2)
            second = run_all_semantic(
                self.data, self.sha, "reviewed", output=output,
                model="fake", ranker=ranker, answer_fn=answer,
                limit=2, log=lambda _: None
            )
            self.assertEqual(len(second["results"]), 2)
            self.assertEqual(len(calls), 4)

    def test_fingerprint_prevents_overwriting_incompatible_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "semantic.json"
            empty = load_saved(
                output, self.sha, "reviewed", "fake", 0.25, 3,
                {"P01_reviewed"}
            )
            from scripts.review_eval_cases import save_review
            save_review(empty, output)
            with self.assertRaisesRegex(ValueError, "different settings"):
                load_saved(
                    output, self.sha, "reviewed", "fake", 0.45, 3,
                    {"P01_reviewed"}
                )

    def test_report_is_explicitly_not_independent_accuracy(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "semantic.json"
            def ranker(question, records):
                return [{"memory": r, "similarity": 0.6} for r in records]
            state = run_all_semantic(
                self.data, self.sha, "reviewed",
                output=output, model="fake",
                ranker=ranker,
                answer_fn=lambda q, selected, model: "Unknown",
                limit=1, log=lambda _: None
            )
            result = markdown(state)
            self.assertIn("NOT independent", result)
            self.assertEqual(
                summarize_semantic(state)["reviewed"]["scenarios"], 1
            )

    def test_source_dataset_and_case_are_not_mutated(self):
        case = copy.deepcopy(self.cases["P13"])
        def ranker(question, records):
            return [{"memory": x, "similarity": 0.99} for x in records]
        run_semantic_scenario(
            self.cases["P13"], "topic_overwrite", ranker=ranker,
            answer_fn=lambda question, selected, model: "test"
        )
        self.assertEqual(self.cases["P13"], case)


if __name__ == "__main__":
    unittest.main()
