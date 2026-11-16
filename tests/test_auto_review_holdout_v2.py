"""No-network automated review tests (Ollama is always mocked)."""
import copy
import tempfile
import unittest
from pathlib import Path

from scripts.auto_review_holdout_v2 import (
    assess_response, empty_report, load_report, run_review, summarize,
)
from scripts.review_eval_cases import save_review
from scripts.review_holdout_v2 import load_local_cases


class AutomaticReviewTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.report = empty_report(self.digest, "qwen2.5:1.5b")
        self.response = {
            "relation": "coexists", "reason": "Separate properties",
            "storage_action": "keep_both",
            "axes": {"same_entity": "yes", "same_attribute": "no",
                     "old_fact_known_obsolete": "no",
                     "new_value_known": "yes"},
        }

    def test_valid_draft_keeps_the_non_destructive_action(self):
        result = assess_response(self.response)
        self.assertEqual(result["triage"], "draft")
        self.assertEqual(result["safe_storage_action"], "keep_both")
        self.assertEqual(result["reviewer_type"], "automated_llm_not_human")

    def test_invalid_or_missing_json_is_flagged_conservatively(self):
        result = assess_response(None)
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertEqual(result["triage"], "needs_review")
        self.assertEqual(result["safe_storage_action"], "review_needed")

    def test_replacement_never_automatically_authorizes_supersession(self):
        response = copy.deepcopy(self.response)
        response["relation"] = "replaces"
        response["storage_action"] = "supersede_old"
        response["axes"]["same_attribute"] = "yes"
        response["axes"]["old_fact_known_obsolete"] = "yes"
        entry = assess_response(response)
        self.assertEqual(entry["provisional_label"], "replaces")
        self.assertEqual(entry["safe_storage_action"], "review_needed")
        self.assertIn("human confirmation", " ".join(entry["flags"]))

    def test_contradictory_storage_action_is_flagged(self):
        response = copy.deepcopy(self.response)
        response["storage_action"] = "supersede_old"
        entry = assess_response(response)
        self.assertEqual(entry["triage"], "needs_review")
        self.assertEqual(entry["safe_storage_action"], "review_needed")

    def test_four_and_resume_without_rerun(self):
        calls = []
        saves = []
        def judge(case, model):
            calls.append(case["id"])
            return self.response
        count, ok = run_review(
            self.cases, self.report, limit=4, judge=judge,
            save_fn=lambda data: saves.append(copy.deepcopy(data)),
            output_fn=lambda _: None,
        )
        self.assertEqual((count, ok), (4, True))
        count, ok = run_review(
            self.cases, self.report, limit=2, judge=judge,
            save_fn=lambda data: saves.append(copy.deepcopy(data)),
            output_fn=lambda _: None,
        )
        self.assertEqual((count, ok), (2, True))
        self.assertEqual(calls, [case["id"] for case in self.cases[:6]])
        self.assertEqual(len(saves), 6)

    def test_failure_saves_earlier_cases_and_resumes(self):
        def judge(case, model):
            if case["id"] == "H03":
                raise ConnectionError("Ollama offline")
            return self.response
        count, ok = run_review(
            self.cases, self.report, limit=4, judge=judge,
            save_fn=lambda data: None, output_fn=lambda _: None,
        )
        self.assertEqual((count, ok), (2, False))
        self.assertEqual(len(self.report["answers"]), 2)

    def test_cannot_reuse_report_for_different_model_or_dataset(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "review.json"
            save_review(self.report, path)
            with self.assertRaisesRegex(ValueError, "another dataset or model"):
                load_report(path, self.digest, "gemma3:4b", {c["id"] for c in self.cases})
            with self.assertRaisesRegex(ValueError, "another dataset or model"):
                load_report(path, "x" * 64, "qwen2.5:1.5b", {c["id"] for c in self.cases})

    def test_malformed_ollama_json_becomes_flagged_draft(self):
        from io import BytesIO
        from unittest.mock import patch
        from scripts.auto_review_holdout_v2 import ollama_judge
        fake = BytesIO(b'{"message":{"content":"not valid JSON"}}')
        with patch(
            "scripts.auto_review_holdout_v2.urllib.request.urlopen",
            return_value=fake,
        ):
            raw = ollama_judge(self.cases[0])
        self.assertIsNone(raw)
        entry = assess_response(raw)
        self.assertEqual(entry["triage"], "needs_review")
        self.assertEqual(entry["safe_storage_action"], "review_needed")

    def test_malformed_nested_model_fields_are_safely_flagged(self):
        result = assess_response({
            "relation": ["replaces"],
            "axes": {"same_entity": {"bad": "value"}},
            "storage_action": ["supersede_old"],
            "reason": 42,
        })
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertEqual(result["safe_storage_action"], "review_needed")
        self.assertEqual(result["triage"], "needs_review")

    def test_summary_counts_review_flags(self):
        self.report["answers"]["H01"] = assess_response(self.response)
        bad = copy.deepcopy(self.response)
        bad["relation"] = "uncertain"
        bad["storage_action"] = "review_needed"
        self.report["answers"]["H02"] = assess_response(bad)
        summary = summarize(self.report, 24)
        self.assertEqual(summary["reviewed"], 2)
        self.assertEqual(summary["review_flags"], ["H02"])


if __name__ == "__main__":
    unittest.main()
