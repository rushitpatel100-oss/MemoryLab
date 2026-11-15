"""Offline tests for conservative local duplicate matching."""
import unittest

from memory_text import is_same_stored_fact, normalize_fact, normalize_topic


class MemoryTextTests(unittest.TestCase):
    def test_normalization_ignores_case_spacing_and_terminal_punctuation(self):
        self.assertEqual(
            normalize_fact("  I WORK  in   London! "),
            normalize_fact("i work in london."),
        )
        self.assertEqual(normalize_topic(" TEST_Location  "), "test_location")

    def test_different_facts_are_not_exact_duplicates(self):
        self.assertFalse(is_same_stored_fact(
            "location", "I live in York.", "location", "I work in London."
        ))

    def test_different_topics_do_not_match(self):
        self.assertFalse(is_same_stored_fact(
            "home", "I work in London.", "job", "I work in London."
        ))


if __name__ == "__main__":
    unittest.main()
