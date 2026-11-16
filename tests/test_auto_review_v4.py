"""Mock-only tests for contrastive evidence V4; no Ollama or SQLite."""
import copy
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from scripts.auto_review_v4 import (
    SCHEMA, blank_report, interpret, judge, label_from_axes,
    load_report, run,
)
from scripts.review_eval_cases import save_review
from scripts.review_holdout_v2 import load_local_cases


class ContrastiveReviewTests(unittest.TestCase):
    def setUp(self):
        self.cases, self.digest = load_local_cases()
        self.axes = {
            "same_entity": "yes", "same_attribute": "yes",
            "same_assertion": "yes", "old_fact_known_obsolete": "no",
            "new_value_known": "no",
        }
        self.payload = {
            "axes": dict(self.axes), "old_quote": "My dog Saffron enjoys swimming",
            "new_quote": "Saffron, my dog, likes to swim",
            "reason": "The same dog enjoys swimming in both statements.",
        }
        self.case = self.cases[1]

    def test_schema_requires_binary_assertion_and_obsolescence(self):
        attrs = SCHEMA["properties"]["axes"]["properties"]
        for key in ("same_assertion", "old_fact_known_obsolete",
                    "new_value_known"):
            self.assertEqual(attrs[key]["enum"], ["yes", "no"])
        self.assertEqual(attrs["same_entity"]["enum"], ["yes", "no", "unknown"])

    def test_prompt_and_schema_reach_local_ollama(self):
        def fake_urlopen(request, timeout):
            body = json.loads(request.data)
            self.assertEqual(body["format"], SCHEMA)
            self.assertFalse(body["stream"])
            return BytesIO(json.dumps(
                {"message": {"content": json.dumps(self.payload)}}
            ).encode())
        with patch("scripts.auto_review_v4.urllib.request.urlopen",
                   side_effect=fake_urlopen):
            raw = judge(self.case)
        self.assertEqual(json.loads(raw), self.payload)

    def test_duplicate_can_be_inferred(self):
        result = interpret(self.case, json.dumps(self.payload))
        self.assertEqual(result["provisional_label"], "duplicate")
        self.assertEqual(result["safe_storage_action"], "skip_duplicate")
        self.assertEqual(result["triage"], "draft")

    def test_supported_replacement_never_automatically_applies(self):
        axes = dict(self.axes, same_assertion="no",
                    old_fact_known_obsolete="yes", new_value_known="yes")
        case = {
            "id": "X", "topic": "schedule",
            "old_fact": "The meeting starts at 5 pm.",
            "new_fact": "The meeting moved from 5 pm to 6 pm.",
        }
        response = {"axes": axes, "old_quote": "starts at 5",
                    "new_quote": "moved from 5 pm to 6 pm",
                    "reason": "The time changed."}
        result = interpret(case, response)
        self.assertEqual(result["provisional_label"], "replaces")
        self.assertEqual(result["safe_storage_action"], "review_needed")
        self.assertEqual(result["triage"], "needs_review")

    def test_clear_different_attributes_can_coexist(self):
        axes = dict(self.axes, same_assertion="no", same_attribute="no",
                    old_fact_known_obsolete="no")
        case = {
            "id": "X", "topic": "bag",
            "old_fact": "My bag has a gold zip.",
            "new_fact": "My bag contains a blue pen.",
        }
        payload = {"axes": axes, "old_quote": "gold zip",
                   "new_quote": "blue pen", "reason": "Separate properties."}
        self.assertEqual(interpret(case, payload)["provisional_label"], "coexists")

    def test_indefinite_referent_cannot_prove_supersession(self):
        case = {
            "id": "X", "topic": "clubs",
            "old_fact": "The science club meets at noon.",
            "new_fact": "One of my clubs changed its time.",
        }
        axes = dict(self.axes, same_assertion="no",
                    old_fact_known_obsolete="yes")
        result = interpret(case, {
            "axes": axes, "old_quote": "science club",
            "new_quote": "One of my clubs",
            "reason": "Ambiguous club."
        })
        self.assertEqual(result["provisional_label"], "uncertain")

    def test_unquoted_evidence_cannot_create_confident_label(self):
        payload = dict(self.payload, new_quote="imagined text")
        result = interpret(self.case, payload)
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertEqual(result["safe_storage_action"], "review_needed")

    def test_malformed_output_records_raw_reply_and_abstains(self):
        result = interpret(self.case, "{not JSON}")
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertEqual(result["raw_model_response"], "{not JSON}")
        self.assertTrue(any("JSON" in flag for flag in result["flags"]))

    def test_invalid_forced_binary_value_is_not_treated_as_no_without_flag(self):
        result = interpret(self.case, {
            **self.payload,
            "axes": dict(self.axes, same_assertion="unknown"),
        })
        self.assertEqual(result["provisional_label"], "uncertain")
        self.assertIn("Invalid/missing axis: same_assertion", result["flags"])

    def test_resume_and_do_not_touch_existing_entries(self):
        calls = []
        saves = []
        def fake(case, model):
            calls.append(case["id"])
            return json.dumps(self.payload)
        data = blank_report(self.digest, "qwen2.5:1.5b")
        count, ok = run(self.cases, data, limit=2, judge_fn=fake,
                        save_fn=lambda d: saves.append(copy.deepcopy(d)),
                        output_fn=lambda _: None)
        self.assertEqual((count, ok), (2, True))
        count, ok = run(self.cases, data, limit=2, judge_fn=fake,
                        save_fn=lambda d: saves.append(copy.deepcopy(d)),
                        output_fn=lambda _: None)
        self.assertEqual((count, ok), (2, True))
        self.assertEqual(calls, [c["id"] for c in self.cases[:4]])
        self.assertEqual(len(saves), 4)

    def test_different_model_refuses_existing_report(self):
        report = blank_report(self.digest, "qwen2.5:1.5b")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "output.json"
            save_review(report, path)
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                load_report(path, self.digest, "other", {c["id"] for c in self.cases})


if __name__ == "__main__":
    unittest.main()
