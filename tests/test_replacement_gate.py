"""Offline tests for the cautious replacement-evidence gate."""
import unittest

from replacement_gate import (
    apply_replacement_gate,
    classify_pair_guarded,
    replacement_evidence,
)


class ReplacementEvidenceTests(unittest.TestCase):
    def test_explicit_move_is_a_signal_not_a_verification(self):
        found = replacement_evidence(
            "I currently live in Bristol.",
            "I have moved from Bristol to York.",
        )
        self.assertEqual(found["status"], "transition_signal")
        self.assertIn("Confirm subject and attribute", found["reason"])

    def test_explicit_bicycle_colour_change(self):
        found = replacement_evidence(
            "My bicycle is red.", "I repainted my bicycle from red to blue."
        )
        self.assertEqual(found["status"], "transition_signal")

    def test_independent_work_is_not_a_replacement_signal(self):
        found = replacement_evidence(
            "I have moved from Bristol to York.", "I work in London."
        )
        self.assertEqual(found["status"], "needs_review")

    def test_unnamed_referent_is_not_a_replacement_signal(self):
        found = replacement_evidence(
            "My aunt Farah works at a hospital.",
            "My aunt changed jobs last week.",
        )
        self.assertEqual(found["status"], "needs_review")

    def test_unmatched_old_value_does_not_authorize_replacement(self):
        found = replacement_evidence(
            "I currently live in Bristol.", "I moved from London to York."
        )
        self.assertEqual(found["status"], "needs_review")

    def test_change_without_new_value_requires_review(self):
        found = replacement_evidence(
            "Our meeting is on Tuesday.", "The meeting date changed."
        )
        self.assertEqual(found["status"], "needs_review")

    def test_gate_downgrades_unverified_qwen_replacement(self):
        old = {"topic": "location", "fact": "I live in York."}
        result = apply_replacement_gate(
            old, "I work in London.",
            {"relation": "replaces", "reason": "Qwen assumed new location",
             "source": "qwen"},
        )
        self.assertEqual(result["relation"], "uncertain")
        self.assertEqual(result["raw_relation"], "replaces")
        self.assertEqual(result["gate"]["status"], "needs_review")

    def test_gate_leaves_explicit_transition_as_suggestion(self):
        result = apply_replacement_gate(
            {"topic": "location", "fact": "I currently live in Bristol."},
            "I moved from Bristol to York.",
            {"relation": "replaces", "reason": "A move was stated."},
        )
        self.assertEqual(result["relation"], "replaces")
        self.assertEqual(result["gate"]["status"], "transition_signal")

    def test_gate_leaves_nonreplacement_classifications_unchanged(self):
        result = apply_replacement_gate(
            {"topic": "job", "fact": "I work in London."},
            "I teach art.",
            {"relation": "coexists", "reason": "Both can be true."},
        )
        self.assertEqual(result["relation"], "coexists")
        self.assertEqual(result["gate"]["status"], "not_applicable")

    def test_guarded_classifier_calls_underlying_model_only_once(self):
        calls = []
        def fake_classifier(old, topic, new):
            calls.append((old, topic, new))
            return {"relation": "replaces", "reason": "Update"}
        result = classify_pair_guarded(
            {"topic": "role", "fact": "I work as a designer."},
            "role", "I volunteer as a coach.",
            classifier=fake_classifier,
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["relation"], "uncertain")


if __name__ == "__main__":
    unittest.main()
