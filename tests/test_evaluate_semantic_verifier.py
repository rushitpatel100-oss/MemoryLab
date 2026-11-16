"""Phase 14 semantic verifier tests: no real Ollama or user memory calls."""
import copy
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from scripts.evaluate_semantic_verifier import (
    SCHEMA, POLICY, compare, interpret, load_run, local_judge,
    markdown, new_run, run_cases,
)
from scripts.phase13_review import (
    load_dataset, new_signoff, lock_signoff, record_decision,
)


class SemanticVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset, cls.digest = load_dataset()
        cls.case = cls.dataset["cases"][0]
        cls.ids = {c["id"] for c in cls.dataset["cases"]}

    def test_json_schema_is_sent_to_local_ollama(self):
        payload = {
            "verdict": "supported", "memory_id": 1,
            "quote": self.case["retrieved_memories"][0]["fact"],
            "reason": "Answer follows."
        }
        def fake_open(req, timeout):
            request = json.loads(req.data)
            self.assertEqual(request["format"], SCHEMA)
            self.assertFalse(request["stream"])
            self.assertIn("candidate_answer", request["messages"][1]["content"])
            return BytesIO(json.dumps({
                "message": {"content": json.dumps(payload)}
            }).encode("utf-8"))
        with patch("scripts.evaluate_semantic_verifier.urllib.request.urlopen",
                   side_effect=fake_open):
            self.assertEqual(json.loads(local_judge(self.case)), payload)

    def test_valid_supported_quote_stays_supported(self):
        response = {
            "verdict": "supported", "memory_id": 1,
            "quote": "opens at 9", "reason": "The weekday time is stated."
        }
        got = interpret(self.case, response)
        self.assertEqual(got["verdict"], "supported")
        self.assertTrue(got["valid_support_quote"])
        self.assertEqual(got["validation_issues"], [])

    def test_false_evidence_quote_abstains_with_raw_model_claim_preserved(self):
        response = {"verdict": "supported", "memory_id": 1,
                    "quote": "opens at 11", "reason": "Claimed support."}
        got = interpret(self.case, response)
        self.assertEqual(got["verdict"], "uncertain")
        self.assertEqual(got["raw_verdict"], "supported")
        self.assertIn("unsupported_evidence_quote", got["validation_issues"])

    def test_contradicted_answer_can_be_unsupported_with_valid_quote(self):
        response = {"verdict": "unsupported", "memory_id": 1,
                    "quote": "opens at 9", "reason": "A different time claimed."}
        got = interpret(self.case, response)
        self.assertEqual(got["verdict"], "unsupported")
        self.assertTrue(got["valid_support_quote"])

    def test_not_established_answer_may_lack_quote(self):
        got = interpret(self.case, {
            "verdict": "unsupported", "memory_id": 0, "quote": "",
            "reason": "No new value is given."
        })
        self.assertEqual(got["verdict"], "unsupported")
        self.assertEqual(got["validation_issues"], [])

    def test_invalid_json_does_not_invent_support(self):
        got = interpret(self.case, "{broken")
        self.assertEqual(got["verdict"], "uncertain")
        self.assertIn("invalid_json_object", got["validation_issues"])
        self.assertEqual(got["raw_model_response"], "{broken")

    def test_boolean_memory_id_is_not_valid_integer(self):
        got = interpret(self.case, {
            "verdict": "supported", "memory_id": True,
            "quote": "opens at 9", "reason": "A reason."
        })
        self.assertEqual(got["verdict"], "uncertain")
        self.assertIn("invalid_memory_id_type", got["validation_issues"])

    def test_input_unchanged_and_resume_without_rerunning_saved_cases(self):
        report = new_run(self.digest, "fake", "a" * 64)
        original = copy.deepcopy(self.case)
        calls = []
        def fake(case, model):
            calls.append(case["id"])
            return {"verdict": "uncertain", "memory_id": 0,
                    "quote": "", "reason": "Unsure."}
        saved = []
        n, ok = run_cases(self.dataset["cases"], report, model="fake",
                          limit=2, judge=fake,
                          save=lambda data: saved.append(copy.deepcopy(data)),
                          log=lambda _: None)
        self.assertEqual((n, ok), (2, True))
        n, ok = run_cases(self.dataset["cases"], report, model="fake",
                          limit=2, judge=fake,
                          save=lambda data: saved.append(copy.deepcopy(data)),
                          log=lambda _: None)
        self.assertEqual((n, ok), (2, True))
        self.assertEqual(len(calls), 4)
        self.assertEqual(self.case, original)
        self.assertEqual(len(saved), 4)

    def test_report_refuses_to_merge_different_models_and_signoffs(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "verifier.json"
            from scripts.review_eval_cases import save_review
            save_review(new_run(self.digest, "qwen", "a"*64), path)
            with self.assertRaisesRegex(ValueError, "refusing"):
                load_run(path, self.digest, "other", "a"*64, self.ids)
            with self.assertRaisesRegex(ValueError, "refusing"):
                load_run(path, self.digest, "qwen", "b"*64, self.ids)

    def test_comparison_records_deferrals_as_deferrals_not_true_predictions(self):
        labels = {
            case["id"]: (
                "uncertain" if i == 31 else
                "supported" if i < 9 else "unsupported"
            )
            for i, case in enumerate(self.dataset["cases"])
        }
        signoff = new_signoff(self.digest)
        for cid, label in labels.items():
            record_decision(signoff, cid, label,
                            "uncertain source" if label == "uncertain" else "",
                            self.ids)
        lock_signoff(signoff, self.ids)
        output = new_run(self.digest, "fake", "sha")
        for case in self.dataset["cases"]:
            output["answers"][case["id"]] = interpret(
                case, {"verdict": "uncertain", "memory_id": 0,
                       "quote": "", "reason": "Needs human review."}
            )
        result = compare(self.dataset, self.digest, signoff, output)
        self.assertEqual(result["semantic_counts"]["deferred_supported"], 9)
        self.assertEqual(result["semantic_counts"]["deferred_unsupported"], 22)
        self.assertEqual(result["semantic_counts"]["reviewer_uncertain"], 1)
        self.assertIn("NOT blind independent accuracy",
                      markdown(result, self.digest, "sig", "run"))

    def test_wrong_dataset_refused_in_comparison(self):
        with self.assertRaises((ValueError, KeyError)):
            compare(self.dataset, self.digest, {}, {"dataset_sha256": "wrong"})


if __name__ == "__main__":
    unittest.main()
