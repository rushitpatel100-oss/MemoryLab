"""Mocked tests for the two-stage Qwen comparison workflow."""
import io
import json
import unittest
from unittest.mock import patch

from memory_staged import classify_pair_staged, call_local_json


class StagedClassifierTests(unittest.TestCase):
    OLD = {"topic": "places", "fact": "I live in Aberdeen."}

    def test_normalized_duplicate_skips_model(self):
        def should_not_run(*_):
            self.fail("Duplicate should be handled locally")
        got = classify_pair_staged(
            self.OLD, "places", "  i LIVE in aberdeen! ",
            caller=should_not_run
        )
        self.assertEqual(got["relation"], "duplicate")
        self.assertEqual(got["source"], "local_rule")
        self.assertEqual(got["stages"], [])

    def test_independent_requires_only_first_stage(self):
        calls = []
        def responder(prompt, payload):
            calls.append((prompt, payload))
            return {"scope": "independent",
                    "reason": "Home and work are distinct."}
        got = classify_pair_staged(
            self.OLD, "places", "I work in Dundee.", caller=responder
        )
        self.assertEqual(got["relation"], "coexists")
        self.assertEqual(len(calls), 1)
        self.assertEqual(got["stages"][0]["scope"], "independent")

    def test_ambiguous_scope_returns_uncertain(self):
        got = classify_pair_staged(
            self.OLD, "places", "My friend moved away.",
            caller=lambda *_: {"scope": "unclear",
                               "reason": "Different person"}
        )
        self.assertEqual(got["relation"], "uncertain")
        self.assertEqual(len(got["stages"]), 1)

    def test_same_attribute_two_stages_can_replace(self):
        replies = iter([
            {"scope": "same_attribute", "reason": "Both describe home city."},
            {"relation": "replaces", "reason": "New city explicitly given."},
        ])
        calls = []
        def responder(prompt, payload):
            calls.append(payload)
            return next(replies)
        got = classify_pair_staged(
            self.OLD, "places", "I moved to Inverness.", caller=responder
        )
        self.assertEqual(got["relation"], "replaces")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], calls[1])

    def test_same_attribute_paraphrase_can_be_duplicate(self):
        answers = iter([
            {"scope": "same_attribute", "reason": "Same workplace."},
            {"relation": "duplicate", "reason": "Paraphrase of one job."},
        ])
        got = classify_pair_staged(
            {"topic": "work", "fact": "I am employed in Dundee."},
            "work", "My job is in Dundee.", caller=lambda *_: next(answers)
        )
        self.assertEqual(got["relation"], "duplicate")

    def test_unresolved_change_can_abstain(self):
        answers = iter([
            {"scope": "same_attribute", "reason": "Same meeting."},
            {"relation": "uncertain", "reason": "No new time specified."},
        ])
        got = classify_pair_staged(
            {"topic": "meeting", "fact": "My meeting starts at 2 PM."},
            "meeting", "The meeting time changed.",
            caller=lambda *_: next(answers)
        )
        self.assertEqual(got["relation"], "uncertain")

    def test_invalid_first_stage_abstains(self):
        got = classify_pair_staged(
            self.OLD, "places", "I work in Dundee.",
            caller=lambda *_: {"scope": "replaces", "reason": "Invalid"}
        )
        self.assertEqual(got["relation"], "uncertain")
        self.assertEqual(got["source"], "staged_fallback")

    def test_invalid_second_stage_abstains(self):
        answers = iter([
            {"scope": "same_attribute", "reason": "Same home city"},
            {"relation": "delete", "reason": "Invalid"},
        ])
        got = classify_pair_staged(
            self.OLD, "places", "I moved to Inverness.",
            caller=lambda *_: next(answers)
        )
        self.assertEqual(got["relation"], "uncertain")
        self.assertEqual(len(got["stages"]), 2)

    @patch("memory_staged.urllib.request.urlopen")
    def test_wire_payload_is_local_json(self, mocked):
        mocked.return_value = io.BytesIO(json.dumps({
            "message": {"content": json.dumps({
                "scope": "independent", "reason": "Different properties"
            })}
        }).encode())
        output = call_local_json("instructions", {"fictional": True})
        self.assertEqual(output["scope"], "independent")
        wire = json.loads(mocked.call_args.args[0].data.decode())
        self.assertEqual(wire["format"], "json")
        self.assertEqual(wire["options"]["temperature"], 0)


if __name__ == "__main__":
    unittest.main()
