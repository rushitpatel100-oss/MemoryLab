"""Offline regression tests for shared review-risk warnings."""
import unittest

from memory_review_safety import (
    duplicate_risk_signals, replacement_risk_signals,
    requires_confirmation, role_contrasts,
)


class MemoryReviewSafetyTests(unittest.TestCase):
    def test_rosemary_lavender_change_warns(self):
        warnings = duplicate_risk_signals(
            "My balcony planter contains rosemary.",
            "I replaced the rosemary in my balcony planter with lavender.",
        )
        self.assertTrue(any("change/cessation" in w for w in warnings))

    def test_away_jersey_warns_about_distinct_attribute(self):
        warnings = duplicate_risk_signals(
            "The cycling team's home jersey is navy.",
            "The away jersey was changed from navy to grey.",
        )
        self.assertTrue(any("home versus away" in w for w in warnings))

    def test_ordinary_paraphrase_generates_no_lexical_warnings(self):
        self.assertEqual(
            duplicate_risk_signals(
                "My dog Saffron enjoys swimming.",
                "Saffron, my dog, likes to swim.",
            ), []
        )

    def test_false_positive_caution_is_not_a_rejection(self):
        self.assertTrue(duplicate_risk_signals(
            "I moved to London yesterday.",
            "I moved to London yesterday.",
        ))
        # This warning is intentionally NOT a verdict of relation accuracy.

    def test_replacement_with_contrasting_qualifiers_warns(self):
        warnings = replacement_risk_signals(
            "The office printer uses blue toner.",
            "The basement printer changed to green toner.",
        )
        self.assertTrue(any("office versus basement" in w for w in warnings))

    def test_indefinite_role_needs_confirmation(self):
        warnings = replacement_risk_signals(
            "The nature club meets on Thursday.",
            "One of my clubs changed its meeting day.",
        )
        self.assertTrue(any("indefinite referent" in w for w in warnings))

    def test_any_ai_duplicate_requires_human_approval(self):
        self.assertTrue(requires_confirmation("duplicate", "qwen"))
        self.assertTrue(requires_confirmation("replaces", "qwen"))
        self.assertFalse(requires_confirmation("duplicate", "local_rule"))

    def test_other_case_and_token_boundaries(self):
        self.assertEqual(
            role_contrasts(
                "The HOME jersey is navy.",
                "The AWAY jersey is grey.",
            ), ["home versus away"]
        )
        self.assertEqual(
            role_contrasts(
                "There is a basement lab.",
                "The basement lab has four lights.",
            ), []
        )


if __name__ == "__main__":
    unittest.main()
