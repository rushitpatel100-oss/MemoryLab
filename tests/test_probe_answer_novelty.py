"""Phase 12 lexical novelty probe: offline, source-traceable unit tests."""
import copy
import unittest

from answer_generator import NO_MEMORY_ANSWER
from scripts.probe_answer_novelty import (
    check_answer, inspect_run, markdown, words
)
from scripts.evaluate_downstream_memory import load_dataset


class AnswerNoveltyProbeTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"id": 1, "topic": "committee", "fact": "The art committee meets on Friday."},
            {"id": 2, "topic": "committee",
             "fact": "One of my committees changed its meeting day."},
        ]

    def test_novel_day_in_specific_answer_flags(self):
        finding = check_answer(
            "What is the new meeting day?", "It is Monday.", self.records
        )
        self.assertEqual(finding["status"], "unsupported_weekday")
        self.assertEqual(finding["unsupported_weekdays"], ["monday"])

    def test_question_mention_does_not_license_an_unseen_weekday(self):
        finding = check_answer(
            "Did it move to Monday?", "It moved to Monday.", self.records
        )
        self.assertEqual(finding["status"], "unsupported_weekday")

    def test_existing_day_does_not_prove_temporal_relevance(self):
        finding = check_answer(
            "What is the NEW day?", "Friday.", self.records
        )
        self.assertEqual(finding["status"], "no_obvious_lexical_novelty")
        # The tool deliberately does not infer old/new entailment.

    def test_blue_one_paraphrase_keeps_evidence_word(self):
        outcome = check_answer(
            "Which telescope is at the club?",
            "Based on the memory records provided, the blue one.",
            [{"id": 4, "topic": "club",
              "fact": "The club has a blue telescope."}]
        )
        self.assertEqual(outcome["status"], "no_obvious_lexical_novelty")
        self.assertEqual(outcome["unsupported_numbers"], [])

    def test_weekday_plural_and_number_word_normalization(self):
        self.assertIn("thursday", words("Thursdays"))
        self.assertIn("10", words("ten"))
        self.assertIn("10", words("10"))

    def test_unknown_number_is_flagged(self):
        finding = check_answer(
            "At what time?", "It starts at 9.",
            [{"id": 1, "fact": "The event begins at 8."}]
        )
        self.assertEqual(finding["status"], "unsupported_number")

    def test_nonexistent_citation_is_flagged(self):
        finding = check_answer(
            "What colour?", "blue [M99]",
            [{"id": 1, "fact": "The kite is blue."}]
        )
        self.assertEqual(finding["status"], "invalid_citation")

    def test_abstention_preserved(self):
        result = check_answer("What day?", NO_MEMORY_ANSWER, self.records)
        self.assertEqual(result["status"], "abstained")

    def test_requires_selected_records_and_question_text(self):
        with self.assertRaises(ValueError):
            check_answer("Question", "Answer", [{"id": "x", "fact": "A fact"}])

    def test_original_data_not_modified(self):
        old = copy.deepcopy(self.records)
        check_answer("What day?", "Friday [M1]", self.records)
        self.assertEqual(self.records, old)

    def test_report_labels_screening_not_verified_accuracy(self):
        content = markdown({
            "total_questions": 1,
            "counts": {"unsupported_weekday": 1},
            "rows": [{"id": "P01/Q1", "status": "unsupported_weekday",
                      "novel_terms": ["monday"], "answer": "Monday"}],
        }, "f" * 64)
        self.assertIn("Not independent accuracy", content)
        self.assertIn("NOT a semantic entailment check", content)


if __name__ == "__main__":
    unittest.main()
