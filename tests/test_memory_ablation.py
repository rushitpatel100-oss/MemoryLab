"""Offline tests for the two-call memory-impact pilot."""

import unittest
from unittest.mock import patch

from memory_ablation import run_memory_comparison


class MemoryComparisonTests(unittest.TestCase):
    def setUp(self):
        self.memory = {
            "id": 4,
            "topic": "hobby",
            "fact": "My favourite hobby is photography.",
        }

    @patch("memory_ablation.generate_answer")
    def test_calls_model_in_both_conditions(self, mocked_generator):
        mocked_generator.side_effect = [
            "No information available.",
            "Photography. [M4]",
        ]

        result = run_memory_comparison(
            "What hobby do I enjoy?", self.memory
        )

        self.assertEqual(mocked_generator.call_count, 2)
        calls = mocked_generator.call_args_list
        self.assertEqual(calls[0].args[1], [])
        self.assertEqual(calls[1].args[1], [self.memory])
        self.assertTrue(calls[0].kwargs["allow_empty_context"])
        self.assertTrue(calls[1].kwargs["allow_empty_context"])
        self.assertEqual(
            result["with_memory"]["answer"], "Photography. [M4]"
        )
        self.assertEqual(
            result["without_memory"]["answer"], "No information available."
        )

    @patch("memory_ablation.generate_answer")
    def test_blank_question_does_not_call_model(self, mocked_generator):
        with self.assertRaises(ValueError):
            run_memory_comparison(" ", self.memory)
        mocked_generator.assert_not_called()

    @patch("memory_ablation.generate_answer")
    def test_invalid_memory_does_not_call_model(self, mocked_generator):
        with self.assertRaises(ValueError):
            run_memory_comparison("What hobby?", {"topic": "hobby"})
        mocked_generator.assert_not_called()


if __name__ == "__main__":
    unittest.main()
