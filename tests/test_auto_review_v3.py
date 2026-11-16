"""Offline tests of the evidence-first Phase 9 reviewer."""
import copy
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from scripts.auto_review_v3 import (
    SCHEMA, classify_from_evidence, exact_quote, interpret,
    judge_evidence, load_report, new_report, role_conflict, run,
)
from scripts.review_holdout_v2 import load_local_cases
from scripts.review_eval_cases import save_review


class EvidenceFirstReviewTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.ex = {
            "axes": {
                "same_entity": "yes", "same_attribute": "yes",
                "same_assertion": "yes",
                "old_fact_known_obsolete": "no",
                "new_value_known": "no",
            },
            "old_evidence": "My dog Saffron enjoys swimming",
            "new_evidence": "Saffron, my dog, likes to swim",
            "explanation": "These describe the same dog's swimming preference.",
        }
        self.case = self.cases[1]

    def test_schema_has_enum_for_every_evidence_dimension(self):
        names = SCHEMA["properties"]["axes"]["required"]
        self.assertIn("same_assertion", names)
        self.assertEqual(len(names), 5)
        self.assertEqual(SCHEMA["properties"]["old_evidence"]["type"], "string")

    def test_json_schema_is_supplied_to_ollama(self):
        def fake_open(request, timeout):
            payload = json.loads(request.data)
            self.assertEqual(payload["format"], SCHEMA)
            self.assertFalse(payload["stream"])
            return BytesIO(json.dumps({
                "message": {"content": json.dumps(self.ex)}
            }).encode("utf-8"))
        with patch("scripts.auto_review_v3.urllib.request.urlopen",
                   side_effect=fake_open):
            self.assertEqual(judge_evidence(self.case), self.ex)

    def test_paraphrase_can_be_duplicate(self):
        result = interpret(self.case, self.ex)
        self.assertEqual(result["provisional_label"], "duplicate")
        self.assertEqual(result["safe_storage_action"], "skip_duplicate")
        self.assertEqual(result["triage"], "draft")

    def test_replacement_requires_explicit_obsolescence(self):
        axes = copy.deepcopy(self.ex["axes"])
        axes["same_assertion"] = "no"
        axes["old_fact_known_obsolete"] = "yes"
        self.assertEqual(classify_from_evidence(axes), "replaces")
        axes["old_fact_known_obsolete"] = "unknown"
        self.assertEqual(classify_from_evidence(axes), "uncertain")

    def test_separate_properties_are_coexistence(self):
        axes = dict(self.ex["axes"], same_attribute="no", same_assertion="no")
        self.assertEqual(classify_from_evidence(axes), "coexists")

    def test_mismatched_role_cues_flag_prevent_supersession(self):
        self.assertIn(
            "home versus away",
            role_conflict("The home's jersey is navy.",
                          "The away jersey is grey.")
        )
        case = {
            "id": "X", "topic": "team",
            "old_fact": "The home jersey is navy.",
            "new_fact": "The away jersey changed to grey.",
        }
        response = {
            "axes": dict(self.ex["axes"], same_assertion="no",
                         old_fact_known_obsolete="yes"),
            "old_evidence": "home jersey",
            "new_evidence": "away jersey",
            "explanation": "New color",
        }
        result = interpret(case, response)
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertEqual(result["safe_storage_action"], "review_needed")

    def test_missing_quote_results_in_uncertain(self):
        response = dict(self.ex, old_evidence="invented quote")
        result = interpret(self.case, response)
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertIn("Old evidence quote", " ".join(result["flags"]))

    def test_malformed_model_output_never_authorizes_supersession(self):
        result = interpret(self.case, {"axes": {"same_entity": []}})
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertEqual(result["safe_storage_action"], "review_needed")

    def test_run_resumes_without_overwriting(self):
        report = new_report(self.digest, "qwen2.5:1.5b")
        saved = []
        calls = []
        def fake_judge(case, model):
            calls.append(case["id"])
            return None
        x, ok = run(self.cases, report, limit=3, judge=fake_judge,
                    save_fn=lambda data: saved.append(copy.deepcopy(data)),
                    output_fn=lambda _: None)
        self.assertEqual((x, ok), (3, True))
        x, ok = run(self.cases, report, limit=2, judge=fake_judge,
                    save_fn=lambda data: saved.append(copy.deepcopy(data)),
                    output_fn=lambda _: None)
        self.assertEqual((x, ok), (2, True))
        self.assertEqual(calls, [c["id"] for c in self.cases[:5]])
        self.assertEqual(len(saved), 5)

    def test_report_refuses_model_change(self):
        report = new_report(self.digest, "qwen2.5:1.5b")
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "v3.json"
            save_review(report, path)
            with self.assertRaisesRegex(ValueError, "mismatch"):
                load_report(path, self.digest, "other-model",
                            {c["id"] for c in self.cases})


if __name__ == "__main__":
    unittest.main()
